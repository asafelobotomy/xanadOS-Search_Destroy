"""
Trend Analysis & Predictive Forecasting for xanadOS Search & Destroy.

This module provides:
- Historical trend analysis (7d, 30d, 90d, 1y)
- Anomaly detection in security metrics
- Predictive threat forecasting (ARIMA/Prophet)
- Seasonality analysis
- Correlation analysis

Phase 2, Task 2.3.2: Trend Analysis & Predictions
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from collections import defaultdict
import json

# Optional ML dependencies
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning(
        "scikit-learn not installed. Install with: pip install scikit-learn>=1.3.0"
    )

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logging.warning(
        "statsmodels not installed. Install with: pip install statsmodels>=0.14.0"
    )

try:
    from prophet import Prophet

    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logging.warning("Prophet not installed. Install with: pip install prophet>=1.1")


logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class TimeSeriesData:
    """Time series data container."""

    timestamps: list[datetime]
    values: list[float]
    metric_name: str
    unit: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamps": [ts.isoformat() for ts in self.timestamps],
            "values": self.values,
            "metric_name": self.metric_name,
            "unit": self.unit,
            "metadata": self.metadata,
        }


@dataclass
class TrendAnalysis:
    """Trend analysis results."""

    metric_name: str
    timeframe_days: int
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_strength: float  # 0-1, 1 being strongest
    average_value: float
    min_value: float
    max_value: float
    std_deviation: float
    growth_rate_percent: float
    seasonality_detected: bool
    seasonal_period: int | None = None  # In hours/days

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_name": self.metric_name,
            "timeframe_days": self.timeframe_days,
            "trend_direction": self.trend_direction,
            "trend_strength": self.trend_strength,
            "average_value": self.average_value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "std_deviation": self.std_deviation,
            "growth_rate_percent": self.growth_rate_percent,
            "seasonality_detected": self.seasonality_detected,
            "seasonal_period": self.seasonal_period,
        }


@dataclass
class Anomaly:
    """Detected anomaly."""

    timestamp: datetime
    value: float
    expected_value: float
    deviation_percent: float
    severity: str  # "low", "medium", "high", "critical"
    confidence: float  # 0-1
    description: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "expected_value": self.expected_value,
            "deviation_percent": self.deviation_percent,
            "severity": self.severity,
            "confidence": self.confidence,
            "description": self.description,
        }


@dataclass
class Prediction:
    """Forecast prediction."""

    timestamp: datetime
    predicted_value: float
    lower_bound: float  # Lower confidence interval
    upper_bound: float  # Upper confidence interval
    confidence_interval: float  # e.g., 0.95 for 95% CI

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "predicted_value": self.predicted_value,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "confidence_interval": self.confidence_interval,
        }


@dataclass
class ForecastResult:
    """Complete forecast result."""

    metric_name: str
    forecast_days: int
    predictions: list[Prediction]
    model_type: str  # "arima", "prophet", "simple_moving_average"
    model_accuracy: float  # 0-1, based on validation
    training_samples: int
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_name": self.metric_name,
            "forecast_days": self.forecast_days,
            "predictions": [p.to_dict() for p in self.predictions],
            "model_type": self.model_type,
            "model_accuracy": self.model_accuracy,
            "training_samples": self.training_samples,
            "generated_at": self.generated_at,
        }


# ============================================================================
# Trend Analysis Engine
# ============================================================================


class TrendAnalysisEngine:
    """
    Advanced trend analysis and forecasting engine.

    Features:
    - Historical trend analysis (multiple timeframes)
    - Anomaly detection using Isolation Forest
    - Predictive forecasting (ARIMA, Prophet, simple methods)
    - Seasonality detection and analysis
    """

    def __init__(self):
        """Initialize trend analysis engine."""
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.anomaly_detector = None
        logger.info("TrendAnalysisEngine initialized")

    # ========================================
    # Trend Analysis
    # ========================================

    def analyze_trend(
        self, time_series: TimeSeriesData, timeframe_days: int = 30
    ) -> TrendAnalysis:
        """
        Analyze trend in time series data.

        Args:
            time_series: Time series data to analyze
            timeframe_days: Number of days to analyze

        Returns:
            TrendAnalysis with trend metrics
        """
        values = np.array(time_series.values)

        if len(values) == 0:
            return self._empty_trend_analysis(time_series.metric_name, timeframe_days)

        # Basic statistics
        avg_value = float(np.mean(values))
        min_value = float(np.min(values))
        max_value = float(np.max(values))
        std_dev = float(np.std(values))

        # Calculate trend direction and strength
        if len(values) >= 2:
            # Linear regression slope
            x = np.arange(len(values))
            coeffs = np.polyfit(x, values, 1)
            slope = coeffs[0]

            # Normalize slope by average value
            normalized_slope = slope / (avg_value if avg_value != 0 else 1)

            # Determine direction
            if abs(normalized_slope) < 0.01:  # < 1% change per period
                direction = "stable"
                strength = 0.0
            elif normalized_slope > 0:
                direction = "increasing"
                strength = min(abs(normalized_slope) * 100, 1.0)
            else:
                direction = "decreasing"
                strength = min(abs(normalized_slope) * 100, 1.0)

            # Calculate growth rate
            if len(values) >= 7:
                recent_avg = np.mean(values[-7:])
                earlier_avg = np.mean(values[:7])
                growth_rate = ((recent_avg - earlier_avg) / max(earlier_avg, 1)) * 100
            else:
                growth_rate = 0.0
        else:
            direction = "stable"
            strength = 0.0
            growth_rate = 0.0

        # Detect seasonality
        seasonality_detected, seasonal_period = self._detect_seasonality(values)

        return TrendAnalysis(
            metric_name=time_series.metric_name,
            timeframe_days=timeframe_days,
            trend_direction=direction,
            trend_strength=strength,
            average_value=avg_value,
            min_value=min_value,
            max_value=max_value,
            std_deviation=std_dev,
            growth_rate_percent=growth_rate,
            seasonality_detected=seasonality_detected,
            seasonal_period=seasonal_period,
        )

    def _detect_seasonality(
        self, values: np.ndarray, threshold: float = 0.3
    ) -> tuple[bool, int | None]:
        """
        Detect seasonality in time series using autocorrelation.

        Args:
            values: Time series values
            threshold: Correlation threshold (0-1)

        Returns:
            Tuple of (seasonality_detected, seasonal_period)
        """
        if len(values) < 14:  # Need at least 2 weeks
            return False, None

        # Calculate autocorrelation for different lags
        max_lag = min(len(values) // 2, 168)  # Up to 1 week (168 hours)

        best_period = None
        best_correlation = 0.0

        for lag in range(12, max_lag):  # Start from 12 hours
            correlation = np.corrcoef(values[:-lag], values[lag:])[0, 1]

            if correlation > best_correlation:
                best_correlation = correlation
                best_period = lag

        if best_correlation > threshold:
            return True, best_period

        return False, None

    def _empty_trend_analysis(
        self, metric_name: str, timeframe_days: int
    ) -> TrendAnalysis:
        """Create empty trend analysis for no data."""
        return TrendAnalysis(
            metric_name=metric_name,
            timeframe_days=timeframe_days,
            trend_direction="stable",
            trend_strength=0.0,
            average_value=0.0,
            min_value=0.0,
            max_value=0.0,
            std_deviation=0.0,
            growth_rate_percent=0.0,
            seasonality_detected=False,
            seasonal_period=None,
        )

    # ========================================
    # Anomaly Detection
    # ========================================

    def detect_anomalies(
        self,
        time_series: TimeSeriesData,
        contamination: float = 0.05,  # Expected anomaly rate (5%)
    ) -> list[Anomaly]:
        """
        Detect anomalies in time series data using Isolation Forest.

        Args:
            time_series: Time series data to analyze
            contamination: Expected proportion of anomalies (0-0.5)

        Returns:
            List of detected anomalies
        """
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, using simple threshold method")
            return self._detect_anomalies_simple(time_series)

        values = np.array(time_series.values).reshape(-1, 1)

        if len(values) < 10:  # Need minimum data
            return []

        # Train Isolation Forest
        iso_forest = IsolationForest(
            contamination=contamination, random_state=42, n_estimators=100
        )

        predictions = iso_forest.fit_predict(values)
        anomaly_scores = iso_forest.score_samples(values)

        # Identify anomalies
        anomalies = []
        mean_value = float(np.mean(values))
        std_value = float(np.std(values))

        for i, (pred, score) in enumerate(zip(predictions, anomaly_scores)):
            if pred == -1:  # Anomaly detected
                value = float(values[i][0])
                deviation = abs(value - mean_value)
                deviation_percent = (deviation / max(mean_value, 1)) * 100

                # Determine severity
                if deviation > 3 * std_value:
                    severity = "critical"
                elif deviation > 2 * std_value:
                    severity = "high"
                elif deviation > std_value:
                    severity = "medium"
                else:
                    severity = "low"

                # Confidence based on anomaly score
                confidence = min(1.0, abs(score) / 0.5)

                description = f"{time_series.metric_name} anomaly: {value:.2f} (expected ~{mean_value:.2f})"

                anomalies.append(
                    Anomaly(
                        timestamp=time_series.timestamps[i],
                        value=value,
                        expected_value=mean_value,
                        deviation_percent=deviation_percent,
                        severity=severity,
                        confidence=confidence,
                        description=description,
                    )
                )

        return sorted(anomalies, key=lambda a: a.timestamp)

    def _detect_anomalies_simple(
        self, time_series: TimeSeriesData, threshold_std: float = 2.5
    ) -> list[Anomaly]:
        """
        Simple anomaly detection using standard deviation threshold.

        Args:
            time_series: Time series data
            threshold_std: Number of standard deviations for threshold

        Returns:
            List of anomalies
        """
        values = np.array(time_series.values)

        if len(values) < 3:
            return []

        mean_value = float(np.mean(values))
        std_value = float(np.std(values))
        threshold = threshold_std * std_value

        anomalies = []

        for i, value in enumerate(values):
            deviation = abs(value - mean_value)

            if deviation > threshold:
                deviation_percent = (deviation / max(mean_value, 1)) * 100

                # Severity based on deviation
                if deviation > 3 * std_value:
                    severity = "critical"
                elif deviation > 2.5 * std_value:
                    severity = "high"
                elif deviation > 2 * std_value:
                    severity = "medium"
                else:
                    severity = "low"

                confidence = min(1.0, deviation / (4 * std_value))

                anomalies.append(
                    Anomaly(
                        timestamp=time_series.timestamps[i],
                        value=value,
                        expected_value=mean_value,
                        deviation_percent=deviation_percent,
                        severity=severity,
                        confidence=confidence,
                        description=f"Value {value:.2f} deviates from mean {mean_value:.2f}",
                    )
                )

        return sorted(anomalies, key=lambda a: a.timestamp)

    # ========================================
    # Predictive Forecasting
    # ========================================

    def forecast(
        self,
        time_series: TimeSeriesData,
        forecast_days: int = 7,
        model_type: str = "auto",  # "auto", "arima", "prophet", "sma"
    ) -> ForecastResult:
        """
        Forecast future values using time series models.

        Args:
            time_series: Historical time series data
            forecast_days: Number of days to forecast
            model_type: Model to use ("auto" selects best available)

        Returns:
            ForecastResult with predictions
        """
        # Auto-select model based on availability and data size
        if model_type == "auto":
            if PROPHET_AVAILABLE and len(time_series.values) >= 30:
                model_type = "prophet"
            elif STATSMODELS_AVAILABLE and len(time_series.values) >= 20:
                model_type = "arima"
            else:
                model_type = "sma"  # Simple moving average fallback

        # Route to appropriate model
        if model_type == "prophet" and PROPHET_AVAILABLE:
            return self._forecast_prophet(time_series, forecast_days)
        elif model_type == "arima" and STATSMODELS_AVAILABLE:
            return self._forecast_arima(time_series, forecast_days)
        else:
            return self._forecast_simple_ma(time_series, forecast_days)

    def _forecast_prophet(
        self, time_series: TimeSeriesData, forecast_days: int
    ) -> ForecastResult:
        """Forecast using Facebook Prophet."""
        import pandas as pd

        # Prepare data for Prophet
        df = pd.DataFrame({"ds": time_series.timestamps, "y": time_series.values})

        # Initialize and fit model
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,
            interval_width=0.95,
        )

        # Suppress Prophet output
        import logging as std_logging

        prophet_logger = std_logging.getLogger("prophet")
        prophet_logger.setLevel(std_logging.ERROR)

        model.fit(df)

        # Make future dataframe
        future = model.make_future_dataframe(periods=forecast_days, freq="D")
        forecast_df = model.predict(future)

        # Extract predictions (last forecast_days)
        predictions = []
        forecast_rows = forecast_df.tail(forecast_days)

        for _, row in forecast_rows.iterrows():
            predictions.append(
                Prediction(
                    timestamp=row["ds"].to_pydatetime(),
                    predicted_value=float(row["yhat"]),
                    lower_bound=float(row["yhat_lower"]),
                    upper_bound=float(row["yhat_upper"]),
                    confidence_interval=0.95,
                )
            )

        # Calculate model accuracy (MAPE on training data)
        actual = df["y"].values
        predicted = forecast_df["yhat"].values[: len(actual)]
        mape = np.mean(np.abs((actual - predicted) / np.maximum(actual, 1))) * 100
        accuracy = max(0.0, 1.0 - (mape / 100))

        return ForecastResult(
            metric_name=time_series.metric_name,
            forecast_days=forecast_days,
            predictions=predictions,
            model_type="prophet",
            model_accuracy=accuracy,
            training_samples=len(time_series.values),
        )

    def _forecast_arima(
        self, time_series: TimeSeriesData, forecast_days: int
    ) -> ForecastResult:
        """Forecast using ARIMA model."""
        values = np.array(time_series.values)

        # Fit ARIMA model (auto-selected order)
        # Try simple ARIMA(1,1,1) first
        try:
            model = ARIMA(values, order=(1, 1, 1))
            fitted_model = model.fit()

            # Forecast
            forecast_result = fitted_model.forecast(steps=forecast_days)

            # Get confidence intervals
            forecast_obj = fitted_model.get_forecast(steps=forecast_days)
            conf_int = forecast_obj.conf_int(alpha=0.05)  # 95% CI

            # Create predictions
            predictions = []
            last_timestamp = time_series.timestamps[-1]

            for i in range(forecast_days):
                pred_timestamp = last_timestamp + timedelta(days=i + 1)

                predictions.append(
                    Prediction(
                        timestamp=pred_timestamp,
                        predicted_value=float(forecast_result[i]),
                        lower_bound=float(conf_int[i, 0]),
                        upper_bound=float(conf_int[i, 1]),
                        confidence_interval=0.95,
                    )
                )

            # Calculate accuracy (in-sample)
            fitted_values = fitted_model.fittedvalues
            actual = values[1:]  # ARIMA(1,1,1) loses first value
            mape = (
                np.mean(np.abs((actual - fitted_values) / np.maximum(actual, 1))) * 100
            )
            accuracy = max(0.0, 1.0 - (mape / 100))

            return ForecastResult(
                metric_name=time_series.metric_name,
                forecast_days=forecast_days,
                predictions=predictions,
                model_type="arima",
                model_accuracy=accuracy,
                training_samples=len(values),
            )

        except Exception as e:
            logger.warning(f"ARIMA fitting failed: {e}, falling back to simple MA")
            return self._forecast_simple_ma(time_series, forecast_days)

    def _forecast_simple_ma(
        self, time_series: TimeSeriesData, forecast_days: int, window: int = 7
    ) -> ForecastResult:
        """Simple moving average forecast (fallback)."""
        values = np.array(time_series.values)

        if len(values) == 0:
            # No data, predict zeros
            predictions = []
            last_timestamp = datetime.utcnow()

            for i in range(forecast_days):
                pred_timestamp = last_timestamp + timedelta(days=i + 1)
                predictions.append(
                    Prediction(
                        timestamp=pred_timestamp,
                        predicted_value=0.0,
                        lower_bound=0.0,
                        upper_bound=0.0,
                        confidence_interval=0.95,
                    )
                )

            return ForecastResult(
                metric_name=time_series.metric_name,
                forecast_days=forecast_days,
                predictions=predictions,
                model_type="simple_moving_average",
                model_accuracy=0.0,
                training_samples=0,
            )

        # Calculate moving average
        window_size = min(window, len(values))
        ma_value = float(np.mean(values[-window_size:]))

        # Estimate std for confidence interval
        std_value = float(np.std(values[-window_size:]))

        # Create predictions (flat forecast)
        predictions = []
        last_timestamp = time_series.timestamps[-1]

        for i in range(forecast_days):
            pred_timestamp = last_timestamp + timedelta(days=i + 1)

            predictions.append(
                Prediction(
                    timestamp=pred_timestamp,
                    predicted_value=ma_value,
                    lower_bound=max(0, ma_value - 1.96 * std_value),  # 95% CI
                    upper_bound=ma_value + 1.96 * std_value,
                    confidence_interval=0.95,
                )
            )

        # Estimate accuracy
        if len(values) >= window_size:
            actual = values[-window_size:]
            mape = np.mean(np.abs((actual - ma_value) / np.maximum(actual, 1))) * 100
            accuracy = max(0.0, 1.0 - (mape / 100))
        else:
            accuracy = 0.5  # Default accuracy for simple method

        return ForecastResult(
            metric_name=time_series.metric_name,
            forecast_days=forecast_days,
            predictions=predictions,
            model_type="simple_moving_average",
            model_accuracy=accuracy,
            training_samples=len(values),
        )

    # ========================================
    # Correlation Analysis
    # ========================================

    def analyze_correlation(
        self, series_a: TimeSeriesData, series_b: TimeSeriesData
    ) -> dict[str, Any]:
        """
        Analyze correlation between two time series.

        Args:
            series_a: First time series
            series_b: Second time series

        Returns:
            Dictionary with correlation metrics
        """
        # Ensure same length
        min_len = min(len(series_a.values), len(series_b.values))

        if min_len < 2:
            return {
                "correlation": 0.0,
                "p_value": 1.0,
                "relationship": "insufficient_data",
            }

        values_a = np.array(series_a.values[:min_len])
        values_b = np.array(series_b.values[:min_len])

        # Calculate Pearson correlation
        correlation = np.corrcoef(values_a, values_b)[0, 1]

        # Determine relationship strength
        if abs(correlation) > 0.7:
            relationship = "strong"
        elif abs(correlation) > 0.4:
            relationship = "moderate"
        elif abs(correlation) > 0.2:
            relationship = "weak"
        else:
            relationship = "negligible"

        # Direction
        direction = "positive" if correlation > 0 else "negative"

        return {
            "metric_a": series_a.metric_name,
            "metric_b": series_b.metric_name,
            "correlation": float(correlation),
            "relationship": relationship,
            "direction": direction,
            "samples": min_len,
        }
