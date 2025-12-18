# Building Your Own ML Malware Detector

**Complete guide** for users who want to train custom ML models from scratch.

---

## Why Build Your Own Model?

**Pre-trained models aren't included** in the repository because:
1. **Size**: Models are 600KB-5MB (bloat git history)
2. **Security**: Datasets contain live malware (GitHub ToS violation)
3. **Customization**: Your threat landscape differs from ours
4. **Reproducibility**: Training scripts ensure consistency

**Building your own takes 15-30 minutes** and gives you:
- ✅ Model trained on YOUR environment
- ✅ Understanding of how it works
- ✅ Ability to retrain with new threats
- ✅ Full control over hyperparameters

---

## Prerequisites

### System Requirements

**Minimum** (for quick setup):
- CPU: 2+ cores
- RAM: 4GB
- Disk: 2GB free
- OS: Linux (Ubuntu 22.04+, Fedora 38+, Debian 12+)

**Recommended** (for production):
- CPU: 4+ cores
- RAM: 8GB
- Disk: 15GB free (full dataset)
- GPU: Optional (not used by Random Forest)

### Software Requirements

```bash
# Python 3.13+ (required)
python --version  # Should be 3.13 or higher

# uv package manager (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# OR pip (alternative)
pip install --upgrade pip
```

---

## Step-by-Step Guide

### Step 1: Clone Repository

```bash
git clone https://github.com/asafelobotomy/xanadOS-Search_Destroy.git
cd xanadOS-Search_Destroy
```

### Step 2: Install Dependencies

```bash
# Using uv (recommended - faster, better dependency resolution)
uv sync --extra malware-analysis

# OR using pip
pip install -e ".[malware-analysis]"
```

**What gets installed:**
- `scikit-learn==1.5.2` - Machine learning framework
- `joblib==1.4.2` - Model serialization
- `pefile==2024.8.26` - PE file parsing
- `lief==0.15.1` - Universal binary analysis
- `pyelftools==0.31` - ELF file parsing
- `rich==13.9.4` - Beautiful terminal output

### Step 3: Acquire Training Dataset

You have **two options**: Quick (600 samples) or Full (100K samples).

#### Option A: Quick Setup (Recommended for First Time)

**Time**: ~10 minutes | **Size**: ~500MB | **Accuracy**: 95-100%

```bash
# Activate virtual environment
source .venv/bin/activate

# Run quick workflow
python scripts/ml/dataset_workflow.py --quick
```

**What happens:**
1. Downloads 300 malware from MalwareBazaar
   - Free API (no registration)
   - AES-encrypted ZIPs (password: "infected")
   - SHA256 hash verification
2. Collects 300 benign system binaries
   - From `/usr/bin`, `/usr/sbin`, `/lib`
   - ELF format validation
   - Size filter: 1KB - 100MB
3. Organizes into train/val/test
   - 70% train (420 samples)
   - 15% val (90 samples)
   - 15% test (90 samples)

**Security prompt:**
```
⚠️  WARNING: This will download LIVE MALWARE
   • Files analyzed statically only (no execution)
   • Saved with 0600 permissions (no execute bit)
   • SHA256 verified before saving

Continue? (yes/no):
```

Type `yes` to proceed.

#### Option B: Production Setup (For Best Accuracy)

**Time**: ~2 hours | **Size**: ~10GB | **Accuracy**: 99%+

```bash
# Run full workflow
python scripts/ml/dataset_workflow.py --full
```

Downloads 50,000 malware + 50,000 benign samples.

### Step 4: Extract Features

```bash
# Extract 318 static features from all samples
python scripts/ml/extract_features_batch.py

# Optional: Use all CPU cores for faster processing
python scripts/ml/extract_features_batch.py --n-jobs -1
```

**Features extracted** (318 total):
- **File metadata** (2 features):
  - File size
  - Shannon entropy (randomness)
- **Byte histogram** (256 features):
  - Frequency of each byte value (0x00-0xFF)
- **PE headers** (20 features) - for Windows executables:
  - Number of sections
  - Entry point address
  - Import/export counts
  - Timestamp
- **ELF headers** (20 features) - for Linux binaries:
  - ELF class (32/64-bit)
  - Machine architecture
  - Program header count
  - Section types
- **Section analysis** (10 features):
  - Average section entropy
  - Executable sections count
  - Section size statistics
- **String features** (10 features):
  - Suspicious API calls count
  - URL count
  - Registry key references
  - Obfuscation indicators

