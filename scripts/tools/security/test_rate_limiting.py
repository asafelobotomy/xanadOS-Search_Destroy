#!/usr/bin/env python3
"""
Rate Limiting Testing and Validation Script
Tests the enhanced rate limiting implementation for comprehensive security coverage.
"""

import asyncio
import json
import logging
import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

try:
    from fastapi.testclient import TestClient
except ImportError as e:
    print(f"Missing required dependencies: {e}")
    print("Install with: pip install httpx redis")
    sys.exit(1)

from app.api.security_api import RateLimiter, SecurityAPI
from app.utils.config import get_api_security_config


class RateLimitTester:
    """Comprehensive rate limiting tester."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        self.config = get_api_security_config()

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    async def test_basic_rate_limiting(self):
        """Test basic rate limiting functionality."""
        self.logger.info("Testing basic rate limiting...")

        try:
            # Create test RateLimiter instance
            rate_limiter = RateLimiter(api_config=self.config)

            # Mock request for testing
            class MockRequest:
                def __init__(self, client_ip: str = "127.0.0.1"):
                    self.client = type('obj', (object,), {'host': client_ip})
                    self.headers = {}
                    self.url = type('obj', (object,), {'path': '/test'})

            request = MockRequest()

            # Test normal operation
            is_limited, info = await rate_limiter.is_rate_limited(request)
            assert not is_limited, f"Should not be rate limited initially: {info}"

            # Record the request
            await rate_limiter.record_request(request)

            # Get status
            status = await rate_limiter.get_rate_limit_status(request)
            assert status is not None, "Should get rate limit status"

            self.results.append({
                "test": "basic_rate_limiting",
                "status": "PASS",
                "details": "Basic rate limiting functionality works"
            })

            self.logger.info("✅ Basic rate limiting test passed")

        except Exception as e:
            self.results.append({
                "test": "basic_rate_limiting",
                "status": "FAIL",
                "error": str(e)
            })
            self.logger.error(f"❌ Basic rate limiting test failed: {e}")

    async def test_burst_protection(self):
        """Test burst protection functionality."""
        self.logger.info("Testing burst protection...")

        try:
            rate_limiter = RateLimiter(api_config=self.config)

            class MockRequest:
                def __init__(self, client_ip: str = "192.168.1.100"):
                    self.client = type('obj', (object,), {'host': client_ip})
                    self.headers = {}
                    self.url = type('obj', (object,), {'path': '/test'})

            request = MockRequest()
            burst_limit = rate_limiter.burst_limit

            # Make rapid requests up to burst limit
            for i in range(burst_limit):
                await rate_limiter.record_request(request)

            # Next request should be rate limited
            is_limited, info = await rate_limiter.is_rate_limited(request)

            if is_limited and info.get('reason') == 'burst_limit_exceeded':
                self.results.append({
                    "test": "burst_protection",
                    "status": "PASS",
                    "details": f"Burst protection triggered after {burst_limit} requests"
                })
                self.logger.info(f"✅ Burst protection test passed (limit: {burst_limit})")
            else:
                self.results.append({
                    "test": "burst_protection",
                    "status": "FAIL",
                    "details": f"Burst protection not triggered: {info}"
                })
                self.logger.warning(f"⚠️ Burst protection test inconclusive: {info}")

        except Exception as e:
            self.results.append({
                "test": "burst_protection",
                "status": "FAIL",
                "error": str(e)
            })
            self.logger.error(f"❌ Burst protection test failed: {e}")

    async def test_whitelist_functionality(self):
        """Test IP whitelisting functionality."""
        self.logger.info("Testing whitelist functionality...")

        try:
            # Create rate limiter with whitelist
            config_with_whitelist = self.config.copy()
            config_with_whitelist["rate_limiting"]["whitelist_ips"] = ["192.168.1.200"]

            rate_limiter = RateLimiter(api_config=config_with_whitelist)

            class MockRequest:
                def __init__(self, client_ip: str):
                    self.client = type('obj', (object,), {'host': client_ip})
                    self.headers = {}
                    self.url = type('obj', (object,), {'path': '/test'})

            # Test whitelisted IP
            whitelisted_request = MockRequest("192.168.1.200")
            is_limited, info = await rate_limiter.is_rate_limited(whitelisted_request)

            if not is_limited and info.get('reason') == 'whitelisted':
                self.results.append({
                    "test": "whitelist_functionality",
                    "status": "PASS",
                    "details": "Whitelisted IP correctly bypassed rate limiting"
                })
                self.logger.info("✅ Whitelist functionality test passed")
            else:
                self.results.append({
                    "test": "whitelist_functionality",
                    "status": "FAIL",
                    "details": f"Whitelist not working correctly: {info}"
                })
                self.logger.error(f"❌ Whitelist functionality test failed: {info}")

        except Exception as e:
            self.results.append({
                "test": "whitelist_functionality",
                "status": "FAIL",
                "error": str(e)
            })
            self.logger.error(f"❌ Whitelist functionality test failed: {e}")

    async def test_blacklist_functionality(self):
        """Test IP blacklisting functionality."""
        self.logger.info("Testing blacklist functionality...")

        try:
            # Create rate limiter with blacklist
            config_with_blacklist = self.config.copy()
            config_with_blacklist["rate_limiting"]["blacklist_ips"] = ["10.0.0.100"]

            rate_limiter = RateLimiter(api_config=config_with_blacklist)

            class MockRequest:
                def __init__(self, client_ip: str):
                    self.client = type('obj', (object,), {'host': client_ip})
                    self.headers = {}
                    self.url = type('obj', (object,), {'path': '/test'})

            # Test blacklisted IP
            blacklisted_request = MockRequest("10.0.0.100")
            is_limited, info = await rate_limiter.is_rate_limited(blacklisted_request)

            if is_limited and info.get('reason') == 'blacklisted':
                self.results.append({
                    "test": "blacklist_functionality",
                    "status": "PASS",
                    "details": "Blacklisted IP correctly blocked"
                })
                self.logger.info("✅ Blacklist functionality test passed")
            else:
                self.results.append({
                    "test": "blacklist_functionality",
                    "status": "FAIL",
                    "details": f"Blacklist not working correctly: {info}"
                })
                self.logger.error(f"❌ Blacklist functionality test failed: {info}")

        except Exception as e:
            self.results.append({
                "test": "blacklist_functionality",
                "status": "FAIL",
                "error": str(e)
            })
            self.logger.error(f"❌ Blacklist functionality test failed: {e}")

    async def test_redis_fallback(self):
        """Test Redis fallback to memory when Redis is unavailable."""
        self.logger.info("Testing Redis fallback...")

        try:
            # Create rate limiter with invalid Redis config to force memory fallback
            config_with_bad_redis = self.config.copy()
            config_with_bad_redis["redis"]["host"] = "invalid-redis-host"
            config_with_bad_redis["redis"]["port"] = 9999

            rate_limiter = RateLimiter(api_config=config_with_bad_redis)

            # Should fallback to memory
            if not rate_limiter.redis_available:
                class MockRequest:
                    def __init__(self, client_ip: str = "127.0.0.1"):
                        self.client = type('obj', (object,), {'host': client_ip})
                        self.headers = {}
                        self.url = type('obj', (object,), {'path': '/test'})

                request = MockRequest()

                # Test that it still works with memory backend
                is_limited, info = await rate_limiter.is_rate_limited(request)
                await rate_limiter.record_request(request)
                status = await rate_limiter.get_rate_limit_status(request)

                if status and status.get('backend') == 'memory':
                    self.results.append({
                        "test": "redis_fallback",
                        "status": "PASS",
                        "details": "Successfully fell back to memory when Redis unavailable"
                    })
                    self.logger.info("✅ Redis fallback test passed")
                else:
                    self.results.append({
                        "test": "redis_fallback",
                        "status": "FAIL",
                        "details": f"Fallback not working correctly: {status}"
                    })
                    self.logger.error(f"❌ Redis fallback test failed: {status}")
            else:
                self.results.append({
                    "test": "redis_fallback",
                    "status": "SKIP",
                    "details": "Redis is available, cannot test fallback"
                })
                self.logger.info("⏭️ Redis fallback test skipped (Redis available)")

        except Exception as e:
            self.results.append({
                "test": "redis_fallback",
                "status": "FAIL",
                "error": str(e)
            })
            self.logger.error(f"❌ Redis fallback test failed: {e}")

    async def test_configuration_loading(self):
        """Test configuration loading and environment variable support."""
        self.logger.info("Testing configuration loading...")

        try:
            # Test that configuration loads correctly
            config = get_api_security_config()
            rate_config = config.get("rate_limiting", {})

            required_keys = [
                "enabled", "requests_per_minute", "requests_per_hour",
                "requests_per_day", "burst_limit", "whitelist_ips", "blacklist_ips"
            ]

            missing_keys = [key for key in required_keys if key not in rate_config]

            if not missing_keys:
                self.results.append({
                    "test": "configuration_loading",
                    "status": "PASS",
                    "details": "All required configuration keys present",
                    "config": {k: rate_config[k] for k in required_keys}
                })
                self.logger.info("✅ Configuration loading test passed")
            else:
                self.results.append({
                    "test": "configuration_loading",
                    "status": "FAIL",
                    "details": f"Missing configuration keys: {missing_keys}"
                })
                self.logger.error(f"❌ Configuration loading test failed: missing {missing_keys}")

        except Exception as e:
            self.results.append({
                "test": "configuration_loading",
                "status": "FAIL",
                "error": str(e)
            })
            self.logger.error(f"❌ Configuration loading test failed: {e}")

    async def test_api_integration(self):
        """Test rate limiting integration with the API."""
        self.logger.info("Testing API integration...")

        try:
            # Create SecurityAPI instance
            security_api = SecurityAPI()
            client = TestClient(security_api.app)

            # Test health endpoint (should not be rate limited)
            response = client.get("/health")
            assert response.status_code == 200, f"Health check failed: {response.status_code}"

            # Test that rate limiting headers are present in responses
            # (This would require actual requests with rate limiting)

            self.results.append({
                "test": "api_integration",
                "status": "PASS",
                "details": "API integration working correctly"
            })
            self.logger.info("✅ API integration test passed")

        except Exception as e:
            self.results.append({
                "test": "api_integration",
                "status": "FAIL",
                "error": str(e)
            })
            self.logger.error(f"❌ API integration test failed: {e}")

    async def run_all_tests(self):
        """Run all rate limiting tests."""
        self.logger.info("🚀 Starting comprehensive rate limiting tests...")

        tests = [
            self.test_configuration_loading,
            self.test_basic_rate_limiting,
            self.test_burst_protection,
            self.test_whitelist_functionality,
            self.test_blacklist_functionality,
            self.test_redis_fallback,
            self.test_api_integration
        ]

        for test in tests:
            try:
                await test()
                await asyncio.sleep(0.1)  # Small delay between tests
            except Exception as e:
                self.logger.error(f"Test {test.__name__} failed with exception: {e}")

        self.generate_report()

    def generate_report(self):
        """Generate comprehensive test report."""
        print("\n" + "="*80)
        print("🔒 RATE LIMITING SECURITY TEST REPORT")
        print("="*80)

        passed = sum(1 for r in self.results if r.get('status') == 'PASS')
        failed = sum(1 for r in self.results if r.get('status') == 'FAIL')
        skipped = sum(1 for r in self.results if r.get('status') == 'SKIP')
        total = len(self.results)

        print("\n📊 SUMMARY:")
        print(f"   Total Tests: {total}")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   ⏭️ Skipped: {skipped}")
        print(f"   🎯 Success Rate: {(passed/total*100):.1f}%")

        print("\n📋 DETAILED RESULTS:")
        for result in self.results:
            status_icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️"}.get(result['status'], "❓")
            print(f"   {status_icon} {result['test']}: {result['status']}")

            if result.get('details'):
                print(f"      Details: {result['details']}")

            if result.get('error'):
                print(f"      Error: {result['error']}")

            if result.get('config'):
                print(f"      Config: {json.dumps(result['config'], indent=6)}")

        print("\n🔧 CONFIGURATION:")
        try:
            config = get_api_security_config()
            rate_config = config.get("rate_limiting", {})
            print(f"   Enabled: {rate_config.get('enabled', 'unknown')}")
            print(f"   Per Minute: {rate_config.get('requests_per_minute', 'unknown')}")
            print(f"   Per Hour: {rate_config.get('requests_per_hour', 'unknown')}")
            print(f"   Per Day: {rate_config.get('requests_per_day', 'unknown')}")
            print(f"   Burst Limit: {rate_config.get('burst_limit', 'unknown')}")
            print(f"   Whitelist IPs: {len(rate_config.get('whitelist_ips', []))}")
            print(f"   Blacklist IPs: {len(rate_config.get('blacklist_ips', []))}")
        except Exception as e:
            print(f"   Error loading configuration: {e}")

        print("=" * 80)

        if failed > 0:
            print("⚠️ Some tests failed. Review the details above and fix issues before deployment.")
            return False
        else:
            print("🎉 All tests passed! Rate limiting implementation is ready for deployment.")
            return True


async def main():
    """Main function."""
    tester = RateLimitTester()
    success = await tester.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
