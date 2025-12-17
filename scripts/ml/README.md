# ML Scripts Directory

Dataset acquisition and processing scripts for Phase 3: ML-Based Threat Detection.

## Scripts Overview

### 1. Dataset Acquisition

#### `download_malwarebazaar.py`
Downloads malware samples from MalwareBazaar API.

**Features**:
- Free API access (no registration)
- SHA256 verification
- Resume support (skips existing files)
- Metadata tracking
- Rate limiting (1 req/sec)

**Usage**:
```bash
# Download 50K samples (production)
uv run python scripts/ml/download_malwarebazaar.py --samples 50000

# Download 5K samples (testing)
uv run python scripts/ml/download_malwarebazaar.py --samples 5000

# Custom output directory
uv run python scripts/ml/download_malwarebazaar.py --samples 10000 --output-dir /path/to/dir
```

**Output**:
- Files: `data/malware/{sha256_hash}`
- Metadata: `data/malware/metadata.json`

---

#### `collect_benign.py`
Collects clean executable files from system directories.

**Features**:
- Scans trusted system paths
- ELF/PE format validation
- Size filtering (1KB - 100MB)
- SHA256 deduplication
- Safe file copying (non-destructive)

**Usage**:
```bash
# Collect 50K benign files
uv run python scripts/ml/collect_benign.py --samples 50000

# Include user directories
uv run python scripts/ml/collect_benign.py --samples 50000 --include-user-dirs
```

**Output**:
- Files: `data/benign/{filename}_{hash}`
- Metadata: `data/benign/metadata.json`

---

#### `organize_dataset.py`
Organizes samples into train/validation/test splits.

**Features**:
- 70/15/15 split (configurable)
- Shuffled with fixed seed (reproducibility)
- Creates organized directory structure
- Generates dataset metadata

**Usage**:
```bash
# Standard 70/15/15 split
uv run python scripts/ml/organize_dataset.py

# Custom split ratios
uv run python scripts/ml/organize_dataset.py --train-ratio 0.8 --val-ratio 0.1 --test-ratio 0.1

# Custom seed for different shuffle
uv run python scripts/ml/organize_dataset.py --seed 123
```

**Output**:
```
data/organized/
├── train/
│   ├── malware/
│   └── benign/
├── val/
│   ├── malware/
│   └── benign/
├── test/
│   ├── malware/
│   └── benign/
└── metadata.json
```

---

### 2. Workflow Automation

#### `dataset_workflow.py`
Complete automation of dataset acquisition (all 3 steps).

**Features**:
- Preset modes: quick/small/full
- Time and size estimation
- Progress tracking
- Error handling

**Usage**:
```bash
# Quick test (1K samples, ~10 minutes)
uv run python scripts/ml/dataset_workflow.py --quick

# Small dataset (10K samples, ~2 hours) - RECOMMENDED
uv run python scripts/ml/dataset_workflow.py --small

# Full production (100K samples, ~14 hours)
uv run python scripts/ml/dataset_workflow.py --full

# Custom counts
uv run python scripts/ml/dataset_workflow.py --malware 10000 --benign 10000
```

**Workflow Steps**:
1. Download malware from MalwareBazaar
2. Collect benign files from system
3. Organize into train/val/test splits

---

## Dataset Modes Comparison

| Mode | Malware | Benign | Total | Time | Size | Use Case |
|------|---------|--------|-------|------|------|----------|
| `--quick` | 500 | 500 | 1,000 | ~10 min | ~0.5 GB | Testing scripts |
| `--small` | 5,000 | 5,000 | 10,000 | ~2 hours | ~5 GB | **Prototyping** ⭐ |
| `--full` | 50,000 | 50,000 | 100,000 | ~14 hours | ~50 GB | Production training |

---

## Recommended Workflow

### Initial Setup (Day 2-3)
```bash
# 1. Start with small dataset for validation
uv run python scripts/ml/dataset_workflow.py --small

# 2. Verify dataset organization
ls -lh data/organized/*/
cat data/organized/metadata.json

# 3. Check dataset stats
uv run python -c "
import json
from pathlib import Path
meta = json.loads(Path('data/organized/metadata.json').read_text())
print(f'Total: {meta[\"total_samples\"]:,}')
print(f'Train: {meta[\"splits\"][\"train\"][\"total\"]:,}')
print(f'Val: {meta[\"splits\"][\"val\"][\"total\"]:,}')
print(f'Test: {meta[\"splits\"][\"test\"][\"total\"]:,}')
"
```

### Production Dataset (Optional)
```bash
# Run overnight for full 100K dataset
nohup uv run python scripts/ml/dataset_workflow.py --full > dataset_acquisition.log 2>&1 &

# Monitor progress
tail -f dataset_acquisition.log
```

---

## Safety Guidelines

⚠️ **CRITICAL**: The malware directory contains LIVE MALWARE.

**Safety Measures**:
1. Never execute files from `data/malware/`
2. Use isolated VM/container for analysis
3. Keep proper file permissions (0700)
4. Add to antivirus exclusions if needed
5. Encrypt at rest (optional)

**Disk Space Requirements**:
- Quick: 0.5 GB
- Small: 5 GB
- Full: 50+ GB

---

## Troubleshooting

### MalwareBazaar API Issues
```bash
# Check API status
curl -X POST https://mb-api.abuse.ch/api/v1/ \
     -d "query=get_recent&selector=10"

# Increase delay if rate-limited
uv run python scripts/ml/download_malwarebazaar.py --samples 5000 --delay 2.0
```

### Insufficient Benign Samples
```bash
# Include user directories
uv run python scripts/ml/collect_benign.py --samples 50000 --include-user-dirs

# Or download Debian packages
# (see data/README.md for alternative sources)
```

### Dataset Verification
```bash
# Check sample counts
find data/organized/train/malware -type f | wc -l
find data/organized/train/benign -type f | wc -l

# Verify metadata
python -c "
import json
from pathlib import Path
meta = json.loads(Path('data/organized/metadata.json').read_text())
assert meta['splits']['train']['malware'] == meta['splits']['train']['benign']
print('✅ Dataset balanced')
"
```

---

## Next Steps

After dataset acquisition:

**Day 4-5**: Feature Extraction
- Implement `app/ml/feature_extractor.py`
- Extract static features (PE/ELF headers, entropy, strings)
- Run batch extraction: `scripts/ml/extract_features_batch.py`

**Week 3-4**: Model Training
- Train Random Forest baseline
- Achieve 90%+ accuracy
- Export to ONNX format

See: `docs/project/PHASE_3_IMPLEMENTATION_KICKOFF.md`
