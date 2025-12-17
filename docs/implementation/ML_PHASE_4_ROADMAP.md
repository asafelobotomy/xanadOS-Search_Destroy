# ML Phase 4: Complete ML Integration Roadmap

**Status**: Planning Phase
**Created**: 2025-12-17
**Target Completion**: 4-6 weeks
**Current ML Model**: v1.1.0 (100% test accuracy, PRODUCTION)

---

## Executive Summary

This roadmap details the complete integration of ML-based malware detection into xanadOS Search & Destroy, covering all four implementation tracks:

- **[A] Deep Learning Models** - Advanced neural architectures
- **[B] Integration & Deployment** - Production system integration
- **[C] Advanced ML Techniques** - Gradient boosting and ensembles
- **[D] Production Hardening** - Monitoring and automation

**Key Strategy**: Parallel development with incremental integration, prioritizing quick wins and high-impact features.

---

## Phase Overview

```
Week 1-2: Quick Wins (Integration + Basic Hardening)
   ├─ [B1] UnifiedScannerEngine integration
   ├─ [B2] REST API endpoint
   ├─ [D1] Basic monitoring dashboard
   └─ [D2] Model performance tracking

Week 2-3: Advanced Models (Parallel Development)
   ├─ [C1] XGBoost/LightGBM training
   ├─ [C2] Ensemble methods (voting/stacking)
   └─ [A1] CNN architecture design

Week 3-4: Deep Learning Exploration
   ├─ [A2] CNN training on raw bytes
   ├─ [A3] LSTM for sequential patterns
   └─ [A4] Model comparison & selection

Week 4-5: Production Hardening
   ├─ [D3] A/B testing framework
   ├─ [D4] Automated retraining pipeline
   └─ [D5] Adversarial robustness testing

Week 5-6: Final Integration & Polish
   ├─ GUI integration (all models)
   ├─ Performance optimization
   ├─ Documentation & deployment guides
   └─ Production release preparation
```

---

## Track A: Deep Learning Models

**Goal**: Explore neural network architectures for malware detection
**Priority**: Medium (parallel development, experimental)
**Risk**: High (may not outperform Random Forest on small dataset)
**Dependencies**: Requires PyTorch (already installed)

### A1: CNN for Binary Classification (Week 3)

**Objective**: Train CNN on raw byte sequences

**Implementation**:
```python
# Architecture: 1D-CNN for byte sequences
- Input: Raw bytes (first 2048 bytes of file)
- Conv1D layers: 3-4 layers with increasing filters
- MaxPooling for dimensionality reduction
- Dense layers: 2 hidden layers
- Output: Binary classification (malware/benign)
```

**Tasks**:
1. Create data loader for raw bytes
   - Read first N bytes from malware/benign samples
   - Normalize byte values (0-255 → 0-1)
   - Create PyTorch Dataset/DataLoader

2. Design CNN architecture (`app/ml/deep_learning.py`)
   - Conv1D(256, 128) → ReLU → MaxPool
   - Conv1D(128, 64) → ReLU → MaxPool
   - Flatten → Dense(256) → Dropout(0.5)
   - Dense(1) → Sigmoid

3. Training loop
   - Loss: Binary Cross-Entropy
   - Optimizer: Adam (lr=0.001)
   - Batch size: 32
   - Epochs: 50 with early stopping
   - Monitor validation loss

4. Evaluation & comparison
   - Compare with Random Forest baseline
   - Analyze feature learning (conv filters)
   - Generate confusion matrix

**Expected Outcome**: 85-95% accuracy (may not beat RF due to small dataset)

**Files to Create**:
- `app/ml/cnn_malware_detector.py` (CNN model class)
- `scripts/ml/train_cnn.py` (training script)
- `scripts/ml/prepare_raw_bytes.py` (data preprocessing)

**Time Estimate**: 3-5 days

---

### A2: LSTM for Sequential Patterns (Week 3-4)

**Objective**: Capture sequential byte patterns with LSTM

**Architecture**:
```python
- Input: Byte sequences (chunks of 512 bytes)
- Embedding: Map bytes 0-255 to 128D vectors
- LSTM(128 hidden units, 2 layers, bidirectional)
- Attention layer (optional)
- Dense classifier
```

**Tasks**:
1. Sequence preprocessing
   - Split files into fixed-length sequences
   - Pad/truncate to uniform length
   - Create sequence batches

2. LSTM model (`app/ml/lstm_detector.py`)
   - Embedding layer for byte values
   - Bidirectional LSTM
   - Attention mechanism (optional)
   - Classification head

3. Training with sequence batching
   - Handle variable-length sequences
   - Gradient clipping (prevent exploding gradients)
   - Learning rate scheduling

4. Evaluation
   - Test on unseen samples
   - Analyze attention weights (if used)
   - Compare inference speed vs RF

**Expected Outcome**: 80-90% accuracy, slower inference than CNN

**Files to Create**:
- `app/ml/lstm_detector.py`
- `scripts/ml/train_lstm.py`
- `scripts/ml/prepare_sequences.py`

**Time Estimate**: 4-6 days

---

### A3: Model Comparison & Selection (Week 4)

**Tasks**:
1. Standardized evaluation across all models
   - Same test set for all (90 samples)
   - Metrics: accuracy, precision, recall, F1, AUC
   - Inference time benchmarks

2. Create comparison dashboard
   - Side-by-side performance table
   - ROC curve comparison
   - Confusion matrix grid

3. Model selection criteria
   - Accuracy (primary)
   - Inference speed (secondary)
   - Model size (tertiary)
   - Interpretability

