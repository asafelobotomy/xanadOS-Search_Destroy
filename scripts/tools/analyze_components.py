#!/usr/bin/env python3
"""
Component Standardization and Library Analysis Tool
Analyzes all xanadOS components for standardization opportunities and library improvements.
"""

import ast
import logging
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ComponentInfo:
    """Information about a component file."""
    path: str
    imports: set[str]
    functions: list[str]
    classes: list[str]
    dependencies: set[str]
    patterns: list[str]
    complexity_score: int
    library_candidates: list[str]


@dataclass
class LibraryRecommendation:
    """Library recommendation with benefits analysis."""
    name: str
    description: str
    current_implementation: str
    benefits: list[str]
    installation: str
    integration_effort: str
    performance_impact: str
    components_affected: list[str]


class ComponentStandardizer:
    """Tool for standardizing components and analyzing library benefits."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.app_dir = self.project_root / "app"
        self.logger = logging.getLogger(__name__)

        # Component analysis results
        self.components: dict[str, ComponentInfo] = {}
        self.common_patterns: dict[str, int] = defaultdict(int)
        self.library_usage: dict[str, set[str]] = defaultdict(set)
        self.standardization_opportunities: list[dict[str, Any]] = []
        self.library_recommendations: list[LibraryRecommendation] = []

        # Library analysis database
        self.security_libraries = {
            "cryptography": "Modern cryptographic library for Python",
            "pycryptodome": "Cryptographic library with AES, RSA, etc.",
            "hashlib": "Built-in secure hashing library",
            "secrets": "Secure random number generation",
            "bcrypt": "Password hashing library",
            "pynacl": "Networking and Cryptography library",
            "paramiko": "SSH2 protocol library",
            "scapy": "Packet manipulation library",
            "yara-python": "YARA malware identification library",
        }

        self.ml_libraries = {
            "scikit-learn": "Machine learning library with algorithms",
            "tensorflow": "Deep learning framework",
            "pytorch": "Dynamic neural network framework",
            "xgboost": "Gradient boosting framework",
            "lightgbm": "Gradient boosting framework",
            "numpy": "Numerical computing library",
            "pandas": "Data manipulation and analysis",
            "matplotlib": "Plotting library",
            "seaborn": "Statistical data visualization",
        }

        self.async_libraries = {
            "asyncio": "Built-in asynchronous I/O framework",
            "aiofiles": "Asynchronous file operations",
            "aiohttp": "Asynchronous HTTP client/server",
            "uvloop": "Fast asyncio event loop",
            "trio": "Async/await native I/O library",
            "anyio": "Async compatibility layer",
        }

        self.performance_libraries = {
            "numba": "JIT compiler for numerical functions",
            "cython": "Python to C compiler",
            "pypy": "Fast Python implementation",
            "multiprocessing": "Process-based parallelism",
            "concurrent.futures": "High-level async execution",
            "joblib": "Parallel computing with NumPy",
            "ray": "Distributed computing framework",
        }

        self.monitoring_libraries = {
            "psutil": "System and process monitoring",
            "prometheus_client": "Prometheus monitoring",
            "structlog": "Structured logging",
            "sentry-sdk": "Error tracking and monitoring",
            "statsd": "StatsD client for metrics",
            "opencensus": "Application performance monitoring",
        }

    def analyze_all_components(self) -> dict[str, Any]:
        """Analyze all components for standardization opportunities."""
        self.logger.info("Starting comprehensive component analysis")

        # Find all Python files in app directory
        python_files = list(self.app_dir.rglob("*.py"))
        self.logger.info(f"Found {len(python_files)} Python files to analyze")

        # Analyze each component
        for file_path in python_files:
            try:
                component_info = self._analyze_component(file_path)
                if component_info:
                    self.components[str(file_path)] = component_info
            except Exception as e:
                self.logger.error(f"Failed to analyze {file_path}: {e}")

        # Identify patterns and opportunities
        self._identify_common_patterns()
        self._identify_standardization_opportunities()
        self._generate_library_recommendations()

        return self._generate_analysis_report()

    def _analyze_component(self, file_path: Path) -> ComponentInfo:
        """Analyze a single component file."""
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            # Parse AST
            tree = ast.parse(content)

            # Extract information
            imports = self._extract_imports(tree)
            functions = self._extract_functions(tree)
            classes = self._extract_classes(tree)
            dependencies = self._extract_dependencies(imports)
            patterns = self._identify_patterns(content)
            complexity = self._calculate_complexity(tree)

            return ComponentInfo(
                path=str(file_path.relative_to(self.project_root)),
                imports=imports,
                functions=functions,
                classes=classes,
                dependencies=dependencies,
                patterns=patterns,
                complexity_score=complexity,
                library_candidates=self._suggest_libraries(content, imports)
            )

        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}")
            return None

    def _extract_imports(self, tree: ast.AST) -> set[str]:
        """Extract all imports from AST."""
        imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
                    for alias in node.names:
                        imports.add(f"{node.module}.{alias.name}")

        return imports

    def _extract_functions(self, tree: ast.AST) -> list[str]:
        """Extract all function names from AST."""
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.AsyncFunctionDef):
                functions.append(f"async {node.name}")

        return functions

    def _extract_classes(self, tree: ast.AST) -> list[str]:
        """Extract all class names from AST."""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)

        return classes

    def _extract_dependencies(self, imports: set[str]) -> set[str]:
        """Extract external dependencies from imports."""
        dependencies = set()

        # Standard library modules (simplified list)
        stdlib_modules = {
            'asyncio', 'json', 'logging', 'os', 'sys', 'time', 'datetime',
            'pathlib', 'subprocess', 'threading', 'multiprocessing', 'collections',
            'functools', 'itertools', 'tempfile', 'shutil', 'hashlib', 'secrets',
            'socket', 're', 'uuid', 'base64', 'pickle', 'csv'
        }

        for imp in imports:
            root_module = imp.split('.')[0]
            if root_module not in stdlib_modules and not root_module.startswith('app'):
                dependencies.add(root_module)

        return dependencies

    def _identify_patterns(self, content: str) -> list[str]:
        """Identify common code patterns in content."""
        patterns = []

        # Common patterns to look for
        pattern_checks = {
            'async_await': r'async def|await\s+',
            'exception_handling': r'try:|except\s+',
            'logging': r'\.log|logging\.',
            'file_operations': r'open\(|with\s+open',
            'subprocess': r'subprocess\.|Popen',
            'threading': r'threading\.|Thread\(',
            'multiprocessing': r'multiprocessing\.|Process\(',
            'database': r'\.execute\(|cursor\.|connection\.',
            'http_requests': r'requests\.|urllib\.',
            'json_handling': r'json\.|\.loads\(|\.dumps\(',
            'regex': r're\.|regex|pattern',
            'crypto': r'hash|encrypt|decrypt|cipher',
            'ml_inference': r'predict\(|fit\(|transform\(',
            'gpu_operations': r'cuda|gpu|torch\.',
            'monitoring': r'psutil\.|memory\(\)|cpu\(',
        }

        for pattern_name, regex in pattern_checks.items():
            if re.search(regex, content, re.IGNORECASE):
                patterns.append(pattern_name)
                self.common_patterns[pattern_name] += 1

        return patterns

    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate complexity score for the component."""
        complexity = 0

        for node in ast.walk(tree):
            # Count complexity-contributing structures
            if isinstance(node, ast.If | ast.While | ast.For | ast.Try):
                complexity += 1
            elif isinstance(node, ast.FunctionDef):
                complexity += len(node.args.args)  # Parameter complexity
            elif isinstance(node, ast.ClassDef):
                complexity += 2  # Classes add complexity

        return complexity

    def _suggest_libraries(self, content: str, imports: set[str]) -> list[str]:
        """Suggest libraries that could benefit this component."""
        suggestions = []

        # Check for manual implementations that could use libraries
        if 'hash' in content.lower() and 'hashlib' not in imports:
            suggestions.append('hashlib')

        if any(pattern in content.lower() for pattern in ['encrypt', 'decrypt', 'cipher']) and 'cryptography' not in imports:
            suggestions.append('cryptography')

        if 'async' in content and 'aiofiles' not in imports and 'open(' in content:
            suggestions.append('aiofiles')

        if any(pattern in content for pattern in [r'\.fit\(', r'\.predict\(', 'machine learning']) and 'sklearn' not in imports:
            suggestions.append('scikit-learn')

        if 'gpu' in content.lower() and 'torch' not in imports and 'tensorflow' not in imports:
            suggestions.append('pytorch')

        if 'multiprocessing' in content and 'joblib' not in imports:
            suggestions.append('joblib')

        return suggestions

    def _identify_common_patterns(self):
        """Identify patterns that appear across multiple components."""
        # Find patterns that appear in many components
        total_components = len(self.components)
        common_threshold = max(3, total_components * 0.3)  # At least 30% of components

        for pattern, count in self.common_patterns.items():
            if count >= common_threshold:
                self.logger.info(f"Common pattern '{pattern}' found in {count} components")

    def _identify_standardization_opportunities(self):
        """Identify opportunities for standardization."""

        # Group components by similar patterns
        pattern_groups = defaultdict(list)
        for path, component in self.components.items():
            pattern_key = tuple(sorted(component.patterns))
            pattern_groups[pattern_key].append(path)

        # Find groups with multiple components (standardization opportunities)
        for patterns, components in pattern_groups.items():
            if len(components) > 1:
                self.standardization_opportunities.append({
                    'patterns': list(patterns),
                    'components': components,
                    'opportunity': f"Standardize {', '.join(patterns)} across {len(components)} components",
                    'priority': len(components)  # More components = higher priority
                })

        # Sort by priority
        self.standardization_opportunities.sort(key=lambda x: x['priority'], reverse=True)

    def _generate_library_recommendations(self):
        """Generate library recommendations based on analysis."""

        # Analyze current manual implementations
        manual_crypto = []
        manual_ml = []
        manual_async = []
        manual_monitoring = []

        for path, component in self.components.items():
            if 'crypto' in component.patterns and not any(lib in component.dependencies for lib in ['cryptography', 'pycryptodome']):
                manual_crypto.append(path)

            if 'ml_inference' in component.patterns and not any(lib in component.dependencies for lib in ['sklearn', 'tensorflow', 'torch']):
                manual_ml.append(path)

            if 'async_await' in component.patterns and not any(lib in component.dependencies for lib in ['aiofiles', 'aiohttp']):
                manual_async.append(path)

            if 'monitoring' in component.patterns and 'psutil' not in component.dependencies:
                manual_monitoring.append(path)

        # Generate recommendations
        if manual_crypto:
            self.library_recommendations.append(LibraryRecommendation(
                name="cryptography",
                description="Replace manual crypto implementations with secure, tested library",
                current_implementation="Manual cryptographic operations",
                benefits=[
                    "Secure, peer-reviewed implementations",
                    "Performance optimizations",
                    "Standard compliance",
                    "Regular security updates"
                ],
                installation="pip install cryptography",
                integration_effort="Medium - Replace manual crypto code",
                performance_impact="Positive - Optimized C implementations",
                components_affected=manual_crypto
            ))

        if manual_ml:
            self.library_recommendations.append(LibraryRecommendation(
                name="scikit-learn",
                description="Standardize ML operations with proven algorithms",
                current_implementation="Manual ML implementations",
                benefits=[
                    "Proven algorithms",
                    "Consistent API",
                    "Built-in validation",
                    "Extensive documentation"
                ],
                installation="pip install scikit-learn",
                integration_effort="Low - Replace manual ML code",
                performance_impact="Positive - Optimized implementations",
                components_affected=manual_ml
            ))

        if manual_async:
            self.library_recommendations.append(LibraryRecommendation(
                name="aiofiles",
                description="Improve async file operations",
                current_implementation="Blocking file operations in async code",
                benefits=[
                    "True async file I/O",
                    "Better concurrency",
                    "Prevent event loop blocking",
                    "Improved performance"
                ],
                installation="pip install aiofiles",
                integration_effort="Low - Replace file operations",
                performance_impact="Positive - Non-blocking I/O",
                components_affected=manual_async
            ))

    def _generate_analysis_report(self) -> dict[str, Any]:
        """Generate comprehensive analysis report."""

        # Calculate statistics
        total_components = len(self.components)
        total_functions = sum(len(comp.functions) for comp in self.components.values())
        total_classes = sum(len(comp.classes) for comp in self.components.values())
        avg_complexity = sum(comp.complexity_score for comp in self.components.values()) / total_components if total_components > 0 else 0

        # Most common dependencies
        all_deps = []
        for comp in self.components.values():
            all_deps.extend(comp.dependencies)

        dep_counts = defaultdict(int)
        for dep in all_deps:
            dep_counts[dep] += 1

        common_deps = sorted(dep_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "summary": {
                "total_components": total_components,
                "total_functions": total_functions,
                "total_classes": total_classes,
                "average_complexity": avg_complexity,
                "common_patterns": dict(self.common_patterns),
                "common_dependencies": common_deps
            },
            "standardization_opportunities": self.standardization_opportunities,
            "library_recommendations": [
                {
                    "name": rec.name,
                    "description": rec.description,
                    "benefits": rec.benefits,
                    "installation": rec.installation,
                    "integration_effort": rec.integration_effort,
                    "performance_impact": rec.performance_impact,
                    "components_affected": len(rec.components_affected),
                    "affected_files": rec.components_affected[:5]  # Show first 5
                }
                for rec in self.library_recommendations
            ],
            "component_details": {
                path: {
                    "functions": len(comp.functions),
                    "classes": len(comp.classes),
                    "dependencies": list(comp.dependencies),
                    "patterns": comp.patterns,
                    "complexity": comp.complexity_score,
                    "library_suggestions": comp.library_candidates
                }
                for path, comp in list(self.components.items())[:20]  # Limit output
            }
        }

    def generate_standardization_plan(self) -> dict[str, Any]:
        """Generate a detailed standardization plan."""

        plan = {
            "phase_1_critical": {
                "description": "Critical standardizations with high impact",
                "tasks": []
            },
            "phase_2_improvements": {
                "description": "Performance and maintainability improvements",
                "tasks": []
            },
            "phase_3_enhancements": {
                "description": "Advanced optimizations and features",
                "tasks": []
            }
        }

        # Categorize opportunities by priority
        for opp in self.standardization_opportunities:
            task = {
                "title": opp['opportunity'],
                "components": len(opp['components']),
                "patterns": opp['patterns'],
                "effort": "Medium" if len(opp['components']) > 5 else "Low"
            }

            if len(opp['components']) > 10:
                plan["phase_1_critical"]["tasks"].append(task)
            elif len(opp['components']) > 5:
                plan["phase_2_improvements"]["tasks"].append(task)
            else:
                plan["phase_3_enhancements"]["tasks"].append(task)

        # Add library recommendations
        for rec in self.library_recommendations:
            task = {
                "title": f"Implement {rec.name}",
                "description": rec.description,
                "components": len(rec.components_affected),
                "effort": rec.integration_effort,
                "impact": rec.performance_impact
            }

            if rec.integration_effort == "Low":
                plan["phase_2_improvements"]["tasks"].append(task)
            else:
                plan["phase_3_enhancements"]["tasks"].append(task)

        return plan


