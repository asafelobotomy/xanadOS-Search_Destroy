#!/bin/bash
# Build verification script

echo "🔍 Verifying project structure and build readiness..."

# Check project structure
required_files=(
    "app/main.py"
    "app/gui/main_window.py" 
    "app/gui/scan_dialog.py"
    "app/gui/settings_dialog.py"
    "requirements.txt"
    "packaging/flatpak/org.xanados.SearchAndDestroy.yml"
    "Makefile"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    echo "✅ All required files present"
else
    echo "❌ Missing required files:"
    printf '  %s\n' "${missing_files[@]}"
    exit 1
fi

# Check Python syntax
echo "🐍 Checking Python syntax..."
if ./.venv/bin/python -m py_compile app/main.py app/gui/*.py app/core/*.py app/utils/*.py 2>/dev/null; then
    echo "✅ Python syntax OK"
else
    echo "❌ Python syntax errors found"
    exit 1
fi

# Check imports
echo "🔗 Checking critical imports..."
if ./.venv/bin/python -c "
import sys
sys.path.insert(0, 'src')
try:
    from PyQt6.QtWidgets import QApplication
    import pyclamd
    print('✅ Critical imports OK')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"; then
    true
else
    exit 1
fi

echo ""
echo "🎯 Project verification complete - ready for Flatpak build!"
