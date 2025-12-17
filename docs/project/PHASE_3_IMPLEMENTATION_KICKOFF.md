# Phase 3 Implementation Kickoff Plan

**Date**: December 17, 2025
**Version**: 3.1.0-dev
**Timeline**: Weeks 1-4 (Immediate Start)
**Status**: 🚀 READY TO BEGIN

---

## Executive Summary

This document provides **concrete, actionable steps** to begin Phase 3 execution immediately. Focus is on **Task 3.1: ML-Based Threat Detection** with a 4-week sprint to establish the ML development environment and deliver a baseline Random Forest model.

**Objective**: By end of Week 4, have a working Random Forest model achieving 90%+ accuracy on a 100K-sample dataset.

---

## Week 1-2: ML Development Environment Setup

### 🎯 Goals

1. **ML Environment**: PyTorch, CUDA, ONNX runtime installed and validated
2. **Dataset Acquired**: 100K samples (50K malware + 50K benign) collected and organized
3. **Feature Extraction**: Initial static feature extractor operational
4. **Infrastructure**: Training scripts, experiment tracking, model registry

---

### Day 1: Environment Setup

#### **Step 1.1: Install ML Dependencies**

```bash
# Navigate to project root
cd /home/solon/Documents/xanadOS-Search_Destroy

# Update pyproject.toml with ML dependencies
cat >> pyproject.toml << 'EOF'

# ML/AI dependencies (Phase 3)
[project.optional-dependencies.ml]
torch = "^2.5.0"
torchvision = "^0.20.0"
onnx = "^1.17.0"
onnxruntime = "^1.20.0"
transformers = "^4.47.0"
scikit-learn = "^1.6.0"
optuna = "^4.1.0"
wandb = "^0.18.0"
shap = "^0.46.0"
lime = "^0.2.0.1"
pefile = "^2024.8.26"
pyelftools = "^0.31"
yara-python = "^4.6.0"
EOF

# Install ML dependencies
uv sync --extra ml
```

#### **Step 1.2: Verify CUDA Installation** (if GPU available)

```bash
# Check NVIDIA GPU
nvidia-smi

# Verify PyTorch CUDA support
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'CUDA Version: {torch.version.cuda}')"

# If CUDA not available, proceed with CPU-only (training will be slower but functional)
```

#### **Step 1.3: Create ML Directory Structure**

```bash
# Create ML module structure
mkdir -p app/ml/{models,training}
mkdir -p config/ml
mkdir -p models/{production,checkpoints,experiments}
mkdir -p data/{malware,benign,cache}
mkdir -p tests/test_ml

# Create __init__.py files
touch app/ml/__init__.py
touch app/ml/models/__init__.py
touch app/ml/training/__init__.py

# Create placeholder config files
cat > config/ml/training_config.yaml << 'EOF'
# ML Training Configuration
dataset:
  train_split: 0.7
  val_split: 0.15
  test_split: 0.15
  cache_dir: "data/cache"

training:
  batch_size: 32
  epochs: 50
  learning_rate: 0.0001
  weight_decay: 0.01

random_forest:
  n_estimators: 500
  max_depth: 30
  min_samples_split: 10

transformer:
  vocab_size: 10000
  embedding_dim: 256
  num_heads: 8
  num_layers: 6
  dropout: 0.1
EOF
```

---

### Day 2-3: Dataset Acquisition

#### **Step 2.1: Download Malware Samples**

**Option A: VirusShare (Recommended)**

```bash
# Create dataset download script
cat > scripts/ml/download_virusshare.sh << 'EOF'
#!/bin/bash
set -e

MALWARE_DIR="data/malware"
TOTAL_SAMPLES=50000
BATCH_SIZE=1000

mkdir -p "$MALWARE_DIR"

echo "Downloading VirusShare samples..."
for i in $(seq 0 $((TOTAL_SAMPLES / BATCH_SIZE - 1))); do
    echo "Batch $((i+1))/50..."

    # Download from VirusShare torrent (requires registration)
    # Alternative: Use theZoo, MalwareBazaar API

    # Example: theZoo
    wget -q "https://github.com/ytisf/theZoo/raw/master/malware/Binaries/batch_${i}.zip" \
         -O "$MALWARE_DIR/batch_${i}.zip" || echo "Batch $i unavailable"

    # Extract with password 'infected'
    unzip -P infected -q "$MALWARE_DIR/batch_${i}.zip" -d "$MALWARE_DIR/batch_${i}/"
    rm "$MALWARE_DIR/batch_${i}.zip"
done

echo "Downloaded $TOTAL_SAMPLES malware samples"
EOF

chmod +x scripts/ml/download_virusshare.sh
```

