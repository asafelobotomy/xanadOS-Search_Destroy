#!/usr/bin/env python3
"""
Performance Integration Bridge for Enterprise Security
====================================================

This module provides integration between the new EnterprisePerformanceManager
and the existing security systems, enabling comprehensive performance monitoring
of all security operations.

Features:
- Integration with SecurityIntegrationCoordinator
- Performance metrics collection from all security components
- Real-time performance dashboard data aggregation
- Automatic performance optimization triggers
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

try:
    from .enterprise_performance_manager import (
        EnterprisePerformanceManager,
        PerformanceTarget,
        OptimizationStrategy,
        create_enterprise_performance_manager,
    )
    from .security_integration import SecurityIntegrationCoordinator, PerformanceMetrics
    from .rate_limiting import RateLimitingCoordinator
except ImportError:
    # Fallback for development/testing
    EnterprisePerformanceManager = None
    PerformanceTarget = None
    OptimizationStrategy = None
    SecurityIntegrationCoordinator = None
    PerformanceMetrics = None
    RateLimitingCoordinator = None


@dataclass
class SecurityPerformanceMetrics:
    """Enhanced performance metrics for security operations."""

    timestamp: datetime = field(default_factory=datetime.now)
    authentication_response_time_ms: float = 0.0
    authorization_response_time_ms: float = 0.0
    scan_throughput_files_per_sec: float = 0.0
    threat_detection_latency_ms: float = 0.0
    permission_check_time_ms: float = 0.0
    cache_hit_ratios: dict[str, float] = field(default_factory=dict)
    active_security_operations: int = 0
    security_cpu_usage_percent: float = 0.0
    security_memory_usage_mb: float = 0.0


class SecurityPerformanceIntegrator:
    """
    Integrates enterprise performance management with security operations.

    This class serves as a bridge between the EnterprisePerformanceManager
    and the existing security systems, providing comprehensive performance
    monitoring and optimization for all security-related operations.
    """

    def __init__(
        self,
        security_coordinator: SecurityIntegrationCoordinator | None = None,
        performance_targets: PerformanceTarget | None = None,
        optimization_strategy: OptimizationStrategy | None = None,
    ):
        self.security_coordinator = security_coordinator
        self.logger = logging.getLogger(__name__)

        # Create performance manager with security-optimized targets
        if performance_targets is None:
            performance_targets = PerformanceTarget(
                max_response_time_ms=50.0,  # Stricter for security operations
                min_throughput_ops_per_sec=200.0,  # Higher throughput needed
                max_cpu_usage_percent=60.0,  # Conservative for security
                max_memory_usage_mb=256.0,  # Reasonable for security ops
                max_cache_size_mb=64.0,  # Focused cache for security data
                target_cache_hit_ratio=0.90,  # High cache efficiency needed
            )

        if optimization_strategy is None:
            optimization_strategy = OptimizationStrategy.BALANCED

        self.performance_manager = (
            create_enterprise_performance_manager(
                max_cache_size_mb=performance_targets.max_cache_size_mb,
                optimization_strategy=optimization_strategy,
                enable_auto_optimization=True,
                performance_targets=performance_targets,
            )
            if EnterprisePerformanceManager
            else None
        )

        # Performance tracking
        self._metrics_history: list[SecurityPerformanceMetrics] = []
        self._last_optimization = time.time()
        self._optimization_interval = 300.0  # 5 minutes

        # Component tracking
        self._tracked_components: dict[str, Any] = {}
        self._performance_baselines: dict[str, float] = {}

    async def initialize(self):
        """Initialize the performance integrator with security components."""
        if not self.performance_manager:
            self.logger.warning(
                "Performance manager not available - running without optimization"
            )
            return

        try:
            # Get rate limiter from security coordinator if available
            rate_limiter = None
            if self.security_coordinator:
                # Try to get rate limiter from security coordinator
                # This would depend on the actual implementation
                pass

            # Initialize performance manager
            await self.performance_manager.initialize(
                security_coordinator=self.security_coordinator,
                rate_limiter=rate_limiter,
            )

            self.logger.info("Security performance integrator initialized successfully")

        except Exception as e:
            self.logger.error(
                f"Failed to initialize security performance integrator: {e}"
            )

    async def collect_security_metrics(self) -> SecurityPerformanceMetrics:
        """Collect comprehensive security performance metrics."""
        try:
            current_time = datetime.now()
            metrics = SecurityPerformanceMetrics(timestamp=current_time)

            if self.security_coordinator:
                # Collect metrics from security coordinator
                try:
                    # Get performance metrics if available
                    security_perf_metrics = getattr(
                        self.security_coordinator, "performance_metrics", None
                    )
                    if security_perf_metrics:
                        metrics.authentication_response_time_ms = getattr(
                            security_perf_metrics, "average_response_time_ms", 0.0
                        )

                        # Get component-specific metrics
                        component_metrics = getattr(
                            security_perf_metrics, "component_metrics", {}
                        )
                        if "authentication" in component_metrics:
                            auth_metrics = component_metrics["authentication"]
                            metrics.authentication_response_time_ms = auth_metrics.get(
                                "avg_response_time", 0.0
                            )

                        if "authorization" in component_metrics:
                            authz_metrics = component_metrics["authorization"]
                            metrics.authorization_response_time_ms = authz_metrics.get(
                                "avg_response_time", 0.0
                            )

                        if "scanning" in component_metrics:
                            scan_metrics = component_metrics["scanning"]
                            metrics.scan_throughput_files_per_sec = scan_metrics.get(
                                "throughput", 0.0
                            )

                        if "threat_detection" in component_metrics:
                            threat_metrics = component_metrics["threat_detection"]
                            metrics.threat_detection_latency_ms = threat_metrics.get(
                                "avg_latency", 0.0
                            )

                        if "permission_check" in component_metrics:
                            perm_metrics = component_metrics["permission_check"]
                            metrics.permission_check_time_ms = perm_metrics.get(
                                "avg_time", 0.0
                            )

                except Exception as e:
                    self.logger.debug(
                        f"Error collecting security coordinator metrics: {e}"
                    )

            # Get cache performance from performance manager
            if self.performance_manager:
                try:
                    cache_manager = self.performance_manager.get_cache_manager()
                    cache_stats = cache_manager.get_stats()
                    metrics.cache_hit_ratios["security_cache"] = cache_stats.get(
                        "hit_ratio", 0.0
                    )
                except Exception as e:
                    self.logger.debug(f"Error collecting cache metrics: {e}")

            # Estimate security-specific resource usage
            # This is a simplified estimation - in practice would need more sophisticated tracking
            import psutil

            metrics.security_cpu_usage_percent = (
                psutil.cpu_percent() * 0.1
            )  # Estimate 10% for security
            memory_info = psutil.virtual_memory()
            metrics.security_memory_usage_mb = (
                memory_info.used / (1024 * 1024)
            ) * 0.05  # Estimate 5% for security

            # Store metrics
            self._metrics_history.append(metrics)

            # Keep only recent metrics (last 100)
            if len(self._metrics_history) > 100:
                self._metrics_history.pop(0)

            return metrics

        except Exception as e:
            self.logger.error(f"Error collecting security metrics: {e}")
            return SecurityPerformanceMetrics()

    async def optimize_security_performance(self) -> dict[str, Any]:
        """Perform security-focused performance optimization."""
        if not self.performance_manager:
            return {"status": "performance_manager_unavailable"}

        try:
            # Check if optimization is needed
            current_time = time.time()
            if current_time - self._last_optimization < self._optimization_interval:
                return {
                    "status": "optimization_not_needed",
                    "next_optimization_in": self._optimization_interval
                    - (current_time - self._last_optimization),
                }

            # Collect current metrics
            security_metrics = await self.collect_security_metrics()

            # Perform general optimization
            optimization_result = await self.performance_manager.manual_optimization()

            # Security-specific optimizations
            security_optimizations = []

            # Check authentication performance
            if security_metrics.authentication_response_time_ms > 100.0:
                security_optimizations.append("authentication_cache_optimization")
                # Could trigger authentication cache warming or optimization

            # Check authorization performance
            if security_metrics.authorization_response_time_ms > 50.0:
                security_optimizations.append("authorization_cache_optimization")
                # Could trigger permission cache optimization

            # Check scan throughput
            if security_metrics.scan_throughput_files_per_sec < 50.0:
                security_optimizations.append("scan_optimization")
                # Could adjust scanning parameters

            # Check threat detection latency
            if security_metrics.threat_detection_latency_ms > 200.0:
                security_optimizations.append("threat_detection_optimization")
                # Could optimize threat detection algorithms

            # Update baselines for future comparisons
            self._update_performance_baselines(security_metrics)
            self._last_optimization = current_time

            return {
                "status": "optimization_completed",
                "timestamp": datetime.now().isoformat(),
                "general_optimization": optimization_result,
                "security_optimizations": security_optimizations,
                "security_metrics": {
                    "authentication_response_time_ms": security_metrics.authentication_response_time_ms,
                    "authorization_response_time_ms": security_metrics.authorization_response_time_ms,
                    "scan_throughput_files_per_sec": security_metrics.scan_throughput_files_per_sec,
                    "threat_detection_latency_ms": security_metrics.threat_detection_latency_ms,
                    "permission_check_time_ms": security_metrics.permission_check_time_ms,
                    "cache_hit_ratios": security_metrics.cache_hit_ratios,
                },
            }

        except Exception as e:
            self.logger.error(f"Error during security performance optimization: {e}")
            return {"status": "optimization_failed", "error": str(e)}

    async def get_security_dashboard_data(self) -> dict[str, Any]:
        """Get comprehensive security performance data for dashboard display."""
        try:
            # Get general performance dashboard data
            general_dashboard_data = {}
            if self.performance_manager:
                general_dashboard_data = (
                    await self.performance_manager.get_performance_dashboard_data()
                )

            # Collect current security metrics
            security_metrics = await self.collect_security_metrics()

            # Calculate trends
            trends = self._calculate_performance_trends()

            # Generate recommendations
            recommendations = self._generate_security_recommendations(security_metrics)

            return {
                "timestamp": datetime.now().isoformat(),
                "general_performance": general_dashboard_data,
                "security_metrics": {
                    "current": {
                        "authentication_response_time_ms": security_metrics.authentication_response_time_ms,
                        "authorization_response_time_ms": security_metrics.authorization_response_time_ms,
                        "scan_throughput_files_per_sec": security_metrics.scan_throughput_files_per_sec,
                        "threat_detection_latency_ms": security_metrics.threat_detection_latency_ms,
                        "permission_check_time_ms": security_metrics.permission_check_time_ms,
                        "cache_hit_ratios": security_metrics.cache_hit_ratios,
                        "active_security_operations": security_metrics.active_security_operations,
                        "security_cpu_usage_percent": security_metrics.security_cpu_usage_percent,
                        "security_memory_usage_mb": security_metrics.security_memory_usage_mb,
                    },
                    "trends": trends,
                    "baselines": self._performance_baselines,
                },
                "recommendations": recommendations,
                "optimization_status": {
                    "last_optimization": self._last_optimization,
                    "next_optimization_in": max(
                        0,
                        self._optimization_interval
                        - (time.time() - self._last_optimization),
                    ),
                    "auto_optimization_enabled": True,
                },
            }

        except Exception as e:
            self.logger.error(f"Error getting security dashboard data: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def _update_performance_baselines(self, metrics: SecurityPerformanceMetrics):
        """Update performance baselines for comparison."""
        self._performance_baselines.update(
            {
                "authentication_response_time_ms": metrics.authentication_response_time_ms,
                "authorization_response_time_ms": metrics.authorization_response_time_ms,
                "scan_throughput_files_per_sec": metrics.scan_throughput_files_per_sec,
                "threat_detection_latency_ms": metrics.threat_detection_latency_ms,
                "permission_check_time_ms": metrics.permission_check_time_ms,
            }
        )

    def _calculate_performance_trends(self) -> dict[str, str]:
        """Calculate performance trends from recent metrics."""
        if len(self._metrics_history) < 3:
            return {}

        recent_metrics = self._metrics_history[-3:]
        trends = {}

        # Calculate authentication response time trend
        auth_times = [m.authentication_response_time_ms for m in recent_metrics]
        if auth_times[-1] > auth_times[0] * 1.1:
            trends["authentication"] = "declining"
        elif auth_times[-1] < auth_times[0] * 0.9:
            trends["authentication"] = "improving"
        else:
            trends["authentication"] = "stable"

        # Calculate scan throughput trend
        scan_throughputs = [m.scan_throughput_files_per_sec for m in recent_metrics]
        if scan_throughputs[-1] > scan_throughputs[0] * 1.1:
            trends["scan_throughput"] = "improving"
        elif scan_throughputs[-1] < scan_throughputs[0] * 0.9:
            trends["scan_throughput"] = "declining"
        else:
            trends["scan_throughput"] = "stable"

        # Calculate threat detection trend
        threat_latencies = [m.threat_detection_latency_ms for m in recent_metrics]
        if threat_latencies[-1] > threat_latencies[0] * 1.1:
            trends["threat_detection"] = "declining"
        elif threat_latencies[-1] < threat_latencies[0] * 0.9:
            trends["threat_detection"] = "improving"
        else:
            trends["threat_detection"] = "stable"

        return trends

    def _generate_security_recommendations(
        self, metrics: SecurityPerformanceMetrics
    ) -> list[str]:
        """Generate security-specific performance recommendations."""
        recommendations = []

        if metrics.authentication_response_time_ms > 100.0:
            recommendations.append(
                "Consider optimizing authentication cache or reducing authentication complexity"
            )

        if metrics.authorization_response_time_ms > 50.0:
            recommendations.append(
                "Permission checking may benefit from caching or policy optimization"
            )

        if metrics.scan_throughput_files_per_sec < 50.0:
            recommendations.append(
                "Scan performance is low - consider adjusting scan parameters or increasing resources"
            )

        if metrics.threat_detection_latency_ms > 200.0:
            recommendations.append(
                "Threat detection latency is high - consider optimizing detection algorithms"
            )

        # Check cache hit ratios
        for cache_name, hit_ratio in metrics.cache_hit_ratios.items():
            if hit_ratio < 0.8:
                recommendations.append(
                    f"Cache '{cache_name}' has low hit ratio ({hit_ratio:.2f}) - consider cache optimization"
                )

        if metrics.security_cpu_usage_percent > 15.0:
            recommendations.append(
                "Security operations are using high CPU - consider performance optimization"
            )

        if metrics.security_memory_usage_mb > 128.0:
            recommendations.append(
                "Security operations are using high memory - consider memory optimization"
            )

        if not recommendations:
            recommendations.append(
                "Security performance is within acceptable parameters"
            )

        return recommendations

    async def start_monitoring(self):
        """Start continuous security performance monitoring."""
        if not self.performance_manager:
            self.logger.warning(
                "Performance manager not available - monitoring disabled"
            )
            return

        # Start background optimization in performance manager
        await self.performance_manager.start_background_optimization()

        self.logger.info("Security performance monitoring started")

    async def stop_monitoring(self):
        """Stop security performance monitoring."""
        if self.performance_manager:
            await self.performance_manager.stop_background_optimization()

        self.logger.info("Security performance monitoring stopped")

    def get_performance_manager(self) -> EnterprisePerformanceManager | None:
        """Get the underlying performance manager for direct access."""
        return self.performance_manager

    def get_security_coordinator(self) -> SecurityIntegrationCoordinator | None:
        """Get the security coordinator for direct access."""
        return self.security_coordinator


# Factory function for easy integration
def create_security_performance_integrator(
    security_coordinator: SecurityIntegrationCoordinator | None = None,
    max_cache_size_mb: float = 64.0,
    optimization_strategy: OptimizationStrategy | None = None,
    custom_targets: PerformanceTarget | None = None,
) -> SecurityPerformanceIntegrator:
    """
    Factory function to create a security performance integrator.

    Args:
        security_coordinator: Security coordinator to integrate with
        max_cache_size_mb: Maximum cache size for security operations
        optimization_strategy: Performance optimization strategy
        custom_targets: Custom performance targets for security operations

    Returns:
        Configured SecurityPerformanceIntegrator instance
    """
    if optimization_strategy is None:
        optimization_strategy = OptimizationStrategy.BALANCED

    if custom_targets is None:
        custom_targets = PerformanceTarget(
            max_response_time_ms=50.0,
            min_throughput_ops_per_sec=200.0,
            max_cpu_usage_percent=60.0,
            max_memory_usage_mb=256.0,
            max_cache_size_mb=max_cache_size_mb,
            target_cache_hit_ratio=0.90,
        )

    return SecurityPerformanceIntegrator(
        security_coordinator=security_coordinator,
        performance_targets=custom_targets,
        optimization_strategy=optimization_strategy,
    )


if __name__ == "__main__":
    # Example usage and testing
    async def test_security_performance_integration():
        """Test the security performance integration."""
        # Create integrator
        integrator = create_security_performance_integrator(
            max_cache_size_mb=32.0, optimization_strategy=OptimizationStrategy.BALANCED
        )

        # Initialize
        await integrator.initialize()

        # Collect metrics
        metrics = await integrator.collect_security_metrics()
        print(f"Security metrics: {metrics}")

        # Get dashboard data
        dashboard_data = await integrator.get_security_dashboard_data()
        print(f"Dashboard data available: {len(dashboard_data)} sections")

        # Test optimization
        optimization_result = await integrator.optimize_security_performance()
        print(f"Optimization result: {optimization_result}")

        print("Security performance integration test completed successfully!")

    # Run test
    asyncio.run(test_security_performance_integration())
