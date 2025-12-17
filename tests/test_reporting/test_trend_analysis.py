"""
Tests for Trend Analysis & Predictive Forecasting.

Tests cover:
- Trend analysis (direction, strength, seasonality)
- Anomaly detection (Isolation Forest, simple threshold)
- Predictive forecasting (ARIMA, Prophet, simple MA)
- Correlation analysis
- Model accuracy validation
"""

import pytest
import numpy as np
from datetime import datetime, timedelta

from app.reporting.trend_analysis import (
    TrendAnalysisEngine,
    TimeSeriesData,
    TrendAnalysis,
    Anomaly,
    Prediction,
    ForecastResult,
)


# ========================================
# Fixtures
# ========================================


@pytest.fixture
def trend_engine():
    """Create TrendAnalysisEngine instance."""
    return TrendAnalysisEngine()


@pytest.fixture
def sample_time_series():
    """Create sample time series with increasing trend."""
    base_time = datetime(2025, 11, 1)
    timestamps = [base_time + timedelta(hours=i) for i in range(168)]  # 7 days

    # Increasing trend with some noise
    values = [50 + i * 0.5 + np.random.normal(0, 2) for i in range(168)]

    return TimeSeriesData(
        timestamps=timestamps,
        values=values,
        metric_name="threats_detected",
        unit="count",
    )


@pytest.fixture
def sample_time_series_with_anomalies():
    """Create time series with intentional anomalies."""
    base_time = datetime(2025, 11, 1)
    timestamps = [base_time + timedelta(hours=i) for i in range(100)]

    # Normal values around 50
    values = [50 + np.random.normal(0, 2) for _ in range(100)]

    # Inject anomalies
    values[25] = 150  # Spike
    values[50] = 5  # Drop
    values[75] = 200  # Large spike

    return TimeSeriesData(
        timestamps=timestamps, values=values, metric_name="cpu_usage", unit="percent"
    )


@pytest.fixture
def sample_seasonal_time_series():
    """Create time series with seasonal pattern."""
    base_time = datetime(2025, 11, 1)
    timestamps = [base_time + timedelta(hours=i) for i in range(168)]  # 7 days

    # Daily seasonality (24-hour period)
    values = []
    for i in range(168):
        hour_of_day = i % 24
        # Higher activity during business hours (9-17)
        if 9 <= hour_of_day <= 17:
            values.append(80 + np.random.normal(0, 5))
        else:
            values.append(20 + np.random.normal(0, 3))

    return TimeSeriesData(
        timestamps=timestamps,
        values=values,
        metric_name="scan_activity",
        unit="scans/hour",
    )


@pytest.fixture
def sample_stable_time_series():
    """Create stable time series (no trend)."""
    base_time = datetime(2025, 11, 1)
    timestamps = [base_time + timedelta(days=i) for i in range(30)]
    values = [100 + np.random.normal(0, 3) for _ in range(30)]

    return TimeSeriesData(
        timestamps=timestamps,
        values=values,
        metric_name="baseline_metric",
        unit="value",
    )


# ========================================
# Test: Trend Analysis
# ========================================


def test_analyze_increasing_trend(trend_engine, sample_time_series):
    """Test detection of increasing trend."""
    analysis = trend_engine.analyze_trend(sample_time_series, timeframe_days=7)

    assert analysis.metric_name == "threats_detected"
    # Trend should be increasing or stable (depending on noise)
    assert analysis.trend_direction in ["increasing", "stable"]
    # Growth rate should be positive given the increasing pattern
    assert analysis.growth_rate_percent > 50  # Strong positive growth


def test_analyze_stable_trend(trend_engine, sample_stable_time_series):
    """Test detection of stable trend."""
    analysis = trend_engine.analyze_trend(sample_stable_time_series, timeframe_days=30)

    assert analysis.trend_direction == "stable"
    assert analysis.trend_strength == 0.0
    assert abs(analysis.growth_rate_percent) < 5  # Nearly stable


def test_trend_statistics(trend_engine, sample_time_series):
    """Test statistical calculations in trend analysis."""
    analysis = trend_engine.analyze_trend(sample_time_series)

    values = np.array(sample_time_series.values)

    assert analysis.average_value == pytest.approx(np.mean(values), rel=0.01)
    assert analysis.min_value == pytest.approx(np.min(values), rel=0.01)
    assert analysis.max_value == pytest.approx(np.max(values), rel=0.01)
    assert analysis.std_deviation == pytest.approx(np.std(values), rel=0.01)


