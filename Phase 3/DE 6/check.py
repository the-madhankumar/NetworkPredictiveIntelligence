from pathlib import Path
from pyspark.sql import SparkSession

BASE_DIR = Path(__file__).resolve().parent
PARQUET_PATH = (
    BASE_DIR.parents[1] / "Dataset" / "analytics" / "hourly_grid_summary.parquet"
)

spark = SparkSession.builder.appName("InspectSchema").getOrCreate()

# Load the Parquet file
df = spark.read.parquet(str(PARQUET_PATH))

# Print column names list
print("Column Names:")
print(df.columns)

# Print full schema with data types
print("\nDataFrame Schema:")
df.printSchema()

# View first 5 rows
df.show(5, truncate=False)

spark.stop()