**Deliverable**: `docs/implementation/MODEL_COMPARISON_REPORT.md`

**Time Estimate**: 2 days

---

## Track B: Integration & Deployment

**Goal**: Integrate ML models into production system
**Priority**: HIGH (immediate value)
**Risk**: Low (well-defined integration points)
**Dependencies**: Existing UnifiedScannerEngine, FastAPI backend

### B1: UnifiedScannerEngine Integration (Week 1)

**Objective**: Add ML-based scanning to existing scanner

**Implementation**:

**File**: `app/core/ml_scanner_integration.py`
```python
class MLThreatDetector:
    """ML-based malware detection using production model."""

    def __init__(self):
        self.registry = ModelRegistry()
        self.feature_extractor = FeatureExtractor()
        self.model = self._load_production_model()

    def _load_production_model(self):
        """Load production model from registry."""
        model, metadata = self.registry.load_model(
            name="malware_detector_rf",
            stage="production"
        )
        return model

    def scan_file(self, file_path: Path) -> MLScanResult:
        """Scan file with ML model."""
        # Extract features
        features = self.feature_extractor.extract_features(file_path)

        # Predict
        prediction = self.model.predict([features])[0]
        probability = self.model.predict_proba([features])[0]

        # Create result
        return MLScanResult(
            file_path=str(file_path),
            is_malware=bool(prediction),
            confidence=float(probability[1]),
            model_version=self.model.version,
            detection_time=time.time()
        )
```

**Integration into UnifiedScannerEngine**:
```python
# In app/core/unified_scanner_engine.py

from app.core.ml_scanner_integration import MLThreatDetector

class UnifiedScannerEngine:
    def __init__(self):
        # Existing scanners
        self.clamav = ClamAVWrapper()
        self.yara = YaraScanner()

        # NEW: ML scanner
        self.ml_detector = MLThreatDetector()

    def scan_file(self, file_path: Path) -> ScanResult:
        """Multi-engine scan with ML detection."""
        results = []

        # Traditional scanners
        results.append(self.clamav.scan_file(file_path))
        results.append(self.yara.scan_file(file_path))

        # ML detection
        ml_result = self.ml_detector.scan_file(file_path)
        results.append(ml_result)

        # Aggregate results (weighted voting)
        return self._aggregate_results(results)
```

**Tasks**:
1. Create `MLThreatDetector` class
2. Integrate into `UnifiedScannerEngine.scan_file()`
3. Implement result aggregation logic
4. Add ML toggle in config (`enable_ml_detection: true`)
5. Unit tests for ML scanner
6. Integration tests with real samples

**Expected Outcome**: ML scanning available in all scan operations

**Files to Modify**:
- `app/core/unified_scanner_engine.py` (add ML scanner)
- `app/utils/config.py` (add ML config options)
- `tests/test_core/test_ml_integration.py` (new tests)

**Time Estimate**: 2-3 days

---

### B2: REST API Endpoint (Week 1-2)

**Objective**: Create HTTP endpoint for ML inference

**File**: `app/api/ml_inference.py`
```python
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

app = FastAPI()

class InferenceRequest(BaseModel):
    file_hash: str
    features: list[float]  # Pre-extracted features

class InferenceResponse(BaseModel):
    is_malware: bool
    confidence: float
    model_version: str
    inference_time_ms: float

@app.post("/api/ml/predict")
async def predict_malware(file: UploadFile = File(...)):
    """Predict if uploaded file is malware."""
    # Save temp file
    temp_path = save_upload(file)

    # Extract features
    features = feature_extractor.extract_features(temp_path)

    # Predict
    result = ml_detector.scan_file(temp_path)

    # Clean up
    temp_path.unlink()

    return InferenceResponse(
        is_malware=result.is_malware,
        confidence=result.confidence,
        model_version=result.model_version,
        inference_time_ms=result.detection_time * 1000
    )

@app.get("/api/ml/models")
async def list_models():
    """List available models in registry."""
    registry = ModelRegistry()
    models = registry.list_models(name="malware_detector_rf")
    return {"models": models}

@app.post("/api/ml/models/{version}/promote")
async def promote_model(version: str):
    """Promote model to production."""
    registry = ModelRegistry()
    result = registry.promote_to_production(
        name="malware_detector_rf",
        version=version
    )
    return {"status": "success", "path": str(result)}
```

**Tasks**:
1. Create FastAPI endpoints
2. Add authentication (API key required)
3. Rate limiting (prevent abuse)
4. CORS configuration
5. API documentation (OpenAPI/Swagger)
6. Client SDK for Python (`app/api/ml_client.py`)

