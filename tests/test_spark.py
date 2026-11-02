import shutil

import pytest
from pandas.testing import assert_frame_equal

from ad_budget.analytics import pandas_analyze
from ad_budget.generate import generate_csv

pytest.importorskip("pyspark")
pytestmark = pytest.mark.skipif(shutil.which("java") is None, reason="Java not installed")


def test_spark_parity(tmp_path):
    from ad_budget.spark import spark_analyze

    path = generate_csv(tmp_path / "spark.csv", 1000)
    assert_frame_equal(
        pandas_analyze(path),
        spark_analyze(path),
        check_dtype=False,
        check_exact=False,
        rtol=1e-9,
        atol=0.01,
    )
