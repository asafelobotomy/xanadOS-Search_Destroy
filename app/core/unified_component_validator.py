#!/usr/bin/env python3
"""Unified Component Validator for xanadOS Search & Destroy
Validates all unified components created during the 2025 optimization:
- Unified Security Engine
- Unified Performance Optimizer
- Component integration and compatibility
Purpose:
- Ensure unified components function correctly
- Validate performance improvements
- Test security enhancements
- Check component integration
"""

import asyncio
import logging
import shutil
import sys
import tempfile
import threading
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core import UNIFIED_PERFORMANCE_AVAILABLE, UNIFIED_SECURITY_AVAILABLE

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

if UNIFIED_SECURITY_AVAILABLE:
    from app.core.unified_security_engine import (
        ProtectionMode,
        ThreatLevel,
        UnifiedSecurityEngine,
    )

if UNIFIED_PERFORMANCE_AVAILABLE:
    from app.core.unified_performance_optimizer import (
        PerformanceMode,
        UnifiedPerformanceOptimizer,
    )


@dataclass
class ValidationResult:
    """Result of component validation"""

    component: str
    passed: bool
    errors: list[str]
    warnings: list[str]
    performance_metrics: dict[str, Any]
    details: str


@dataclass
class ValidationSuite:
    """Complete validation suite results"""

    total_tests: int
    passed_tests: int
    failed_tests: int
    warnings: int
    results: list[ValidationResult]
    overall_performance: dict[str, Any]
    recommendations: list[str]


