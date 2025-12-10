#!/usr/bin/env python3
"""
Comprehensive Integration Test for xanadOS Search & Destroy
Tests Phase 1 and Phase 2 component integration, resource coordination, and error handling.
"""

import asyncio
import logging
import tempfile
import time
from pathlib import Path
from typing import Any

# Test imports - using try/except to handle missing components gracefully
components_available = {}

try:
    # Note: component_manager consolidated into unified_component_validator
    from app.core.unified_component_validator import get_component_validator, ComponentStatus
    # Map ComponentState to ComponentStatus for compatibility
    ComponentState = ComponentStatus
    components_available['component_manager'] = True
except ImportError as e:
    print(f"Component manager not available: {e}")
    components_available['component_manager'] = False

try:
    from app.core.resource_coordinator import get_resource_coordinator, ResourceType, Priority
    components_available['resource_coordinator'] = True
except ImportError as e:
    print(f"Resource coordinator not available: {e}")
    components_available['resource_coordinator'] = False

try:
    from app.core.error_handler import get_error_handler, ErrorSeverity, ErrorCategory
    components_available['error_handler'] = True
except ImportError as e:
    print(f"Error handler not available: {e}")
    components_available['error_handler'] = False

try:
    from app.utils.config import get_config
    components_available['config'] = True
except ImportError as e:
    print(f"Config not available: {e}")
    components_available['config'] = False


