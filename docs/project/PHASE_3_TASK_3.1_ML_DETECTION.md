# Task 3.1: ML-Based Threat Detection - Implementation Specification

**Version**: 3.1.0
**Timeline**: 3 months (Weeks 1-12)
**Priority**: CRITICAL
**Status**: 📋 SPECIFICATION

---

## Overview

Implement advanced machine learning-based malware detection using transformer models, ensemble learning, and behavioral analysis. This establishes the foundation for AI-powered threat detection capabilities.

---

## 1. Objectives

### 1.1 Primary Goals

1. **High Accuracy**: Achieve 95%+ detection rate on test dataset
2. **Low False Positives**: Maintain <1% false positive rate
3. **Real-Time Performance**: <1s inference time per file
4. **Explainability**: Provide SHAP values for predictions
5. **Scalability**: Handle 1000+ files/minute throughput

### 1.2 Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Detection Rate | ≥95% | F1-score on test set (10,000 samples) |
| False Positive Rate | ≤1% | FPR on benign dataset (5,000 samples) |
| Inference Time | <1s | Average latency across 1,000 files |
| Model Size | <500MB | Quantized ONNX model size |
| Malware Family Classification | 1000+ families | Multi-class accuracy |

---

## 2. Architecture

### 2.1 Component Overview

```
app/ml/
├── __init__.py
├── feature_extractor.py       # Static + dynamic feature extraction
├── models/
│   ├── __init__.py
│   ├── transformer.py         # BERT-based sequence model
│   ├── random_forest.py       # Baseline ML model
│   ├── anomaly_detector.py    # Isolation Forest, One-Class SVM
│   └── ensemble.py            # Weighted voting ensemble
├── training/
│   ├── __init__.py
│   ├── dataset.py             # Dataset management, splitting
│   ├── trainer.py             # Training loop, checkpointing
│   ├── evaluator.py           # Model evaluation, metrics
│   └── hyperparameter_tuning.py  # Optuna integration
├── inference.py               # Real-time prediction engine
├── explainability.py          # SHAP, LIME integration
└── model_registry.py          # Model versioning, A/B testing

config/ml/
├── transformer_config.yaml    # Transformer hyperparameters
├── random_forest_config.yaml  # RF hyperparameters
└── training_config.yaml       # Training settings

tests/test_ml/
├── test_feature_extractor.py
├── test_models.py
├── test_training.py
├── test_inference.py
└── test_explainability.py
```

### 2.2 Feature Engineering

#### **Static Features** (50+ features)

**PE/ELF Headers**:
- `file_type`: PE, ELF, Mach-O, etc.
- `arch`: x86, x64, ARM, etc.
- `entropy`: Overall file entropy
- `section_count`: Number of sections
- `section_entropy[]`: Per-section entropy
- `imports[]`: Imported functions (hashed)
- `exports[]`: Exported functions
- `strings_count`: Number of strings
- `suspicious_strings[]`: Regex matches (URL, IP, Base64)

**File Metadata**:
- `file_size`: Bytes
- `creation_time`: Timestamp
- `modification_time`: Timestamp
- `magic_bytes`: File signature
- `packer_detected`: UPX, MPRESS, etc.

**Code Analysis**:
- `control_flow_complexity`: McCabe complexity
- `api_call_graph`: Function call graph features
- `opcode_n_grams`: Instruction sequence patterns
- `code_to_data_ratio`: Proportion of executable code

#### **Dynamic Features** (30+ features) - *Future*

**System Calls** (requires sandbox - Task 3.4):
- `syscall_sequence[]`: Ordered syscalls
- `file_operations[]`: open, read, write, delete
- `network_activity[]`: connect, send, recv
- `process_creation[]`: fork, exec
- `registry_modifications[]`: Windows registry changes

**Behavioral Indicators**:
- `persistence_mechanism`: Startup, cron, service
- `lateral_movement`: Network scanning, SMB
- `data_exfiltration`: Large uploads, DNS tunneling
- `anti_analysis`: Debugger detection, VM detection

