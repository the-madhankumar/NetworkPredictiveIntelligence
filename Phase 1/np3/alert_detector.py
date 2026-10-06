import logging
from pathlib import Path

import pandas as pd


logger = logging.getLogger(__name__)


class AlertDetector:

    def __init__(
        self,
        grid_hourly,
        activity_floor=100,
        spike_ratio=1.5,
        drop_ratio=0.5,
        high_activity_ratio=1.5
    ):
        self.grid_hourly = grid_hourly.copy()

        self.activity_floor = activity_floor
        self.spike_ratio = spike_ratio
        self.drop_ratio = drop_ratio
        self.high_activity_ratio = high_activity_ratio

        self.daily_totals = None
        self.alerts_df = None

        logger.info(
            "AlertDetector initialized with %d grid-hour records",
            len(self.grid_hourly)
        )

    @staticmethod
    def leave_out_one_median(values):
        values = values.reset_index(drop=True)

        result = []

        for index in range(len(values)):
            remaining_values = values.drop(index)

            if len(remaining_values) == 0:
                result.append(pd.NA)
            else:
                result.append(remaining_values.median())

        return pd.Series(result, index=values.index)

    def calculate_daily_activity(self):
        """
        Calculate total daily activity for each grid.
        """

        self.daily_totals = (
            self.grid_hourly
            .groupby(
                ["date", "grid_id"],
                as_index=False
            )["total_activity"]
            .sum()
            .rename(
                columns={
                    "total_activity": "daily_total_activity"
                }
            )
        )

        self.grid_hourly = self.grid_hourly.merge(
            self.daily_totals,
            on=["date", "grid_id"],
            how="left"
        )

        logger.info(
            "Daily activity calculated for %d grid-days",
            len(self.daily_totals)
        )

        return self.grid_hourly

    def calculate_baseline(self):
        """
        Calculate leave-one-out median baseline for each grid/day.
        """

        self.grid_hourly = self.grid_hourly.sort_values(
            ["grid_id", "date"]
        ).reset_index(drop=True)

        self.grid_hourly["baseline_activity"] = (
            self.grid_hourly
            .groupby(["date", "grid_id"])["total_activity"]
            .transform(self.leave_out_one_median)
        )

        self.grid_hourly["previous_activity"] = (
            self.grid_hourly
            .groupby(["date", "grid_id"])["total_activity"]
            .shift(1)
        )

        logger.info("Within-day activity baseline calculated")

        return self.grid_hourly

    def apply_alert_rules(self):
        """
        Apply HIGH_ACTIVITY, ACTIVITY_SPIKE and ACTIVITY_DROP rules.
        """

        alerts = []

        eligible_mask = (
            self.grid_hourly["total_activity"]
            >= self.activity_floor
        )

        logger.info(
            "Activity floor: %s",
            self.activity_floor
        )

        logger.info(
            "Eligible grid-hours: %d",
            eligible_mask.sum()
        )

        for index, row in self.grid_hourly.iterrows():

            if not eligible_mask.iloc[index]:
                continue

            current_activity = row["total_activity"]
            baseline_activity = row["baseline_activity"]
            previous_activity = row["previous_activity"]

            grid_id = row["grid_id"]
            timestamp = row["date"]

            # Avoid division by zero / missing baseline
            if (
                pd.isna(baseline_activity)
                or baseline_activity == 0
            ):
                continue

            # HIGH_ACTIVITY
            if (
                current_activity
                >= self.high_activity_ratio * baseline_activity
            ):
                alerts.append({
                    "grid_id": grid_id,
                    "timestamp": timestamp,
                    "alert_type": "HIGH_ACTIVITY",
                    "current_activity": current_activity,
                    "baseline_activity": baseline_activity,
                    "reason": (
                        f"Current activity is "
                        f"{current_activity / baseline_activity:.2f}x "
                        f"the within-day baseline"
                    )
                })

            # ACTIVITY_SPIKE
            if (
                pd.notna(previous_activity)
                and previous_activity > 0
                and current_activity
                >= self.spike_ratio * previous_activity
            ):
                alerts.append({
                    "grid_id": grid_id,
                    "timestamp": timestamp,
                    "alert_type": "ACTIVITY_SPIKE",
                    "current_activity": current_activity,
                    "baseline_activity": baseline_activity,
                    "reason": (
                        f"Current activity is "
                        f"{current_activity / previous_activity:.2f}x "
                        f"the previous hour"
                    )
                })

            # ACTIVITY_DROP
            if (
                current_activity
                <= self.drop_ratio * baseline_activity
            ):
                alerts.append({
                    "grid_id": grid_id,
                    "timestamp": timestamp,
                    "alert_type": "ACTIVITY_DROP",
                    "current_activity": current_activity,
                    "baseline_activity": baseline_activity,
                    "reason": (
                        f"Current activity is "
                        f"{current_activity / baseline_activity:.2f}x "
                        f"the within-day baseline"
                    )
                })

        self.alerts_df = pd.DataFrame(
            alerts,
            columns=[
                "grid_id",
                "timestamp",
                "alert_type",
                "current_activity",
                "baseline_activity",
                "reason"
            ]
        )

        logger.info(
            "Alert rules applied. Total alerts: %d",
            len(self.alerts_df)
        )

        return self.alerts_df

    def export_alerts(self, output_path):
        output_path = Path(output_path)
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.alerts_df.to_csv(
            output_path,
            index=False
        )

        logger.info(
            "Alerts exported to %s",
            output_path
        )

    def operational_summary(self):
        """
        Generate short operational alert summary.
        """

        if self.alerts_df is None:
            raise ValueError(
                "Run apply_alert_rules() before operational_summary()"
            )

        if self.alerts_df.empty:
            logger.info("No alerts generated")

            return {
                "alerts_by_type": {},
                "top_10_grids": {},
                "alert_proportion": 0
            }

        alerts_by_type = (
            self.alerts_df["alert_type"]
            .value_counts()
            .to_dict()
        )

        top_10_grids = (
            self.alerts_df["grid_id"]
            .value_counts()
            .head(10)
            .to_dict()
        )

        total_grid_hours = len(self.grid_hourly)

        alerted_grid_hours = (
            self.alerts_df[
                ["grid_id", "timestamp"]
            ]
            .drop_duplicates()
            .shape[0]
        )

        alert_proportion = (
            alerted_grid_hours / total_grid_hours
            if total_grid_hours > 0
            else 0
        )

        summary = {
            "alerts_by_type": alerts_by_type,
            "top_10_grids": top_10_grids,
            "alert_proportion": alert_proportion
        }

        logger.info(
            "Alerts by type: %s",
            alerts_by_type
        )

        logger.info(
            "Top 10 grids by alert count: %s",
            top_10_grids
        )

        logger.info(
            "Alert proportion: %.2f%%",
            alert_proportion * 100
        )

        return summary

    def limitations(self):
        """
        Return baseline limitations and false-positive explanation.
        """

        return """
            The rule-based baseline identifies unusual activity relative
            to the same grid's activity during the same day. It does not
            determine the cause of the unusual activity.

            Possible false positives include planned events, holidays,
            maintenance activity, temporary traffic shifts, changes in
            customer behaviour, or other legitimate network events.

            The activity-only baseline cannot distinguish between a genuine
            network fault, a planned event, unusual customer behaviour,
            a special event, or a data-quality issue.

            It also does not use weather, outages, alarms, topology,
            network configuration, customer segments, historical days,
            or external events. Therefore, an alert is an investigation
            signal and not a diagnosis.
        """
    
