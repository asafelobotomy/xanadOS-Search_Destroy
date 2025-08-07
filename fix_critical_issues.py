#!/usr/bin/env python3
"""
Fix critical syntax errors and remaining issues after cleanup.
"""

import os
import re
from pathlib import Path


def fix_indentation_errors():
    """Fix critical indentation and syntax errors."""
    
    # Fix app/core/__init__.py indentation
    init_file = Path("app/core/__init__.py")
    if init_file.exists():
        content = init_file.read_text()
        # Fix unexpected indent at line 8
        lines = content.split('\n')
        if len(lines) > 7:
            # Remove extra indentation
            lines[7] = lines[7].lstrip()
        init_file.write_text('\n'.join(lines))
        print(f"✅ Fixed {init_file}")
    
    # Fix app/core/advanced_reporting.py
    reporting_file = Path("app/core/advanced_reporting.py")
    if reporting_file.exists():
        content = reporting_file.read_text()
        lines = content.split('\n')
        # Find the try statement around line 1655 and add proper indentation
        for i, line in enumerate(lines):
            if i > 1650 and i < 1660 and line.strip().startswith('try:'):
                # Ensure the next line is properly indented
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if not next_line.strip():
                        lines[i + 1] = "        pass  # Placeholder"
                    elif not next_line.startswith('    '):
                        lines[i + 1] = "        " + next_line.lstrip()
                break
        reporting_file.write_text('\n'.join(lines))
        print(f"✅ Fixed {reporting_file}")
    
    # Fix app/core/file_scanner.py
    scanner_file = Path("app/core/file_scanner.py")
    if scanner_file.exists():
        content = scanner_file.read_text()
        lines = content.split('\n')
        # Fix line 469 indentation
        if len(lines) > 468:
            lines[468] = lines[468].lstrip()
        scanner_file.write_text('\n'.join(lines))
        print(f"✅ Fixed {scanner_file}")
    
    # Fix app/gui/__init__.py
    gui_init = Path("app/gui/__init__.py")
    if gui_init.exists():
        content = gui_init.read_text()
        lines = content.split('\n')
        # Fix try statement indentation
        for i, line in enumerate(lines):
            if 'try:' in line and i + 1 < len(lines):
                next_line = lines[i + 1]
                if not next_line.strip():
                    lines[i + 1] = "    pass  # Placeholder"
                elif not next_line.startswith('    '):
                    lines[i + 1] = "    " + next_line.lstrip()
        gui_init.write_text('\n'.join(lines))
        print(f"✅ Fixed {gui_init}")
    
    # Fix app/gui/main_window.py
    main_window = Path("app/gui/main_window.py")
    if main_window.exists():
        content = main_window.read_text()
        lines = content.split('\n')
        # Fix unexpected indent
        if len(lines) > 14:
            lines[14] = lines[14].lstrip()
        main_window.write_text('\n'.join(lines))
        print(f"✅ Fixed {main_window}")
    
    # Fix app/gui/rkhunter_components.py
    rkhunter_comp = Path("app/gui/rkhunter_components.py")
    if rkhunter_comp.exists():
        content = rkhunter_comp.read_text()
        lines = content.split('\n')
        # Fix unexpected indent
        if len(lines) > 11:
            lines[11] = lines[11].lstrip()
        rkhunter_comp.write_text('\n'.join(lines))
        print(f"✅ Fixed {rkhunter_comp}")


def fix_syntax_errors():
    """Fix syntax errors like invalid escape sequences."""
    
    # Fix heuristic_analysis.py invalid escape
    heuristic_file = Path("app/core/heuristic_analysis.py")
    if heuristic_file.exists():
        content = heuristic_file.read_text()
        # Fix invalid \x escape - use raw string or escape properly
        content = content.replace(r'\\x', r'\\\\x')
        heuristic_file.write_text(content)
        print(f"✅ Fixed escape sequences in {heuristic_file}")