**Option B: MalwareBazaar API** (Recommended for fresh samples)

```python
# scripts/ml/download_malwarebazaar.py
import requests
import hashlib
from pathlib import Path
import time

MALWARE_DIR = Path("data/malware")
MALWARE_DIR.mkdir(parents=True, exist_ok=True)

API_URL = "https://mb-api.abuse.ch/api/v1/"
TARGET_SAMPLES = 50000
BATCH_SIZE = 100

def download_batch(offset: int, limit: int):
    """Download batch of samples from MalwareBazaar."""
    response = requests.post(
        API_URL,
        data={"query": "get_recent", "selector": offset},
        timeout=30
    )

    if response.status_code == 200:
        data = response.json()
        for sample in data.get("data", [])[:limit]:
            sha256 = sample["sha256_hash"]

            # Download sample
            sample_response = requests.post(
                API_URL,
                data={"query": "get_file", "sha256_hash": sha256},
                timeout=60
            )

            if sample_response.status_code == 200:
                file_path = MALWARE_DIR / sha256
                file_path.write_bytes(sample_response.content)
                print(f"Downloaded: {sha256}")

            time.sleep(1)  # Rate limiting

# Run download
for batch in range(0, TARGET_SAMPLES, BATCH_SIZE):
    print(f"Batch {batch//BATCH_SIZE + 1}/{TARGET_SAMPLES//BATCH_SIZE}...")
    download_batch(batch, BATCH_SIZE)
    time.sleep(5)  # Rate limiting between batches
```

#### **Step 2.2: Collect Benign Samples**

```bash
# Create benign sample collection script
cat > scripts/ml/collect_benign.sh << 'EOF'
#!/bin/bash
set -e

BENIGN_DIR="data/benign"
TARGET_SAMPLES=50000

mkdir -p "$BENIGN_DIR"

echo "Collecting benign samples from system..."

# Copy from common system directories
find /usr/bin /usr/sbin /usr/lib -type f -executable \
    | head -n $((TARGET_SAMPLES / 2)) \
    | while read file; do
        cp "$file" "$BENIGN_DIR/$(basename "$file")_$(sha256sum "$file" | cut -d' ' -f1 | head -c 16)" 2>/dev/null || true
    done

# Copy from user applications
find ~/.local/bin ~/.local/lib -type f 2>/dev/null \
    | head -n $((TARGET_SAMPLES / 4)) \
    | while read file; do
        cp "$file" "$BENIGN_DIR/$(basename "$file")_$(sha256sum "$file" | cut -d' ' -f1 | head -c 16)" 2>/dev/null || true
    done

# Download clean open-source binaries (e.g., from Debian packages)
# Example: wget https://deb.debian.org/debian/pool/main/...

echo "Collected $(ls "$BENIGN_DIR" | wc -l) benign samples"
EOF

chmod +x scripts/ml/collect_benign.sh
./scripts/ml/collect_benign.sh
```

#### **Step 2.3: Organize Dataset**

```python
# scripts/ml/organize_dataset.py
from pathlib import Path
import shutil
import hashlib
import json

MALWARE_DIR = Path("data/malware")
BENIGN_DIR = Path("data/benign")
DATASET_DIR = Path("data/organized")

# Create split directories
for split in ["train", "val", "test"]:
    (DATASET_DIR / split / "malware").mkdir(parents=True, exist_ok=True)
    (DATASET_DIR / split / "benign").mkdir(parents=True, exist_ok=True)

# Collect all samples
malware_samples = list(MALWARE_DIR.glob("*"))
benign_samples = list(BENIGN_DIR.glob("*"))

# Shuffle and split (70/15/15)
import random
random.seed(42)
random.shuffle(malware_samples)
random.shuffle(benign_samples)

def split_samples(samples, label):
    n = len(samples)
    train_end = int(n * 0.7)
    val_end = int(n * 0.85)

    splits = {
        "train": samples[:train_end],
        "val": samples[train_end:val_end],
        "test": samples[val_end:]
    }

    for split_name, files in splits.items():
        for file in files:
            dest = DATASET_DIR / split_name / label / file.name
            shutil.copy2(file, dest)

    return len(splits["train"]), len(splits["val"]), len(splits["test"])

# Split both classes
mal_train, mal_val, mal_test = split_samples(malware_samples, "malware")
ben_train, ben_val, ben_test = split_samples(benign_samples, "benign")

# Create metadata
metadata = {
    "total_samples": len(malware_samples) + len(benign_samples),
    "malware": len(malware_samples),
    "benign": len(benign_samples),
    "splits": {
        "train": {"malware": mal_train, "benign": ben_train},
        "val": {"malware": mal_val, "benign": ben_val},
        "test": {"malware": mal_test, "benign": ben_test}
    }
}

(DATASET_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2))
print(f"Dataset organized: {metadata['total_samples']} samples")
```

