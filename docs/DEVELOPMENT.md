# Development Setup

## Virtual Environment Setup

This project uses a Python virtual environment. To set up for development:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
pip install PyQt6

# Run the application
python app/main.py

# Run tests
python -m pytest tests/
```

## Directory Structure

- `app/` - Main application source code
- `tests/` - Test suite
- `docs/` - Documentation (empty, ready for future docs)
- `config/` - Configuration files (local.json is ignored)
- `data/logs/` - Application log files (ignored)
- `data/reports/` - Generated scan reports (ignored)
- `data/quarantine/` - Quarantined files (ignored)
- `.venv/` - Python virtual environment (ignored)
