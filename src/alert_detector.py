import logging
import numpy as np
import pandas as pd

logging.basicConfig(
    filename = "../log/alert_detector.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


class AlertDetector:
    def __init__(
                self, 
                df,
                activity_floor = 100,
                spike_ratio = 1.5,
                high_activity_ratio = 1.5,
                drop_ratio = 0.5
            ):
        self.df = df
        self.activity_floor = activity_floor
        self.spike_ratio = spike_ratio
        self.high_activity_ratio = high_activity_ratio
        self.drop_ratio = drop_ratio

        self.alerts = None

        logger.info("Dataframe loaded")

    def validate_input(self):
        required_cols = [
            "grid_id",
            "date",
            "hour",
            "total_activity"
        ]

        missing = []
        dataframe_cols = df.columns.tolist()
        for col in required_cols:
            if col not in dataframe_cols:
                missing.append(col)

        if len(missing) == 0:
            logger.info("No missing columns")
        else:
            logger.error(f"Missing Columns {missing}")

    def prepare_timestamp(self):
        self.df["timestamp"] = pd.to_datetime(
            self.df["date"].astype(str) + " " + self.df["hour"].astype(str) + ":00:00"
        )

        self.df["day"] = self.df["timestamp"].dt.date

        logger.info("Added timestamp by combining date and hour")

    def calculate_daily_activity(self):
        self.df["daily_total_activity"] = (
            self.df.groupby(
                ["grid_id", self.df["timestamp"].dt.date]
            )["total_activity"]
            .transform("sum")
        )

        logger.info("Daily total activity created")

    def select_activity_floor(self):
        floor_percentile = 0.10

        self.activity_floor = self.df["total_activity"].quantile(
            floor_percentile
        )

        self.floor_percentile = floor_percentile * 100
        self.floor_reason = (
            "Activity floor is set at the 10th percentile of hourly "
            "total activity to identify unusually low-activity periods."
        )

        logger.info(
            f"Activity floor selected: {self.activity_floor:.2f} "
            f"(P{self.floor_percentile:.0f})"
        )

    def calculate_baseline(self):
        self.df["baseline_activity"] = np.nan

        for (grid_id, day), group in self.df.groupby(
            ["grid_id", "day"]
        ):
            values = group["total_activity"].to_numpy()

            baselines = []

            for i in range(len(values)):
                other_values = np.delete(values, i)

                if len(other_values) == 0:
                    baselines.append(np.nan)
                else:
                    baselines.append(np.median(other_values))

            self.df.loc[group.index, "baseline"] = baselines

        logger.info(
            f"Calculate baseline after Columns: "
            f"{self.df.columns.tolist()}"
        )

        logger.info("Baseline activity calculated")

    def calculate_previous_activity(self):
        logger.info(f"Previous Activity Columns: {self.df.columns}")
        self.updated_df = self.df.sort_values(
            ["grid_id", "day", "hour"]
        )

        self.df["previous_activity"] = (
            self.updated_df.groupby("grid_id")["total_activity"].shift(1)
        )

        logger.info("Previous activity calculated")

    def calculate_activity_ratios(self):
        self.df["baseline_ratio"] = (
            self.df["total_activity"]
            / self.df["baseline"].replace(0, np.nan)
        )

        self.df["previous_hour_ratio"] = (
            self.df["total_activity"]
            / self.df["previous_activity"].replace(0, np.nan)
        )

        logger.info("Activity ratios calculated")

    def apply_alert_rules(self):
        valid_activity = (
            self.df["total_activity"] >= self.activity_floor
        )

        ignored = (~valid_activity).sum()

        logger.info(
            f"Activity floor: {self.activity_floor:.2f}. "
            f"Ignored {ignored} low-activity grid-hours."
        )

        self.df["high_activity"] = (
            valid_activity
            & self.df["baseline"].notna()
            & (
                self.df["total_activity"]
                >= self.high_activity_ratio * self.df["baseline"]
            )
        )

        self.df["activity_spike"] = (
            valid_activity
            & self.df["previous_activity"].notna()
            & (
                self.df["total_activity"]
                >= self.spike_ratio * self.df["previous_activity"]
            )
        )

        self.df["activity_drop"] = (
            valid_activity
            & self.df["baseline"].notna()
            & (
                self.df["total_activity"]
                <= self.drop_ratio * self.df["baseline"]
            )
        )

        logger.info("Alert rules applied")

    def generate_alert_record(self):
        alerts = []

        for _, row in self.df.iterrows():

            # HIGH_ACTIVITY
            if row["high_activity"]:
                alerts.append({
                    "grid_id": row["grid_id"],
                    "timestamp": row["timestamp"],
                    "alert_type": "HIGH_ACTIVITY",
                    "current_activity": row["total_activity"],
                    "baseline_activity": row["baseline"],
                    "reason": (
                        f"Current activity is "
                        f"{row['baseline_ratio']:.2f}x "
                        f"the within-day baseline"
                    ),
                })

            # ACTIVITY_SPIKE
            if row["activity_spike"]:
                alerts.append({
                    "grid_id": row["grid_id"],
                    "timestamp": row["timestamp"],
                    "alert_type": "ACTIVITY_SPIKE",
                    "current_activity": row["total_activity"],
                    "baseline_activity": row["baseline"],
                    "reason": (
                        f"Current activity is "
                        f"{row['previous_hour_ratio']:.2f}x "
                        f"the previous hour"
                    ),
                })

            # ACTIVITY_DROP
            if row["activity_drop"]:
                alerts.append({
                    "grid_id": row["grid_id"],
                    "timestamp": row["timestamp"],
                    "alert_type": "ACTIVITY_DROP",
                    "current_activity": row["total_activity"],
                    "baseline_activity": row["baseline"],
                    "reason": (
                        f"Current activity is "
                        f"{row['baseline_ratio']:.2f}x "
                        f"the within-day baseline"
                    ),
                })

        self.alerts = pd.DataFrame(alerts)

        logger.info(
            f"Generated {len(self.alerts)} alert records"
        )

        logger.info("Alert detection summary:")
        logger.info(
            "  HIGH_ACTIVITY  : %d",
            self.df["high_activity"].sum()
        )
        logger.info(
            "  ACTIVITY_SPIKE : %d",
            self.df["activity_spike"].sum()
        )
        logger.info(
            "  ACTIVITY_DROP  : %d",
            self.df["activity_drop"].sum()
        )
        logger.info(
            "  Alert Proportion: %.2f%%",
            (len(self.alerts) / len(self.df) * 100)
            if len(self.df) > 0
            else 0
        )

        return self.alerts

    def export(self, path):
        self.alerts.to_csv(path, index=False)
        logger.info(f"Exported as csv to the file path {path} of rows {self.alerts.shape[0]}")

if __name__ == "__main__":
    df = pd.read_csv("../Dataset/landing/grid_hourly.csv")

    alert_dectector = AlertDetector(df)
    alert_dectector.validate_input()

    alert_dectector.prepare_timestamp()
    alert_dectector.calculate_daily_activity()

    alert_dectector.calculate_baseline()
    alert_dectector.calculate_previous_activity()

    alert_dectector.calculate_activity_ratios()
    alert_dectector.apply_alert_rules()

    alert_dectector.generate_alert_record()

    export_file_path = "../Dataset/landing/alerts.csv"
    alert_dectector.export(path=export_file_path)