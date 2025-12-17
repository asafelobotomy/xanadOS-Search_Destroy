# Models Directory

**Purpose**: Trained ML models for malware detection
**Status**: ⚠️ **Models NOT included in git repository** - See setup instructions below

## ⚠️ Important: Models Are Gitignored

All `.pkl` model files are excluded from the repository for these reasons:

1. **Security**: Prevents accidental upload of large binary files
2. **Size**: Models are 1-5MB each, bloat git history
3. **Flexibility**: Users should train on their own threat landscape
4. **Updates**: Models retrained frequently as threats evolve

## Directory Structure

```
models/
├── production/              # Production-ready models (GITIGNORED)
│   └── malware_detector_rf/
│       └── malware_detector_rf_v1.1.0.pkl  ❌ NOT IN GIT
│
├── checkpoints/             # Training checkpoints (GITIGNORED)
│   └── malware_detector_rf/
│       ├── malware_detector_rf_v1.0.0.pkl  ❌ NOT IN GIT
│       └── malware_detector_rf_v1.1.0.pkl  ❌ NOT IN GIT
│
└── README.md               # This file ✅ IN GIT
```

## Quick Setup (Get Models Working in 15 Minutes)

### Option 1: Train Your Own (Recommended)

```bash
# 1. Install dependencies
uv sync --extra malware-analysis

# 2. Acquire dataset (500 samples, ~10 minutes)
uv run python scripts/ml/dataset_workflow.py --quick

# 3. Train model (~2-5 minutes)
uv run python scripts/ml/train_random_forest.py

# 4. Verify model exists
ls -lh models/production/malware_detector_rf/
# Should show: malware_detector_rf_v1.0.0.pkl
```

**Result**: Functional ML detection in ~15 minutes

### Option 2: Download Pre-Trained (Faster)

```bash
# Download from GitHub releases (when available)
wget https://github.com/asafelobotomy/xanadOS-Search_Destroy/releases/download/v0.3.0/models.tar.gz

# Extract to models directory
tar -xzf models.tar.gz

# Verify integrity
cd models/production/malware_detector_rf
sha256sum -c checksums.txt
```

## Model Registry

The `registry.json` file tracks all model versions and their performance:

```json
{
  "random_forest": {
    "v1.0.0": {
      "path": "experiments/random_forest_v1.0.0.pkl",
      "metrics": {
        "accuracy": 0.925,
        "precision": 0.912,
        "recall": 0.938,
        "f1_score": 0.925,
        "roc_auc": 0.958
      },
      "timestamp": "2025-12-17T10:30:00"
    }
  }
}
```

## Model Formats

- **Random Forest**: `.pkl` (scikit-learn joblib)
- **Transformer**: `.onnx` (ONNX quantized INT8)
- **Ensemble**: `.json` (config referencing component models)

## Production Deployment

Use `ModelRegistry.deploy_model(name, version)` for zero-downtime deployment:
1. Validates model exists in registry
2. Creates atomic symlink to production path
3. Scanner engine loads from `production/*.onnx`

## Model Performance Baselines

**Random Forest Baseline** (Week 4 target):
- Accuracy: ≥90%
- F1-Score: ≥0.90
- Inference: <1s per file

**Transformer Model** (Week 8 target):
- Accuracy: ≥95%
- F1-Score: ≥0.95
- Inference: <1s per file

**Ensemble Model** (Week 10 target):
- Accuracy: ≥97%
- F1-Score: ≥0.97
- False Positive Rate: <0.5%