**Output:**
```
📊 Processing train split...
✅ Processed: 420/420 samples (100.0%)
   Success: 415/420 (98.8%)
   Failed: 5/420 (1.2%)

📊 Processing val split...
✅ Processed: 90/90 samples (100.0%)

📊 Processing test split...
✅ Processed: 90/90 samples (100.0%)

✅ Features saved to: data/features/
```

### Step 5: Train the Model

```bash
# Train Random Forest with default hyperparameters
python scripts/ml/train_random_forest.py
```

**Training details:**
- Algorithm: Random Forest Classifier
- Trees: 500
- Class weighting: Balanced (handles imbalanced datasets)
- Training time: 3-5 seconds (quick setup), 1-2 minutes (full)

**Expected output:**
```
🌲 Random Forest Baseline Training

📊 Class distribution:
  • Malware: 70 (16.7%)
  • Benign:  350 (83.3%)
  • Ratio:   1:5.0 (malware:benign)

⚖️  Class weights (balanced):
  • Benign:  0.600
  • Malware: 3.000

🚀 Training model...
✅ Training complete in 3.77 seconds

======================================================================
Metric               Train        Val          Test
-------------------- ------------ ------------ ------------
Accuracy             1.0000       1.0000       0.9889
Precision            1.0000       1.0000       1.0000
Recall               1.0000       1.0000       0.9333
F1                   1.0000       1.0000       0.9655
Auc                  1.0000       1.0000       1.0000
======================================================================

💾 Model saved: models/checkpoints/malware_detector_rf/malware_detector_rf_v1.0.0.pkl
```

### Step 6: Test the Model

```bash
# Test on sample files
python scripts/ml/test_ml_detector.py
```

**Expected results:**
```
🤖 Testing Random Forest ML Detector

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ File                         ┃ Type     ┃ Prediction ┃ Confidence ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ malware_sample_1             │ Malware  │ MALWARE ✓  │     93.60% │
│ malware_sample_2             │ Malware  │ MALWARE ✓  │     80.00% │
│ system_binary_1              │ Benign   │ BENIGN ✓   │      0.20% │
│ system_binary_2              │ Benign   │ BENIGN ✓   │      1.40% │
└──────────────────────────────┴──────────┴────────────┴────────────┘

Accuracy: 100.0% (10/10 correct)
Avg scan time: 436.04 ms
```

**✅ Success! Your model is working.**

---

## Using Your Trained Model

### Option 1: Python API

```python
from pathlib import Path
from app.ml.random_forest_detector import RandomForestDetector

# Initialize detector
detector = RandomForestDetector(model_version="1.0.0")

# Scan a file
result = detector.scan_file("/path/to/suspicious/file")

print(f"Malware: {result.is_malware}")
print(f"Confidence: {result.confidence:.2%}")
print(f"Scan time: {result.prediction_time:.3f}s")

# Get statistics
stats = detector.get_statistics()
print(f"Scans performed: {stats['scans_performed']}")
print(f"Detection rate: {stats['detection_rate']:.2%}")
```

### Option 2: Command Line

```bash
# Scan single file
python -c "
from app.ml.random_forest_detector import RandomForestDetector
result = RandomForestDetector().scan_file('/path/to/file')
print(f'Malware: {result.is_malware} (confidence: {result.confidence:.1%})')
"

# Scan directory (batch)
python -c "
from pathlib import Path
from app.ml.random_forest_detector import RandomForestDetector

detector = RandomForestDetector()
for file in Path('/path/to/directory').rglob('*'):
    if file.is_file():
        result = detector.scan_file(file)
        if result.is_malware:
            print(f'⚠️  {file.name}: {result.confidence:.1%}')
"
```

### Option 3: Integration with Main Scanner

```python
from app.core.unified_scanner_engine import UnifiedScannerEngine

# Enable ML scanning
scanner = UnifiedScannerEngine(
    clamav_enabled=True,
    yara_enabled=True,
    ml_enabled=True,  # ← Enable ML detector
)

# Scan with all engines (ClamAV + YARA + ML)
result = scanner.scan_file("/path/to/file")
```

---

## Advanced Topics

### Improving Model Accuracy

If your model achieves <95% accuracy, try:

**1. Collect more data:**
```bash
# Increase dataset size
python scripts/ml/dataset_workflow.py --malware 10000 --benign 10000
```

**2. Hyperparameter tuning:**
```bash
# Optimize hyperparameters (takes ~1 hour)
python scripts/ml/tune_random_forest.py --n-trials 100

# Uses Optuna to find best:
# • Number of trees
# • Max depth
# • Min samples split
# • Feature selection
```

