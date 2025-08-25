#!/bin/bash
# Import Fix Script for xanadOS-Search_Destroy
# Fixes relative imports to absolute imports

set -euo pipefail

echo "🔧 Fixing relative imports across the codebase..."

# Navigate to project root
cd "$(dirname "$0")/../.."

# Backup files before modification
echo "📦 Creating backup..."
mkdir -p backups/import-fix-$(date +%Y%m%d-%H%M%S)
find app/ -name "*.py" -exec cp {} backups/import-fix-$(date +%Y%m%d-%H%M%S)/ \;

# Fix core imports
echo "🔄 Fixing 'from core' imports..."
find app/ -name "*.py" -exec sed -i 's/from core\./from app.core./g' {} \;

# Fix gui imports
echo "🔄 Fixing 'from gui' imports..."
find app/ -name "*.py" -exec sed -i 's/from gui\./from app.gui./g' {} \;

# Fix utils imports
echo "🔄 Fixing 'from utils' imports..."
find app/ -name "*.py" -exec sed -i 's/from utils\./from app.utils./g' {} \;

# Fix monitoring imports
echo "🔄 Fixing 'from monitoring' imports..."
find app/ -name "*.py" -exec sed -i 's/from monitoring\./from app.monitoring./g' {} \;

echo "✅ Import fixes complete!"

# Test main imports
echo "🧪 Testing core imports..."
if python -c "from app.main import main; print('✅ app.main imports successfully')"; then
    echo "✅ Core application imports working"
else
    echo "❌ Core application imports still have issues"
fi

echo "🧪 Testing GUI imports..."
if python -c "from app.gui.main_window import MainWindow; print('✅ MainWindow imports successfully')"; then
    echo "✅ GUI components imports working"
else
    echo "❌ GUI components imports still have issues"
fi

echo "📋 Import fix summary:"
echo "- Processed all Python files in app/ directory"
echo "- Fixed relative imports to absolute imports"
echo "- Created backup in backups/ directory"
echo "- Tested main application imports"