if __name__ == "__main__":

    # Load NP2 output
    grid_hourly = pd.read_csv("../dataset/landing/grid_hourly.csv")

    # Convert columns
    grid_hourly["date"] = pd.to_datetime(
        grid_hourly["date"],
        errors="coerce"
    )

    grid_hourly["timestamp"] = (
        grid_hourly["date"]
        + pd.to_timedelta(grid_hourly["hour"], unit="h")
    )

    # Create detector
    detector = AlertDetector(grid_hourly)

    # Calculate daily activity
    detector.calculate_daily_activity()

    # Calculate baseline
    detector.calculate_baseline()

    # Apply rules
    alerts = detector.apply_alert_rules()

    # Show alerts
    print("\n" + "=" * 60)
    print("GENERATED ALERTS")
    print("=" * 60)

    if alerts.empty:
        print("No alerts generated.")
    else:
        print(alerts.to_string(index=False))

    # Export
    detector.export_alerts(
        "../data/landing/alerts.csv"
    )

    # Summary
    summary = detector.operational_summary()

    print("\n" + "=" * 60)
    print("OPERATIONAL SUMMARY")
    print("=" * 60)

    print("\nAlerts by type:")
    print(summary["alerts_by_type"])

    print("\nTop 10 grids:")
    print(summary["top_10_grids"])

    print(
        "\nAlert proportion:",
        f"{summary['alert_proportion']:.2%}"
    )

    # Limitations
    print("\n" + "=" * 60)
    print("BASELINE LIMITATIONS")
    print("=" * 60)

    print(detector.limitations())