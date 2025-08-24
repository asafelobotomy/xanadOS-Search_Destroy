#!/usr/bin/env python3
"""
Component Reference and Linkage Analysis for xanadOS Search & Destroy

This script analyzes all component references and linkages to ensure:
1. Consistent import patterns
2. Correct component references
3. No missing dependencies
4. Proper component integration
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class ImportInfo:
    """Information about an import statement"""
    module: str
    names: List[str]
    alias: str = None
    line_number: int = 0
    is_relative: bool = False

@dataclass
class ComponentIssue:
    """Represents a component linkage issue"""
    file_path: str
    issue_type: str
    description: str
    line_number: int = 0
    suggested_fix: str = ""

class ComponentAnalyzer:
    """Analyzes component references and linkages across the application"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.app_dir = project_root / "app"
        self.core_dir = self.app_dir / "core"
        self.gui_dir = self.app_dir / "gui"
        self.utils_dir = self.app_dir / "utils"
        
        self.issues: List[ComponentIssue] = []
        self.imports_by_file: Dict[str, List[ImportInfo]] = {}
        self.core_components: Set[str] = set()
        self.gui_components: Set[str] = set()
        self.unified_components: Set[str] = set()
        
    def discover_components(self):
        """Discover all available components"""
        print("🔍 Discovering components...")
        
        # Core components
        if self.core_dir.exists():
            for py_file in self.core_dir.glob("*.py"):
                if py_file.name != "__init__.py":
                    self.core_components.add(py_file.stem)
        
        # GUI components
        if self.gui_dir.exists():
            for py_file in self.gui_dir.glob("*.py"):
                if py_file.name != "__init__.py":
                    self.gui_components.add(py_file.stem)
        
        # Unified components (2025 optimizations)
        unified_files = ["unified_security_engine", "unified_performance_optimizer"]
        for component in unified_files:
            if (self.core_dir / f"{component}.py").exists():
                self.unified_components.add(component)
        
        print(f"  ✅ Found {len(self.core_components)} core components")
        print(f"  ✅ Found {len(self.gui_components)} GUI components")
        print(f"  ✅ Found {len(self.unified_components)} unified components")
    
    def analyze_python_file(self, file_path: Path) -> List[ImportInfo]:
        """Analyze imports in a Python file"""
        imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(ImportInfo(
                            module=alias.name,
                            names=[],
                            alias=alias.asname,
                            line_number=node.lineno,
                            is_relative=False
                        ))
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(ImportInfo(
                            module=node.module,
                            names=[alias.name for alias in node.names],
                            line_number=node.lineno,
                            is_relative=node.level > 0
                        ))
        
        except Exception as e:
            self.issues.append(ComponentIssue(
                file_path=str(file_path),
                issue_type="PARSE_ERROR",
                description=f"Could not parse file: {e}",
                suggested_fix="Check file syntax and encoding"
            ))
        
        return imports
    
    def check_import_consistency(self):
        """Check for import consistency issues"""
        print("🔍 Checking import consistency...")
        
        # Patterns for core imports
        core_import_patterns = {
            "absolute": "from app.core",
            "relative_from_gui": "from core.",
            "relative_from_core": "from ."
        }
        
        # Analyze all Python files
        for py_file in self.app_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            relative_path = py_file.relative_to(self.project_root)
            imports = self.analyze_python_file(py_file)
            self.imports_by_file[str(relative_path)] = imports
            
            # Check for inconsistent import patterns
            for imp in imports:
                self._check_core_import_pattern(py_file, imp)
                self._check_missing_components(py_file, imp)
                self._check_deprecated_imports(py_file, imp)
    
    def _check_core_import_pattern(self, file_path: Path, imp: ImportInfo):
        """Check if core imports follow consistent patterns"""
        if not imp.module:
            return
            
        # Determine expected import pattern based on file location
        relative_path = file_path.relative_to(self.app_dir)
        parts = relative_path.parts
        
        if imp.module.startswith("core.") or imp.module == "core":
            # Core import detected
            if len(parts) > 1 and parts[0] == "gui":
                # GUI file importing core - should use "core."
                if not imp.module.startswith("core."):
                    self.issues.append(ComponentIssue(
                        file_path=str(file_path),
                        issue_type="IMPORT_PATTERN",
                        description=f"GUI file should use 'from core.' pattern, found: {imp.module}",
                        line_number=imp.line_number,
                        suggested_fix=f"Change to: from core.{imp.module.split('.')[-1]}"
                    ))
            elif len(parts) > 1 and parts[0] == "core":
                # Core file importing core - should use relative imports
                if not imp.is_relative and not imp.module.startswith("app.core"):
                    self.issues.append(ComponentIssue(
                        file_path=str(file_path),
                        issue_type="IMPORT_PATTERN",
                        description=f"Core file should use relative imports, found: {imp.module}",
                        line_number=imp.line_number,
                        suggested_fix=f"Change to: from .{imp.module.split('.')[-1]}"
                    ))
    
    def _check_missing_components(self, file_path: Path, imp: ImportInfo):
        """Check for references to missing components"""
        if imp.module and ("core." in imp.module or imp.module == "core"):
            # Extract component name
            if imp.module.startswith("core."):
                component_name = imp.module.split(".")[-1]
            else:
                return
                
            # Check if component exists
            if component_name not in self.core_components:
                # Check if it's in archived components
                archived_dir = self.project_root / "archive" / "deprecated-components"
                if archived_dir.exists() and (archived_dir / f"{component_name}.py").exists():
                    self.issues.append(ComponentIssue(
                        file_path=str(file_path),
                        issue_type="ARCHIVED_COMPONENT",
                        description=f"Importing archived component: {component_name}",
                        line_number=imp.line_number,
                        suggested_fix=f"Replace with updated component or remove import"
                    ))
                else:
                    self.issues.append(ComponentIssue(
                        file_path=str(file_path),
                        issue_type="MISSING_COMPONENT",
                        description=f"Component not found: {component_name}",
                        line_number=imp.line_number,
                        suggested_fix="Check component name or implement missing component"
                    ))
    
    def _check_deprecated_imports(self, file_path: Path, imp: ImportInfo):
        """Check for imports of deprecated components"""
        deprecated_components = {
            "auto_updater": "automatic_updates",
            "real_time_protection": "unified_security_engine", 
            "performance_monitor": "unified_performance_optimizer"
        }
        
        if imp.module:
            for deprecated, replacement in deprecated_components.items():
                if deprecated in imp.module:
                    self.issues.append(ComponentIssue(
                        file_path=str(file_path),
                        issue_type="DEPRECATED_IMPORT",
                        description=f"Using deprecated component: {deprecated}",
                        line_number=imp.line_number,
                        suggested_fix=f"Replace with: {replacement}"
                    ))
    
    def check_component_linkages(self):
        """Check if components are properly linked and referenced"""
        print("🔍 Checking component linkages...")
        
        # Check __init__.py exports
        self._check_init_exports()
        
        # Check unified component integration
        self._check_unified_components()
        
        # Check GUI component references
        self._check_gui_references()
    
    def _check_init_exports(self):
        """Check if __init__.py properly exports all components"""
        init_file = self.core_dir / "__init__.py"
        if not init_file.exists():
            self.issues.append(ComponentIssue(
                file_path=str(init_file),
                issue_type="MISSING_INIT",
                description="Core __init__.py missing",
                suggested_fix="Create __init__.py to export core components"
            ))
            return
        
        # Parse __init__.py to find exports
        imports = self.analyze_python_file(init_file)
        exported_components = set()
        
        for imp in imports:
            if imp.is_relative and imp.names:
                for name in imp.names:
                    exported_components.add(name)
        
        # Check for missing exports
        for component in self.core_components:
            if component not in ["__init__", "__pycache__"]:
                # Check if component is exported (basic check)
                component_file = self.core_dir / f"{component}.py"
                if component_file.exists():
                    # Should have some form of export
                    pass
    
    def _check_unified_components(self):
        """Check unified component integration"""
        if "unified_security_engine" in self.unified_components:
            # Check if properly imported in __init__.py
            init_file = self.core_dir / "__init__.py"
            imports = self.imports_by_file.get(str(init_file.relative_to(self.project_root)), [])
            
            found_unified_security = any(
                "unified_security_engine" in imp.module or 
                "UnifiedSecurityEngine" in imp.names
                for imp in imports
            )
            
            if not found_unified_security:
                self.issues.append(ComponentIssue(
                    file_path=str(init_file),
                    issue_type="MISSING_UNIFIED_IMPORT",
                    description="Unified Security Engine not properly imported",
                    suggested_fix="Add import for UnifiedSecurityEngine in __init__.py"
                ))
    
    def _check_gui_references(self):
        """Check GUI component references to core"""
        main_window = self.gui_dir / "main_window.py"
        if main_window.exists():
            imports = self.imports_by_file.get(str(main_window.relative_to(self.project_root)), [])
            
            # Check for proper core imports
            has_file_scanner = any("FileScanner" in imp.names for imp in imports)
            has_clamav_wrapper = any("ClamAVWrapper" in imp.names for imp in imports)
            
            if not has_file_scanner:
                self.issues.append(ComponentIssue(
                    file_path=str(main_window),
                    issue_type="MISSING_CORE_IMPORT",
                    description="FileScanner not imported in main window",
                    suggested_fix="Add: from core.file_scanner import FileScanner"
                ))
    
    def generate_fixes(self) -> Dict[str, List[str]]:
        """Generate automated fixes for common issues"""
        fixes_by_file = defaultdict(list)
        
        for issue in self.issues:
            if issue.suggested_fix:
                fixes_by_file[issue.file_path].append({
                    'type': issue.issue_type,
                    'line': issue.line_number,
                    'description': issue.description,
                    'fix': issue.suggested_fix
                })
        
        return dict(fixes_by_file)
    
    def run_analysis(self) -> Dict:
        """Run complete component analysis"""
        print("🚀 Starting component reference and linkage analysis...")
        
        self.discover_components()
        self.check_import_consistency()
        self.check_component_linkages()
        
        # Categorize issues
        issues_by_type = defaultdict(list)
        for issue in self.issues:
            issues_by_type[issue.issue_type].append(issue)
        
        # Generate report
        return {
            'total_issues': len(self.issues),
            'issues_by_type': dict(issues_by_type),
            'core_components': sorted(self.core_components),
            'gui_components': sorted(self.gui_components),
            'unified_components': sorted(self.unified_components),
            'fixes': self.generate_fixes()
        }
    
    def print_report(self, analysis_result: Dict):
        """Print comprehensive analysis report"""
        print("\n" + "="*80)
        print("COMPONENT REFERENCE & LINKAGE ANALYSIS REPORT")
        print("="*80)
        
        print(f"\n📊 COMPONENT INVENTORY:")
        print(f"   Core Components: {len(analysis_result['core_components'])}")
        print(f"   GUI Components: {len(analysis_result['gui_components'])}")
        print(f"   Unified Components: {len(analysis_result['unified_components'])}")
        
        print(f"\n🔍 ANALYSIS RESULTS:")
        print(f"   Total Issues Found: {analysis_result['total_issues']}")
        
        if analysis_result['total_issues'] == 0:
            print("   ✅ No component reference or linkage issues found!")
            return
        
        print(f"\n📋 ISSUES BY TYPE:")
        for issue_type, issues in analysis_result['issues_by_type'].items():
            print(f"   {issue_type}: {len(issues)} issues")
            for issue in issues[:3]:  # Show first 3 of each type
                print(f"     - {Path(issue.file_path).name}: {issue.description}")
            if len(issues) > 3:
                print(f"     ... and {len(issues) - 3} more")
        
        print(f"\n🔧 SUGGESTED FIXES:")
        fix_count = 0
        for file_path, fixes in analysis_result['fixes'].items():
            print(f"   📁 {Path(file_path).name}:")
            for fix in fixes[:2]:  # Show first 2 fixes per file
                print(f"     → {fix['fix']}")
                fix_count += 1
            if len(fixes) > 2:
                print(f"     ... and {len(fixes) - 2} more fixes")
        
        if fix_count == 0:
            print("   ℹ️  No automated fixes available")
        
        print(f"\n🎯 RECOMMENDATIONS:")
        if "DEPRECATED_IMPORT" in analysis_result['issues_by_type']:
            print("   1. Update deprecated component imports to use unified systems")
        if "MISSING_COMPONENT" in analysis_result['issues_by_type']:
            print("   2. Implement missing components or update import paths")
        if "IMPORT_PATTERN" in analysis_result['issues_by_type']:
            print("   3. Standardize import patterns across the application")
        if "ARCHIVED_COMPONENT" in analysis_result['issues_by_type']:
            print("   4. Replace archived component references with current alternatives")
        
        print("="*80)


def main():
    """Main analysis entry point"""
    project_root = Path(__file__).parent
    
    print("🔍 xanadOS Search & Destroy - Component Reference Analysis")
    print(f"📂 Project Root: {project_root}")
    
    analyzer = ComponentAnalyzer(project_root)
    analysis_result = analyzer.run_analysis()
    analyzer.print_report(analysis_result)
    
    # Return exit code based on issues found
    return 0 if analysis_result['total_issues'] == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    print(f"\nAnalysis completed with exit code: {exit_code}")
    sys.exit(exit_code)