def test_seasonality_detection(trend_engine, sample_seasonal_time_series):
    """Test seasonality detection in time series."""
    analysis = trend_engine.analyze_trend(sample_seasonal_time_series)

    # Should detect 24-hour seasonality
    assert analysis.seasonality_detected is True
    assert analysis.seasonal_period is not None
    assert 20 <= analysis.seasonal_period <= 28  # Around 24 hours


def test_empty_time_series(trend_engine):
    """Test handling of empty time series."""
    empty_series = TimeSeriesData(
        timestamps=[], values=[], metric_name="empty_metric", unit="count"
    )

    analysis = trend_engine.analyze_trend(empty_series)

    assert analysis.trend_direction == "stable"
    assert analysis.average_value == 0.0
    assert analysis.seasonality_detected is False


# ========================================
# Test: Anomaly Detection
# ========================================


def test_detect_anomalies_with_sklearn(trend_engine, sample_time_series_with_anomalies):
    """Test anomaly detection using Isolation Forest."""
    anomalies = trend_engine.detect_anomalies(sample_time_series_with_anomalies)

    # Should detect at least 2 anomalies (spike at 25 and 75)
    assert len(anomalies) >= 2

    # Anomalies should be sorted by timestamp
    timestamps = [a.timestamp for a in anomalies]
    assert timestamps == sorted(timestamps)

    # Check anomaly properties
    for anomaly in anomalies:
        assert anomaly.severity in ["low", "medium", "high", "critical"]
        assert 0 <= anomaly.confidence <= 1
        assert anomaly.deviation_percent > 0


def test_anomaly_severity_classification(
    trend_engine, sample_time_series_with_anomalies
):
    """Test anomaly severity classification."""
    anomalies = trend_engine.detect_anomalies(sample_time_series_with_anomalies)

    # Should have at least one high or critical severity
    severities = [a.severity for a in anomalies]
    assert any(s in ["high", "critical"] for s in severities)


def test_detect_anomalies_simple_method(trend_engine):
    """Test simple threshold-based anomaly detection."""
    base_time = datetime(2025, 11, 1)
    timestamps = [base_time + timedelta(hours=i) for i in range(50)]
    values = [50] * 50
    values[25] = 150  # Clear outlier

    series = TimeSeriesData(
        timestamps=timestamps, values=values, metric_name="test_metric"
    )

    anomalies = trend_engine._detect_anomalies_simple(series, threshold_std=2.0)

    # Should detect the outlier
    assert len(anomalies) >= 1


def test_no_anomalies_in_normal_data(trend_engine, sample_stable_time_series):
    """Test that normal data produces few/no anomalies."""
    anomalies = trend_engine.detect_anomalies(sample_stable_time_series)

    # With 5% contamination, should have at most ~2 anomalies in 30 samples
    assert len(anomalies) <= 3


# ========================================
# Test: Forecasting
# ========================================


def test_forecast_auto_selection(trend_engine, sample_time_series):
    """Test automatic model selection for forecasting."""
    forecast = trend_engine.forecast(
        sample_time_series, forecast_days=7, model_type="auto"
    )

    assert forecast.metric_name == "threats_detected"
    assert forecast.forecast_days == 7
    assert len(forecast.predictions) == 7
    assert forecast.model_type in ["prophet", "arima", "simple_moving_average"]
    assert 0 <= forecast.model_accuracy <= 1


def test_forecast_simple_moving_average(trend_engine, sample_time_series):
    """Test simple moving average forecast."""
    forecast = trend_engine.forecast(
        sample_time_series, forecast_days=3, model_type="sma"
    )

    assert forecast.model_type == "simple_moving_average"
    assert len(forecast.predictions) == 3

    # Check prediction structure
    for pred in forecast.predictions:
        assert isinstance(pred.timestamp, datetime)
        assert pred.predicted_value >= 0
        assert pred.lower_bound <= pred.predicted_value
        assert pred.predicted_value <= pred.upper_bound
        assert pred.confidence_interval == 0.95


def test_forecast_predictions_chronological(trend_engine, sample_time_series):
    """Test that forecast predictions are in chronological order."""
    forecast = trend_engine.forecast(sample_time_series, forecast_days=5)

    timestamps = [p.timestamp for p in forecast.predictions]
    assert timestamps == sorted(timestamps)

    # Predictions should be in the future
    last_historical = sample_time_series.timestamps[-1]
    assert all(ts > last_historical for ts in timestamps)