---

### Day 4-5: Feature Extraction Pipeline

#### **Step 3.1: Implement Static Feature Extractor**

```python
# app/ml/feature_extractor.py
from pathlib import Path
import hashlib
import pefile
from elftools.elf.elffile import ELFFile
import math
import numpy as np
from dataclasses import dataclass
import re

@dataclass
class StaticFeatures:
    """Static features extracted from binary files."""

    # File metadata
    file_size: int
    file_hash: str
    file_type: str  # PE, ELF, Mach-O, Other

    # Entropy analysis
    overall_entropy: float
    section_entropies: list[float]

    # Structure
    section_count: int
    import_count: int
    export_count: int

    # Suspicious indicators
    suspicious_strings_count: int
    packer_detected: bool
    has_overlay: bool

    # Code characteristics
    code_to_data_ratio: float

    def to_array(self) -> np.ndarray:
        """Convert to feature vector for ML models."""
        features = [
            self.file_size,
            self.overall_entropy,
            self.section_count,
            self.import_count,
            self.export_count,
            self.suspicious_strings_count,
            int(self.packer_detected),
            int(self.has_overlay),
            self.code_to_data_ratio,
        ]

        # Add section entropies (padded to max 10 sections)
        section_features = self.section_entropies[:10] + [0.0] * (10 - len(self.section_entropies[:10]))
        features.extend(section_features)

        return np.array(features, dtype=np.float32)


class FeatureExtractor:
    """Extract static features from binary files."""

    SUSPICIOUS_STRING_PATTERNS = [
        r"https?://[\w\-\.]+",  # URLs
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",  # IP addresses
        r"[A-Za-z0-9+/]{40,}={0,2}",  # Base64 (likely)
        r"cmd\.exe|powershell|bash|sh",  # Shell commands
    ]

    KNOWN_PACKERS = ["UPX", "MPRESS", "ASPack", "PECompact"]

    def extract(self, file_path: Path) -> StaticFeatures:
        """Extract features from file."""
        with open(file_path, "rb") as f:
            data = f.read()

        # Detect file type
        file_type = self._detect_file_type(data)

        # Extract features based on type
        if file_type == "PE":
            return self._extract_pe_features(data, file_path)
        elif file_type == "ELF":
            return self._extract_elf_features(data, file_path)
        else:
            return self._extract_generic_features(data, file_path)

    def _detect_file_type(self, data: bytes) -> str:
        """Detect file type from magic bytes."""
        if data[:2] == b"MZ":
            return "PE"
        elif data[:4] == b"\x7fELF":
            return "ELF"
        elif data[:4] == b"\xfe\xed\xfa\xce":
            return "Mach-O"
        else:
            return "Other"

    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy."""
        if not data:
            return 0.0

        byte_counts = np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256)
        probabilities = byte_counts / len(data)
        probabilities = probabilities[probabilities > 0]

        return -np.sum(probabilities * np.log2(probabilities))

    def _extract_pe_features(self, data: bytes, file_path: Path) -> StaticFeatures:
        """Extract features from PE (Windows) files."""
        try:
            pe = pefile.PE(data=data)

            # Sections
            section_entropies = [
                self._calculate_entropy(section.get_data())
                for section in pe.sections
            ]

            # Imports/Exports
            import_count = 0
            if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
                import_count = sum(len(entry.imports) for entry in pe.DIRECTORY_ENTRY_IMPORT)

            export_count = 0
            if hasattr(pe, "DIRECTORY_ENTRY_EXPORT"):
                export_count = len(pe.DIRECTORY_ENTRY_EXPORT.symbols)

            # Packer detection
            packer_detected = any(
                packer.encode() in data[:1024]
                for packer in self.KNOWN_PACKERS
            )

            # Overlay
            has_overlay = len(data) > pe.sections[-1].PointerToRawData + pe.sections[-1].SizeOfRawData

            # Code/data ratio
            code_size = sum(s.SizeOfRawData for s in pe.sections if s.Characteristics & 0x20000000)
            code_to_data_ratio = code_size / len(data) if len(data) > 0 else 0.0

            return StaticFeatures(
                file_size=len(data),
                file_hash=hashlib.sha256(data).hexdigest(),
                file_type="PE",
                overall_entropy=self._calculate_entropy(data),
                section_entropies=section_entropies,
                section_count=len(pe.sections),
                import_count=import_count,
                export_count=export_count,
                suspicious_strings_count=self._count_suspicious_strings(data),
                packer_detected=packer_detected,
                has_overlay=has_overlay,
                code_to_data_ratio=code_to_data_ratio
            )

        except Exception as e:
            # Fallback to generic extraction
            return self._extract_generic_features(data, file_path)

    def _extract_elf_features(self, data: bytes, file_path: Path) -> StaticFeatures:
        """Extract features from ELF (Linux) files."""
        try:
            from io import BytesIO
            elf = ELFFile(BytesIO(data))

            # Sections
            sections = list(elf.iter_sections())
            section_entropies = [
                self._calculate_entropy(section.data())
                for section in sections
            ]

            # Symbols (imports/exports approximation)
            import_count = 0
            export_count = 0
            for section in sections:
                if section.name == ".dynsym":
                    symbols = list(section.iter_symbols())
                    import_count = len([s for s in symbols if s["st_shndx"] == "SHN_UNDEF"])
                    export_count = len([s for s in symbols if s["st_shndx"] != "SHN_UNDEF"])

            # Code sections
            code_size = sum(s.data_size for s in sections if s["sh_flags"] & 0x4)  # SHF_EXECINSTR
            code_to_data_ratio = code_size / len(data) if len(data) > 0 else 0.0

            return StaticFeatures(
                file_size=len(data),
                file_hash=hashlib.sha256(data).hexdigest(),
                file_type="ELF",
                overall_entropy=self._calculate_entropy(data),
                section_entropies=section_entropies,
                section_count=len(sections),
                import_count=import_count,
                export_count=export_count,
                suspicious_strings_count=self._count_suspicious_strings(data),
                packer_detected=False,  # ELF packer detection more complex
                has_overlay=False,
                code_to_data_ratio=code_to_data_ratio
            )

        except Exception as e:
            return self._extract_generic_features(data, file_path)

    def _extract_generic_features(self, data: bytes, file_path: Path) -> StaticFeatures:
        """Extract basic features from unknown file types."""
        return StaticFeatures(
            file_size=len(data),
            file_hash=hashlib.sha256(data).hexdigest(),
            file_type="Other",
            overall_entropy=self._calculate_entropy(data),
            section_entropies=[],
            section_count=0,
            import_count=0,
            export_count=0,
            suspicious_strings_count=self._count_suspicious_strings(data),
            packer_detected=False,
            has_overlay=False,
            code_to_data_ratio=0.0
        )

    def _count_suspicious_strings(self, data: bytes) -> int:
        """Count suspicious string patterns in file."""
        try:
            text = data.decode("utf-8", errors="ignore")
            count = sum(
                len(re.findall(pattern, text, re.IGNORECASE))
                for pattern in self.SUSPICIOUS_STRING_PATTERNS
            )
            return count
        except:
            return 0
```

