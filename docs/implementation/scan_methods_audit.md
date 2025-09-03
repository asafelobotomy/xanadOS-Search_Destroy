# 📋 **SCAN METHODS AUDIT REPORT**

## 📊 **GUI SCANNING ELEMENTS ANALYSIS**

### 🎯 **Available Scan Buttons & Controls**

#### **1. Quick Scan Button** (`self.quick_scan_btn`)

- **GUI Label**: "Quick Scan"
- **Location**: Dashboard tab (actions area)
- **Connection**: `self.quick_scan_btn.clicked.connect(self.quick_scan)`
- **Method**: `quick_scan()`→`start_quick_scan()`→`start_scan(quick_scan=True)`
- **Scan Type**: Sets `quick_scan=True` parameter
- **Target Path**: Automatically selects Downloads folder (or first available from: Downloads,
  Desktop, Documents, temp)
- **✅ STATUS**: **CORRECT** - Properly calls with `quick_scan=True`

#### **2. Main Start Scan Button** (`self.start_scan_btn`)

- **GUI Label**: "🚀 Start Scan"
- **Location**: Scan tab (actions section)
- **Connection**: `self.start_scan_btn.clicked.connect(self.start_scan)`
- **Method**: `start_scan()`(no parameters, defaults to`quick_scan=False`)
- **Scan Type**: Determined by `scan_type_combo` selection
- **Target Path**: Based on scan type + user-selected path
- **✅ STATUS**: **CORRECT** - Uses combo box for scan type determination

#### **3. Scan Type Combo Box** (`self.scan_type_combo`)

- **GUI Options**:
- "🚀 Quick Scan" → Data: "QUICK"
- "🔍 Full Scan" → Data: "FULL"
- "⚙️ Custom Scan" → Data: "CUSTOM"
- **Connection**: `self.scan_type_combo.currentTextChanged.connect(self.on_scan_type_changed)`
- **Method**: Used by `start_scan()`to determine`effective_scan_type`
- **✅ STATUS**: **CORRECT** - Proper data mapping

#### **4. Path Selection Buttons**

- **Home Folder Button** (`self.home_scan_btn`):
- Label: "🏠 Home Folder"
- Connection: `lambda: self.set_scan_path(str(Path.home()))`
- **✅ STATUS**: **CORRECT** - Sets path only, doesn't trigger scan
- **Downloads Button** (`self.downloads_scan_btn`):
- Label: "📥 Downloads"
- Connection: `lambda: self.set_scan_path(str(Path.home() / "Downloads"))`
- **✅ STATUS**: **CORRECT** - Sets path only, doesn't trigger scan
- **Custom Path Button** (`self.custom_scan_btn`):
- Label: "📁 Choose Folder..."
- Connection: `self.custom_scan_btn.clicked.connect(self.select_scan_path)`
- **✅ STATUS**: **CORRECT** - Opens file dialog, sets path only

#### **5. RKHunter Scan Button** (`self.rkhunter_scan_btn`)

- **GUI Label**: "🔍 RKHunter Scan" (or "📦 Setup RKHunter" if not installed)
- **Connection**:
- Available: `self.start_rkhunter_scan`
- Not Available: `self.install_rkhunter`
- **Method**: Direct RKHunter scan (independent of ClamAV)
- **✅ STATUS**: **CORRECT** - Separate RKHunter-only functionality

#### **6. Stop Scan Button** (`self.stop_scan_btn`)

- **GUI Label**: "⏹️ Stop Scan"
- **Connection**: `self.stop_scan_btn.clicked.connect(self.stop_scan)`
- **✅ STATUS**: **CORRECT** - Properly stops running scans

---

## 🔄 **SCAN TYPE DETERMINATION LOGIC**

### **Priority Order in `start_scan()` Method**

1. **First Priority**: `quick_scan` parameter

- If `quick_scan=True`→`effective_scan_type = "QUICK"`

2. **Second Priority**: `scan_type_combo.currentData()`

- If combo has data → `effective_scan_type = scan_type_data`

3. **Default**: Fall back to FULL

- If no parameter or combo data → `effective_scan_type = "FULL"`

### **✅ CORRECT BEHAVIOR**: This logic properly handles both scan triggering methods

- **Dedicated Quick Scan button**: Uses `quick_scan=True` parameter (Priority 1)
- **Main Scan button**: Uses combo box selection (Priority 2)

---

## 📍 **PATH SELECTION LOGIC**

### **Scan Type → Path Mapping**

#### **QUICK Scan**

