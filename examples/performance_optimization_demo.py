#!/usr/bin/env python3
"""
Enterprise Performance Integration Example
==========================================

Demonstrates how to integrate the new enterprise performance optimization
features with existing security systems.

This example shows:
1. Setting up the enterprise performance manager
2. Integrating with security coordinator
3. Collecting and monitoring performance metrics
4. Performing optimization
5. Accessing dashboard data
"""

import asyncio
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

try:
    from app.core.enterprise_performance_manager import (
        create_enterprise_performance_manager,
        PerformanceTarget,
        OptimizationStrategy,
    )
    from app.core.security_performance_integration import (
        create_security_performance_integrator,
    )
    from app.core.security_integration import SecurityIntegrationCoordinator
    from app.core.rate_limiting import RateLimitingCoordinator
except ImportError as e:
    logger.warning(f"Import error (expected in testing): {e}")

    # Create mock classes for demonstration
    class MockPerformanceManager:
        async def initialize(self, **kwargs):
            pass

        async def get_performance_dashboard_data(self):
            return {"mock": "data"}

        async def manual_optimization(self):
            return {"status": "mock_optimization"}

        def get_cache_manager(self):
            return MockCache()

    class MockCache:
        def get_stats(self):
            return {"hit_ratio": 0.85, "size_mb": 32.0}

        def set(self, key, value):
            return True

        def get(self, key):
            return f"cached_{key}" if key else None

    class MockIntegrator:
        async def initialize(self):
            pass

        async def collect_security_metrics(self):
            return {"timestamp": datetime.now()}

        async def get_security_dashboard_data(self):
            return {"mock": "security_data"}

        async def optimize_security_performance(self):
            return {"status": "mock_security_optimization"}

    def create_enterprise_performance_manager(**kwargs):
        return MockPerformanceManager()

    def create_security_performance_integrator(**kwargs):
        return MockIntegrator()