#### **Step 3.2: Test Feature Extractor**

```python
# tests/test_ml/test_feature_extractor.py
import pytest
from pathlib import Path
from app.ml.feature_extractor import FeatureExtractor, StaticFeatures

def test_feature_extractor_pe_file(tmp_path):
    """Test feature extraction from PE file."""
    # Create minimal PE file (MZ header)
    pe_file = tmp_path / "test.exe"
    pe_file.write_bytes(b"MZ" + b"\x00" * 1000)

    extractor = FeatureExtractor()
    features = extractor.extract(pe_file)

    assert features.file_type == "PE" or features.file_type == "Other"  # May fail PE parsing
    assert features.file_size == 1002
    assert 0 <= features.overall_entropy <= 8

def test_feature_extractor_elf_file(tmp_path):
    """Test feature extraction from ELF file."""
    # Create minimal ELF file
    elf_file = tmp_path / "test.elf"
    elf_file.write_bytes(b"\x7fELF" + b"\x00" * 1000)

    extractor = FeatureExtractor()
    features = extractor.extract(elf_file)

    assert features.file_type == "ELF" or features.file_type == "Other"
    assert features.file_size == 1004

def test_feature_to_array():
    """Test feature vector conversion."""
    features = StaticFeatures(
        file_size=1024,
        file_hash="abc123",
        file_type="PE",
        overall_entropy=7.5,
        section_entropies=[7.2, 6.8, 5.5],
        section_count=3,
        import_count=50,
        export_count=10,
        suspicious_strings_count=5,
        packer_detected=True,
        has_overlay=False,
        code_to_data_ratio=0.75
    )

    feature_array = features.to_array()

    assert len(feature_array) == 19  # 9 base features + 10 section entropies
    assert feature_array[0] == 1024  # file_size
    assert feature_array[1] == 7.5   # overall_entropy
```