**Example API Usage**:
```bash
# Scan a file
curl -X POST http://localhost:8000/api/ml/predict \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@/path/to/suspicious.exe"

# List models
curl http://localhost:8000/api/ml/models

# Promote model
curl -X POST http://localhost:8000/api/ml/models/1.2.0/promote \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Expected Outcome**: REST API for remote ML inference

**Files to Create**:
- `app/api/ml_inference.py` (FastAPI endpoints)
- `app/api/ml_client.py` (Python client SDK)
- `docs/api/ML_API_REFERENCE.md` (API docs)

**Time Estimate**: 3-4 days

---

### B3: GUI Integration (Week 2)

**Objective**: Add ML scanning to PyQt6 GUI

**Implementation**:

**New Widget**: `app/gui/ml_scan_panel.py`
```python
class MLScanPanel(QWidget):
    """Panel for ML-based scanning."""

    def __init__(self):
        super().__init__()
        self.ml_detector = MLThreatDetector()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # ML scanner toggle
        self.ml_enabled = QCheckBox("Enable ML Detection")
        self.ml_enabled.setChecked(True)

        # Model selector
        self.model_selector = QComboBox()
        self.load_available_models()

        # Confidence threshold slider
        self.confidence_threshold = QSlider(Qt.Horizontal)
        self.confidence_threshold.setRange(50, 100)
        self.confidence_threshold.setValue(80)

        # Scan button
        self.scan_btn = QPushButton("Scan with ML")
        self.scan_btn.clicked.connect(self.on_scan_clicked)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels([
            "File", "Verdict", "Confidence", "Model"
        ])

        layout.addWidget(self.ml_enabled)
        layout.addWidget(self.model_selector)
        layout.addWidget(QLabel("Confidence Threshold:"))
        layout.addWidget(self.confidence_threshold)
        layout.addWidget(self.scan_btn)
        layout.addWidget(self.results_table)

        self.setLayout(layout)

    def on_scan_clicked(self):
        """Handle scan button click."""
        file_path = QFileDialog.getOpenFileName(
            self, "Select File to Scan"
        )[0]

        if file_path:
            self.run_scan(Path(file_path))

    def run_scan(self, file_path: Path):
        """Run ML scan in background thread."""
        # Create scan thread
        thread = ScanThread(self.ml_detector, file_path)
        thread.result_ready.connect(self.on_scan_complete)
        thread.start()

    def on_scan_complete(self, result: MLScanResult):
        """Handle scan completion."""
        # Add to results table
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)

        self.results_table.setItem(row, 0, QTableWidgetItem(result.file_path))

        verdict = "MALWARE" if result.is_malware else "CLEAN"
        verdict_item = QTableWidgetItem(verdict)
        if result.is_malware:
            verdict_item.setForeground(QColor("red"))
        else:
            verdict_item.setForeground(QColor("green"))
        self.results_table.setItem(row, 1, verdict_item)

        confidence_pct = f"{result.confidence * 100:.1f}%"
        self.results_table.setItem(row, 2, QTableWidgetItem(confidence_pct))

        self.results_table.setItem(row, 3, QTableWidgetItem(result.model_version))
```

**Integration into MainWindow**:
```python
# In app/gui/main_window.py

def setup_tabs(self):
    # Existing tabs
    self.tabs.addTab(ScanTab(), "Scanner")
    self.tabs.addTab(QuarantineTab(), "Quarantine")

    # NEW: ML Scan tab
    self.tabs.addTab(MLScanPanel(), "ML Detection")
```

**Tasks**:
1. Create `MLScanPanel` widget
2. Add to main window tabs
3. Implement background scanning (threads)
4. Add progress indicators
5. Result visualization (confidence meter)
6. Export results to CSV/JSON

**Expected Outcome**: ML scanning accessible via GUI

**Files to Create/Modify**:
- `app/gui/ml_scan_panel.py` (new widget)
- `app/gui/main_window.py` (add tab)
- `app/gui/scan_thread.py` (background ML scanning)

**Time Estimate**: 3-4 days

---

## Track C: Advanced ML Techniques

**Goal**: Explore gradient boosting and ensemble methods
**Priority**: Medium (performance improvements)
**Risk**: Low (proven techniques)
**Dependencies**: XGBoost, LightGBM (need installation)

### C1: XGBoost/LightGBM Training (Week 2-3)

**Objective**: Train gradient boosting models for comparison

**Implementation**:

**Script**: `scripts/ml/train_xgboost.py`
```python
import xgboost as xgb
from app.ml.training_utils import load_features, compute_metrics

# Load features
X_train, y_train = load_features("train")
X_val, y_val = load_features("val")
X_test, y_test = load_features("test")

# Combine train+val for final training
X_train_val = np.vstack([X_train, X_val])
y_train_val = np.concatenate([y_train, y_val])

# XGBoost hyperparameters
params = {
    'objective': 'binary:logistic',
    'max_depth': 6,
    'learning_rate': 0.1,
    'n_estimators': 200,
    'scale_pos_weight': 5.0,  # Handle class imbalance
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'random_state': 42
}

# Train XGBoost
xgb_model = xgb.XGBClassifier(**params)
xgb_model.fit(
    X_train_val, y_train_val,
    eval_set=[(X_test, y_test)],
    early_stopping_rounds=20,
    verbose=True
)

# Evaluate
y_pred = xgb_model.predict(X_test)
y_pred_proba = xgb_model.predict_proba(X_test)[:, 1]
metrics = compute_metrics(y_test, y_pred, y_pred_proba)

print(f"XGBoost Test Accuracy: {metrics['accuracy']:.4f}")
print(f"Precision: {metrics['precision']:.4f}")
print(f"Recall: {metrics['recall']:.4f}")

# Save model
registry = ModelRegistry()
registry.register_model(xgb_model, metadata, stage="checkpoint")
```

**LightGBM Alternative**:
```python
import lightgbm as lgb

lgb_params = {
    'objective': 'binary',
    'metric': 'binary_logloss',
    'boosting_type': 'gbdt',
    'num_leaves': 31,
    'learning_rate': 0.05,
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'scale_pos_weight': 5.0
}

train_data = lgb.Dataset(X_train_val, label=y_train_val)
test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

