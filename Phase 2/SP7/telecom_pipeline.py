import os
import json
import glob
import argparse
import logging
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import broadcast


# --------------------------------------------------
# Spark Session
# --------------------------------------------------
def create_spark():
    return (
        SparkSession.builder
        .appName("Milano Telecom ETL Pipeline")
        .getOrCreate()
    )


# --------------------------------------------------
# Logging
# --------------------------------------------------
def setup_logger(log_dir):
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "telecom_pipeline.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


# --------------------------------------------------
# Read Raw Daily Files
# --------------------------------------------------
def read_raw(spark, input_path):
    files = glob.glob(os.path.join(input_path, "*.csv"))

    if len(files) == 0:
        raise FileNotFoundError(
            f"No daily activity files found in {input_path}"
        )

    df = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(files)
    )

    logging.info(f"Input files : {len(files)}")
    logging.info(f"Input rows  : {df.count()}")

    return df


# --------------------------------------------------
# Read Milano GeoJSON
# --------------------------------------------------
def read_reference(spark, reference_path):

    geojson_file = os.path.join(reference_path, "milano-grid.geojson")

    with open(geojson_file, "r") as f:
        geo = json.load(f)

    rows = []

    for feature in geo["features"]:
        rows.append(
            (
                int(feature["properties"]["cellId"]),
                json.dumps(feature["geometry"])
            )
        )

    grid_df = spark.createDataFrame(rows, ["grid_id", "geometry"])

    logging.info(f"Grid lookup rows : {grid_df.count()}")

    return grid_df


# --------------------------------------------------
# Cleaning Logic (SP1 / SP2)
# --------------------------------------------------
def clean(df):

    before = df.count()

    cleaned = (
        df
        .dropna(subset=["cellid", "time"])
        .withColumnRenamed("cellid", "grid_id")
        .withColumnRenamed("time", "timestamp")
        .withColumn(
            "timestamp",
            F.from_unixtime(F.col("timestamp") / 1000).cast("timestamp")
        )
        .withColumn("date", F.to_date("timestamp"))
        .fillna(0)
    )

    after = cleaned.count()

    logging.info(f"Rejected rows : {before - after}")
    logging.info(f"Clean rows    : {after}")

    return cleaned


# --------------------------------------------------
# Country Aggregation (Must occur first)
# --------------------------------------------------
def country_aggregation(df):

    country_summary = (
        df
        .groupBy("countrycode")
        .agg(
            F.sum("smsin").alias("sms_in"),
            F.sum("smsout").alias("sms_out"),
            F.sum("callin").alias("call_in"),
            F.sum("callout").alias("call_out"),
            F.sum("internet").alias("internet_activity")
        )
    )

    logging.info(
        f"Country summary rows : {country_summary.count()}"
    )

    return country_summary


# --------------------------------------------------
# Grid / Hour Aggregation
# --------------------------------------------------
def aggregate(df):

    hourly = (
        df
        .groupBy("timestamp", "grid_id", "date")
        .agg(
            F.sum("smsin").alias("sms_in"),
            F.sum("smsout").alias("sms_out"),
            F.sum("callin").alias("call_in"),
            F.sum("callout").alias("call_out"),
            F.sum("internet").alias("internet_activity")
        )
        .withColumn(
            "total_activity",
            F.col("sms_in")
            + F.col("sms_out")
            + F.col("call_in")
            + F.col("call_out")
            + F.col("internet_activity")
        )
    )

    logging.info(f"Hourly rows : {hourly.count()}")

    return hourly


# --------------------------------------------------
# Grid Enrichment
# --------------------------------------------------
def enrich(hourly_df, grid_df):

    enriched = (
        hourly_df
        .join(
            broadcast(grid_df),
            on="grid_id",
            how="left"
        )
    )

    logging.info(f"Enriched rows : {enriched.count()}")

    return enriched


# --------------------------------------------------
# Write Outputs (SP6)
# --------------------------------------------------
def write_outputs(
    cleaned_df,
    hourly_df,
    country_df,
    enriched_df,
    grid_df,
    output_path
):

    processed = os.path.join(output_path, "processed", "activity")
    analytics = os.path.join(output_path, "analytics")
    reference = os.path.join(output_path, "reference")

    # Clean activity
    (
        cleaned_df.write
        .mode("overwrite")
        .partitionBy("date")
        .parquet(processed)
    )

    # Hourly summary (NO geometry)
    (
        hourly_df.write
        .mode("overwrite")
        .parquet(
            os.path.join(
                analytics,
                "hourly_grid_summary"
            )
        )
    )

    # Country summary
    (
        country_df.write
        .mode("overwrite")
        .option("header", True)
        .csv(
            os.path.join(
                analytics,
                "country_summary"
            )
        )
    )

    # Dashboard summary
    dashboard = (
        hourly_df
        .groupBy("grid_id")
        .agg(
            F.sum("total_activity").alias("total_activity")
        )
        .orderBy(F.desc("total_activity"))
        .limit(100)
    )

    (
        dashboard.write
        .mode("overwrite")
        .option("header", True)
        .csv(
            os.path.join(
                analytics,
                "dashboard_summary"
            )
        )
    )

    # Static grid reference
    (
        grid_df.write
        .mode("overwrite")
        .parquet(reference)
    )

    logging.info("Outputs written successfully.")


# --------------------------------------------------
# Main
# --------------------------------------------------
def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--logs", default="logs")

    args = parser.parse_args()

    setup_logger(args.logs)

    logging.info("========== JOB STARTED ==========")

    start = datetime.now()

    spark = create_spark()

    try:

        raw = read_raw(spark, args.input)

        grid = read_reference(spark, args.reference)

        cleaned = clean(raw)

        country = country_aggregation(cleaned)

        hourly = aggregate(cleaned)

        enriched = enrich(hourly, grid)

        write_outputs(
            cleaned,
            hourly,
            country,
            enriched,
            grid,
            args.output
        )

        logging.info("JOB STATUS : SUCCESS")

    except Exception as e:

        logging.error(str(e))

        logging.error("JOB STATUS : FAILED")

        raise

    finally:

        end = datetime.now()

        logging.info(f"Start : {start}")
        logging.info(f"End   : {end}")

        spark.stop()


if __name__ == "__main__":
    main()