def run_component_analysis(project_root: str = "."):
    """Run complete component analysis and generate reports."""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    standardizer = ComponentStandardizer(project_root)

    print("🔍 Analyzing all components...")
    analysis_report = standardizer.analyze_all_components()

    print("\n📋 Generating standardization plan...")
    standardization_plan = standardizer.generate_standardization_plan()

    # Print summary report
    print("\n" + "="*80)
    print("📊 COMPONENT STANDARDIZATION & LIBRARY ANALYSIS REPORT")
    print("="*80)

    summary = analysis_report["summary"]
    print(f"📁 Total Components: {summary['total_components']}")
    print(f"⚙️  Total Functions: {summary['total_functions']}")
    print(f"🏗️  Total Classes: {summary['total_classes']}")
    print(f"📈 Average Complexity: {summary['average_complexity']:.1f}")

    print("\n🔧 Most Common Patterns:")
    for pattern, count in sorted(summary['common_patterns'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  • {pattern}: {count} components")

    print("\n📦 Most Common Dependencies:")
    for dep, count in summary['common_dependencies'][:10]:
        print(f"  • {dep}: {count} components")

    print("\n🎯 Standardization Opportunities:")
    opportunities = analysis_report["standardization_opportunities"]
    for i, opp in enumerate(opportunities[:5], 1):
        print(f"  {i}. {opp['opportunity']} (Priority: {opp['priority']})")

    print("\n📚 Library Recommendations:")
    for rec in analysis_report["library_recommendations"]:
        print(f"\n  📖 {rec['name']}")
        print(f"     {rec['description']}")
        print(f"     Benefits: {', '.join(rec['benefits'][:2])}...")
        print(f"     Affects {rec['components_affected']} components")
        print(f"     Integration: {rec['integration_effort']}")
        print(f"     Performance: {rec['performance_impact']}")

    print("\n📅 STANDARDIZATION PLAN:")
    for phase_name, phase in standardization_plan.items():
        print(f"\n🚀 {phase_name.upper().replace('_', ' ')}")
        print(f"   {phase['description']}")
        for task in phase['tasks'][:3]:  # Show first 3 tasks
            print(f"   • {task['title']}")
            if 'effort' in task:
                print(f"     Effort: {task['effort']}, Components: {task.get('components', 'N/A')}")

    print(f"\n💡 Analysis complete! Found {len(opportunities)} standardization opportunities")
    print(f"📚 {len(analysis_report['library_recommendations'])} library recommendations generated")

    return analysis_report, standardization_plan


if __name__ == "__main__":
    import sys

    # Determine project root dynamically
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        # Default to script's parent directory structure (scripts/tools/analyze_components.py)
        script_path = Path(__file__).resolve()
        project_root = str(script_path.parent.parent.parent)

    run_component_analysis(project_root)