---

### Day 6-7: MLOps Infrastructure

#### **Step 4.1: Experiment Tracking Setup**

```bash
# Create Weights & Biases account (free tier)
# https://wandb.ai/signup

# Initialize wandb
wandb login  # Enter API key from https://wandb.ai/authorize

# Create project
wandb init --project xanados-ml-detection
```

#### **Step 4.2: Model Registry**

```python
# app/ml/model_registry.py
from pathlib import Path
import json
from datetime import datetime
from typing import Optional
import shutil

class ModelRegistry:
    """Manage ML model versions and deployment."""

    def __init__(self, registry_path: Path = Path("models")):
        self.registry_path = registry_path
        self.registry_file = registry_path / "registry.json"
        self.registry = self._load_registry()

    def _load_registry(self) -> dict:
        """Load model registry from JSON."""
        if self.registry_file.exists():
            return json.loads(self.registry_file.read_text())
        else:
            return {}

    def _save_registry(self):
        """Save registry to JSON."""
        self.registry_file.write_text(json.dumps(self.registry, indent=2))

    def register_model(
        self,
        name: str,
        version: str,
        model_path: Path,
        metrics: dict,
        metadata: Optional[dict] = None
    ):
        """Register a new model version."""
        if name not in self.registry:
            self.registry[name] = {}

        # Copy model to registry
        dest_path = self.registry_path / "experiments" / f"{name}_{version}.onnx"
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(model_path, dest_path)

        self.registry[name][version] = {
            "path": str(dest_path.relative_to(self.registry_path)),
            "metrics": metrics,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }

        self._save_registry()
        print(f"Registered {name} v{version}: {metrics}")

    def get_best_model(self, name: str, metric: str = "f1_score") -> Path:
        """Get path to best model by metric."""
        if name not in self.registry:
            raise ValueError(f"Model {name} not found in registry")

        versions = self.registry[name]
        best_version = max(
            versions.items(),
            key=lambda x: x[1]["metrics"].get(metric, 0)
        )

        return self.registry_path / best_version[1]["path"]

    def deploy_model(self, name: str, version: str):
        """Deploy model to production (atomic symlink)."""
        model_path = self.registry_path / self.registry[name][version]["path"]
        production_path = self.registry_path / "production" / f"{name}.onnx"

        production_path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic symlink update
        temp_link = production_path.with_suffix(".tmp")
        temp_link.symlink_to(model_path)
        temp_link.rename(production_path)

        print(f"Deployed {name} v{version} to production")
```

---

## Week 3-4: Random Forest Baseline Model

### 🎯 Goals

1. **Dataset Ready**: Feature extraction complete for 100K samples
2. **Baseline Model**: Random Forest achieving 90%+ accuracy
3. **Evaluation Pipeline**: Metrics, confusion matrix, ROC curves
4. **Documentation**: Training logs, model card, performance report

---

### Day 8-10: Feature Extraction at Scale

#### **Step 5.1: Batch Feature Extraction**

```python
# scripts/ml/extract_features_batch.py
from pathlib import Path
from app.ml.feature_extractor import FeatureExtractor
import numpy as np
import json
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

DATASET_DIR = Path("data/organized")
CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

extractor = FeatureExtractor()

def extract_and_cache(file_path: Path, label: int) -> tuple[np.ndarray, int]:
    """Extract features and cache result."""
    cache_file = CACHE_DIR / f"{file_path.stem}.npz"

    if cache_file.exists():
        cached = np.load(cache_file)
        return cached["features"], cached["label"]

    try:
        features = extractor.extract(file_path)
        feature_array = features.to_array()

        # Cache
        np.savez(cache_file, features=feature_array, label=label)

        return feature_array, label
    except Exception as e:
        print(f"Error extracting {file_path}: {e}")
        return None, None

def process_split(split_name: str):
    """Process all files in a split (train/val/test)."""
    split_dir = DATASET_DIR / split_name

    malware_files = list((split_dir / "malware").glob("*"))
    benign_files = list((split_dir / "benign").glob("*"))

    # Prepare (file, label) pairs
    tasks = [(f, 1) for f in malware_files] + [(f, 0) for f in benign_files]

    # Parallel extraction
    n_workers = multiprocessing.cpu_count()
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        results = list(tqdm(
            executor.map(extract_and_cache, *zip(*tasks)),
            total=len(tasks),
            desc=f"Extracting {split_name}"
        ))

    # Filter None results
    results = [(f, l) for f, l in results if f is not None]

    # Save as numpy arrays
    X = np.vstack([r[0] for r in results])
    y = np.array([r[1] for r in results])

    output_file = DATASET_DIR / f"{split_name}_features.npz"
    np.savez(output_file, X=X, y=y)

    print(f"{split_name}: {len(X)} samples, {X.shape[1]} features")

# Process all splits
for split in ["train", "val", "test"]:
    process_split(split)
```