lgb_model = lgb.train(
    lgb_params,
    train_data,
    num_boost_round=1000,
    valid_sets=[test_data],
    early_stopping_rounds=50
)
```

**Tasks**:
1. Install XGBoost and LightGBM
   ```bash
   uv add xgboost lightgbm
   ```

2. Create training scripts
   - `scripts/ml/train_xgboost.py`
   - `scripts/ml/train_lightgbm.py`
   - `scripts/ml/tune_xgboost.py` (hyperparameter tuning)

3. Hyperparameter tuning with Optuna
   - Search space: max_depth, learning_rate, n_estimators
   - Objective: maximize validation accuracy
   - 100 trials with 5-fold CV

4. Compare with Random Forest
   - Same test set (90 samples)
   - Metrics: accuracy, speed, model size
   - Feature importance analysis

**Expected Outcome**: XGBoost/LightGBM achieve 95-100% accuracy

**Files to Create**:
- `scripts/ml/train_xgboost.py`
- `scripts/ml/train_lightgbm.py`
- `scripts/ml/tune_gradient_boosting.py`

**Time Estimate**: 3-4 days

---

### C2: Ensemble Methods (Week 3)

**Objective**: Combine multiple models with voting/stacking

**Implementation**:

**Voting Classifier**:
```python
from sklearn.ensemble import VotingClassifier

# Load trained models
rf_model, _ = registry.load_model("malware_detector_rf", "1.1.0")
xgb_model, _ = registry.load_model("malware_detector_xgb", "1.0.0")
lgb_model, _ = registry.load_model("malware_detector_lgb", "1.0.0")

# Create voting ensemble
voting_ensemble = VotingClassifier(
    estimators=[
        ('rf', rf_model),
        ('xgb', xgb_model),
        ('lgb', lgb_model)
    ],
    voting='soft',  # Use predicted probabilities
    weights=[1, 2, 2]  # Weight gradient boosting higher
)

# No additional training needed for soft voting
# Evaluate on test set
y_pred = voting_ensemble.predict(X_test)
metrics = compute_metrics(y_test, y_pred, y_pred_proba)
```

**Stacking Classifier**:
```python
from sklearn.ensemble import StackingClassifier
from sklearn.linear_model import LogisticRegression

# Create stacking ensemble
stacking_ensemble = StackingClassifier(
    estimators=[
        ('rf', rf_model),
        ('xgb', xgb_model),
        ('lgb', lgb_model)
    ],
    final_estimator=LogisticRegression(),
    cv=5  # Use cross-validation for meta-learner
)

# Train meta-learner
stacking_ensemble.fit(X_train_val, y_train_val)

# Evaluate
y_pred = stacking_ensemble.predict(X_test)
metrics = compute_metrics(y_test, y_pred, y_pred_proba)
```

**Tasks**:
1. Implement voting ensemble
2. Implement stacking ensemble
3. Compare ensemble vs individual models
4. Register best ensemble in model registry
5. Create ensemble deployment guide

**Expected Outcome**: Ensemble achieves 99-100% accuracy with better robustness

**Files to Create**:
- `scripts/ml/train_ensemble.py`
- `app/ml/ensemble_detector.py`
- `docs/implementation/ENSEMBLE_GUIDE.md`

**Time Estimate**: 2-3 days

---

### C3: Adversarial Robustness Testing (Week 4)

**Objective**: Test model robustness against evasion attacks

**Implementation**:

**Script**: `scripts/ml/adversarial_testing.py`
```python
"""Test model robustness against adversarial attacks."""

import numpy as np
from app.ml.model_registry import ModelRegistry
from app.ml.feature_extractor import FeatureExtractor

def test_feature_perturbation(model, X_test, y_test, epsilon=0.1):
    """Test robustness to feature perturbation."""
    X_perturbed = X_test + np.random.normal(0, epsilon, X_test.shape)

    # Original predictions
    y_pred_original = model.predict(X_test)

    # Perturbed predictions
    y_pred_perturbed = model.predict(X_perturbed)

    # Calculate prediction flip rate
    flip_rate = np.mean(y_pred_original != y_pred_perturbed)

    return flip_rate

def test_feature_masking(model, X_test, mask_ratio=0.2):
    """Test robustness to feature masking (simulating evasion)."""
    n_features = X_test.shape[1]
    n_mask = int(n_features * mask_ratio)

    X_masked = X_test.copy()
    mask_indices = np.random.choice(n_features, n_mask, replace=False)
    X_masked[:, mask_indices] = 0  # Zero out features

    # Compare predictions
    y_pred_original = model.predict(X_test)
    y_pred_masked = model.predict(X_masked)

    flip_rate = np.mean(y_pred_original != y_pred_masked)

    return flip_rate

# Run tests
registry = ModelRegistry()
model, _ = registry.load_model("malware_detector_rf", stage="production")

X_test, y_test = load_features("test")

print("Adversarial Robustness Tests:")
print(f"Perturbation (ε=0.1): {test_feature_perturbation(model, X_test, y_test):.2%} flip rate")
print(f"Feature Masking (20%): {test_feature_masking(model, X_test):.2%} flip rate")
```

**Tasks**:
1. Implement perturbation attacks
2. Implement feature masking
3. Test against known evasion techniques
4. Document robustness metrics
5. Recommendations for improving robustness

**Expected Outcome**: Robustness report with recommendations

**Files to Create**:
- `scripts/ml/adversarial_testing.py`
- `docs/security/ADVERSARIAL_ROBUSTNESS_REPORT.md`

**Time Estimate**: 2-3 days

---

## Track D: Production Hardening

**Goal**: Make ML system production-ready
**Priority**: HIGH (operational excellence)
**Risk**: Low (infrastructure work)
**Dependencies**: FastAPI, Redis (for caching), Prometheus (for monitoring)

### D1: Model Performance Monitoring (Week 1)

**Objective**: Track model performance in production

**Implementation**:

**File**: `app/ml/monitoring.py`
```python
"""Production model monitoring."""

