#!/usr/bin/env python3
"""
Component Standardization Implementation Tool
Implements standardization patterns across xanadOS components.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class StandardizationPattern:
    """Definition of a standardization pattern."""
    name: str
    description: str
    before_pattern: str
    after_pattern: str
    file_pattern: str
    priority: int


@dataclass
class ImplementationResult:
    """Result of implementing a standardization."""
    pattern_name: str
    file_path: str
    changes_made: int
    success: bool
    error_message: str = ""


class StandardizationImplementer:
    """Implements standardization patterns across components."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.app_dir = self.project_root / "app"
        self.logger = logging.getLogger(__name__)

        # Define standardization patterns
        self.patterns = [
            StandardizationPattern(
                name="modern_typing",
                description="Replace deprecated typing imports with modern syntax",
                before_pattern=r"from typing import\s+([^,\n]+(?:,\s*[^,\n]+)*)",
                after_pattern=self._modernize_typing_imports,
                file_pattern="**/*.py",
                priority=1
            ),
            StandardizationPattern(
                name="error_handling",
                description="Standardize exception handling patterns",
                before_pattern=r"except\s+Exception\s*:\s*\n\s*pass",
                after_pattern="except Exception as e:\n    logger.error(f\"Error occurred: {e}\")\n    raise",
                file_pattern="**/*.py",
                priority=2
            ),
            StandardizationPattern(
                name="logging_format",
                description="Standardize logging import and usage",
                before_pattern=r"import logging\n(?!.*logger = logging\.getLogger)",
                after_pattern="import logging\n\nlogger = logging.getLogger(__name__)",
                file_pattern="**/*.py",
                priority=3
            ),
            StandardizationPattern(
                name="file_operations",
                description="Standardize file operations with context managers",
                before_pattern=r"open\(([^)]+)\)\s*\n([^w])",
                after_pattern=r"with open(\1) as f:\n\2",
                file_pattern="**/*.py",
                priority=4
            ),
            StandardizationPattern(
                name="async_file_operations",
                description="Replace blocking file ops in async functions with aiofiles",
                before_pattern=r"(async\s+def\s+\w+.*?:\s*(?:[^}])*?)open\(([^)]+)\)",
                after_pattern=r"\1aiofiles.open(\2)",
                file_pattern="**/*.py",
                priority=5
            )
        ]

    def _modernize_typing_imports(self, match) -> str:
        """Convert old typing imports to modern syntax."""
        imports_str = match.group(1)

        # Map old imports to modern equivalents
        type_mapping = {
            'Dict': 'dict',
            'List': 'list',
            'Set': 'set',
            'Tuple': 'tuple',
            'Optional': 'Optional',  # Keep Optional for now
            'Union': 'Union',       # Keep Union for now
            'Any': 'Any',
            'Callable': 'Callable'
        }

        imports = [imp.strip() for imp in imports_str.split(',')]
        modern_imports = []

        for imp in imports:
            if imp in type_mapping:
                if type_mapping[imp] in ['dict', 'list', 'set', 'tuple']:
                    # These don't need importing anymore
                    continue
                else:
                    modern_imports.append(type_mapping[imp])
            else:
                modern_imports.append(imp)

        if modern_imports:
            return f"from typing import {', '.join(modern_imports)}"
        else:
            return ""

    def implement_all_patterns(self) -> dict[str, Any]:
        """Implement all standardization patterns."""
        results = []
        summary = {
            'total_files_processed': 0,
            'total_changes_made': 0,
            'patterns_applied': {},
            'errors': []
        }

        # Get all Python files
        python_files = list(self.app_dir.rglob("*.py"))
        summary['total_files_processed'] = len(python_files)

        # Apply each pattern
        for pattern in sorted(self.patterns, key=lambda p: p.priority):
            self.logger.info(f"Applying pattern: {pattern.name}")
            pattern_results = self._apply_pattern(pattern, python_files)
            results.extend(pattern_results)

            # Update summary
            pattern_changes = sum(r.changes_made for r in pattern_results if r.success)
            summary['patterns_applied'][pattern.name] = {
                'files_affected': len([r for r in pattern_results if r.success and r.changes_made > 0]),
                'total_changes': pattern_changes,
                'errors': len([r for r in pattern_results if not r.success])
            }
            summary['total_changes_made'] += pattern_changes

            # Collect errors
            for result in pattern_results:
                if not result.success:
                    summary['errors'].append({
                        'pattern': pattern.name,
                        'file': result.file_path,
                        'error': result.error_message
                    })

        return {
            'results': results,
            'summary': summary
        }

    def _apply_pattern(self, pattern: StandardizationPattern, files: list[Path]) -> list[ImplementationResult]:
        """Apply a standardization pattern to files."""
        results = []

        for file_path in files:
            try:
                result = self._apply_pattern_to_file(pattern, file_path)
                results.append(result)
            except Exception as e:
                results.append(ImplementationResult(
                    pattern_name=pattern.name,
                    file_path=str(file_path),
                    changes_made=0,
                    success=False,
                    error_message=str(e)
                ))

        return results

    def _apply_pattern_to_file(self, pattern: StandardizationPattern, file_path: Path) -> ImplementationResult:
        """Apply a standardization pattern to a single file."""
        try:
            # Read file content
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            original_content = content
            changes_made = 0

            # Apply pattern based on type
            if callable(pattern.after_pattern):
                # Custom function for complex replacements
                new_content, changes = self._apply_function_pattern(pattern, content)
                content = new_content
                changes_made += changes
            else:
                # Simple regex replacement
                matches = list(re.finditer(pattern.before_pattern, content, re.MULTILINE | re.DOTALL))
                if matches:
                    content = re.sub(pattern.before_pattern, pattern.after_pattern, content, flags=re.MULTILINE | re.DOTALL)
                    changes_made = len(matches)

            # Write back if changes were made
            if content != original_content and changes_made > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            return ImplementationResult(
                pattern_name=pattern.name,
                file_path=str(file_path.relative_to(self.project_root)),
                changes_made=changes_made,
                success=True
            )

        except Exception as e:
            return ImplementationResult(
                pattern_name=pattern.name,
                file_path=str(file_path.relative_to(self.project_root)),
                changes_made=0,
                success=False,
                error_message=str(e)
            )

    def _apply_function_pattern(self, pattern: StandardizationPattern, content: str) -> tuple[str, int]:
        """Apply a pattern that uses a function for replacement."""
        changes = 0

        if pattern.name == "modern_typing":
            # Handle typing imports modernization
            matches = list(re.finditer(pattern.before_pattern, content))
            for match in reversed(matches):  # Process in reverse to maintain positions
                replacement = pattern.after_pattern(match)
                if replacement != match.group(0):
                    start, end = match.span()
                    content = content[:start] + replacement + content[end:]
                    changes += 1

        return content, changes

    def generate_implementation_report(self, results: dict[str, Any]) -> str:
        """Generate a detailed implementation report."""
        summary = results['summary']

        report = []
        report.append("=" * 80)
        report.append("🔧 COMPONENT STANDARDIZATION IMPLEMENTATION REPORT")
        report.append("=" * 80)
        report.append("")

        # Summary statistics
        report.append(f"📁 Files Processed: {summary['total_files_processed']}")
        report.append(f"✨ Total Changes Made: {summary['total_changes_made']}")
        report.append(f"⚠️  Errors Encountered: {len(summary['errors'])}")
        report.append("")

        # Pattern-by-pattern results
        report.append("📋 PATTERN IMPLEMENTATION RESULTS:")
        report.append("")

        for pattern_name, stats in summary['patterns_applied'].items():
            report.append(f"🔨 {pattern_name.replace('_', ' ').title()}")
            report.append(f"   Files Affected: {stats['files_affected']}")
            report.append(f"   Changes Made: {stats['total_changes']}")
            report.append(f"   Errors: {stats['errors']}")
            report.append("")

        # Error details
        if summary['errors']:
            report.append("❌ ERRORS ENCOUNTERED:")
            report.append("")
            for error in summary['errors'][:10]:  # Show first 10 errors
                report.append(f"   Pattern: {error['pattern']}")
                report.append(f"   File: {error['file']}")
                report.append(f"   Error: {error['error']}")
                report.append("")

        # Most affected files
        file_changes = {}
        for result in results['results']:
            if result.success and result.changes_made > 0:
                if result.file_path not in file_changes:
                    file_changes[result.file_path] = 0
                file_changes[result.file_path] += result.changes_made

        if file_changes:
            report.append("📊 MOST AFFECTED FILES:")
            report.append("")
            sorted_files = sorted(file_changes.items(), key=lambda x: x[1], reverse=True)[:10]
            for file_path, changes in sorted_files:
                report.append(f"   {file_path}: {changes} changes")
            report.append("")

        # Success rate
        total_attempts = len(results['results'])
        successful = len([r for r in results['results'] if r.success])
        success_rate = (successful / total_attempts * 100) if total_attempts > 0 else 0

        report.append(f"✅ Success Rate: {success_rate:.1f}% ({successful}/{total_attempts})")

        return "\n".join(report)


def implement_standardization(project_root: str = "."):
    """Run standardization implementation."""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    implementer = StandardizationImplementer(project_root)

    print("🔧 Implementing standardization patterns...")
    results = implementer.implement_all_patterns()

    print("\n📋 Generating implementation report...")
    report = implementer.generate_implementation_report(results)

    print("\n" + report)

    return results


if __name__ == "__main__":
    import sys
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    implement_standardization(project_root)