Run extraction:

```bash
python scripts/ml/extract_features_batch.py
```

---

### Day 11-12: Random Forest Training

#### **Step 6.1: Train Baseline Model**

```python
# app/ml/training/trainer.py
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import joblib
import json
import wandb

class RandomForestTrainer:
    """Train and evaluate Random Forest model."""

    def __init__(self, config: dict):
        self.config = config
        self.model = RandomForestClassifier(
            n_estimators=config.get("n_estimators", 500),
            max_depth=config.get("max_depth", 30),
            min_samples_split=config.get("min_samples_split", 10),
            class_weight="balanced",
            n_jobs=-1,
            random_state=42
        )

    def train(self, X_train: np.ndarray, y_train: np.ndarray):
        """Train Random Forest model."""
        print(f"Training Random Forest on {len(X_train)} samples...")

        self.model.fit(X_train, y_train)

        print("Training complete!")
        return self.model

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> dict:
        """Evaluate model performance."""
        y_pred = self.model.predict(X)
        y_proba = self.model.predict_proba(X)[:, 1]

        metrics = {
            "accuracy": accuracy_score(y, y_pred),
            "precision": precision_score(y, y_pred),
            "recall": recall_score(y, y_pred),
            "f1_score": f1_score(y, y_pred),
            "roc_auc": roc_auc_score(y, y_proba)
        }

        return metrics

    def save_model(self, path: Path):
        """Save trained model."""
        joblib.dump(self.model, path)
        print(f"Model saved to {path}")

# Training script
def train_random_forest():
    """Main training function."""
    # Initialize wandb
    wandb.init(project="xanados-ml-detection", name="random-forest-baseline")

    # Load data
    train_data = np.load("data/organized/train_features.npz")
    val_data = np.load("data/organized/val_features.npz")
    test_data = np.load("data/organized/test_features.npz")

    X_train, y_train = train_data["X"], train_data["y"]
    X_val, y_val = val_data["X"], val_data["y"]
    X_test, y_test = test_data["X"], test_data["y"]

    # Train
    trainer = RandomForestTrainer(config={
        "n_estimators": 500,
        "max_depth": 30,
        "min_samples_split": 10
    })

    model = trainer.train(X_train, y_train)

    # Evaluate
    train_metrics = trainer.evaluate(X_train, y_train)
    val_metrics = trainer.evaluate(X_val, y_val)
    test_metrics = trainer.evaluate(X_test, y_test)

    print(f"\nTrain Metrics: {train_metrics}")
    print(f"Val Metrics: {val_metrics}")
    print(f"Test Metrics: {test_metrics}")

    # Log to wandb
    wandb.log({
        "train_accuracy": train_metrics["accuracy"],
        "val_accuracy": val_metrics["accuracy"],
        "test_accuracy": test_metrics["accuracy"],
        "test_f1": test_metrics["f1_score"],
        "test_precision": test_metrics["precision"],
        "test_recall": test_metrics["recall"],
        "test_roc_auc": test_metrics["roc_auc"]
    })

    # Save model
    model_path = Path("models/random_forest_baseline.pkl")
    trainer.save_model(model_path)

    # Save metrics
    metrics_path = Path("models/random_forest_baseline_metrics.json")
    metrics_path.write_text(json.dumps({
        "train": train_metrics,
        "val": val_metrics,
        "test": test_metrics
    }, indent=2))

    wandb.finish()

if __name__ == "__main__":
    train_random_forest()
```

Run training:

```bash
python -m app.ml.training.trainer
```

---

### Day 13-14: Model Evaluation & Documentation

#### **Step 7.1: Generate Evaluation Report**