import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional
import numpy as np

class ModelMonitor:
    """Monitor model performance in production."""

    def __init__(self, log_dir: Path = Path("models/monitoring")):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.metrics_log = self.log_dir / "metrics.jsonl"
        self.predictions_log = self.log_dir / "predictions.jsonl"

    def log_prediction(
        self,
        file_path: str,
        prediction: bool,
        confidence: float,
        model_version: str,
        inference_time_ms: float,
        ground_truth: Optional[bool] = None
    ):
        """Log a single prediction."""
        record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "file_path": file_path,
            "prediction": prediction,
            "confidence": confidence,
            "model_version": model_version,
            "inference_time_ms": inference_time_ms,
            "ground_truth": ground_truth
        }

        with open(self.predictions_log, "a") as f:
            f.write(json.dumps(record) + "\n")

    def compute_metrics(self, time_window_hours: int = 24):
        """Compute metrics over recent predictions."""
        cutoff_time = datetime.now(UTC).timestamp() - (time_window_hours * 3600)

        predictions = []
        ground_truths = []
        confidences = []
        inference_times = []

        # Read recent predictions
        with open(self.predictions_log) as f:
            for line in f:
                record = json.loads(line)
                timestamp = datetime.fromisoformat(record["timestamp"]).timestamp()

                if timestamp >= cutoff_time:
                    predictions.append(record["prediction"])
                    confidences.append(record["confidence"])
                    inference_times.append(record["inference_time_ms"])

                    if record.get("ground_truth") is not None:
                        ground_truths.append(record["ground_truth"])

        metrics = {
            "total_predictions": len(predictions),
            "malware_predictions": sum(predictions),
            "avg_confidence": np.mean(confidences),
            "avg_inference_time_ms": np.mean(inference_times),
            "p95_inference_time_ms": np.percentile(inference_times, 95),
            "p99_inference_time_ms": np.percentile(inference_times, 99)
        }

        # If we have ground truth, compute accuracy
        if ground_truths:
            accuracy = np.mean([
                p == gt for p, gt in zip(predictions, ground_truths)
            ])
            metrics["accuracy"] = accuracy

        return metrics

    def generate_report(self):
        """Generate monitoring report."""
        metrics_24h = self.compute_metrics(time_window_hours=24)
        metrics_7d = self.compute_metrics(time_window_hours=168)

        report = f"""
# Model Monitoring Report
Generated: {datetime.now(UTC).isoformat()}

## Last 24 Hours
- Total Predictions: {metrics_24h['total_predictions']}
- Malware Detected: {metrics_24h['malware_predictions']}
- Average Confidence: {metrics_24h['avg_confidence']:.2%}
- Average Inference Time: {metrics_24h['avg_inference_time_ms']:.2f} ms
- P95 Inference Time: {metrics_24h['p95_inference_time_ms']:.2f} ms
- P99 Inference Time: {metrics_24h['p99_inference_time_ms']:.2f} ms

## Last 7 Days
- Total Predictions: {metrics_7d['total_predictions']}
- Malware Detected: {metrics_7d['malware_predictions']}
- Average Confidence: {metrics_7d['avg_confidence']:.2%}
"""

        if 'accuracy' in metrics_24h:
            report += f"\n- 24h Accuracy: {metrics_24h['accuracy']:.2%}"

        if 'accuracy' in metrics_7d:
            report += f"\n- 7d Accuracy: {metrics_7d['accuracy']:.2%}"

        return report
```

**Dashboard Widget**:
```python
# app/gui/monitoring_dashboard.py

class MonitoringDashboard(QWidget):
    """Real-time monitoring dashboard for ML model."""

    def __init__(self):
        super().__init__()
        self.monitor = ModelMonitor()
        self.setup_ui()

        # Update every 5 seconds
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_metrics)
        self.timer.start(5000)

    def update_metrics(self):
        """Update metrics display."""
        metrics = self.monitor.compute_metrics(time_window_hours=1)

        self.total_predictions_label.setText(
            f"Total Predictions: {metrics['total_predictions']}"
        )
        self.avg_confidence_label.setText(
            f"Avg Confidence: {metrics['avg_confidence']:.1%}"
        )
        self.avg_inference_time_label.setText(
            f"Avg Inference: {metrics['avg_inference_time_ms']:.1f} ms"
        )
```

**Tasks**:
1. Create `ModelMonitor` class
2. Integrate logging into `MLThreatDetector`
3. Create monitoring dashboard widget
4. Add alerting for degraded performance
5. Export metrics to Prometheus format (optional)

**Expected Outcome**: Real-time performance monitoring

**Files to Create**:
- `app/ml/monitoring.py`
- `app/gui/monitoring_dashboard.py`
- `scripts/ml/generate_monitoring_report.py`

**Time Estimate**: 3-4 days

---

### D2: A/B Testing Framework (Week 4)

**Objective**: Compare model versions in production

**Implementation**:

**File**: `app/ml/ab_testing.py`
```python
"""A/B testing framework for model comparison."""

import random
from dataclasses import dataclass
from typing import Dict

@dataclass
class ABTestConfig:
    """A/B test configuration."""
    test_name: str
    model_a: str  # e.g., "v1.0.0"
    model_b: str  # e.g., "v1.1.0"
    traffic_split: float  # 0.0-1.0, % of traffic to B
    enabled: bool = True

