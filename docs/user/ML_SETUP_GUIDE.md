# ML Feature Setup Guide

**Purpose**: Enable ML-based malware detection in xanadOS Search & Destroy
**Time Required**: ~15 minutes (quick setup) or ~2 hours (full production setup)
**Status**: Models and datasets excluded from repository for security

## Why Models Aren't Included

For security and practical reasons, the following files are **NOT** included in the git repository:

### Excluded (Gitignored):
- **Trained models** (.pkl files, ~1-5MB each) - Binary files, large size
- **Malware samples** (data/malware/, 172MB) - Security risk, GitHub ToS violation
- **Benign binaries** (data/benign/, 39MB) - Large binary files
- **Datasets** (data/organized/, 210MB) - Training data splits
- **Feature caches** (data/features/, 2.4MB) - Regenerated automatically

### Included (In Repository):
- ✅ **All source code** (ML infrastructure, training scripts, API)
- ✅ **Dataset acquisition scripts** (download from MalwareBazaar, collect binaries)
- ✅ **Training scripts** (train, tune, promote models)
- ✅ **Feature extraction** (PE/ELF analysis)
- ✅ **Model registry** (versioning, metadata)

## Quick Setup (15 Minutes)

**Goal**: Get ML detection working with minimal dataset

### Step 1: Install Dependencies

```bash
cd xanadOS-Search_Destroy

# Install ML dependencies
uv sync --extra malware-analysis

# Verify installation
uv run python -c "import sklearn, joblib, pefile; print('✅ ML dependencies installed')"
```

### Step 2: Acquire Dataset (Quick - 500 samples)

```bash
# Download and organize dataset automatically
uv run python scripts/ml/dataset_workflow.py --quick

# This will:
# • Download 250 malware samples from MalwareBazaar
# • Collect 250 benign system binaries
# • Organize into train/val/test splits
# • Takes ~10 minutes (with rate limiting)
```