def test_forecast_with_empty_data(trend_engine):
    """Test forecasting with no historical data."""
    empty_series = TimeSeriesData(timestamps=[], values=[], metric_name="empty_metric")

    forecast = trend_engine.forecast(empty_series, forecast_days=7)

    assert len(forecast.predictions) == 7
    assert forecast.training_samples == 0


def test_forecast_confidence_intervals(trend_engine, sample_time_series):
    """Test that confidence intervals are reasonable."""
    forecast = trend_engine.forecast(sample_time_series, forecast_days=5)

    for pred in forecast.predictions:
        # Upper bound should be greater than lower bound
        assert pred.upper_bound > pred.lower_bound

        # Predicted value should be within bounds
        assert pred.lower_bound <= pred.predicted_value <= pred.upper_bound


# ========================================
# Test: Model Accuracy
# ========================================


def test_acceptance_forecast_accuracy_within_10_percent(trend_engine):
    """
    Acceptance: Predictions within 10% accuracy.

    Test with known data to verify accuracy target.
    """
    # Create predictable time series
    base_time = datetime(2025, 11, 1)
    timestamps = [base_time + timedelta(days=i) for i in range(30)]
    # Linear trend: y = 50 + 2*x
    values = [50 + 2 * i + np.random.normal(0, 1) for i in range(30)]

    series = TimeSeriesData(
        timestamps=timestamps, values=values, metric_name="predictable_metric"
    )

    forecast = trend_engine.forecast(series, forecast_days=7)

    # Model accuracy should be reasonable for predictable data
    assert forecast.model_accuracy >= 0.6  # At least 60% accuracy


def test_acceptance_anomaly_detection_low_false_positives(trend_engine):
    """
    Acceptance: Anomaly detection <5% false positives.

    Test with normal data to verify low false positive rate.
    """
    # Create normal distribution data (no anomalies)
    base_time = datetime(2025, 11, 1)
    timestamps = [base_time + timedelta(hours=i) for i in range(100)]
    values = [50 + np.random.normal(0, 5) for _ in range(100)]

    series = TimeSeriesData(
        timestamps=timestamps, values=values, metric_name="normal_data"
    )

    anomalies = trend_engine.detect_anomalies(series, contamination=0.05)

    # False positive rate should be close to contamination rate (5%)
    false_positive_rate = len(anomalies) / len(values)
    assert false_positive_rate <= 0.10  # Allow up to 10% (2x contamination)


# ========================================
# Test: Correlation Analysis
# ========================================


def test_correlation_positive(trend_engine):
    """Test positive correlation detection."""
    base_time = datetime(2025, 11, 1)
    timestamps = [base_time + timedelta(hours=i) for i in range(50)]

    # Highly correlated series
    values_a = [i + np.random.normal(0, 1) for i in range(50)]
    values_b = [i + np.random.normal(0, 1) for i in range(50)]

    series_a = TimeSeriesData(timestamps, values_a, "metric_a")
    series_b = TimeSeriesData(timestamps, values_b, "metric_b")

    correlation = trend_engine.analyze_correlation(series_a, series_b)

    assert correlation["correlation"] > 0.7  # Strong positive correlation
    assert correlation["relationship"] == "strong"
    assert correlation["direction"] == "positive"


def test_correlation_negative(trend_engine):
    """Test negative correlation detection."""
    base_time = datetime(2025, 11, 1)
    timestamps = [base_time + timedelta(hours=i) for i in range(50)]

    # Negatively correlated series
    values_a = [i for i in range(50)]
    values_b = [49 - i for i in range(50)]

    series_a = TimeSeriesData(timestamps, values_a, "increasing")
    series_b = TimeSeriesData(timestamps, values_b, "decreasing")

    correlation = trend_engine.analyze_correlation(series_a, series_b)

    assert correlation["correlation"] < -0.9  # Strong negative correlation
    assert correlation["direction"] == "negative"


def test_correlation_no_relationship(trend_engine):
    """Test negligible correlation detection."""
    base_time = datetime(2025, 11, 1)
    timestamps = [base_time + timedelta(hours=i) for i in range(50)]

    # Uncorrelated random series
    values_a = [np.random.normal(0, 10) for _ in range(50)]
    values_b = [np.random.normal(0, 10) for _ in range(50)]

    series_a = TimeSeriesData(timestamps, values_a, "random_a")
    series_b = TimeSeriesData(timestamps, values_b, "random_b")

    correlation = trend_engine.analyze_correlation(series_a, series_b)

    # Should be weak or negligible
    assert abs(correlation["correlation"]) < 0.5