**3. Feature engineering:**
```python
# Add custom features to app/ml/feature_extractor.py
# Examples:
# • N-gram analysis
# • Control flow graphs
# • Import function entropy
# • PE resource characteristics
```

### Retraining with New Samples

```bash
# 1. Download new malware (append to existing)
python scripts/ml/download_malwarebazaar.py --samples 1000 --skip-existing

# 2. Collect new benign files
python scripts/ml/collect_benign.py --samples 1000

# 3. Re-organize dataset
python scripts/ml/organize_dataset.py

# 4. Re-extract features
python scripts/ml/extract_features_batch.py

# 5. Retrain model
python scripts/ml/train_random_forest.py
```

### Model Versioning

```bash
# Models are saved with version numbers
ls models/checkpoints/malware_detector_rf/
# malware_detector_rf_v1.0.0.pkl
# malware_detector_rf_v1.1.0.pkl
# malware_detector_rf_v2.0.0.pkl

# Load specific version
detector = RandomForestDetector(model_version="2.0.0")
```

---

## Security Best Practices

### Isolated Training Environment

**Recommended setup for production:**

```bash
# Use Docker with no network access
docker run -it --rm --network=none \
  -v $(pwd)/data:/workspace/data \
  -v $(pwd)/models:/workspace/models \
  python:3.13 bash

# Inside container:
cd /workspace
pip install scikit-learn joblib pefile lief rich
python scripts/ml/train_random_forest.py
```

### Verify Downloaded Files

```bash
# Check file permissions (no execute bit)
ls -l data/malware/ | head -5
# Expected: -rw------- (0600)

# Verify hashes match metadata
python -c "
import json, hashlib
from pathlib import Path

metadata = json.loads(Path('data/malware/metadata.json').read_text())
for sha256, info in list(metadata.items())[:5]:
    file_path = Path('data/malware') / sha256
    if file_path.exists():
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        match = '✅' if actual_hash == sha256 else '❌'
        print(f'{match} {sha256[:16]}...')
"
```

### What to NEVER Do

❌ **NEVER execute malware files:**
```bash
# ❌ DANGEROUS - DO NOT RUN
./data/malware/somefile
python data/malware/script.py
chmod +x data/malware/*
```

❌ **NEVER import malware as Python modules:**
```python
# ❌ DANGEROUS - DO NOT DO
import sys
sys.path.insert(0, "data/malware")
import malware_sample  # This executes code!
```

✅ **ALWAYS use static analysis only:**
```python
# ✅ SAFE - Static analysis
from app.ml.feature_extractor import FeatureExtractor
extractor = FeatureExtractor()
features = extractor.extract(Path("data/malware/somefile"))
# Only reads bytes, no execution
```

---

## Troubleshooting

### Common Issues

**Issue**: "Missing ML dependencies"
```bash
# Solution: Install malware-analysis extras
uv sync --extra malware-analysis
```

**Issue**: "No model found"
```bash
# Solution: Train a model first
python scripts/ml/train_random_forest.py
```

**Issue**: "No features found"
```bash
# Solution: Extract features first
python scripts/ml/extract_features_batch.py
```

**Issue**: Low accuracy (<90%)
```bash
# Solutions:
# 1. Use more data (--full instead of --quick)
# 2. Check class balance in metadata
# 3. Tune hyperparameters
python scripts/ml/tune_random_forest.py
```

---

## FAQ

**Q: Can I use pre-trained models?**
A: Not recommended. Train your own for your specific threat landscape.

**Q: How often should I retrain?**
A: Monthly or when encountering new malware families.

**Q: Does this require GPU?**
A: No. Random Forest is CPU-only. Deep learning models (future) may use GPU.

**Q: Is this production-ready?**
A: Yes, but monitor false positives and retrain regularly.

**Q: Can I contribute my trained model?**
A: No - models are environment-specific. Contribute training improvements instead.

**Q: What if I can't download malware?**
A: Contact security researchers or use public malware repositories (VirusShare, theZoo).

---

## Next Steps

After building your model:

1. **Integrate**: Use in production scanning workflows
2. **Monitor**: Track false positives/negatives
3. **Improve**: Collect new samples and retrain
4. **Contribute**: Share improvements to training scripts

**Related Documentation:**
- [ML Setup Guide](../../docs/user/ML_SETUP_GUIDE.md)
- [Phase 3 Roadmap](../../docs/project/PHASE_3_STRATEGIC_PLAN.md)
- [Training Scripts README](../../scripts/ml/README.md)

---

**Questions or issues?** Open a GitHub issue or see the docs.
