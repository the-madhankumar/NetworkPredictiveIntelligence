import os
import json
import logging
from datetime import datetime

import pandas as pd
import mysql.connector


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_PROJECT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../../"))

PARQUET_PATH = os.path.join(
    BASE_PROJECT_DIR,
    "Dataset",
    "analytics",
    "hourly_grid_summary.parquet"
)

GEOJSON_PATH = os.path.join(
    BASE_PROJECT_DIR,
    "Dataset",
    "reference",
    "milano-grid.geojson"
)

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_DATABASE = os.getenv(
    "MYSQL_DATABASE",
    "network_predictive_intelligence"
)

LOG_DIR = os.path.join(BASE_PROJECT_DIR, "log")
BATCH_SIZE = 10000

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(LOG_DIR, "warehouse_load.log"),
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )


# ============================================================
# LOAD PARQUET
# ============================================================

def load_parquet():

    logger.info(
        "Reading hourly_grid_summary Parquet: %s",
        PARQUET_PATH
    )

    if not os.path.exists(PARQUET_PATH):
        raise FileNotFoundError(
            f"Parquet source not found: {PARQUET_PATH}"
        )

    df = pd.read_parquet(PARQUET_PATH)

    required_columns = [
        "grid_id",
        "timestamp",
        "sms_in",
        "sms_out",
        "call_in",
        "call_out",
        "internet_activity",
        "total_activity"
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required Parquet columns: {missing}"
        )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="raise"
    )

    df["grid_id"] = pd.to_numeric(
        df["grid_id"],
        errors="raise"
    ).astype(int)

    metric_columns = [
        "sms_in",
        "sms_out",
        "call_in",
        "call_out",
        "internet_activity",
        "total_activity"
    ]

    for column in metric_columns:
        df[column] = (
            pd.to_numeric(
                df[column],
                errors="coerce"
            )
            .fillna(0.0)
            .astype(float)
        )

    df["total_sms"] = (
        df["sms_in"] +
        df["sms_out"]
    )

    df["total_calls"] = (
        df["call_in"] +
        df["call_out"]
    )

    df["internet_share"] = (
        df["internet_activity"]
        .div(df["total_activity"].replace(0, pd.NA))
        .fillna(0.0)
        .astype(float)
    )

    df = df.sort_values(
        ["timestamp", "grid_id"]
    ).reset_index(drop=True)

    logger.info(
        "Parquet rows: %d",
        len(df)
    )

    logger.info(
        "Distinct timestamps: %d",
        df["timestamp"].nunique()
    )

    logger.info(
        "Distinct grids: %d",
        df["grid_id"].nunique()
    )

    return df


# ============================================================
# LOAD GEOJSON
# ============================================================

def load_geojson():

    logger.info(
        "Reading static reference: %s",
        GEOJSON_PATH
    )

    if not os.path.exists(GEOJSON_PATH):
        raise FileNotFoundError(
            f"GeoJSON reference not found: {GEOJSON_PATH}"
        )

    with open(
        GEOJSON_PATH,
        "r",
        encoding="utf-8"
    ) as file:
        geojson = json.load(file)

    if geojson.get("type") != "FeatureCollection":
        raise ValueError(
            "GeoJSON must be a FeatureCollection."
        )

    features = geojson.get("features", [])

    if not features:
        raise ValueError(
            "GeoJSON contains no features."
        )

    logger.info(
        "GeoJSON features: %d",
        len(features)
    )

    return features


# ============================================================
# EXTRACT GRID REFERENCE
# ============================================================