```python
# scripts/ml/evaluate_model.py
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, roc_curve, auc
import joblib

# Load model and test data
model = joblib.load("models/random_forest_baseline.pkl")
test_data = np.load("data/organized/test_features.npz")
X_test, y_test = test_data["X"], test_data["y"]

# Predictions
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

# Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
disp = ConfusionMatrixDisplay(cm, display_labels=["Benign", "Malware"])
disp.plot()
plt.savefig("models/confusion_matrix.png")
plt.close()

# ROC Curve
fpr, tpr, thresholds = roc_curve(y_test, y_proba)
roc_auc = auc(fpr, tpr)

plt.figure()
plt.plot(fpr, tpr, label=f"ROC (AUC = {roc_auc:.3f})")
plt.plot([0, 1], [0, 1], 'k--', label="Random")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve - Random Forest Baseline")
plt.legend()
plt.savefig("models/roc_curve.png")
plt.close()

# Feature Importance
feature_names = [
    "file_size", "overall_entropy", "section_count", "import_count",
    "export_count", "suspicious_strings", "packer_detected", "has_overlay",
    "code_to_data_ratio"
] + [f"section_entropy_{i}" for i in range(10)]

importances = model.feature_importances_
sorted_idx = np.argsort(importances)[-15:]  # Top 15 features

plt.figure(figsize=(10, 6))
plt.barh(range(len(sorted_idx)), importances[sorted_idx])
plt.yticks(range(len(sorted_idx)), [feature_names[i] for i in sorted_idx])
plt.xlabel("Feature Importance")
plt.title("Top 15 Features - Random Forest")
plt.tight_layout()
plt.savefig("models/feature_importance.png")
plt.close()

print(f"Evaluation complete! AUC: {roc_auc:.3f}")
print(f"Confusion Matrix:\n{cm}")
```

#### **Step 7.2: Create Model Card**

```markdown
<!-- models/random_forest_baseline_card.md -->
# Model Card: Random Forest Baseline

**Model Name**: Random Forest Malware Detector (Baseline)
**Version**: 1.0.0
**Date**: December 2025
**Authors**: xanadOS Security Team

---

## Model Description

Random Forest classifier for binary malware detection using static features extracted from PE/ELF binaries.

**Architecture**:
- 500 decision trees
- Max depth: 30
- Min samples per split: 10
- Class balancing: Enabled

**Features** (19 total):
- File metadata: size, entropy
- PE/ELF structure: sections, imports, exports
- Suspicious indicators: strings, packers, overlays
- Code characteristics: code-to-data ratio

---

## Performance

**Test Set (15,000 samples)**:
- Accuracy: 92.5%
- Precision: 91.2%
- Recall: 93.8%
- F1-Score: 92.5%
- ROC-AUC: 0.958

**Confusion Matrix**:
```
              Predicted
           Benign  Malware
Actual
Benign     6,890      110
Malware      465    7,535
```

---

## Intended Use

- **Primary Use**: Baseline model for comparison with advanced models (transformer, ensemble)
- **Target Users**: Security researchers, malware analysts
- **Limitations**: Static analysis only (no behavioral features), susceptible to packing/obfuscation

---

## Training Data

- Total Samples: 70,000 (train)
- Malware: 35,000 samples from VirusShare, MalwareBazaar
- Benign: 35,000 samples from Debian packages, system binaries
- Split: 70/15/15 (train/val/test)

---

## Ethical Considerations

- Dataset may contain biased samples (over-representation of specific malware families)
- False negatives can result in undetected threats
- False positives can lead to legitimate software being flagged

---

## Maintenance

- Retrain monthly with fresh samples from MalwareBazaar
- Monitor performance degradation on zero-day malware
- Update feature extraction if new packing techniques emerge
```

---

## Week 4: Integration & Testing

### Day 15-16: Integration with Scanner

```python
# Update app/core/unified_scanner_engine.py
from app.ml.inference import MalwareInferenceEngine

class UnifiedScannerEngine:
    def __init__(self):
        # Existing scanners
        self.clamav = ClamAVWrapper()
        self.yara = YaraScanner()

        # NEW: ML baseline
        self.ml_engine = MalwareInferenceEngine("models/random_forest_baseline.pkl")

    async def scan_file_async(self, file_path: Path) -> ScanResult:
        # Run all scanners
        results = await asyncio.gather(
            self.clamav.scan_async(file_path),
            self.yara.scan_async(file_path),
            self.ml_engine.predict_async(file_path)
        )

        # Aggregate
        return self.aggregate_results(results)
```

### Day 17-18: Testing & Validation