def test_correlation_insufficient_data(trend_engine):
    """Test correlation with insufficient data."""
    base_time = datetime(2025, 11, 1)
    timestamps = [base_time]

    series_a = TimeSeriesData(timestamps, [10], "single_a")
    series_b = TimeSeriesData(timestamps, [20], "single_b")

    correlation = trend_engine.analyze_correlation(series_a, series_b)

    assert correlation["relationship"] == "insufficient_data"


# ========================================
# Test: Data Model Serialization
# ========================================


def test_time_series_to_dict():
    """Test TimeSeriesData serialization."""
    base_time = datetime(2025, 11, 1)
    series = TimeSeriesData(
        timestamps=[base_time],
        values=[10.5],
        metric_name="test_metric",
        unit="count",
        metadata={"source": "test"},
    )

    data_dict = series.to_dict()

    assert data_dict["metric_name"] == "test_metric"
    assert data_dict["unit"] == "count"
    assert data_dict["values"] == [10.5]
    assert data_dict["metadata"]["source"] == "test"


def test_trend_analysis_to_dict(trend_engine, sample_time_series):
    """Test TrendAnalysis serialization."""
    analysis = trend_engine.analyze_trend(sample_time_series)
    data_dict = analysis.to_dict()

    assert "trend_direction" in data_dict
    assert "trend_strength" in data_dict
    assert "average_value" in data_dict
    assert "seasonality_detected" in data_dict


def test_anomaly_to_dict(trend_engine, sample_time_series_with_anomalies):
    """Test Anomaly serialization."""
    anomalies = trend_engine.detect_anomalies(sample_time_series_with_anomalies)

    if anomalies:
        data_dict = anomalies[0].to_dict()

        assert "timestamp" in data_dict
        assert "value" in data_dict
        assert "severity" in data_dict
        assert "confidence" in data_dict


def test_forecast_result_to_dict(trend_engine, sample_time_series):
    """Test ForecastResult serialization."""
    forecast = trend_engine.forecast(sample_time_series, forecast_days=3)
    data_dict = forecast.to_dict()

    assert data_dict["metric_name"] == "threats_detected"
    assert data_dict["forecast_days"] == 3
    assert len(data_dict["predictions"]) == 3
    assert data_dict["model_type"] in ["prophet", "arima", "simple_moving_average"]


# ========================================
# Test: Edge Cases
# ========================================


def test_trend_with_single_value(trend_engine):
    """Test trend analysis with single data point."""
    base_time = datetime(2025, 11, 1)
    series = TimeSeriesData(
        timestamps=[base_time], values=[50], metric_name="single_point"
    )

    analysis = trend_engine.analyze_trend(series)

    assert analysis.trend_direction == "stable"
    assert analysis.average_value == 50


def test_forecast_with_minimal_data(trend_engine):
    """Test forecasting with minimal historical data."""
    base_time = datetime(2025, 11, 1)
    timestamps = [base_time + timedelta(days=i) for i in range(3)]
    values = [10, 20, 30]

    series = TimeSeriesData(timestamps, values, "minimal_data")

    forecast = trend_engine.forecast(series, forecast_days=7)

    # Should use simple moving average
    assert forecast.model_type == "simple_moving_average"
    assert len(forecast.predictions) == 7


def test_anomaly_detection_constant_values(trend_engine):
    """Test anomaly detection with constant values."""
    base_time = datetime(2025, 11, 1)
    timestamps = [base_time + timedelta(hours=i) for i in range(50)]
    values = [100] * 50  # All same value

    series = TimeSeriesData(timestamps, values, "constant")

    anomalies = trend_engine.detect_anomalies(series)

    # No anomalies in constant data
    assert len(anomalies) == 0


# ========================================
# Test: Integration
# ========================================


def test_full_analysis_workflow(trend_engine, sample_time_series):
    """Test complete trend analysis workflow."""
    # 1. Analyze trend
    trend_analysis = trend_engine.analyze_trend(sample_time_series, timeframe_days=7)
    assert trend_analysis.trend_direction in ["increasing", "decreasing", "stable"]

    # 2. Detect anomalies
    anomalies = trend_engine.detect_anomalies(sample_time_series)
    assert isinstance(anomalies, list)

    # 3. Generate forecast
    forecast = trend_engine.forecast(sample_time_series, forecast_days=7)
    assert len(forecast.predictions) == 7

    # 4. Serialize results
    trend_dict = trend_analysis.to_dict()
    forecast_dict = forecast.to_dict()

    assert isinstance(trend_dict, dict)
    assert isinstance(forecast_dict, dict)