def extract_grid_reference(features):

    grid_records = {}
    duplicate_grids = set()

    for feature in features:

        properties = feature.get(
            "properties",
            {}
        )

        grid_id = (
            properties.get("cellId")
            or properties.get("grid_id")
            or properties.get("CellID")
            or properties.get("cell_id")
            or properties.get("id")
        )

        if grid_id is None:
            raise ValueError(
                "GeoJSON feature is missing grid_id."
            )

        grid_id = int(grid_id)

        if grid_id in grid_records:
            duplicate_grids.add(grid_id)

        geometry = feature.get("geometry")

        if geometry is None:
            raise ValueError(
                f"Grid {grid_id} has no geometry."
            )

        coordinates = geometry.get(
            "coordinates"
        )

        centroid_latitude = None
        centroid_longitude = None

        if coordinates:

            try:

                geometry_type = geometry.get(
                    "type"
                )

                if geometry_type == "Polygon":

                    outer_ring = coordinates[0]

                elif geometry_type == "MultiPolygon":

                    outer_ring = coordinates[0][0]

                else:

                    outer_ring = None

                if outer_ring:

                    longitudes = [
                        point[0]
                        for point in outer_ring
                    ]

                    latitudes = [
                        point[1]
                        for point in outer_ring
                    ]

                    centroid_longitude = (
                        min(longitudes) +
                        max(longitudes)
                    ) / 2.0

                    centroid_latitude = (
                        min(latitudes) +
                        max(latitudes)
                    ) / 2.0

            except (
                IndexError,
                TypeError,
                ValueError
            ):

                logger.warning(
                    "Could not calculate centroid "
                    "for grid %s.",
                    grid_id
                )

        geometry_reference = (
            f"milano-grid.geojson:grid_id={grid_id}"
        )

        grid_records[grid_id] = {
            "grid_id": grid_id,
            "centroid_latitude": centroid_latitude,
            "centroid_longitude": centroid_longitude,
            "geometry_reference": geometry_reference
        }

    if duplicate_grids:

        raise ValueError(
            "Duplicate grid IDs in GeoJSON: "
            f"{sorted(duplicate_grids)}"
        )

    logger.info(
        "Unique grid reference records: %d",
        len(grid_records)
    )

    return grid_records


# ============================================================
# CREATE WAREHOUSE TABLES
# ============================================================

def create_tables(connection):

    logger.info(
        "Creating warehouse tables."
    )

    cursor = connection.cursor()

    cursor.execute(
        "DROP TABLE IF EXISTS fact_network_activity"
    )

    cursor.execute(
        "DROP TABLE IF EXISTS dim_grid"
    )

    cursor.execute(
        "DROP TABLE IF EXISTS dim_time"
    )

    cursor.execute("""
        CREATE TABLE dim_time (
            time_key BIGINT PRIMARY KEY,
            timestamp DATETIME NOT NULL UNIQUE,
            date_value DATE NOT NULL,
            year_value INT NOT NULL,
            month_value INT NOT NULL,
            day_value INT NOT NULL,
            hour_value INT NOT NULL
        ) ENGINE=InnoDB
    """)

    cursor.execute("""
        CREATE TABLE dim_grid (
            grid_id INT PRIMARY KEY,
            centroid_latitude DOUBLE NULL,
            centroid_longitude DOUBLE NULL,
            geometry_reference VARCHAR(255) NULL
        ) ENGINE=InnoDB
    """)

    cursor.execute("""
        CREATE TABLE fact_network_activity (
            activity_id BIGINT AUTO_INCREMENT PRIMARY KEY,
            grid_id INT NOT NULL,
            time_key BIGINT NOT NULL,
            sms_in DOUBLE NOT NULL,
            sms_out DOUBLE NOT NULL,
            call_in DOUBLE NOT NULL,
            call_out DOUBLE NOT NULL,
            internet_activity DOUBLE NOT NULL,
            total_sms DOUBLE NOT NULL,
            total_calls DOUBLE NOT NULL,
            total_activity DOUBLE NOT NULL,
            internet_share DOUBLE NOT NULL,

            CONSTRAINT fk_fact_grid
                FOREIGN KEY (grid_id)
                REFERENCES dim_grid(grid_id),

            CONSTRAINT fk_fact_time
                FOREIGN KEY (time_key)
                REFERENCES dim_time(time_key),

            UNIQUE KEY uk_fact_grid_time (
                grid_id,
                time_key
            ),

            INDEX idx_fact_grid (
                grid_id
            ),

            INDEX idx_fact_time (
                time_key
            )
        ) ENGINE=InnoDB
    """)

    connection.commit()

    cursor.close()

    logger.info(
        "Warehouse tables created successfully."
    )


# ============================================================
# LOAD DIM_TIME
# ============================================================

