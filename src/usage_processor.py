import logging

from pathlib import Path

import pandas as pd

from pathlib import Path

import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger(__name__)


class UsageProcessor:
    REQUIRED_COLUMNS = [
        "datetime",
        "CellID",
        "countrycode",
        "smsin",
        "smsout",
        "callin",
        "callout",
        "internet"
    ]

    CANONICAL_MAPPING = {
        "datetime": "timestamp",
        "CellID": "grid_id",
        "countrycode": "country_code",
        "smsin": "sms_in",
        "smsout": "sms_out",
        "callin": "call_in",
        "callout": "call_out",
        "internet": "internet_activity"
    }

    ACTIVITY_COLUMNS = [
        "sms_in",
        "sms_out",
        "call_in",
        "call_out",
        "internet_activity"
    ]

    def __init__(self, file_path=None, df=None):
        logger.info("Initializing UsageProcessor.")

        if file_path is None and df is None:
            logger.error(
                "Initialization failed: neither file_path nor df was provided."
            )
            raise ValueError(
                "Either file_path or df must be provided."
            )

        if file_path is not None and df is not None:
            logger.error(
                "Initialization failed: both file_path and df were provided."
            )
            raise ValueError(
                "Provide either file_path or df, not both."
            )

        self.file_path = file_path
        self.raw_df = None
        self.canonical_df = None
        self.analytics_df = None
        self.daily_summary = None
        self.grid_summary = None
        self.rows_loaded = 0
        self.rows_rejected = 0
        self.nulls_handled = 0

        if df is not None:
            self.raw_df = df.copy()
            logger.info(
                "DataFrame supplied directly. Rows: %d",
                len(self.raw_df)
            )

    def load_data(self):
        logger.info("Starting data loading.")

        if self.raw_df is not None:
            logger.info(
                "DataFrame supplied directly. Rows: %d",
                len(self.raw_df)
            )
            logger.info("Data loading completed.")
            return self.raw_df

        if self.file_path is None:
            logger.error("No input file provided.")
            raise ValueError("No input file provided.")

        path = Path(self.file_path)

        logger.info("Checking input file: %s", path)

        if not path.exists():
            logger.error(
                "Input file not found: %s",
                path
            )
            raise FileNotFoundError(
                f"Input file not found: {path}"
            )

        logger.info("Reading input CSV file.")

        self.raw_df = pd.read_csv(path)

        self.rows_loaded = len(self.raw_df)

        logger.info(
            "Loaded input rows: %d",
            self.rows_loaded
        )

        logger.info(
            "Input columns: %s",
            list(self.raw_df.columns)
        )

        missing_columns = [
            column
            for column in self.REQUIRED_COLUMNS
            if column not in self.raw_df.columns
        ]

        if missing_columns:
            logger.error(
                "Missing required columns: %s",
                missing_columns
            )
            raise ValueError(
                f"Missing required columns: {missing_columns}"
            )

        logger.info("Required column validation passed.")
        logger.info("Data loading completed successfully.")

        return self.raw_df

    def clean_data(self):
        logger.info("Starting data cleaning.")

        if self.raw_df is None:
            logger.error(
                "clean_data() called before load_data()."
            )
            raise RuntimeError(
                "load_data() must be called before clean_data()."
            )

        logger.info(
            "Input rows before cleaning: %d",
            len(self.raw_df)
        )

        self.canonical_df = self.raw_df.rename(
            columns=self.CANONICAL_MAPPING
        ).copy()

        logger.info("Column names converted to canonical names.")

        logger.info("Converting timestamp column.")

        self.canonical_df["timestamp"] = pd.to_datetime(
            self.canonical_df["timestamp"],
            errors="coerce"
        )

        logger.info("Timestamp conversion completed.")

        logger.info(
            "Converting activity columns to numeric."
        )

        for column in self.ACTIVITY_COLUMNS:
            self.canonical_df[column] = pd.to_numeric(
                self.canonical_df[column],
                errors="coerce"
            )

            logger.debug(
                "Numeric conversion completed for column: %s",
                column
            )

        logger.info(
            "Activity column numeric conversion completed."
        )

        invalid_location_time = (
            self.canonical_df["grid_id"].isna() |
            self.canonical_df["timestamp"].isna()
        )

        rejected = invalid_location_time.sum()

        logger.info(
            "Rows with missing grid_id/timestamp: %d",
            rejected
        )

        if rejected > 0:
            logger.warning(
                "Rows rejected due to missing grid_id/timestamp: %d",
                rejected
            )

            self.rows_rejected += rejected

            self.canonical_df = (
                self.canonical_df.loc[
                    ~invalid_location_time
                ].copy()
            )

        logger.info("Validating grid_id range.")

        invalid_grid = (
            (self.canonical_df["grid_id"] < 1) |
            (self.canonical_df["grid_id"] > 10000)
        )

        invalid_grid_count = invalid_grid.sum()

        logger.info(
            "Invalid grid_id count: %d",
            invalid_grid_count
        )

        if invalid_grid_count > 0:
            logger.error(
                "Found %d invalid grid_id values.",
                invalid_grid_count
            )
            raise ValueError(
                f"Found {invalid_grid_count} invalid grid_id values."
            )

        logger.info(
            "Checking for negative activity values."
        )

        negative_counts = (
            self.canonical_df[self.ACTIVITY_COLUMNS]
            .lt(0)
            .sum()
        )

        total_negative = negative_counts.sum()

        logger.info(
            "Total negative activity values: %d",
            total_negative
        )

        if total_negative > 0:
            logger.error(
                "Found %d negative activity values.",
                total_negative
            )
            raise ValueError(
                f"Found {total_negative} negative activity values."
            )

        logger.info(
            "Checking activity columns for null values."
        )

        null_count_before = (
            self.canonical_df[self.ACTIVITY_COLUMNS]
            .isna()
            .sum()
            .sum()
        )

        logger.info(
            "Activity nulls found: %d",
            null_count_before
        )

        self.canonical_df[self.ACTIVITY_COLUMNS] = (
            self.canonical_df[self.ACTIVITY_COLUMNS]
            .fillna(0)
        )

        self.nulls_handled = int(null_count_before)

        logger.info(
            "Activity nulls handled by curated rule: %d",
            self.nulls_handled
        )

        logger.info(
            "Rows rejected: %d",
            self.rows_rejected
        )

        logger.info(
            "Data cleaning completed. Final rows: %d",
            len(self.canonical_df)
        )

        return self.canonical_df

    def derive_time_features(self):
        logger.info("Starting time feature derivation.")

        if self.canonical_df is None:
            logger.error(
                "derive_time_features() called before clean_data()."
            )
            raise RuntimeError(
                "clean_data() must be called first."
            )

        self.canonical_df["date"] = (
            self.canonical_df["timestamp"].dt.date
        )

        self.canonical_df["hour"] = (
            self.canonical_df["timestamp"].dt.hour
        )

        self.canonical_df["day_of_week"] = (
            self.canonical_df["timestamp"].dt.day_name()
        )

        logger.info("Time features derived.")

        return self.canonical_df

    def aggregate_to_grid_time(self):
        logger.info(
            "Starting grid/hour aggregation."
        )

        if self.canonical_df is None:
            logger.error(
                "aggregate_to_grid_time() called before clean_data()."
            )
            raise RuntimeError(
                "clean_data() must be called first."
            )

        group_columns = [
            "timestamp",
            "grid_id"
        ]

        self.analytics_df = (
            self.canonical_df
            .groupby(group_columns, as_index=False)
            [
                self.ACTIVITY_COLUMNS
            ]
            .sum()
        )

        self.analytics_df["date"] = (
            self.analytics_df["timestamp"].dt.date
        )

        self.analytics_df["hour"] = (
            self.analytics_df["timestamp"].dt.hour
        )

        self.analytics_df["day_of_week"] = (
            self.analytics_df["timestamp"].dt.day_name()
        )

        logger.info(
            "Input rows before aggregation: %d",
            len(self.canonical_df)
        )

        logger.info(
            "Output rows after grid/hour aggregation: %d",
            len(self.analytics_df)
        )

        logger.info(
            "Rows reduced by aggregation: %d",
            len(self.canonical_df) - len(self.analytics_df)
        )

        logger.info(
            "Validating aggregated data."
        )

        duplicate_count = (
            self.analytics_df
            .duplicated(
                subset=["grid_id", "timestamp"]
            )
            .sum()
        )

        logger.info(
            "Duplicate grid_id/timestamp records: %d",
            duplicate_count
        )

        if duplicate_count > 0:
            logger.error(
                "Grid/hour aggregation produced duplicate records."
            )
            raise ValueError(
                "Grid/hour aggregation produced duplicate "
                "(grid_id, timestamp) records."
            )

        if len(self.analytics_df) >= len(self.canonical_df):
            logger.error(
                "Aggregation did not reduce the row count."
            )
            raise ValueError(
                "Aggregation did not reduce the row count."
            )

        logger.info(
            "Grid/hour aggregation completed successfully."
        )

        return self.analytics_df

    def derive_activity_features(self):
        logger.info(
            "Starting activity feature derivation."
        )

        if self.analytics_df is None:
            logger.error(
                "derive_activity_features() called before "
                "aggregate_to_grid_time()."
            )
            raise RuntimeError(
                "aggregate_to_grid_time() must be called first."
            )

        self.analytics_df["total_sms"] = (
            self.analytics_df["sms_in"] +
            self.analytics_df["sms_out"]
        )

        self.analytics_df["total_calls"] = (
            self.analytics_df["call_in"] +
            self.analytics_df["call_out"]
        )

        self.analytics_df["total_activity"] = (
            self.analytics_df["total_sms"] +
            self.analytics_df["total_calls"] +
            self.analytics_df["internet_activity"]
        )

        logger.info(
            "Activity features derived."
        )

        return self.analytics_df

    def compute_kpis(self):
        logger.info("Starting KPI computation.")

        if self.analytics_df is None:
            logger.error(
                "compute_kpis() called before "
                "derive_activity_features()."
            )
            raise RuntimeError(
                "derive_activity_features() must be called first."
            )
        
        logger.info("Computing daily KPI summary.")

        self.daily_summary = (
            self.analytics_df
            .groupby("date", as_index=False)
            .agg(
                total_sms=("total_sms", "sum"),
                total_calls=("total_calls", "sum"),
                total_activity=("total_activity", "sum"),
                average_activity=("total_activity", "mean"),
                peak_activity=("total_activity", "max")
            )
        )

        logger.info("Computing grid KPI summary.")

        self.grid_summary = (
            self.analytics_df
            .groupby("grid_id", as_index=False)
            .agg(
                total_sms=("total_sms", "sum"),
                total_calls=("total_calls", "sum"),
                total_activity=("total_activity", "sum"),
                average_activity=("total_activity", "mean"),
                peak_activity=("total_activity", "max")
            )
            .sort_values(
                "total_activity",
                ascending=False
            )
        )

        logger.info(
            "Daily KPI summary computed. Rows: %d",
            len(self.daily_summary)
        )

        logger.info(
            "Grid KPI summary computed. Rows: %d",
            len(self.grid_summary)
        )

        logger.info("KPI computation completed.")

        return self.daily_summary, self.grid_summary

    def export_summary(self, output_dir="../data/processed"):
        logger.info(
            "Starting summary export."
        )

        if self.daily_summary is None:
            logger.error(
                "export_summary() called before compute_kpis()."
            )
            raise RuntimeError(
                "compute_kpis() must be called first."
            )

        output_path = Path(output_dir)

        logger.info(
            "Preparing output directory: %s",
            output_path
        )

        output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        daily_file = output_path / "daily_summary.csv"
        grid_file = output_path / "grid_summary.csv"

        logger.info(
            "Exporting daily summary."
        )

        self.daily_summary.to_csv(
            daily_file,
            index=False
        )

        logger.info(
            "Exporting grid summary."
        )

        self.grid_summary.to_csv(
            grid_file,
            index=False
        )

        logger.info(
            "Daily summary exported: %s",
            daily_file
        )

        logger.info(
            "Grid summary exported: %s",
            grid_file
        )

        logger.info(
            "Final output rows: %d",
            len(self.analytics_df)
        )

        logger.info(
            "Summary export completed successfully."
        )

        return daily_file, grid_file
    