class ABTestManager:
    """Manage A/B tests for model comparison."""

    def __init__(self):
        self.registry = ModelRegistry()
        self.monitor = ModelMonitor()
        self.active_tests: Dict[str, ABTestConfig] = {}

    def create_test(
        self,
        test_name: str,
        model_a: str,
        model_b: str,
        traffic_split: float = 0.5
    ):
        """Create new A/B test."""
        config = ABTestConfig(
            test_name=test_name,
            model_a=model_a,
            model_b=model_b,
            traffic_split=traffic_split
        )

        self.active_tests[test_name] = config
        return config

    def select_model(self, test_name: str) -> str:
        """Select model variant for this request."""
        test = self.active_tests.get(test_name)

        if not test or not test.enabled:
            return test.model_a  # Default to A

        # Random assignment based on traffic split
        if random.random() < test.traffic_split:
            return test.model_b
        else:
            return test.model_a

    def get_test_results(self, test_name: str):
        """Get A/B test results."""
        test = self.active_tests[test_name]

        # Load predictions from monitor
        predictions_a = self._get_predictions_for_model(test.model_a)
        predictions_b = self._get_predictions_for_model(test.model_b)

        results = {
            "model_a": {
                "version": test.model_a,
                "count": len(predictions_a),
                "avg_confidence": np.mean([p["confidence"] for p in predictions_a]),
                "avg_inference_ms": np.mean([p["inference_time_ms"] for p in predictions_a])
            },
            "model_b": {
                "version": test.model_b,
                "count": len(predictions_b),
                "avg_confidence": np.mean([p["confidence"] for p in predictions_b]),
                "avg_inference_ms": np.mean([p["inference_time_ms"] for p in predictions_b])
            }
        }

        return results
```

**Usage**:
```python
# Create A/B test
ab_manager = ABTestManager()
ab_manager.create_test(
    test_name="rf_v1.0_vs_v1.1",
    model_a="1.0.0",
    model_b="1.1.0",
    traffic_split=0.3  # 30% traffic to v1.1.0
)

# During inference
selected_version = ab_manager.select_model("rf_v1.0_vs_v1.1")
model, _ = registry.load_model("malware_detector_rf", selected_version)

# After 1 week, check results
results = ab_manager.get_test_results("rf_v1.0_vs_v1.1")
print(f"Model A: {results['model_a']['avg_confidence']:.2%} confidence")
print(f"Model B: {results['model_b']['avg_confidence']:.2%} confidence")
```

**Tasks**:
1. Create `ABTestManager` class
2. Integrate into inference pipeline
3. Add A/B test configuration UI
4. Statistical significance testing
5. Automated winner selection

**Expected Outcome**: Data-driven model selection

**Files to Create**:
- `app/ml/ab_testing.py`
- `scripts/ml/analyze_ab_test.py`
- `docs/operations/AB_TESTING_GUIDE.md`

**Time Estimate**: 3-4 days

---

### D3: Automated Retraining Pipeline (Week 4-5)

**Objective**: Automated model retraining on new data

**Implementation**:

**Script**: `scripts/ml/automated_retraining.py`
```python
#!/usr/bin/env python3
"""Automated model retraining pipeline."""

import argparse
from datetime import datetime, UTC
from pathlib import Path

from app.ml.model_registry import ModelRegistry
from app.ml.monitoring import ModelMonitor
from scripts.ml.download_malwarebazaar import download_samples
from scripts.ml.extract_features import extract_features_batch
from scripts.ml.train_random_forest import train_random_forest

def should_retrain(monitor: ModelMonitor, threshold: float = 0.95) -> bool:
    """Check if retraining is needed based on performance."""
    metrics = monitor.compute_metrics(time_window_hours=168)  # 7 days

    if "accuracy" not in metrics:
        print("⚠️ No ground truth available, skipping retraining check")
        return False

    accuracy = metrics["accuracy"]

    if accuracy < threshold:
        print(f"⚠️ Accuracy ({accuracy:.2%}) below threshold ({threshold:.2%})")
        return True

    print(f"✅ Accuracy ({accuracy:.2%}) above threshold, no retraining needed")
    return False

def retrain_pipeline(
    download_new_samples: bool = True,
    num_samples: int = 100,
    auto_promote: bool = False
):
    """Execute full retraining pipeline."""

    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║        🤖 AUTOMATED RETRAINING PIPELINE 🤖                   ║")
    print("╚═══════════════════════════════════════════════════════════════╝\n")

    # Step 1: Check if retraining needed
    monitor = ModelMonitor()

    if not should_retrain(monitor):
        print("✅ Retraining not needed at this time")
        return

    # Step 2: Download new samples (optional)
    if download_new_samples:
        print("\n📥 Downloading new malware samples...")
        download_samples(num_samples=num_samples)

    # Step 3: Extract features
    print("\n🔧 Extracting features from new samples...")
    extract_features_batch(
        input_dir=Path("data/organized"),
        output_dir=Path("data/features_retrain")
    )

    # Step 4: Train new model
    print("\n🏋️ Training new model...")
    new_version = get_next_version()

    train_random_forest(
        features_dir=Path("data/features_retrain"),
        output_version=new_version,
        hyperparameter_tuning=True
    )

    # Step 5: Evaluate new model
    print("\n📊 Evaluating new model...")
    registry = ModelRegistry()
    new_model, new_metadata = registry.load_model(
        "malware_detector_rf",
        new_version
    )

    test_accuracy = new_metadata.metrics.get("test_accuracy", 0.0)

    # Step 6: Compare with production
    prod_models = registry.list_models(
        name="malware_detector_rf",
        stage="production"
    )

    if prod_models:
        prod_accuracy = prod_models[0].metrics.get("test_accuracy", 0.0)

        if test_accuracy > prod_accuracy:
            print(f"\n✅ New model ({test_accuracy:.2%}) better than production ({prod_accuracy:.2%})")

            if auto_promote:
                print("🚀 Auto-promoting new model to production...")
                registry.promote_to_production(
                    "malware_detector_rf",
                    new_version
                )
            else:
                print("💡 Run promote_to_production.py to deploy new model")
        else:
            print(f"\n⚠️ New model ({test_accuracy:.2%}) not better than production ({prod_accuracy:.2%})")

    print("\n✅ Retraining pipeline complete!")

