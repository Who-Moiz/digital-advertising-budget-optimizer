"""Spark SQL aggregation using an explicit CSV schema and distributed validation."""

from pathlib import Path

import pandas as pd

from ad_budget.analytics import with_kpis
from ad_budget.schema import COLUMNS, DIMENSIONS, MEASURES, PLATFORMS


def spark_analyze(
    path: str | Path, group_by: str = "platform", master: str = "local[2]"
) -> pd.DataFrame:
    if group_by not in DIMENSIONS:
        raise ValueError(f"group_by must be one of {DIMENSIONS}.")
    try:
        from pyspark.sql import SparkSession
        from pyspark.sql import functions as F
        from pyspark.sql import types as T
    except ImportError as exc:
        raise RuntimeError("Spark requires pip install '.[spark]' and Java 17.") from exc
    spark = SparkSession.builder.master(master).appName("AdBudgetOptimizer").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    try:
        # Validate the header before applying a positional Spark schema.
        header = pd.read_csv(path, nrows=0).columns.tolist()
        if header != list(COLUMNS):
            raise ValueError("Spark CSV columns must match the documented schema and order.")
        numeric = {*MEASURES, "age"}
        schema = T.StructType(
            [T.StructField(c, T.DoubleType() if c in numeric else T.StringType()) for c in COLUMNS]
        )
        frame = (
            spark.read.option("header", True)
            .option("mode", "FAILFAST")
            .schema(schema)
            .csv(str(Path(path).resolve()))
        )
        invalid = F.lit(False)
        for col in COLUMNS:
            invalid = invalid | F.col(col).isNull()
            if col in numeric:
                invalid = (
                    invalid | F.isnan(col) | (F.abs(F.col(col)) == float("inf")) | (F.col(col) < 0)
                )
            else:
                invalid = invalid | (F.trim(F.col(col)) == "")
        for col in ("impressions", "clicks", "conversions", "age"):
            invalid = invalid | (F.col(col) != F.floor(F.col(col)))
        invalid = (
            invalid
            | (~F.col("platform").isin(*PLATFORMS))
            | (~F.col("age").between(18, 100))
            | (F.col("clicks") > F.col("impressions"))
            | (F.col("conversions") > F.col("clicks"))
            | F.to_date("date", "yyyy-MM-dd").isNull()
        )
        if frame.filter(invalid).limit(1).count():
            raise ValueError("CSV contains records that violate the data contract.")
        rows = frame.groupBy(group_by).agg(*[F.sum(c).alias(c) for c in MEASURES]).collect()
        if not rows:
            raise ValueError("Dataset must contain at least one row.")
        totals = pd.DataFrame([r.asDict() for r in rows]).sort_values(group_by)
        return with_kpis(totals[[group_by, *MEASURES]].reset_index(drop=True))
    finally:
        spark.stop()