FILE_PATH = "data/raw/sms-call-internet-mi-2013-11-01.csv"


def main():
    processor = UsageProcessor(
        file_path=FILE_PATH
    )

    processor.load_data()

    processor.clean_data()

    processor.derive_time_features()

    processor.aggregate_to_grid_time()

    processor.derive_activity_features()

    # processor.compute_kpis()

    # processor.export_summary()

    processor.analytics_df.duplicated(
        ["grid_id", "timestamp"]
    ).sum()

    print("country_code" in processor.analytics_df.columns)

    # np3 threshold calculation:
    print("=== TOTAL ACTIVITY ===")
    print(processor.analytics_df["total_activity"].describe())

    daily_grid_activity = (
        processor.analytics_df
        .groupby("grid_id")["total_activity"]
        .sum()
    )

    print("=== DAILY ACTIVITY PER GRID ===")
    print(daily_grid_activity.describe())

    print("=== LOWEST-ACTIVITY GRIDS ===")
    print(
        daily_grid_activity
        .sort_values()
        .head(20)
    )

    print(
        "5th percentile:",
        daily_grid_activity.quantile(0.05)
    )

    print(
        "10th percentile:",
        daily_grid_activity.quantile(0.10)
    )

    print(
        "15th percentile:",
        daily_grid_activity.quantile(0.15)
    )


if __name__ == "__main__":
    main()