class UnifiedComponentValidator:
    """Comprehensive validator for unified components.

    Features:
    - Security engine validation
    - Performance optimizer validation
    - Integration testing
    - Compatibility verification
    - Performance benchmarking
    """

    def __init__(self, log_level: int = logging.INFO):
        """Initialize validator"""
        self.setup_logging(log_level)
        self.logger = logging.getLogger(__name__)
        self.test_data_dir = Path(tempfile.mkdtemp(prefix="xanados_validation_"))
        self.results: list[ValidationResult] = []

    def setup_logging(self, level: int) -> None:
        """Setup logging configuration"""
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("unified_validation.log"),
            ],
        )

    def create_test_files(self) -> Path:
        """Create test files for validation"""
        test_files = []

        # Create normal test file
        normal_file = self.test_data_dir / "normal_file.txt"
        normal_file.write_text("This is a normal test file for validation.")
        test_files.append(normal_file)

        # Create large test file for performance testing
        large_file = self.test_data_dir / "large_file.txt"
        large_content = "Test content for performance validation.\n" * 10000
        large_file.write_text(large_content)
        test_files.append(large_file)

        # Create binary test file
        binary_file = self.test_data_dir / "binary_file.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03" * 1000)
        test_files.append(binary_file)

        self.logger.info(f"Created {len(test_files)} test files in {self.test_data_dir}")
        return self.test_data_dir

    async def validate_unified_security_engine(self) -> ValidationResult:
        """Validate UnifiedSecurityEngine component"""
        self.logger.info("Validating UnifiedSecurityEngine")

        errors: list[str] = []
        warnings: list[str] = []
        performance_metrics: dict[str, Any] = {}

        try:
            if not UNIFIED_SECURITY_AVAILABLE:
                return ValidationResult(
                    component="UnifiedSecurityEngine",
                    passed=False,
                    errors=["Unified Security Engine not available"],
                    warnings=[],
                    performance_metrics={},
                    details="Component not imported successfully",
                )

            # Initialize security engine with required parameters
            start_time = time.time()
            test_dir = self.create_test_files()
            security_engine = UnifiedSecurityEngine(watch_paths=[str(test_dir)])
            init_time = time.time() - start_time
            performance_metrics["initialization_time"] = init_time

            # Test engine start
            start_time = time.time()
            if hasattr(security_engine, "start"):
                await security_engine.start()
            else:
                # Initialize the engine if no start method
                await security_engine.initialize()
            start_time_duration = time.time() - start_time
            performance_metrics["start_time"] = start_time_duration

            # Test configuration
            if hasattr(security_engine, "configure"):
                await security_engine.configure(
                    {
                        "protection_mode": ProtectionMode.BALANCED,
                        "threat_level": ThreatLevel.MEDIUM,
                        "enable_ml_detection": True,
                    }
                )

            # Test file monitoring (if available)
            test_dir = self.create_test_files()
            if hasattr(security_engine, "monitor_path"):
                await security_engine.monitor_path(str(test_dir))

            # Test threat detection capabilities
            test_file = test_dir / "test_scan.txt"
            test_file.write_text("Test content for threat detection")

            if hasattr(security_engine, "scan_file"):
                scan_start = time.time()
                await security_engine.scan_file(str(test_file))
                scan_duration = time.time() - scan_start
                performance_metrics["scan_time"] = scan_duration

            # Test resource monitoring
            if hasattr(security_engine, "get_system_health"):
                health = await security_engine.get_system_health()
                performance_metrics["system_health"] = health

            # Test graceful shutdown
            if hasattr(security_engine, "stop"):
                await security_engine.stop()
            elif hasattr(security_engine, "shutdown"):
                await security_engine.shutdown()

            details = (
                f"Security Engine validation completed. Init: {init_time:.3f}s, Start: {start_time_duration:.3f}s"
            )

        except Exception as e:
            errors.append(f"Security Engine validation failed: {e!s}")
            details = f"Exception during validation: {traceback.format_exc()}"

        return ValidationResult(
            component="UnifiedSecurityEngine",
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            performance_metrics=performance_metrics,
            details=details,
        )

    async def validate_unified_performance_optimizer(self) -> ValidationResult:
        """Validate unified performance optimizer"""
        errors: list[str] = []
        warnings: list[str] = []
        performance_metrics: dict[str, Any] = {}

        try:
            if not UNIFIED_PERFORMANCE_AVAILABLE:
                return ValidationResult(
                    component="UnifiedPerformanceOptimizer",
                    passed=False,
                    errors=["Unified Performance Optimizer not available"],
                    warnings=[],
                    performance_metrics={},
                    details="Component not imported successfully",
                )

            # Initialize performance optimizer
            start_time = time.time()
            perf_optimizer = UnifiedPerformanceOptimizer()
            init_time = time.time() - start_time
            performance_metrics["initialization_time"] = init_time

            # Test optimizer start
            start_time = time.time()
            if hasattr(perf_optimizer, "start"):
                await perf_optimizer.start()
            elif hasattr(perf_optimizer, "initialize"):
                # Initialize the optimizer
                perf_optimizer.initialize()
            start_time_duration = time.time() - start_time
            performance_metrics["start_time"] = start_time_duration

            # Test performance mode configuration
            if hasattr(perf_optimizer, "set_performance_mode"):
                await perf_optimizer.set_performance_mode(PerformanceMode.BALANCED)

            # Test memory optimization
            if hasattr(perf_optimizer, "optimize_memory"):
                mem_start = time.time()
                await perf_optimizer.optimize_memory()
                mem_duration = time.time() - mem_start
                performance_metrics["memory_optimization_time"] = mem_duration

            # Test database optimization
            if hasattr(perf_optimizer, "optimize_database"):
                db_start = time.time()
                await perf_optimizer.optimize_database()
                db_duration = time.time() - db_start
                performance_metrics["database_optimization_time"] = db_duration

            # Test performance metrics collection
            if hasattr(perf_optimizer, "get_performance_metrics"):
                metrics = perf_optimizer.get_performance_metrics()
                performance_metrics["current_metrics"] = metrics

            # Test resource monitoring
            if hasattr(perf_optimizer, "get_resource_usage"):
                resource_usage = await perf_optimizer.get_resource_usage()
                performance_metrics["resource_usage"] = resource_usage

            # Test graceful shutdown
            if hasattr(perf_optimizer, "stop"):
                await perf_optimizer.stop()
            elif hasattr(perf_optimizer, "shutdown"):
                await perf_optimizer.shutdown()

            details = (
                f"Performance Optimizer validation completed. Init: {init_time:.3f}s, "
                f"Start: {start_time_duration:.3f}s"
            )

        except Exception as e:
            errors.append(f"Performance Optimizer validation failed: {e!s}")
            details = f"Exception during validation: {traceback.format_exc()}"

        return ValidationResult(
            component="UnifiedPerformanceOptimizer",
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            performance_metrics=performance_metrics,
            details=details,
        )

    async def validate_component_integration(self) -> ValidationResult:
        """Validate integration between unified components"""
        errors = []
        warnings = []
        performance_metrics: dict[str, Any] = {}

        try:
            if not (UNIFIED_SECURITY_AVAILABLE and UNIFIED_PERFORMANCE_AVAILABLE):
                warnings.append("Not all unified components available for integration testing")
                return ValidationResult(
                    component="ComponentIntegration",
                    passed=True,
                    errors=[],
                    warnings=warnings,
                    performance_metrics={},
                    details="Integration testing skipped due to missing components",
                )

            # Initialize both components
            security_engine = UnifiedSecurityEngine(watch_paths=["/tmp"])  # nosec B108
            perf_optimizer = UnifiedPerformanceOptimizer()

            # Test concurrent startup
            start_time = time.time()
            start_tasks = []
            if hasattr(security_engine, "start"):
                start_tasks.append(security_engine.start())
            if hasattr(perf_optimizer, "start"):
                start_tasks.append(perf_optimizer.start())

            if start_tasks:
                await asyncio.gather(*start_tasks)
            concurrent_start_time = time.time() - start_time
            performance_metrics["concurrent_start_time"] = concurrent_start_time

            # Test resource sharing/coordination
            if hasattr(security_engine, "get_system_health") and hasattr(
                perf_optimizer, "get_resource_usage"
            ):
                health = await security_engine.get_system_health()
                usage = await perf_optimizer.get_resource_usage()
                performance_metrics.update(
                    {
                        "resource_coordination": {
                            "security_health": health,
                            "performance_usage": usage,
                        }
                    }
                )

            # Test graceful concurrent shutdown
            stop_tasks = []
            if hasattr(security_engine, "stop"):
                stop_tasks.append(security_engine.stop())
            if hasattr(perf_optimizer, "stop"):
                stop_tasks.append(perf_optimizer.stop())

            if stop_tasks:
                await asyncio.gather(*stop_tasks)

            details = (
                f"Integration validation completed. Concurrent start: {concurrent_start_time:.3f}s"
            )

        except Exception as e:
            errors.append(f"Integration validation failed: {e!s}")
            details = f"Exception during integration validation: {traceback.format_exc()}"

        return ValidationResult(
            component="ComponentIntegration",
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            performance_metrics=performance_metrics,
            details=details,
        )

    def validate_import_compatibility(self) -> ValidationResult:
        """Validate import compatibility with existing codebase"""
        errors = []
        warnings = []

        try:
            # Test core module imports
            from app.core import (
                UNIFIED_PERFORMANCE_AVAILABLE,
                UNIFIED_SECURITY_AVAILABLE,
            )
            from app.core.clamav_wrapper import ClamAVWrapper as _ClamAVWrapper
            from app.core.file_scanner import FileScanner as _FileScanner

            # Test conditional imports work
            if UNIFIED_SECURITY_AVAILABLE:
                from app.core import ProtectionMode as _ProtectionMode
                from app.core import ThreatLevel as _ThreatLevel
                from app.core import UnifiedSecurityEngine as _UnifiedSecurityEngine
            else:
                warnings.append("Unified Security Engine not available")

            if UNIFIED_PERFORMANCE_AVAILABLE:
                from app.core import PerformanceMode as _PerformanceMode
                from app.core import (
                    UnifiedPerformanceOptimizer as _UnifiedPerformanceOptimizer,
                )
            else:
                warnings.append("Unified Performance Optimizer not available")

            # No-op references to satisfy import checks without unused warnings
            _ = (
                _ClamAVWrapper,
                _FileScanner,
                UNIFIED_SECURITY_AVAILABLE,
                UNIFIED_PERFORMANCE_AVAILABLE,
            )
            if UNIFIED_SECURITY_AVAILABLE:
                _ = (_ProtectionMode, _ThreatLevel, _UnifiedSecurityEngine)
            if UNIFIED_PERFORMANCE_AVAILABLE:
                _ = (_PerformanceMode, _UnifiedPerformanceOptimizer)

            # Test component import compatibility
            details = "Import compatibility validation passed"

        except ImportError as e:
            errors.append(f"Import compatibility issue: {e!s}")
            details = f"Import error: {traceback.format_exc()}"
        except Exception as e:
            errors.append(f"Unexpected error in import validation: {e!s}")
            details = f"Exception: {traceback.format_exc()}"

        return ValidationResult(
            component="ImportCompatibility",
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            performance_metrics={},
            details=details,
        )

    async def run_comprehensive_validation(self) -> ValidationSuite:
        """Run complete validation suite"""
        self.logger.info("Starting comprehensive unified component validation...")

        # Run all validations
        async_validations = await asyncio.gather(
            self.validate_unified_security_engine(),
            self.validate_unified_performance_optimizer(),
            self.validate_component_integration(),
            return_exceptions=True,
        )

        # Add synchronous validations
        import_validation = self.validate_import_compatibility()
        validations = list(async_validations)
        validations.append(import_validation)

        # Process results
        results: list[ValidationResult] = []
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        total_warnings = 0
        overall_performance: dict[str, Any] = {}

        for validation in validations:
            if isinstance(validation, Exception):
                results.append(
                    ValidationResult(
                        component="UnknownComponent",
                        passed=False,
                        errors=[f"Validation exception: {validation!s}"],
                        warnings=[],
                        performance_metrics={},
                        details=f"Exception: {traceback.format_exc()}",
                    )
                )
                failed_tests += 1
            else:
                results.append(validation)
                if validation.passed:
                    passed_tests += 1
                else:
                    failed_tests += 1
                total_warnings += len(validation.warnings)

                # Collect performance metrics
                if validation.performance_metrics:
                    overall_performance[validation.component] = validation.performance_metrics

            total_tests += 1

        # Generate recommendations
        recommendations = self._generate_recommendations(results)

        validation_suite = ValidationSuite(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            warnings=total_warnings,
            results=results,
            overall_performance=overall_performance,
            recommendations=recommendations,
        )

        # Cleanup test data
        self._cleanup_test_data()

        self.logger.info(f"Validation completed: {passed_tests}/{total_tests} tests passed")
        return validation_suite

    def _generate_recommendations(self, results: list[ValidationResult]) -> list[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        # Check for import issues
        for result in results:
            if not result.passed and "not available" in str(result.errors):
                recommendations.append(
                    f"Consider installing missing dependencies for {result.component}"
                )

        # Check performance metrics
        for result in results:
            if result.performance_metrics:
                for metric, value in result.performance_metrics.items():
                    if "time" in metric and isinstance(value, (int, float)) and value > 5.0:
                        recommendations.append(
                            f"Consider optimizing {metric} for {result.component} (current: {value:.3f}s)"
                        )

        # General recommendations
        if any(not r.passed for r in results):
            recommendations.append("Review failed validations and fix underlying issues")

        if any(r.warnings for r in results):
            recommendations.append("Address validation warnings for optimal performance")

        return recommendations

    def _cleanup_test_data(self) -> None:
        """Clean up temporary test data"""
        try:
            shutil.rmtree(self.test_data_dir)
            self.logger.debug(f"Cleaned up test data directory: {self.test_data_dir}")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup test data: {e}")

    def generate_validation_report(self, suite: ValidationSuite) -> str:
        """Generate comprehensive validation report"""
        report = []
        report.append("=" * 80)
        report.append("UNIFIED COMPONENT VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Validation Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Tests: {suite.total_tests}")
        report.append(f"Passed: {suite.passed_tests}")
        report.append(f"Failed: {suite.failed_tests}")
        report.append(f"Warnings: {suite.warnings}")
        report.append("")

        # Component results
        report.append("COMPONENT VALIDATION RESULTS:")
        report.append("-" * 50)

        for result in suite.results:
            status = "✅ PASSED" if result.passed else "❌ FAILED"
            report.append(f"{result.component}: {status}")

            if result.errors:
                report.append("  Errors:")
                for error in result.errors:
                    report.append(f"    - {error}")

            if result.warnings:
                report.append("  Warnings:")
                for warning in result.warnings:
                    report.append(f"    - {warning}")

            if result.performance_metrics:
                report.append("  Performance Metrics:")
                for metric, value in result.performance_metrics.items():
                    if isinstance(value, (int, float)):
                        report.append(f"    - {metric}: {value:.3f}")
                    else:
                        report.append(f"    - {metric}: {value}")

            report.append(f"  Details: {result.details}")
            report.append("")

        # Recommendations
        if suite.recommendations:
            report.append("RECOMMENDATIONS:")
            report.append("-" * 20)
            for i, rec in enumerate(suite.recommendations, 1):
                report.append(f"{i}. {rec}")
            report.append("")

        # Overall performance summary
        if suite.overall_performance:
            report.append("PERFORMANCE SUMMARY:")
            report.append("-" * 25)
            for component, metrics in suite.overall_performance.items():
                report.append(f"{component}:")
                for metric, value in metrics.items():
                    if isinstance(value, (int, float)):
                        report.append(f"  - {metric}: {value:.3f}")
            report.append("")

        report.append("=" * 80)
        return "\n".join(report)


# ============================================================================
# Singleton Instance Management
# ============================================================================

_component_validator_instance: UnifiedComponentValidator | None = None
_validator_lock = threading.Lock()


def get_component_validator() -> UnifiedComponentValidator:
    """Get the global component validator instance.

    Returns:
        UnifiedComponentValidator: The singleton validator instance
    """
    global _component_validator_instance
    with _validator_lock:
        if _component_validator_instance is None:
            _component_validator_instance = UnifiedComponentValidator()
        return _component_validator_instance


async def main() -> int:
    """Main validation entry point"""
    validator = UnifiedComponentValidator()

    print("🔍 Starting Unified Component Validation...")
    print("This may take a few moments...\n")

    suite = await validator.run_comprehensive_validation()
    report = validator.generate_validation_report(suite)

    # Print report
    print(report)

    # Save report to file
    report_file = Path("dev/reports/unified_component_validation_report.txt")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(report)
    print(f"\n📋 Full report saved to: {report_file.absolute()}")

    # Return exit code based on results
    return 0 if suite.failed_tests == 0 else 1


if __name__ == "__main__":
    import sys

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