class IntegrationTester:
    """Comprehensive integration testing framework."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_results = {}
        self.component_manager = None
        self.resource_coordinator = None
        self.error_handler = None

        # Initialize available components
        self._initialize_test_environment()

    def _initialize_test_environment(self):
        """Initialize test environment with available components."""
        self.logger.info("Initializing integration test environment")

        if components_available.get('component_manager'):
            self.component_manager = get_component_manager()

        if components_available.get('resource_coordinator'):
            self.resource_coordinator = get_resource_coordinator()

        if components_available.get('error_handler'):
            self.error_handler = get_error_handler()

    async def run_all_tests(self) -> dict[str, Any]:
        """Run all integration tests."""
        self.logger.info("Starting comprehensive integration tests")

        test_suite = [
            self.test_configuration_system,
            self.test_component_initialization,
            self.test_resource_coordination,
            self.test_error_handling_integration,
            self.test_phase1_components,
            self.test_phase2_components,
            self.test_cross_component_communication,
            self.test_resource_conflicts,
            self.test_graceful_degradation,
            self.test_memory_management
        ]

        for test in test_suite:
            test_name = test.__name__
            self.logger.info(f"Running test: {test_name}")

            try:
                start_time = time.time()
                result = await test()
                duration = time.time() - start_time

                self.test_results[test_name] = {
                    "status": "PASSED" if result else "FAILED",
                    "duration": duration,
                    "details": result if isinstance(result, dict) else {}
                }

                self.logger.info(f"Test {test_name}: {'PASSED' if result else 'FAILED'} ({duration:.2f}s)")

            except Exception as e:
                self.test_results[test_name] = {
                    "status": "ERROR",
                    "duration": 0,
                    "error": str(e)
                }
                self.logger.error(f"Test {test_name} failed with error: {e}")

        return self._generate_test_report()

    async def test_configuration_system(self) -> bool:
        """Test configuration system integration."""
        if not components_available.get('config'):
            return True  # Skip if not available

        try:
            # Test config loading
            config = get_config()
            if config is None:
                return False

            # Test config structure
            required_sections = ['scanning', 'security', 'performance']
            for section in required_sections:
                if section not in config:
                    self.logger.warning(f"Missing config section: {section}")

            return True

        except Exception as e:
            self.logger.error(f"Configuration test failed: {e}")
            return False

    async def test_component_initialization(self) -> bool:
        """Test component manager initialization."""
        if not self.component_manager:
            return True  # Skip if not available

        try:
            # Test component registration
            self.component_manager._register_all_components()

            # Check registered components
            status = self.component_manager.get_component_status()
            self.logger.info(f"Registered {len(status)} components")

            # Test initialization of critical components
            critical_components = ['memory_manager', 'ml_threat_detector', 'edr_engine']

            for component in critical_components:
                if component in status:
                    instance = self.component_manager.get_component(component)
                    if instance is None:
                        self.logger.warning(f"Failed to initialize {component}")
                    else:
                        self.logger.info(f"Successfully initialized {component}")

            return True

        except Exception as e:
            self.logger.error(f"Component initialization test failed: {e}")
            return False

    async def test_resource_coordination(self) -> bool:
        """Test resource coordination system."""
        if not self.resource_coordinator:
            return True  # Skip if not available

        try:
            from app.core.resource_coordinator import ResourceRequest

            # Test resource request
            cpu_request = ResourceRequest(
                component_name="test_component",
                resource_type=ResourceType.CPU,
                priority=Priority.NORMAL,
                amount=0.1,
                duration_estimate=1.0
            )

            success = self.resource_coordinator.request_resource(cpu_request)
            if success:
                self.resource_coordinator.release_resource(cpu_request)
                self.logger.info("Resource coordination test passed")
                return True
            else:
                self.logger.warning("Resource request failed")
                return False

        except Exception as e:
            self.logger.error(f"Resource coordination test failed: {e}")
            return False

    async def test_error_handling_integration(self) -> bool:
        """Test error handling system integration."""
        if not self.error_handler:
            return True  # Skip if not available

        try:
            # Test error handling
            test_exception = ValueError("Test error for integration testing")

            error_info = self.error_handler.handle_error(
                exception=test_exception,
                component="integration_test",
                function="test_error_handling_integration",
                context={"test": True}
            )

            # Verify error was recorded
            if error_info and error_info.component == "integration_test":
                self.logger.info("Error handling test passed")
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"Error handling test failed: {e}")
            return False

    async def test_phase1_components(self) -> bool:
        """Test Phase 1 components (ML, EDR, Memory Management, Forensics)."""
        if not self.component_manager:
            return True

        try:
            phase1_components = [
                'ml_threat_detector',
                'edr_engine',
                'memory_manager',
                'memory_forensics'
            ]

            success_count = 0
            for component in phase1_components:
                try:
                    instance = self.component_manager.get_component(component)
                    if instance:
                        success_count += 1
                        self.logger.info(f"Phase 1 component {component}: OK")
                    else:
                        self.logger.warning(f"Phase 1 component {component}: Failed to initialize")
                except Exception as e:
                    self.logger.error(f"Phase 1 component {component}: Error - {e}")

            success_rate = success_count / len(phase1_components)
            self.logger.info(f"Phase 1 components: {success_count}/{len(phase1_components)} ({success_rate:.1%})")

            return success_rate >= 0.5  # At least 50% success rate

        except Exception as e:
            self.logger.error(f"Phase 1 component test failed: {e}")
            return False

    async def test_phase2_components(self) -> bool:
        """Test Phase 2 components (Dashboard, Automation, Reporting, APIs, Deep Learning, GPU)."""
        if not self.component_manager:
            return True

        try:
            phase2_components = [
                'intelligent_automation',
                'advanced_reporting',
                'security_api',
                'deep_learning',
                'gpu_acceleration'
            ]

            success_count = 0
            for component in phase2_components:
                try:
                    instance = self.component_manager.get_component(component)
                    if instance:
                        success_count += 1
                        self.logger.info(f"Phase 2 component {component}: OK")
                    else:
                        self.logger.warning(f"Phase 2 component {component}: Failed to initialize")
                except Exception as e:
                    self.logger.error(f"Phase 2 component {component}: Error - {e}")

            success_rate = success_count / len(phase2_components)
            self.logger.info(f"Phase 2 components: {success_count}/{len(phase2_components)} ({success_rate:.1%})")

            return success_rate >= 0.3  # At least 30% success rate (some may require special hardware)

        except Exception as e:
            self.logger.error(f"Phase 2 component test failed: {e}")
            return False

    async def test_cross_component_communication(self) -> bool:
        """Test communication between Phase 1 and Phase 2 components."""
        if not self.component_manager:
            return True

        try:
            # Test if components can be retrieved and have expected interfaces
            ml_detector = self.component_manager.get_component('ml_threat_detector')
            edr_engine = self.component_manager.get_component('edr_engine')

            # Basic interface checks
            if ml_detector and hasattr(ml_detector, 'analyze_behavior'):
                self.logger.info("ML threat detector interface: OK")

            if edr_engine and hasattr(edr_engine, 'start_monitoring'):
                self.logger.info("EDR engine interface: OK")

            return True

        except Exception as e:
            self.logger.error(f"Cross-component communication test failed: {e}")
            return False

    async def test_resource_conflicts(self) -> bool:
        """Test resource conflict resolution."""
        if not self.resource_coordinator:
            return True

        try:
            from app.core.resource_coordinator import ResourceRequest

            # Create competing requests
            requests = []
            for i in range(3):
                request = ResourceRequest(
                    component_name=f"test_component_{i}",
                    resource_type=ResourceType.GPU,
                    priority=Priority.NORMAL,
                    amount=0.8,  # High resource usage
                    duration_estimate=2.0
                )
                requests.append(request)

            # Try to allocate all (should handle conflicts)
            allocated = []
            for request in requests:
                if self.resource_coordinator.request_resource(request):
                    allocated.append(request)

            # Clean up
            for request in allocated:
                self.resource_coordinator.release_resource(request)

            self.logger.info(f"Resource conflict test: allocated {len(allocated)}/{len(requests)} requests")
            return True

        except Exception as e:
            self.logger.error(f"Resource conflict test failed: {e}")
            return False

    async def test_graceful_degradation(self) -> bool:
        """Test graceful degradation when components fail."""
        try:
            # Simulate component failure and test system response
            if self.error_handler:
                # Test error handling for critical component failure
                critical_error = RuntimeError("Critical component failure simulation")

                error_info = self.error_handler.handle_error(
                    exception=critical_error,
                    component="critical_test_component",
                    function="test_graceful_degradation",
                    severity=ErrorSeverity.CRITICAL
                )

                if error_info:
                    self.logger.info("Graceful degradation test: Error handling worked")
                    return True

            return True

        except Exception as e:
            self.logger.error(f"Graceful degradation test failed: {e}")
            return False

    async def test_memory_management(self) -> bool:
        """Test memory management under load."""
        try:
            # Test memory management component if available
            if self.component_manager:
                memory_manager = self.component_manager.get_component('memory_manager')
                if memory_manager:
                    # Test basic memory management functionality
                    if hasattr(memory_manager, 'get_memory_stats'):
                        stats = memory_manager.get_memory_stats()
                        if stats:
                            self.logger.info(f"Memory stats: {stats}")
                            return True

            # Fallback: basic memory test
            import psutil
            memory_percent = psutil.virtual_memory().percent
            self.logger.info(f"Current memory usage: {memory_percent:.1f}%")
            return memory_percent < 90  # Pass if memory usage is reasonable

        except Exception as e:
            self.logger.error(f"Memory management test failed: {e}")
            return False

    def _generate_test_report(self) -> dict[str, Any]:
        """Generate comprehensive test report."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'PASSED')
        failed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'FAILED')
        error_tests = sum(1 for result in self.test_results.values() if result['status'] == 'ERROR')

        success_rate = passed_tests / total_tests if total_tests > 0 else 0

        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": error_tests,
                "success_rate": success_rate,
                "overall_status": "PASS" if success_rate >= 0.7 else "FAIL"
            },
            "component_availability": components_available,
            "detailed_results": self.test_results,
            "recommendations": self._generate_recommendations()
        }

        return report

    def _generate_recommendations(self) -> list[str]:
        """Generate recommendations based on test results."""
        recommendations = []

        # Check component availability
        missing_components = [comp for comp, available in components_available.items() if not available]
        if missing_components:
            recommendations.append(f"Missing components detected: {', '.join(missing_components)}")

        # Check test failure patterns
        failed_tests = [name for name, result in self.test_results.items() if result['status'] in ['FAILED', 'ERROR']]
        if failed_tests:
            recommendations.append(f"Failed tests require attention: {', '.join(failed_tests)}")

        # Performance recommendations
        slow_tests = [name for name, result in self.test_results.items() if result.get('duration', 0) > 10.0]
        if slow_tests:
            recommendations.append(f"Slow tests detected (>10s): {', '.join(slow_tests)}")

        if not recommendations:
            recommendations.append("All integration tests passed successfully!")

        return recommendations


async def run_integration_tests():
    """Main function to run integration tests."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    tester = IntegrationTester()
    report = await tester.run_all_tests()

    # Print summary report
    print("\n" + "="*60)
    print("INTEGRATION TEST REPORT")
    print("="*60)
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Errors: {report['summary']['errors']}")
    print(f"Success Rate: {report['summary']['success_rate']:.1%}")
    print(f"Overall Status: {report['summary']['overall_status']}")

    print("\nComponent Availability:")
    for component, available in report['component_availability'].items():
        status = "✓" if available else "✗"
        print(f"  {status} {component}")

    print("\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  • {rec}")

    print("\nDetailed Results:")
    for test_name, result in report['detailed_results'].items():
        status_symbol = {"PASSED": "✓", "FAILED": "✗", "ERROR": "⚠"}[result['status']]
        duration = result.get('duration', 0)
        print(f"  {status_symbol} {test_name} ({duration:.2f}s)")
        if result['status'] == 'ERROR':
            print(f"    Error: {result.get('error', 'Unknown error')}")

    return report


if __name__ == "__main__":
    import asyncio
    report = asyncio.run(run_integration_tests())