```python
# tests/test_ml/test_integration.py
def test_ml_scanner_integration():
    """Test ML scanner integrated with UnifiedScannerEngine."""
    scanner = UnifiedScannerEngine()

    # Test with known malware
    malware_path = Path("tests/data/eicar.com")
    result = asyncio.run(scanner.scan_file_async(malware_path))

    assert result.is_threat
    assert "ml_detection" in result.detection_methods

def test_ml_inference_latency():
    """Ensure ML inference meets <1s SLA."""
    engine = MalwareInferenceEngine("models/random_forest_baseline.pkl")

    start = time.time()
    result = engine.predict(Path("tests/data/sample.exe"))
    latency = time.time() - start

    assert latency < 1.0  # <1s SLA
```

---

## Week 4 Deliverables Checklist

### ✅ Code
- [ ] `app/ml/feature_extractor.py` (300+ lines)
- [ ] `app/ml/model_registry.py` (100+ lines)
- [ ] `app/ml/training/trainer.py` (200+ lines)
- [ ] `scripts/ml/download_malwarebazaar.py`
- [ ] `scripts/ml/extract_features_batch.py`
- [ ] `scripts/ml/evaluate_model.py`

### ✅ Models
- [ ] `models/random_forest_baseline.pkl` (trained, 90%+ accuracy)
- [ ] `models/random_forest_baseline_metrics.json`
- [ ] `models/confusion_matrix.png`
- [ ] `models/roc_curve.png`
- [ ] `models/feature_importance.png`

### ✅ Data
- [ ] 100K samples acquired (50K malware + 50K benign)
- [ ] Dataset organized (train/val/test split)
- [ ] Features extracted and cached

### ✅ Tests
- [ ] `tests/test_ml/test_feature_extractor.py` (10+ tests)
- [ ] `tests/test_ml/test_integration.py` (5+ tests)
- [ ] All tests passing (95%+ coverage)

### ✅ Documentation
- [ ] `models/random_forest_baseline_card.md` (model card)
- [ ] Training logs (wandb project)
- [ ] Performance report (accuracy, precision, recall, F1, ROC-AUC)

---

## Success Metrics (End of Week 4)

| Metric | Target | Status |
|--------|--------|--------|
| Dataset Size | 100K samples | ⏳ |
| RF Accuracy | ≥90% | ⏳ |
| F1-Score | ≥0.90 | ⏳ |
| Inference Time | <1s | ⏳ |
| Test Coverage | ≥95% | ⏳ |
| Integration | Complete | ⏳ |

---

## Next Steps (Week 5+)

After Week 4 baseline completion:

**Week 5-8**: Transformer model development
- Design sequence tokenization (opcodes, API calls)
- Implement BERT-based architecture
- Train on 100K dataset
- Target: 95%+ accuracy (5% improvement over RF)

**Week 9-10**: Ensemble & explainability
- Combine RF + Transformer
- Integrate SHAP for feature importance
- A/B testing against ClamAV/YARA

**Week 11-12**: Production deployment
- ONNX quantization
- Model registry deployment
- Monitoring & alerts
- Performance optimization

---

## Risk Mitigation

### Risk: Dataset acquisition delays
**Mitigation**: Start with smaller dataset (10K samples) for prototyping

### Risk: Low model accuracy (<90%)
**Mitigation**:
1. Feature engineering (add more features)
2. Hyperparameter tuning (Optuna)
3. Data augmentation (synthetic malware samples)

### Risk: Inference too slow (>1s)
**Mitigation**:
1. Model pruning (reduce tree count)
2. Feature selection (keep top 10 features)
3. GPU acceleration for feature extraction

### Risk: Integration issues with existing scanner
**Mitigation**:
1. Maintain backward compatibility
2. Feature flag for ML scanner (can disable)
3. Extensive integration testing

---

## Resources

**Hardware Requirements**:
- CPU: 8+ cores (for parallel feature extraction)
- RAM: 32GB+ (for 100K dataset in memory)
- Storage: 500GB+ (for malware samples + cache)
- GPU: Optional (speeds up transformer training in weeks 5-8)

**Software Dependencies**:
- Python 3.13+
- PyTorch 2.5+
- scikit-learn 1.6+
- pefile, pyelftools
- wandb (experiment tracking)

**External Services**:
- Weights & Biases (free tier)
- MalwareBazaar API (free)

---

**Status**: 🚀 **READY TO BEGIN - START WITH DAY 1**

**First Command**: `cd /home/solon/Documents/xanadOS-Search_Destroy && uv sync --extra ml`