def get_next_version() -> str:
    """Get next semantic version."""
    registry = ModelRegistry()

    try:
        current = registry.get_latest_version("malware_detector_rf")
        major, minor, patch = map(int, current.split("."))

        # Increment minor version
        return f"{major}.{minor + 1}.0"
    except:
        return "1.0.0"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--download-samples", action="store_true")
    parser.add_argument("--num-samples", type=int, default=100)
    parser.add_argument("--auto-promote", action="store_true")

    args = parser.parse_args()

    retrain_pipeline(
        download_new_samples=args.download_samples,
        num_samples=args.num_samples,
        auto_promote=args.auto_promote
    )
```

**Cron Setup** (Linux):
```bash
# Run retraining check weekly (Sundays at 2 AM)
0 2 * * 0 cd /path/to/xanadOS-Search_Destroy && uv run python scripts/ml/automated_retraining.py --download-samples --num-samples 200
```

**Tasks**:
1. Create automated retraining script
2. Add performance degradation detection
3. Implement version auto-increment
4. Setup cron job / systemd timer
5. Email notifications for retraining events

**Expected Outcome**: Self-updating ML system

**Files to Create**:
- `scripts/ml/automated_retraining.py`
- `config/retraining_config.toml`
- `docs/operations/AUTOMATED_RETRAINING_GUIDE.md`

**Time Estimate**: 3-4 days

---

## Implementation Timeline

### Week 1: Quick Wins & Foundation
**Focus**: Integration + Basic Monitoring

- **Day 1-2**: UnifiedScannerEngine integration (B1)
  - Create `MLThreatDetector` class
  - Integrate into scanner engine
  - Unit tests

- **Day 3-4**: REST API endpoint (B2)
  - Create FastAPI endpoints
  - Add authentication
  - Client SDK

- **Day 5-7**: Basic monitoring (D1)
  - `ModelMonitor` class
  - Logging integration
  - Monitoring dashboard

**Deliverables**:
- ✅ ML scanning available in scanner engine
- ✅ REST API for remote inference
- ✅ Basic performance monitoring

---

### Week 2: GUI + Advanced Models Setup
**Focus**: User Interface + Model Exploration

- **Day 8-10**: GUI integration (B3)
  - Create `MLScanPanel` widget
  - Add to main window
  - Background threading

- **Day 11-12**: XGBoost setup (C1)
  - Install dependencies
  - Create training script
  - Initial training

- **Day 13-14**: LightGBM training (C1)
  - Training script
  - Hyperparameter tuning
  - Model comparison

**Deliverables**:
- ✅ ML scanning in GUI
- ✅ XGBoost model trained
- ✅ LightGBM model trained

---

### Week 3: Deep Learning + Ensembles
**Focus**: Advanced Architectures

- **Day 15-17**: CNN development (A1)
  - Raw byte data loader
  - CNN architecture
  - Training pipeline

- **Day 18-19**: Ensemble methods (C2)
  - Voting classifier
  - Stacking classifier
  - Performance comparison

- **Day 20-21**: LSTM development (A2)
  - Sequence preprocessing
  - LSTM architecture
  - Initial training

**Deliverables**:
- ✅ CNN model trained
- ✅ Ensemble models created
- ✅ LSTM model trained

---

### Week 4: Robustness + Production Hardening
**Focus**: Production Readiness

- **Day 22-24**: Model comparison (A3)
  - Standardized evaluation
  - Comparison dashboard
  - Final model selection

- **Day 25-26**: A/B testing (D2)
  - `ABTestManager` implementation
  - Integration into pipeline
  - Statistical testing

- **Day 27-28**: Adversarial testing (C3)
  - Robustness tests
  - Evasion attack simulation
  - Report generation

**Deliverables**:
- ✅ Complete model comparison
- ✅ A/B testing framework
- ✅ Adversarial robustness report

---

### Week 5: Automation + Polish
**Focus**: Operational Excellence

- **Day 29-31**: Automated retraining (D3)
  - Retraining pipeline script
  - Cron job setup
  - Performance degradation detection

- **Day 32-33**: Integration polish
  - Bug fixes
  - Performance optimization
  - Error handling improvements

- **Day 34-35**: Documentation
  - API documentation
  - Deployment guides
  - Operations runbooks

**Deliverables**:
- ✅ Automated retraining pipeline
- ✅ Production-ready system
- ✅ Complete documentation

---

### Week 6: Testing + Deployment
**Focus**: Production Release

- **Day 36-38**: End-to-end testing
  - Integration tests
  - Load testing
  - Security testing

- **Day 39-40**: Production deployment
  - Deploy to production
  - Monitor performance
  - Rollback plan validation

- **Day 41-42**: Final polish & release
  - Release notes
  - User training materials
  - Production handoff

**Deliverables**:
- ✅ Production deployment
- ✅ Release documentation
- ✅ System fully operational

---

## Success Criteria

### Technical Metrics
- ✅ All models achieve ≥95% test accuracy
- ✅ Inference time <100ms per file
- ✅ API response time <200ms (p95)
- ✅ Zero downtime during model updates
- ✅ 99.9% API uptime

### Integration Metrics
- ✅ ML scanning integrated in all scan modes
- ✅ GUI fully functional with ML features
- ✅ REST API production-ready
- ✅ Automated retraining functional

### Operational Metrics
- ✅ Monitoring dashboard operational
- ✅ A/B testing framework functional
- ✅ Automated retraining tested
- ✅ Complete documentation published

---

## Risk Mitigation

### Risk 1: Deep Learning Underperforms
**Likelihood**: Medium
**Impact**: Low (RF already 100% accurate)
**Mitigation**: Keep Random Forest as production default, use DL for research only

### Risk 2: Integration Bugs
**Likelihood**: Medium
**Impact**: High (could break existing scanner)
**Mitigation**: Comprehensive testing, feature flags for ML scanning, rollback plan

### Risk 3: Performance Degradation
**Likelihood**: Low
**Impact**: Medium (slower scanning)
**Mitigation**: Benchmark before/after, optimize inference, caching strategies

### Risk 4: Timeline Slippage
**Likelihood**: Medium
**Impact**: Low (not time-critical)
**Mitigation**: Prioritize high-value features, cut scope if needed (DL can wait)

---

## Resource Requirements

### Infrastructure
- **Development**: Existing setup (sufficient)
- **GPU**: Optional for deep learning (nice to have, not required)
- **Storage**: Additional 1-2 GB for new models
- **Network**: None (all local development)

### Dependencies to Install
```bash
# Gradient boosting
uv add xgboost lightgbm