def load_dim_time(connection, df):

    logger.info(
        "Loading dim_time."
    )

    timestamps = (
        pd.to_datetime(
            df["timestamp"]
        )
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    rows = []

    for timestamp in timestamps:

        timestamp = pd.Timestamp(
            timestamp
        )

        time_key = int(
            timestamp.strftime(
                "%Y%m%d%H"
            )
        )

        rows.append((
            time_key,
            timestamp.to_pydatetime(),
            timestamp.date(),
            timestamp.year,
            timestamp.month,
            timestamp.day,
            timestamp.hour
        ))

    if not rows:
        raise ValueError(
            "No timestamps found for dim_time."
        )

    cursor = connection.cursor()

    cursor.executemany(
        """
        INSERT INTO dim_time (
            time_key,
            timestamp,
            date_value,
            year_value,
            month_value,
            day_value,
            hour_value
        )
        VALUES (
            %s, %s, %s, %s,
            %s, %s, %s
        )
        """,
        rows
    )

    connection.commit()

    cursor.close()

    logger.info(
        "dim_time loaded: %d records",
        len(rows)
    )


# ============================================================
# LOAD DIM_GRID
# ============================================================

def load_dim_grid(
    connection,
    grid_records,
    activity_grid_ids
):

    logger.info(
        "Loading dim_grid."
    )

    rows = []

    for grid_id in sorted(activity_grid_ids):

        if grid_id not in grid_records:
            raise ValueError(
                f"Grid {grid_id} not found "
                "in GeoJSON."
            )

        record = grid_records[grid_id]

        rows.append((
            record["grid_id"],
            record["centroid_latitude"],
            record["centroid_longitude"],
            record["geometry_reference"]
        ))

    cursor = connection.cursor()

    cursor.executemany(
        """
        INSERT INTO dim_grid (
            grid_id,
            centroid_latitude,
            centroid_longitude,
            geometry_reference
        )
        VALUES (
            %s, %s, %s, %s
        )
        """,
        rows
    )

    connection.commit()

    cursor.close()

    logger.info(
        "dim_grid loaded: %d grids",
        len(rows)
    )


# ============================================================
# BUILD DIMENSION MAPS
# ============================================================

def build_dimension_maps(connection):

    logger.info(
        "Building dimension key maps."
    )

    cursor = connection.cursor()

    cursor.execute("""
        SELECT grid_id
        FROM dim_grid
    """)

    grid_key_map = {
        int(row[0]): int(row[0])
        for row in cursor.fetchall()
    }

    cursor.execute("""
        SELECT time_key, timestamp
        FROM dim_time
    """)

    time_key_map = {
        pd.Timestamp(row[1]): int(row[0])
        for row in cursor.fetchall()
    }

    cursor.close()

    logger.info(
        "Grid map records: %d",
        len(grid_key_map)
    )

    logger.info(
        "Time map records: %d",
        len(time_key_map)
    )

    return grid_key_map, time_key_map


# ============================================================
# VALIDATE GRID COVERAGE
# ============================================================

def validate_grid_coverage(
    connection,
    df
):

    logger.info(
        "Validating grid coverage."
    )

    activity_grids = set(
        df["grid_id"]
        .astype(int)
        .unique()
    )

    cursor = connection.cursor()

    cursor.execute("""
        SELECT grid_id
        FROM dim_grid
    """)

    warehouse_grids = {
        int(row[0])
        for row in cursor.fetchall()
    }

    cursor.close()

    missing = (
        activity_grids -
        warehouse_grids
    )

    if missing:

        raise ValueError(
            "Activity grids missing from dim_grid: "
            f"{sorted(missing)}"
        )

    logger.info(
        "Grid coverage validation: PASS"
    )


# ============================================================
# LOAD FACT TABLE
# ============================================================

def load_fact_network_activity(
    connection,
    df,
    grid_key_map,
    time_key_map
):

    logger.info(
        "Loading fact_network_activity."
    )

    insert_sql = """
        INSERT INTO fact_network_activity (
            grid_id,
            time_key,
            sms_in,
            sms_out,
            call_in,
            call_out,
            internet_activity,
            total_sms,
            total_calls,
            total_activity,
            internet_share
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )
    """

    cursor = connection.cursor()

    batch = []
    rows_processed = 0

    for record in df.itertuples(
        index=False
    ):

        grid_id = int(
            record.grid_id
        )

        timestamp = pd.Timestamp(
            record.timestamp
        )

        grid_key = grid_key_map.get(
            grid_id
        )

        time_key = time_key_map.get(
            timestamp
        )

        if grid_key is None:

            raise ValueError(
                f"Grid {grid_id} not found "
                "in dim_grid."
            )

        if time_key is None:

            raise ValueError(
                f"Timestamp {timestamp} not found "
                "in dim_time."
            )

        batch.append((
            grid_key,
            time_key,
            float(record.sms_in),
            float(record.sms_out),
            float(record.call_in),
            float(record.call_out),
            float(record.internet_activity),
            float(record.total_sms),
            float(record.total_calls),
            float(record.total_activity),
            float(record.internet_share)
        ))

        if len(batch) >= BATCH_SIZE:

            cursor.executemany(
                insert_sql,
                batch
            )

            connection.commit()

            rows_processed += len(batch)

            logger.info(
                "Fact rows loaded: %d / %d",
                rows_processed,
                len(df)
            )

            batch.clear()

    if batch:

        cursor.executemany(
            insert_sql,
            batch
        )

        connection.commit()

        rows_processed += len(batch)

    cursor.close()

    logger.info(
        "fact_network_activity loaded: %d rows",
        rows_processed
    )

    if rows_processed != len(df):

        raise ValueError(
            "Fact loading reconciliation failed. "
            f"Expected={len(df)}, "
            f"Loaded={rows_processed}"
        )


# ============================================================
# CREATE INDEXES
# ============================================================

def create_indexes(connection):

    logger.info(
        "Creating warehouse indexes."
    )

    cursor = connection.cursor()

    statements = [
        """
        CREATE INDEX idx_time_date
        ON dim_time(date_value)
        """,
        """
        CREATE INDEX idx_fact_grid_time
        ON fact_network_activity(grid_id, time_key)
        """
    ]

    for statement in statements:

        try:

            cursor.execute(
                statement
            )

        except mysql.connector.Error as error:

            if error.errno != 1061:
                raise

    connection.commit()

    cursor.close()

    logger.info(
        "Indexes validated."
    )


# ============================================================
# VALIDATE WAREHOUSE
# ============================================================

def validate_warehouse(
    connection,
    source_rows,
    expected_time_rows,
    expected_grid_rows
):

    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM dim_time
    """)

    time_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM dim_grid
    """)

    grid_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM fact_network_activity
    """)

    fact_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(DISTINCT time_key)
        FROM fact_network_activity
    """)

    fact_time_keys = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(DISTINCT grid_id)
        FROM fact_network_activity
    """)

    fact_grid_keys = cursor.fetchone()[0]

    cursor.close()

    logger.info(
        "Warehouse counts — "
        "dim_time=%d, dim_grid=%d, fact=%d",
        time_count,
        grid_count,
        fact_count
    )

    logger.info(
        "Fact dimension usage — "
        "time_keys=%d, grid_keys=%d",
        fact_time_keys,
        fact_grid_keys
    )

    if time_count != expected_time_rows:

        raise ValueError(
            "dim_time validation failed. "
            f"Expected={expected_time_rows}, "
            f"Actual={time_count}"
        )

    if grid_count != expected_grid_rows:

        raise ValueError(
            "dim_grid validation failed. "
            f"Expected={expected_grid_rows}, "
            f"Actual={grid_count}"
        )

    if fact_count != source_rows:

        raise ValueError(
            "Fact row validation failed. "
            f"Source={source_rows}, "
            f"Fact={fact_count}"
        )

    if fact_time_keys != expected_time_rows:

        raise ValueError(
            "Fact time-key validation failed. "
            f"Expected={expected_time_rows}, "
            f"Actual={fact_time_keys}"
        )

    if fact_grid_keys != expected_grid_rows:

        raise ValueError(
            "Fact grid-key validation failed. "
            f"Expected={expected_grid_rows}, "
            f"Actual={fact_grid_keys}"
        )

    logger.info(
        "Warehouse reconciliation: PASS"
    )


# ============================================================
# VALIDATION QUERIES
# ============================================================

def run_validation_queries(connection):

    logger.info(
        "Running DE6 validation queries."
    )

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            g.grid_id,
            ROUND(
                SUM(f.total_activity),
                2
            ) AS total_activity
        FROM fact_network_activity f
        JOIN dim_grid g
            ON f.grid_id = g.grid_id
        GROUP BY g.grid_id
        ORDER BY total_activity DESC
        LIMIT 10
    """)

    print("\nTOP 10 GRIDS")
    print("-" * 50)

    for row in cursor.fetchall():
        print(row)

    cursor.execute("""
        SELECT
            t.hour_value,
            ROUND(
                SUM(f.total_activity),
                2
            ) AS total_activity
        FROM fact_network_activity f
        JOIN dim_time t
            ON f.time_key = t.time_key
        GROUP BY t.hour_value
        ORDER BY t.hour_value
    """)

    print("\nHOURLY ACTIVITY TREND")
    print("-" * 50)

    for row in cursor.fetchall():
        print(row)

    cursor.execute("""
        SELECT
            t.timestamp,
            ROUND(
                SUM(f.internet_activity),
                2
            ) AS internet_activity,
            ROUND(
                AVG(f.internet_share),
                4
            ) AS avg_internet_share
        FROM fact_network_activity f
        JOIN dim_time t
            ON f.time_key = t.time_key
        GROUP BY t.timestamp
        ORDER BY avg_internet_share DESC
        LIMIT 10
    """)

    print("\nINTERNET-HEAVY WINDOWS")
    print("-" * 50)

    for row in cursor.fetchall():
        print(row)

    cursor.close()

    logger.info(
        "All validation queries completed."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    start_time = datetime.now()

    logger.info("=" * 60)
    logger.info("DE6 WAREHOUSE LOAD STARTED")
    logger.info("=" * 60)

    connection = None

    try:

        df = load_parquet()

        source_rows = len(df)

        expected_time_rows = (
            df["timestamp"].nunique()
        )

        expected_grid_rows = (
            df["grid_id"].nunique()
        )

        features = load_geojson()

        grid_records = extract_grid_reference(
            features
        )

        activity_grids = set(
            df["grid_id"]
            .astype(int)
            .unique()
        )

        reference_grids = set(
            grid_records.keys()
        )

        missing_grids = (
            activity_grids -
            reference_grids
        )

        if missing_grids:

            raise ValueError(
                "Activity grids missing from "
                "GeoJSON reference: "
                f"{sorted(missing_grids)}"
            )

        connection = get_connection()

        logger.info(
            "Connected to MySQL database: %s",
            MYSQL_DATABASE
        )

        create_tables(
            connection
        )

        load_dim_time(
            connection,
            df
        )

        load_dim_grid(
            connection,
            grid_records,
            activity_grids
        )

        validate_grid_coverage(
            connection,
            df
        )

        grid_key_map, time_key_map = (
            build_dimension_maps(
                connection
            )
        )

        if len(time_key_map) != expected_time_rows:

            raise ValueError(
                "Time dimension count mismatch. "
                f"Expected={expected_time_rows}, "
                f"Actual={len(time_key_map)}"
            )

        if len(grid_key_map) != expected_grid_rows:

            raise ValueError(
                "Grid dimension count mismatch. "
                f"Expected={expected_grid_rows}, "
                f"Actual={len(grid_key_map)}"
            )

        load_fact_network_activity(
            connection,
            df,
            grid_key_map,
            time_key_map
        )

        create_indexes(
            connection
        )

        validate_warehouse(
            connection,
            source_rows,
            expected_time_rows,
            expected_grid_rows
        )

        run_validation_queries(
            connection
        )

        logger.info(
            "FINAL STATUS: SUCCESS"
        )

    except Exception:

        logger.exception(
            "FINAL STATUS: FAILED"
        )

        if connection is not None:
            connection.rollback()

        raise

    finally:

        if connection is not None:

            connection.close()

            logger.info(
                "MySQL connection closed."
            )

        end_time = datetime.now()

        logger.info(
            "Start time: %s",
            start_time
        )

        logger.info(
            "End time: %s",
            end_time
        )

        logger.info("=" * 60)


if __name__ == "__main__":
    main()