**Security Note**: This downloads live malware. See [Security Considerations](#security-considerations).

### Step 3: Train Model

```bash
# Train Random Forest model
uv run python scripts/ml/train_random_forest.py

# Expected output:
# ✅ Training completed: ~98-100% accuracy
# ✅ Model saved to: models/production/malware_detector_rf_v1.0.0.pkl
# Takes ~2-5 minutes
```

### Step 4: Verify ML Features Work

```bash
# Test ML scanner integration
uv run python examples/ml_scanning_demo.py

# Start ML API server
uv run python examples/ml_api_server.py
# Access Swagger docs at: http://localhost:8000/api/ml/docs
```

**Done!** ML detection is now functional.

## Production Setup (2 Hours)

**Goal**: Full production-grade ML detection with comprehensive dataset

### Step 1: Full Dataset Acquisition

```bash
# Download 50,000 malware + 50,000 benign samples
uv run python scripts/ml/dataset_workflow.py --full

# WARNING: This will:
# • Download ~25K malware samples from MalwareBazaar
# • Collect ~25K system binaries
# • Require ~10GB disk space
# • Take 1-2 hours (API rate limiting)
```

### Step 2: Train and Tune Model

```bash
# 1. Train baseline model
uv run python scripts/ml/train_random_forest.py

# 2. Hyperparameter tuning (optional, improves accuracy)
uv run python scripts/ml/tune_random_forest.py

# 3. Promote best model to production
uv run python scripts/ml/promote_to_production.py
```

### Step 3: Validate Performance

```bash
# Run comprehensive tests
uv run python -m pytest tests/test_core/test_ml_integration.py -v

# Expected: 11/11 tests passing
```

## Alternative: Download Pre-Trained Models

**Option**: If you don't want to train models yourself, download pre-trained versions.

### GitHub Releases (Recommended)

```bash
# Download from GitHub releases
wget https://github.com/asafelobotomy/xanadOS-Search_Destroy/releases/download/v0.3.0/models.tar.gz

# Extract to repository
tar -xzf models.tar.gz -C models/

# Verify integrity
cd models/production/malware_detector_rf
sha256sum -c checksums.txt
```

**Note**: Pre-trained models provided for convenience only. Training your own models with your specific threat landscape is recommended for production use.

## Security Considerations

### ⚠️ CRITICAL: Working with Malware

**NEVER run malware samples**. This project uses **static analysis only**.

#### Best Practices:

1. **Isolated Environment**:
   ```bash
   # Use VM or container
   docker run -it --rm --network=none -v $(pwd):/app python:3.13
   ```

2. **Network Isolation** (optional but recommended):
   ```bash
   # Disable network after downloading datasets
   sudo ifconfig wlan0 down
   ```

3. **File Permissions**:
   ```bash
   # Malware files saved with 0600 (owner read/write only)
   ls -l data/malware/ | head -5
   # Expected: -rw------- (no execute permissions)
   ```

4. **Verify Hashes**:
   ```bash
   # All samples verified via SHA256 before saving
   cat data/malware/metadata.json | jq '.[] | .sha256'
   ```

5. **Backup Before Starting**:
   ```bash
   # Take VM snapshot before downloading malware
   # Or backup your system
   ```

### What Gets Downloaded

- **MalwareBazaar API**: Free access, AES-encrypted ZIPs
- **Password**: "infected" (standard for malware archives)
- **Sample Types**: PE executables, DLLs, ELF binaries, scripts
- **Verification**: SHA256 hash check before and after extraction

## Troubleshooting

### Model Loading Fails

**Error**: `FileNotFoundError: No model found at models/production/`

**Solution**:
```bash
# Train a model first
uv run python scripts/ml/train_random_forest.py
```

### Dataset Download Fails

**Error**: `HTTP 404: Sample not available`

**Solution**:
```bash
# Some samples may be unavailable - this is normal
# Script will skip unavailable samples and continue
# Expected: ~80-90% success rate
```

### Import Error: sklearn

**Error**: `ModuleNotFoundError: No module named 'sklearn'`

**Solution**:
```bash
# Install malware-analysis dependencies
uv sync --extra malware-analysis
```

### Slow Training

**Issue**: Model training takes >30 minutes

**Solution**:
```bash
# Reduce dataset size
uv run python scripts/ml/train_random_forest.py --max-samples 1000

# Or use fewer trees
uv run python scripts/ml/train_random_forest.py --n-estimators 50
```

## Continuous Integration Setup

For automated model training in CI/CD:

```yaml
# .github/workflows/train-models.yml
name: Train ML Models

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:

jobs:
  train:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        run: |
          pip install uv
          uv sync --extra malware-analysis

      - name: Acquire dataset
        run: uv run python scripts/ml/dataset_workflow.py --quick

      - name: Train model
        run: uv run python scripts/ml/train_random_forest.py

      - name: Upload model artifact
        uses: actions/upload-artifact@v4
        with:
          name: ml-models
          path: models/production/
```

**Note**: Be cautious about running malware acquisition in public CI - consider using self-hosted runners in isolated environments.

## Model Versioning

Models use semantic versioning:

```
malware_detector_rf_v1.0.0.pkl  # Initial training
malware_detector_rf_v1.1.0.pkl  # Improved features
malware_detector_rf_v2.0.0.pkl  # Architecture change
```

Check current version:
```bash
uv run python -c "from app.ml.model_registry import ModelRegistry; print(ModelRegistry().get_production_model().version)"
```

## Performance Expectations

### Quick Setup (500 samples):
- **Accuracy**: 95-98%
- **False Positives**: 2-5%
- **Scan Speed**: 5-10 files/second
- **Use Case**: Development, testing

### Production Setup (50K samples):
- **Accuracy**: 98-99.5%
- **False Positives**: 0.5-2%
- **Scan Speed**: 5-10 files/second
- **Use Case**: Production deployment

## Further Reading

- [ML Phase 4 Roadmap](../implementation/ML_PHASE_4_ROADMAP.md) - Complete implementation plan
- [Feature Extraction](../developer/FEATURE_EXTRACTION.md) - How features are extracted
- [Model Training](../developer/MODEL_TRAINING.md) - Training process details
- [Security Best Practices](../security/MALWARE_HANDLING.md) - Safe malware handling

## FAQ

**Q: Can I use my own malware samples?**
A: Yes! Place samples in `data/malware/` and run `organize_dataset.py`.

**Q: Do I need GPU for training?**
A: No, Random Forest training is CPU-based. GPU optional for deep learning models.

**Q: How often should I retrain?**
A: Monthly for production environments, or when encountering new threat types.

**Q: Can I use the API without local models?**
A: No, API requires local models. Train locally or download pre-trained versions.

**Q: Is this safe to run on my main system?**
A: We recommend VM/container for malware acquisition, but all operations use static analysis only (no execution).

---

**Last Updated**: December 17, 2025
**Maintainer**: xanadOS Security Team
**License**: See LICENSE file