# Deep learning (already installed)
# PyTorch 2.9.1+cu128 ✅

# Monitoring (optional)
uv add prometheus-client redis
```

### Time Commitment
- **Full implementation**: 4-6 weeks
- **Quick wins only (B1, B2, D1)**: 1-2 weeks
- **Per-track estimates**:
  - Track A (Deep Learning): 2 weeks
  - Track B (Integration): 1.5 weeks
  - Track C (Advanced ML): 1.5 weeks
  - Track D (Hardening): 2 weeks

---

## Next Steps

**Immediate Actions**:

1. **Review this roadmap** - Adjust priorities based on your preferences
2. **Choose starting track** - Recommend Track B (Integration) for quick wins
3. **Set up development environment** - Install additional dependencies
4. **Create feature branch** - `git checkout -b feature/ml-phase-4`

**Recommended Starting Point**:

Start with **Track B (Integration)** since it provides immediate value:
- Week 1: UnifiedScannerEngine integration → REST API → Basic monitoring
- This gives you a fully functional ML scanning system in production
- Other tracks can be developed in parallel or sequentially

**Question for You**:

Which track would you like to start with?
- [A] Deep Learning (experimental, research-focused)
- [B] Integration & Deployment (high value, quick wins) ⭐ **RECOMMENDED**
- [C] Advanced ML (gradient boosting, ensembles)
- [D] Production Hardening (monitoring, automation)

Or would you prefer to follow the timeline sequentially (Week 1 → Week 6)?

---

## Appendix: File Structure

**New Files (Estimated ~40 files)**:

```
app/
├── ml/
│   ├── ml_scanner_integration.py        # NEW: ML scanner wrapper
│   ├── cnn_malware_detector.py          # NEW: CNN model
│   ├── lstm_detector.py                 # NEW: LSTM model
│   ├── ensemble_detector.py             # NEW: Ensemble methods
│   ├── monitoring.py                    # NEW: Performance monitoring
│   └── ab_testing.py                    # NEW: A/B testing framework
│
├── api/
│   ├── ml_inference.py                  # NEW: REST API endpoints
│   └── ml_client.py                     # NEW: Python client SDK
│
└── gui/
    ├── ml_scan_panel.py                 # NEW: ML scanning widget
    └── monitoring_dashboard.py          # NEW: Monitoring dashboard

scripts/ml/
├── train_xgboost.py                     # NEW: XGBoost training
├── train_lightgbm.py                    # NEW: LightGBM training
├── train_cnn.py                         # NEW: CNN training
├── train_lstm.py                        # NEW: LSTM training
├── train_ensemble.py                    # NEW: Ensemble training
├── tune_gradient_boosting.py            # NEW: GB hyperparameter tuning
├── prepare_raw_bytes.py                 # NEW: Raw byte preprocessing
├── prepare_sequences.py                 # NEW: Sequence preprocessing
├── adversarial_testing.py               # NEW: Robustness testing
├── automated_retraining.py              # NEW: Auto-retraining pipeline
├── analyze_ab_test.py                   # NEW: A/B test analysis
└── list_models.py                       # ✅ ALREADY CREATED

docs/
├── implementation/
│   ├── ML_PHASE_4_ROADMAP.md           # ✅ THIS FILE
│   ├── MODEL_COMPARISON_REPORT.md      # NEW: Model comparison
│   └── ENSEMBLE_GUIDE.md               # NEW: Ensemble methods guide
│
├── api/
│   └── ML_API_REFERENCE.md             # NEW: API documentation
│
├── operations/
│   ├── AB_TESTING_GUIDE.md             # NEW: A/B testing guide
│   └── AUTOMATED_RETRAINING_GUIDE.md   # NEW: Retraining guide
│
└── security/
    └── ADVERSARIAL_ROBUSTNESS_REPORT.md # NEW: Security testing report
```

---

**End of Roadmap**

Ready to implement! 🚀