async def demonstrate_performance_optimization():
    """Demonstrate enterprise performance optimization features."""

    logger.info("🚀 Starting Enterprise Performance Optimization Demonstration")

    # Step 1: Create performance manager with custom targets
    logger.info("📊 Step 1: Creating Enterprise Performance Manager")

    # Define performance targets optimized for security operations
    security_targets = (
        PerformanceTarget(
            max_response_time_ms=50.0,  # Fast response for security operations
            min_throughput_ops_per_sec=200.0,  # High throughput requirement
            max_cpu_usage_percent=60.0,  # Conservative CPU usage
            max_memory_usage_mb=256.0,  # Reasonable memory limit
            max_cache_size_mb=64.0,  # Focused cache for security data
            target_cache_hit_ratio=0.90,  # High cache efficiency
        )
        if "PerformanceTarget" in globals()
        else None
    )

    performance_manager = create_enterprise_performance_manager(
        max_cache_size_mb=64.0,
        optimization_strategy=(
            OptimizationStrategy.BALANCED
            if "OptimizationStrategy" in globals()
            else "balanced"
        ),
        enable_auto_optimization=True,
        performance_targets=security_targets,
    )

    logger.info("✅ Performance manager created with security-optimized targets")

    # Step 2: Initialize performance manager
    logger.info("🔧 Step 2: Initializing Performance Manager")

    await performance_manager.initialize()
    logger.info("✅ Performance manager initialized")

    # Step 3: Test cache operations
    logger.info("💾 Step 3: Testing Intelligent Cache System")

    cache_manager = performance_manager.get_cache_manager()

    # Cache some security-related data
    test_data = [
        ("user_permissions_admin", {"permissions": ["read", "write", "admin"]}),
        ("scan_result_file1", {"threat_level": "low", "scan_time": 0.5}),
        ("auth_token_abc123", {"user_id": "user123", "expires": "2025-01-01"}),
        ("threat_signature_malware1", {"signature": "abc123", "severity": "high"}),
    ]

    for key, value in test_data:
        cache_manager.set(key, value)
        logger.info(f"   Cached: {key}")

    # Test cache retrieval
    retrieved = cache_manager.get("user_permissions_admin")
    logger.info(f"   Retrieved from cache: {retrieved}")

    # Get cache statistics
    cache_stats = cache_manager.get_stats()
    logger.info(
        f"   Cache stats: Hit ratio={cache_stats.get('hit_ratio', 0):.2f}, "
        f"Size={cache_stats.get('size_mb', 0):.1f}MB, "
        f"Entries={cache_stats.get('entries', 0)}"
    )

    # Step 4: Create security performance integrator
    logger.info("🔒 Step 4: Creating Security Performance Integrator")

    security_integrator = create_security_performance_integrator(
        security_coordinator=None,  # Would be actual SecurityIntegrationCoordinator in real use
        max_cache_size_mb=64.0,
        optimization_strategy=(
            OptimizationStrategy.BALANCED
            if "OptimizationStrategy" in globals()
            else "balanced"
        ),
    )

    await security_integrator.initialize()
    logger.info("✅ Security performance integrator initialized")

    # Step 5: Collect security metrics
    logger.info("📈 Step 5: Collecting Security Performance Metrics")

    security_metrics = await security_integrator.collect_security_metrics()
    logger.info(
        f"   Security metrics collected at: {security_metrics.get('timestamp', 'unknown')}"
    )

    # Step 6: Get dashboard data
    logger.info("📊 Step 6: Getting Performance Dashboard Data")

    dashboard_data = await performance_manager.get_performance_dashboard_data()
    logger.info(
        f"   Dashboard sections available: {list(dashboard_data.keys()) if isinstance(dashboard_data, dict) else 'mock data'}"
    )

    security_dashboard_data = await security_integrator.get_security_dashboard_data()
    logger.info(
        f"   Security dashboard sections: {list(security_dashboard_data.keys()) if isinstance(security_dashboard_data, dict) else 'mock data'}"
    )

    # Step 7: Perform optimization
    logger.info("⚡ Step 7: Performing Performance Optimization")

    # General performance optimization
    optimization_result = await performance_manager.manual_optimization()
    logger.info(
        f"   General optimization result: {optimization_result.get('status', 'unknown')}"
    )

    # Security-specific optimization
    security_optimization = await security_integrator.optimize_security_performance()
    logger.info(
        f"   Security optimization result: {security_optimization.get('status', 'unknown')}"
    )

    # Step 8: Demonstrate real-time monitoring
    logger.info("⏰ Step 8: Demonstrating Real-time Monitoring")

    logger.info("   Starting monitoring cycle...")
    for i in range(3):
        await asyncio.sleep(1)  # Simulate time passing

        # Collect metrics
        current_metrics = await security_integrator.collect_security_metrics()

        # Get cache performance
        cache_stats = cache_manager.get_stats()

        logger.info(
            f"   Monitoring cycle {i+1}: "
            f"Cache hit ratio={cache_stats.get('hit_ratio', 0):.2f}, "
            f"Metrics timestamp={current_metrics.get('timestamp', 'unknown')}"
        )

    # Step 9: Show recommendations
    logger.info("💡 Step 9: Performance Recommendations")

    dashboard_data = await security_integrator.get_security_dashboard_data()
    recommendations = dashboard_data.get(
        "recommendations", ["System performance is optimal"]
    )

    logger.info("   Current recommendations:")
    for i, recommendation in enumerate(recommendations, 1):
        logger.info(f"   {i}. {recommendation}")

    # Step 10: Cleanup
    logger.info("🧹 Step 10: Cleanup")

    # Stop monitoring (in real implementation)
    # await security_integrator.stop_monitoring()
    logger.info("   Performance monitoring stopped")

    logger.info("🎉 Enterprise Performance Optimization Demonstration Complete!")

    return {
        "cache_stats": cache_stats,
        "optimization_result": optimization_result,
        "security_optimization": security_optimization,
        "recommendations": recommendations,
    }