### 2.3 Model Architectures

#### **Model 1: Transformer (BERT-based)**

**Architecture**:
```python
class MalwareTransformer(nn.Module):
    def __init__(self, vocab_size=10000, embedding_dim=256, num_heads=8):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.encoder = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
                d_model=embedding_dim,
                nhead=num_heads,
                dim_feedforward=1024,
                dropout=0.1
            ),
            num_layers=6
        )
        self.classifier = nn.Linear(embedding_dim, 2)  # Binary: malware/benign

    def forward(self, x):
        # x: [batch_size, seq_len] - tokenized opcode/API sequences
        embedded = self.embedding(x)
        encoded = self.encoder(embedded)
        pooled = encoded.mean(dim=1)  # Global average pooling
        return self.classifier(pooled)
```

**Input**: Tokenized sequences (opcodes, API calls, string patterns)
**Output**: Binary classification (malware/benign) + confidence
**Training**: AdamW optimizer, cross-entropy loss, 50 epochs

#### **Model 2: Random Forest (Baseline)**

**Architecture**:
```python
from sklearn.ensemble import RandomForestClassifier

rf_model = RandomForestClassifier(
    n_estimators=500,
    max_depth=30,
    min_samples_split=10,
    min_samples_leaf=5,
    class_weight='balanced',
    n_jobs=-1
)
```

**Input**: 50+ static features (numerical/categorical)
**Output**: Binary classification + feature importance
**Training**: 5-fold cross-validation

#### **Model 3: Anomaly Detector**

**Architecture**:
```python
from sklearn.ensemble import IsolationForest

anomaly_detector = IsolationForest(
    n_estimators=200,
    contamination=0.05,  # Expected malware ratio
    max_samples=256,
    n_jobs=-1
)
```

**Input**: Static features (unsupervised)
**Output**: Anomaly score (-1 to 1)
**Use Case**: Zero-day detection, unknown malware

#### **Model 4: Ensemble (Weighted Voting)**

**Architecture**:
```python
class EnsembleClassifier:
    def __init__(self, models, weights):
        self.models = models  # [transformer, rf, anomaly]
        self.weights = weights  # [0.5, 0.3, 0.2]

    def predict(self, features):
        predictions = []
        for model, weight in zip(self.models, self.weights):
            pred = model.predict(features)
            predictions.append(pred * weight)

        return np.sum(predictions, axis=0) > 0.5  # Threshold
```

**Weights**: Tuned via grid search on validation set

---

## 3. Data Pipeline

### 3.1 Dataset Acquisition