def remove_remaining_unused_imports():
    """Remove remaining unused imports more carefully."""
    
    files_to_fix = [
        "app/core/async_scanner.py",
        "app/core/automatic_updates.py", 
        "app/core/cloud_integration.py",
        "app/core/database_optimizer.py",
        "app/core/firewall_detector.py",
        "app/core/input_validation.py",
        "app/core/memory_optimizer.py",
        "app/core/multi_language_support.py",
        "app/core/network_security.py",
        "app/core/rkhunter_wrapper.py",
        "app/core/system_service.py",
        "app/core/ui_responsiveness.py",
        "app/core/web_protection.py",
        "app/monitoring/event_processor.py",
        "app/monitoring/file_watcher.py"
    ]
    
    unused_patterns = [
        r'^from typing import.*\b(Tuple|List|Union|Any|Dict|Set|Callable)\b.*$',
        r'^import os$',
        r'^from concurrent\.futures import as_completed$',
        r'^from dataclasses import asdict$',
        r'^from queue import Empty$',
        r'^from PyQt6\.QtCore import.*\b(QLocale|Q_ARG|QMetaObject|QThread)\b.*$',
        r'^from PyQt6\.QtWidgets import.*\bQLabel\b.*$',
        r'^from urllib\.parse import urljoin$'
    ]
    
    for file_path in files_to_fix:
        file_obj = Path(file_path)
        if file_obj.exists():
            content = file_obj.read_text()
            lines = content.split('\n')
            new_lines = []
            
            for line in lines:
                should_remove = False
                for pattern in unused_patterns:
                    if re.match(pattern, line.strip()):
                        should_remove = True
                        break
                
                if not should_remove:
                    new_lines.append(line)
                else:
                    print(f"    Removed: {line.strip()}")
            
            if len(new_lines) != len(lines):
                file_obj.write_text('\n'.join(new_lines))
                print(f"✅ Cleaned imports in {file_path}")


def fix_line_lengths():
    """Fix remaining line length issues by breaking long lines."""
    
    files_with_long_lines = [
        "app/core/automatic_updates.py",
        "app/core/clamav_wrapper.py", 
        "app/core/cloud_integration.py",
        "app/core/firewall_detector.py",
        "app/core/input_validation.py",
        "app/core/memory_optimizer.py",
        "app/core/multi_language_support.py",
        "app/core/rkhunter_wrapper.py",
        "app/core/system_service.py",
        "app/core/web_protection.py",
        "app/monitoring/real_time_monitor.py",
        "app/utils/config.py",
        "app/utils/scan_reports.py"
    ]
    
    for file_path in files_with_long_lines:
        file_obj = Path(file_path)
        if file_obj.exists():
            content = file_obj.read_text()
            lines = content.split('\n')
            new_lines = []
            
            for line in lines:
                if len(line) > 88:
                    # Simple line breaking for common patterns
                    if ' and ' in line and len(line) > 88:
                        line = line.replace(' and ', ' \\\n    and ')
                    elif ', ' in line and len(line) > 88:
                        # Break at commas
                        parts = line.split(', ')
                        if len(parts) > 2:
                            indent = len(line) - len(line.lstrip())
                            new_line = parts[0] + ','
                            for part in parts[1:-1]:
                                new_line += '\n' + ' ' * (indent + 4) + part + ','
                            new_line += '\n' + ' ' * (indent + 4) + parts[-1]
                            line = new_line
                
                new_lines.append(line)
            
            file_obj.write_text('\n'.join(new_lines))
            print(f"✅ Fixed line lengths in {file_path}")


def main():
    """Run all fixes."""
    print("🔧 Fixing critical syntax errors...")
    
    os.chdir("/home/vm/Documents/xanadOS-Search_Destroy")
    
    print("\n1. Fixing indentation errors...")
    fix_indentation_errors()
    
    print("\n2. Fixing syntax errors...")
    fix_syntax_errors()
    
    print("\n3. Removing remaining unused imports...")
    remove_remaining_unused_imports()
    
    print("\n4. Fixing line lengths...")
    fix_line_lengths()
    
    print("\n✅ Critical fixes completed!")


if __name__ == "__main__":
    main()