async def demonstrate_advanced_features():
    """Demonstrate advanced performance features."""

    logger.info("🎯 Advanced Performance Features Demonstration")

    # Create performance manager
    performance_manager = create_enterprise_performance_manager(
        optimization_strategy=(
            OptimizationStrategy.ADAPTIVE
            if "OptimizationStrategy" in globals()
            else "adaptive"
        )
    )
    await performance_manager.initialize()

    # Advanced cache usage
    logger.info("🧠 Advanced Cache Operations")
    cache_manager = performance_manager.get_cache_manager()

    # Cache with TTL
    cache_manager.set("temporary_auth_token", "token123", ttl_seconds=5.0)
    logger.info("   Set temporary token with 5-second TTL")

    # Cache with priority
    cache_manager.set("critical_security_data", {"level": "critical"}, priority=10)
    logger.info("   Set critical data with high priority")

    # Test TTL expiration
    await asyncio.sleep(2)
    token = cache_manager.get("temporary_auth_token")
    logger.info(f"   Token after 2 seconds: {token is not None}")

    await asyncio.sleep(4)
    expired_token = cache_manager.get("temporary_auth_token")
    logger.info(
        f"   Token after 6 seconds (should be expired): {expired_token is not None}"
    )

    # Performance monitoring
    logger.info("📊 Advanced Performance Monitoring")

    # Simulate performance data collection
    for i in range(5):
        dashboard_data = await performance_manager.get_performance_dashboard_data()
        logger.info(f"   Monitoring iteration {i+1}: Data collected")
        await asyncio.sleep(0.5)

    logger.info("✅ Advanced features demonstration complete")


def print_integration_example():
    """Print example code for integrating performance optimization."""

    logger.info("📝 Integration Example Code")

    example_code = '''
# Example: Integrating Performance Optimization with Security System

import asyncio
from app.core.enterprise_performance_manager import create_enterprise_performance_manager, PerformanceTarget, OptimizationStrategy
from app.core.security_performance_integration import create_security_performance_integrator

async def setup_enterprise_security_with_performance():
    """Setup enterprise security with performance optimization."""

    # 1. Create custom performance targets
    targets = PerformanceTarget(
        max_response_time_ms=30.0,      # Very fast security operations
        min_throughput_ops_per_sec=500.0,  # High-performance scanning
        max_cpu_usage_percent=50.0,     # Conservative resource usage
        max_memory_usage_mb=512.0,      # Generous memory for caching
        max_cache_size_mb=128.0,        # Large cache for security data
        target_cache_hit_ratio=0.95     # Very high cache efficiency
    )

    # 2. Create performance manager
    performance_manager = create_enterprise_performance_manager(
        optimization_strategy=OptimizationStrategy.AGGRESSIVE,
        enable_auto_optimization=True,
        performance_targets=targets
    )

    # 3. Create security coordinator (your existing security system)
    # security_coordinator = SecurityIntegrationCoordinator(...)

    # 4. Create security performance integrator
    integrator = create_security_performance_integrator(
        security_coordinator=None,  # Pass your security coordinator here
        optimization_strategy=OptimizationStrategy.AGGRESSIVE,
        custom_targets=targets
    )

    # 5. Initialize everything
    await performance_manager.initialize()
    await integrator.initialize()

    # 6. Start monitoring
    await integrator.start_monitoring()

    # 7. Use the cache for security operations
    cache = performance_manager.get_cache_manager()

    # Cache authentication data
    cache.set("user_auth_data", {"user": "admin", "roles": ["admin", "security"]})

    # Cache scan results
    cache.set("scan_results_file1", {"threats": 0, "scan_time": 0.5})

    # 8. Get real-time dashboard data
    dashboard_data = await integrator.get_security_dashboard_data()
    print(f"Performance dashboard: {dashboard_data}")

    # 9. Manual optimization when needed
    optimization_result = await integrator.optimize_security_performance()
    print(f"Optimization result: {optimization_result}")

    return performance_manager, integrator

# Run the setup
# performance_manager, integrator = await setup_enterprise_security_with_performance()
    '''

    print(example_code)


async def main():
    """Main demonstration function."""

    print("=" * 80)
    print("🚀 ENTERPRISE PERFORMANCE OPTIMIZATION DEMONSTRATION")
    print("=" * 80)

    try:
        # Basic demonstration
        result = await demonstrate_performance_optimization()

        print("\n" + "=" * 60)

        # Advanced features
        await demonstrate_advanced_features()

        print("\n" + "=" * 60)

        # Integration example
        print_integration_example()

        print("\n" + "=" * 80)
        print("✅ ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY")
        print("=" * 80)

        return result

    except Exception as e:
        logger.error(f"❌ Demonstration failed: {e}")
        raise


if __name__ == "__main__":
    # Run the demonstration
    result = asyncio.run(main())
    print(f"\nDemonstration result: {result}")
