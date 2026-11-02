import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from ad_budget.analytics import aggregate, chunked_analyze, pandas_analyze
from ad_budget.generate import generate_csv
from ad_budget.mapreduce import mapreduce_analyze
from ad_budget.optimizer import recommend
from ad_budget.schema import validate


@pytest.fixture
def sample(tmp_path):
    path = generate_csv(tmp_path / "sample.csv", rows=137, seed=7, chunk_size=50)
    return path


def test_generation_contract_and_reproducibility(sample, tmp_path):
    first = pd.read_csv(sample)
    validate(first)
    assert len(first) == 137
    second = generate_csv(tmp_path / "same.csv", 137, 7, 50)
    assert sample.read_bytes() == second.read_bytes()
    assert set(first.platform) == {"Facebook", "Instagram", "Google", "TikTok", "YouTube"}


@pytest.mark.parametrize("dimension", ["platform", "campaign", "device", "age", "date"])
def test_backends_match(sample, dimension):
    expected = pandas_analyze(sample, dimension)
    assert_frame_equal(expected, chunked_analyze(sample, dimension, 11), check_exact=False)
    assert_frame_equal(expected, mapreduce_analyze(sample, dimension, 23, 2), check_exact=False)


def test_weighted_ratios_and_undefined(sample):
    frame = pd.read_csv(sample).iloc[:2].copy()
    frame["platform"] = "Google"
    frame["impressions"] = [100, 1000]
    frame["clicks"] = [10, 1]
    frame["conversions"] = [1, 0]
    frame["spend"] = [20, 5]
    frame["revenue"] = [50, 0]
    result = aggregate(frame).iloc[0]
    assert result.ctr == pytest.approx(100 * 11 / 1100)
    assert result.cpc == pytest.approx(25 / 11)
    assert result.cpa == 25
    assert result.conversion_rate == pytest.approx(100 / 11)
    assert result.roas == 2
    frame[["clicks", "spend", "conversions", "revenue"]] = 0
    zero = aggregate(frame).iloc[0]
    assert np.isnan(zero.cpc) and np.isnan(zero.cpa) and np.isnan(zero.roas)


@pytest.mark.parametrize(
    "column,value",
    [
        ("spend", -1),
        ("revenue", np.inf),
        ("age", 12),
        ("clicks", 0.5),
        ("platform", "Unknown"),
        ("date", "bad"),
    ],
)
def test_validation_rejects_bad_values(sample, column, value):
    frame = pd.read_csv(sample)
    frame[column] = frame[column].astype(object)
    frame.loc[0, column] = value
    with pytest.raises(ValueError):
        validate(frame)


def test_validation_rejects_funnel_and_missing(sample):
    frame = pd.read_csv(sample)
    with pytest.raises(ValueError, match="Missing columns"):
        validate(frame.drop(columns="city"))
    frame.loc[0, "clicks"] = frame.loc[0, "impressions"] + 1
    with pytest.raises(ValueError, match="Counts must satisfy"):
        validate(frame)


def test_allocation_conserves_budget_and_bounds(sample):
    history = pandas_analyze(sample)
    result = recommend(history, 1_000_000.03, 0.05, 0.4)
    assert round(result.recommended_budget.sum(), 2) == 1_000_000.03
    assert result.recommended_share_pct.between(5, 40).all()
    assert result.evidence_weight.between(0, 1).all()
    assert_frame_equal(result, recommend(history, 1_000_000.03, 0.05, 0.4))


def test_optimizer_prefers_stronger_evidence():
    history = pd.DataFrame(
        {
            "platform": ["A", "B"],
            "spend": [100_000, 100_000],
            "revenue": [400_000, 100_000],
            "conversions": [200, 50],
        }
    )
    result = recommend(history, 100_000, 0, 1)
    assert result.loc[0, "recommended_budget"] > result.loc[1, "recommended_budget"]
    assert result.modeled_revenue.sum() >= result.baseline_modeled_revenue.sum() - 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"budget": -1},
        {"budget": np.nan},
        {"min_share": 0.3},
        {"max_share": 0.1},
        {"saturation": 0},
        {"prior_strength": 0},
    ],
)
def test_optimizer_rejects_invalid_parameters(sample, kwargs):
    with pytest.raises(ValueError):
        recommend(pandas_analyze(sample), **kwargs)


def test_no_spend_and_small_budget(sample):
    history = pandas_analyze(sample)
    with pytest.raises(ValueError):
        recommend(history, 0.01)
    history["spend"] = 0
    with pytest.raises(ValueError):
        recommend(history)


def test_invalid_generator_arguments(tmp_path):
    with pytest.raises(ValueError):
        generate_csv(tmp_path / "invalid.csv", 0)