**Sources**:
1. **VirusShare** (https://virusshare.com) - 40M+ malware samples
2. **theZoo** (https://github.com/ytisf/theZoo) - Curated malware collection
3. **MalwareBazaar** (https://bazaar.abuse.ch) - Fresh samples
4. **Benign Dataset**: Clean files from Ubuntu, Debian repositories

**Dataset Composition**:
- **Malware**: 50,000 samples (balanced across families)
- **Benign**: 50,000 samples (system files, applications, libraries)
- **Total**: 100,000 samples

**Split**:
- Training: 70,000 (70%)
- Validation: 15,000 (15%)
- Test: 15,000 (15%)

### 3.2 Data Preprocessing

**Pipeline** (`app/ml/training/dataset.py`):

```python
class MalwareDataset:
    def __init__(self, samples_dir: Path, cache_dir: Path):
        self.samples_dir = samples_dir
        self.cache_dir = cache_dir
        self.extractor = FeatureExtractor()

    def __getitem__(self, idx: int):
        sample_path = self.samples[idx]

        # Check cache
        cache_path = self.cache_dir / f"{sample_path.stem}.npz"
        if cache_path.exists():
            return np.load(cache_path)

        # Extract features
        features = self.extractor.extract(sample_path)

        # Cache for reuse
        np.savez(cache_path, **features)

        return features
```

**Caching Strategy**:
- Cache extracted features (avoid re-extraction)
- SHA256 hash-based cache keys
- Invalidate on feature schema changes

### 3.3 Data Augmentation

**Techniques**:
1. **Opcode Reordering**: Shuffle non-dependent instructions
2. **String Obfuscation**: Modify string constants
3. **Section Padding**: Add benign padding to sections
4. **Packer Simulation**: Apply UPX, MPRESS to benign files

**Goal**: Improve model robustness to packer/obfuscation variants

---

## 4. Training Pipeline

### 4.1 Training Loop

**Pseudocode** (`app/ml/training/trainer.py`):

```python
class ModelTrainer:
    def train(self, model, train_loader, val_loader, epochs=50):
        optimizer = AdamW(model.parameters(), lr=1e-4)
        scheduler = CosineAnnealingLR(optimizer, T_max=epochs)

        best_val_acc = 0.0

        for epoch in range(epochs):
            # Training phase
            model.train()
            train_loss = 0.0

            for batch in train_loader:
                features, labels = batch

                optimizer.zero_grad()
                outputs = model(features)
                loss = F.cross_entropy(outputs, labels)
                loss.backward()
                optimizer.step()

                train_loss += loss.item()

            # Validation phase
            model.eval()
            val_acc, val_f1 = self.evaluate(model, val_loader)

            # Checkpointing
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                self.save_checkpoint(model, epoch, val_acc)

            scheduler.step()

            # Logging
            wandb.log({
                "epoch": epoch,
                "train_loss": train_loss,
                "val_acc": val_acc,
                "val_f1": val_f1
            })
```

### 4.2 Hyperparameter Tuning

**Framework**: Optuna (Tree-structured Parzen Estimator)

**Search Space**:
```python
def objective(trial):
    config = {
        "learning_rate": trial.suggest_loguniform("lr", 1e-5, 1e-3),
        "batch_size": trial.suggest_categorical("batch_size", [32, 64, 128]),
        "dropout": trial.suggest_uniform("dropout", 0.1, 0.5),
        "num_layers": trial.suggest_int("num_layers", 4, 8),
        "embedding_dim": trial.suggest_categorical("emb_dim", [128, 256, 512]),
    }

    model = MalwareTransformer(**config)
    val_f1 = train_and_evaluate(model, train_loader, val_loader)

    return val_f1  # Maximize F1-score
```

**Trials**: 100 trials, 12-hour budget

### 4.3 Model Export

**ONNX Conversion**:
```python
import torch.onnx

# Export to ONNX for production deployment
dummy_input = torch.randn(1, 512)  # Example input
torch.onnx.export(
    model,
    dummy_input,
    "models/malware_transformer.onnx",
    export_params=True,
    opset_version=14,
    input_names=["input"],
    output_names=["output"],
    dynamic_axes={"input": {0: "batch_size"}}
)
```

**Quantization** (INT8 for faster inference):
```python
import onnxruntime as ort
from onnxruntime.quantization import quantize_dynamic

quantize_dynamic(
    "models/malware_transformer.onnx",
    "models/malware_transformer_quantized.onnx",
    weight_type=ort.QuantType.QInt8
)
```

---

## 5. Inference Engine

### 5.1 Real-Time Prediction

**API** (`app/ml/inference.py`):

```python
class MalwareInferenceEngine:
    def __init__(self, model_path: str):
        self.session = ort.InferenceSession(model_path)
        self.extractor = FeatureExtractor()

    def predict(self, file_path: Path) -> dict:
        # Extract features
        features = self.extractor.extract(file_path)

        # Inference
        inputs = {self.session.get_inputs()[0].name: features}
        outputs = self.session.run(None, inputs)

        # Post-processing
        probabilities = softmax(outputs[0])

        return {
            "is_malware": probabilities[1] > 0.5,
            "confidence": float(probabilities[1]),
            "malware_family": self.classify_family(features) if probabilities[1] > 0.5 else None
        }

    def predict_batch(self, file_paths: list[Path]) -> list[dict]:
        # Batch inference for efficiency
        features_batch = [self.extractor.extract(p) for p in file_paths]
        # ... batch processing
```

### 5.2 Model Versioning

**Registry** (`app/ml/model_registry.py`):

```python
class ModelRegistry:
    def __init__(self, registry_path: Path):
        self.registry = self.load_registry(registry_path)

    def register_model(self, name: str, version: str, metrics: dict):
        self.registry[name][version] = {
            "path": f"models/{name}_{version}.onnx",
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }

    def get_best_model(self, name: str, metric: str = "f1_score"):
        versions = self.registry[name]
        best = max(versions.items(), key=lambda x: x[1]["metrics"][metric])
        return best[1]["path"]

    def deploy_model(self, name: str, version: str):
        # Atomic symlink update for zero-downtime deployment
        model_path = self.registry[name][version]["path"]
        symlink_path = Path("models/production.onnx")
        symlink_path.unlink(missing_ok=True)
        symlink_path.symlink_to(model_path)
```

---

## 6. Explainability

### 6.1 SHAP Integration

**API** (`app/ml/explainability.py`):

```python
import shap

class ModelExplainer:
    def __init__(self, model, background_data):
        self.explainer = shap.DeepExplainer(model, background_data)

    def explain_prediction(self, sample_features):
        shap_values = self.explainer.shap_values(sample_features)

        # Top 10 contributing features
        feature_importance = sorted(
            zip(FEATURE_NAMES, shap_values[0]),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:10]

        return {
            "prediction": "malware",
            "confidence": 0.95,
            "explanation": feature_importance,
            "visualization": self.generate_force_plot(shap_values)
        }
```

**GUI Integration**:
- Display SHAP force plots in scan results
- Highlight suspicious features (imports, strings, entropy)
- Interactive feature exploration

---

## 7. Testing Strategy

### 7.1 Unit Tests

**Coverage**: 95%+ for all ML modules

**Test Cases** (`tests/test_ml/test_models.py`):

```python
def test_transformer_forward_pass():
    """Test transformer forward pass with dummy data."""
    model = MalwareTransformer(vocab_size=1000, embedding_dim=128)
    input_seq = torch.randint(0, 1000, (16, 512))  # Batch of 16

    output = model(input_seq)

    assert output.shape == (16, 2)  # Binary classification
    assert torch.all(torch.isfinite(output))  # No NaN/Inf

def test_feature_extractor_pe_file():
    """Test feature extraction from PE file."""
    extractor = FeatureExtractor()
    features = extractor.extract("tests/data/sample.exe")

    assert "file_size" in features
    assert "entropy" in features
    assert "section_count" in features
    assert 0 < features["entropy"] < 8  # Valid entropy range

def test_inference_latency():
    """Ensure inference completes within 1 second."""
    engine = MalwareInferenceEngine("models/production.onnx")

    start = time.time()
    result = engine.predict("tests/data/sample.exe")
    latency = time.time() - start

    assert latency < 1.0  # <1s SLA
    assert "confidence" in result
```

### 7.2 Integration Tests

**Scenarios**:
1. End-to-end: File upload → feature extraction → prediction → result display
2. Batch processing: 1000 files processed with <1min total time
3. Model hot-swapping: Update production model without downtime

### 7.3 Performance Benchmarks

**Benchmark Suite** (`tests/benchmarks/ml_benchmarks.py`):

```python
@pytest.mark.benchmark
def test_inference_throughput(benchmark):
    """Measure files/second throughput."""
    engine = MalwareInferenceEngine("models/production.onnx")
    test_files = list(Path("tests/data/").glob("*.exe"))[:100]

    def run_batch():
        return engine.predict_batch(test_files)

    result = benchmark(run_batch)

    # Should process 100 files in <10s (10+ files/s)
    assert benchmark.stats.mean < 10.0
```

---

## 8. Deployment

### 8.1 Integration with Scanner

**Modification** (`app/core/unified_scanner_engine.py`):

```python
from app.ml.inference import MalwareInferenceEngine

class UnifiedScannerEngine:
    def __init__(self):
        # Existing scanners
        self.clamav = ClamAVWrapper()
        self.yara = YaraScanner()

        # NEW: ML-based scanner
        self.ml_engine = MalwareInferenceEngine("models/production.onnx")

    async def scan_file_async(self, file_path: Path) -> ScanResult:
        # Run all scanners in parallel
        results = await asyncio.gather(
            self.clamav.scan_async(file_path),
            self.yara.scan_async(file_path),
            self.ml_engine.predict_async(file_path)  # NEW
        )

        # Aggregate results
        return self.aggregate_results(results)
```

### 8.2 Model Update Workflow

**Automated Retraining**:
1. Weekly cron job fetches new samples from MalwareBazaar
2. Retrain models on updated dataset
3. Evaluate on hold-out test set
4. If performance improves, deploy to production
5. Monitor for regressions via A/B testing

---

## 9. Deliverables

### 9.1 Code

- [ ] `app/ml/feature_extractor.py` (300+ lines)
- [ ] `app/ml/models/transformer.py` (200+ lines)
- [ ] `app/ml/models/random_forest.py` (150+ lines)
- [ ] `app/ml/models/ensemble.py` (100+ lines)
- [ ] `app/ml/training/dataset.py` (250+ lines)
- [ ] `app/ml/training/trainer.py` (300+ lines)
- [ ] `app/ml/inference.py` (200+ lines)
- [ ] `app/ml/explainability.py` (150+ lines)
- [ ] `app/ml/model_registry.py` (100+ lines)

**Total**: ~1,750 lines of production code

### 9.2 Tests

- [ ] `tests/test_ml/test_feature_extractor.py` (40+ tests)
- [ ] `tests/test_ml/test_models.py` (30+ tests)
- [ ] `tests/test_ml/test_training.py` (20+ tests)
- [ ] `tests/test_ml/test_inference.py` (25+ tests)
- [ ] `tests/benchmarks/ml_benchmarks.py` (10+ benchmarks)

**Total**: 125+ tests

### 9.3 Documentation

- [ ] ML model training guide (50+ pages)
- [ ] Feature engineering specification
- [ ] Model deployment runbook
- [ ] SHAP explainability tutorial
- [ ] Dataset preparation guide

### 9.4 Models

- [ ] `models/malware_transformer.onnx` (quantized, <500MB)
- [ ] `models/random_forest.pkl` (<50MB)
- [ ] `models/ensemble_config.json`

---

## 10. Timeline

| Week | Milestone | Deliverables |
|------|-----------|--------------|
| 1-2 | Dataset preparation, feature extraction | 100K samples, feature extractor |
| 3-4 | Baseline Random Forest training | RF model (90%+ accuracy) |
| 5-8 | Transformer model development | Transformer model (95%+ accuracy) |
| 9-10 | Ensemble & explainability | Ensemble model, SHAP integration |
| 11-12 | Integration, testing, optimization | Production deployment |

---

## 11. Success Criteria

✅ **Phase 3.1 Complete When**:

1. ML models achieve 95%+ detection rate on test set
2. False positive rate <1%
3. Inference latency <1s per file
4. Integration with scanner engine complete
5. 125+ tests passing (95%+ coverage)
6. Documentation published
7. Production deployment successful
8. A/B testing shows improvement over ClamAV/YARA alone

---

**Status**: ✅ **APPROVED - READY FOR IMPLEMENTATION**

**Next Steps**: Begin Week 1 - Dataset acquisition & feature extraction
