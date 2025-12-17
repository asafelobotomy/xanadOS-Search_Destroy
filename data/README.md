# Data Directory

This directory contains malware samples, benign files, and cached features for ML training.

## Directory Structure

```
data/
├── malware/          # Malware samples (50K+ samples)
├── benign/           # Benign files (50K+ samples)
├── organized/        # Organized dataset split into train/val/test
│   ├── train/
│   │   ├── malware/
│   │   └── benign/
│   ├── val/
│   │   ├── malware/
│   │   └── benign/
│   └── test/
│       ├── malware/
│       └── benign/
└── cache/            # Cached extracted features (.npz files)
```

## Dataset Acquisition

**Malware Sources**:
- MalwareBazaar (https://bazaar.abuse.ch/) - Recommended, fresh samples
- VirusShare (https://virusshare.com/) - Large collection (requires registration)
- theZoo (https://github.com/ytisf/theZoo) - Curated collection

**Benign Sources**:
- Debian/Ubuntu packages
- System binaries (/usr/bin, /usr/sbin)
- Open-source applications

**Target**: 100,000 samples total (50K malware + 50K benign)

## Dataset Organization

Use `scripts/ml/organize_dataset.py` to split samples into train/val/test:
- Training: 70% (70,000 samples)
- Validation: 15% (15,000 samples)
- Test: 15% (15,000 samples)

## Security Considerations

⚠️ **WARNING**: This directory contains LIVE MALWARE samples.

**Safety Guidelines**:
1. Never execute files from `malware/` directory
2. Use isolated VM/container for analysis
3. Keep samples encrypted at rest (optional)
4. Ensure proper file permissions (0700)
5. Add to antivirus exclusions (if using ClamAV)

## Cache Files

Extracted features are cached in `.npz` format for fast reloading:
- Cache key: `SHA256(file_content) + file_mtime`
- Invalidated when feature extraction schema changes
- Regenerate cache: `rm -rf data/cache/*`

## Disk Space Requirements

- Malware samples: ~50GB
- Benign samples: ~50GB
- Cached features: ~5GB
- **Total**: ~105GB minimum