````Python
quick_scan_paths = [
    "~/Downloads",     # Primary target
    "~/Desktop",       # Secondary
    "~/Documents",     # Tertiary
    tempfile.gettempdir(),  # System temp
    "/tmp"             # Linux temp
]

# Uses first available path

```text

**✅ STATUS**: **CORRECT** - Focuses on high-risk infection vectors

## **FULL Scan**

```Python
self.scan_path = os.path.expanduser("~")  # Entire home directory

```text

**✅ STATUS**: **CORRECT** - Comprehensive coverage

### **CUSTOM Scan**

```Python

## Uses user-selected path from GUI controls

## Validates path exists before scanning

```text

**✅ STATUS**: **CORRECT** - User control with validation

---

## 🛡️ **RKHUNTER INTEGRATION LOGIC**

### **Full Scan Integration**

- **Condition**: `is_full_system_scan AND rkhunter_enabled AND run_with_full_scan`
- **✅ STATUS**: **CORRECT**

### **Quick Scan Integration**

- **Condition**: `(quick_scan OR effective_scan_type=="QUICK") AND rkhunter_enabled AND run_with_quick_scan`
- **✅ STATUS**: **CORRECT** - Recently fixed to handle both trigger methods

### **Execution Order**

- **Full Scan**: ClamAV → RKHunter (original flow)
- **Quick Scan**: RKHunter → ClamAV (recently improved for conflict prevention)
- **✅ STATUS**: **CORRECT** - Different optimized flows

---

## 🎛️ **SETTINGS INTEGRATION**

### **RKHunter Settings**

- **General Enable**: `rkhunter_settings.enabled`
- **Full Scan Integration**: `rkhunter_settings.run_with_full_scan`
- **Quick Scan Integration**: `rkhunter_settings.run_with_quick_scan`
- **Auto Update**: `rkhunter_settings.auto_update`
- **Categories**: `rkhunter_settings.categories` (rootkits, network, etc.)
- **✅ STATUS**: **CORRECT** - All properly connected to UI checkboxes

### **Scan Options**

- **Archives**: `advanced_settings.scan_archives`
- **Symlinks**: `advanced_settings.follow_symlinks`
- **Depth**: `advanced_settings.scan_depth`
- **File Filter**: `advanced_settings.file_filter`
- **Memory Limit**: `advanced_settings.memory_limit`
- **✅ STATUS**: **CORRECT** - Advanced options properly applied

---

## 🚨 **IDENTIFIED ISSUES & RECOMMENDATIONS**

### ❌ **Issue 1**: Potential UI Confusion

**Problem**: Both the dedicated "Quick Scan" button AND the combo box "Quick Scan" option perform quick scans, but with slightly different behaviors:

- **Dedicated button**: Forces Downloads folder, updates button text
- **Combo option**: Uses selected path, doesn't update button state

**Recommendation**: Add clear tooltips explaining the difference or consolidate functionality.

### ❌ **Issue 2**: Path Override Inconsistency

**Problem**: When using combo box "Quick Scan", if user has selected a custom path, it gets overridden to Downloads folder.

**Current Logic**:

```Python
if effective_scan_type == "QUICK":

## Always overrides to Downloads, ignoring user selection

    self.scan_path = valid_paths[0]  # Downloads

```text

**Recommendation**: Respect user-selected path for combo box quick scans:

```Python
if effective_scan_type == "QUICK":
    if not hasattr(self, 'scan_path') or not self.scan_path:

## Only set default if no path selected

        self.scan_path = valid_paths[0]

## Otherwise keep user selection

```text

### ✅ **Issue 3**: RESOLVED - RKHunter Quick Scan Integration

**Problem**: RKHunter wasn't triggering for quick scans
**Solution**: Fixed logic to check both `quick_scan`parameter AND`effective_scan_type`

---

## 📈 **OVERALL ASSESSMENT**

### **✅ STRENGTHS**

1. **Clear Separation**: Different scan methods are logically separated
2. **Proper Connections**: All buttons connect to correct methods
3. **Flexible Architecture**: Supports multiple triggering paths
4. **Settings Integration**: Comprehensive settings properly applied
5. **RKHunter Integration**: Now working for both full and quick scans

### **⚠️ MINOR IMPROVEMENTS NEEDED**

1. **UI Clarity**: Make difference between quick scan methods clearer
2. **Path Consistency**: Respect user path selection in combo quick scans
3. **Documentation**: Add more detailed tooltips for scan type differences

### **🎯 COMPLIANCE SCORE**: **90/100**

- **Functionality**: 95/100 (works correctly)
- **User Experience**: 85/100 (could be clearer)
- **Code Quality**: 90/100 (well-structured)
````
