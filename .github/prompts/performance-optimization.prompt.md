# Performance Optimization Prompt

You are conducting a comprehensive performance optimization review. Follow this systematic approach to identify bottlenecks and optimization opportunities.

## Performance Optimization Framework

### 1. Baseline Measurement

Before making any optimizations, establish current performance baselines:

```bash

# Example performance measurement commands

ab -n 1000 -c 10 http://localhost:3000/api/users
wrk -t12 -c400 -d30s http://localhost:3000/api/products
siege -c 25 -t 1m http://localhost:3000
```markdown

#### Key Metrics to Measure

- [ ] **Response Time**: 50th, 95th, 99th percentiles
- [ ] **Throughput**: Requests per second under normal load
- [ ] **Resource Utilization**: CPU, memory, disk, network usage
- [ ] **Error Rate**: Percentage of failed requests
- [ ] **Concurrency**: Maximum concurrent users supported

### 2. Performance Profiling

Identify specific bottlenecks using profiling tools:

#### Application Profiling

```python
# Example: Python performance profiling

import cProfile
import pstats

def profile_function(func, *args, **kwargs):
    profiler = cProfile.Profile()
    profiler.enable()

    result = func(*args, **kwargs)

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 slowest functions

    return result
```markdown

#### Database Profiling

```sql
-- PostgreSQL: Enable query logging
SET log_statement = 'all';
SET log_min_duration_statement = 100; -- Log queries >100ms

-- MySQL: Enable slow query log
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 0.1; -- Log queries >100ms
```markdown

### 3. Database Optimization

#### Query Optimization Checklist

- [ ] **Indexes**: Proper indexes for WHERE, JOIN, ORDER BY clauses
- [ ] **Query Structure**: Eliminate N+1 queries and unnecessary JOINs
- [ ] **Data Types**: Appropriate data types for columns
- [ ] **Query Plans**: Analyze execution plans for expensive operations
- [ ] **Statistics**: Updated table statistics for query optimizer

#### Example: Query Optimization

```sql
-- Before: Inefficient query
SELECT u.*, p.title, c.name
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
LEFT JOIN categories c ON p.category_id = c.id
WHERE u.created_at > '2024-01-01'
ORDER BY u.created_at DESC;

-- After: Optimized query with proper indexing
-- Index: CREATE INDEX idx_users_created_at ON users(created_at);
-- Index: CREATE INDEX idx_posts_user_category ON posts(user_id, category_id);

SELECT u.id, u.name, u.email, u.created_at,
       p.title, c.name as category_name
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
LEFT JOIN categories c ON p.category_id = c.id
WHERE u.created_at > '2024-01-01'
ORDER BY u.created_at DESC
LIMIT 50; -- Always limit large result sets
```markdown

#### Database Performance Targets

- **Query Response Time**: <50ms average, <100ms for complex queries
- **Connection Pool**: Maintain 80% utilization, max 100 connections
- **Cache Hit Rate**: >95% for frequently accessed data
- **Index Usage**: >90% of queries should use indexes effectively

### 4. Caching Strategy Implementation

#### Multi-Level Caching

```python
# Example: Comprehensive caching implementation

import redis
import memcache
from functools import wraps

class CacheManager:
    def __init__(self):
        self.l1_cache = {}  # In-memory cache
        self.l2_cache = redis.Redis(host='localhost', port=6379, db=0)
        self.l3_cache = memcache.Client(['127.0.0.1:11211'])

    def cache_with_fallback(self, key, fetch_func, ttl=3600):
        """Multi-level cache with automatic fallback"""

        # L1 Cache (fastest - in-memory)
        if key in self.l1_cache:
            return self.l1_cache[key]

        # L2 Cache (fast - Redis)
        try:
            value = self.l2_cache.get(key)
            if value:
                self.l1_cache[key] = value  # Populate L1
                return value
        except Exception:
            pass

        # L3 Cache (medium - Memcached)
        try:
            value = self.l3_cache.get(key)
            if value:
                self.l1_cache[key] = value
                self.l2_cache.setex(key, ttl, value)
                return value
        except Exception:
            pass

        # Cache miss - fetch from source
        value = fetch_func()

        # Populate all cache levels
        self.l1_cache[key] = value
        try:
            self.l2_cache.setex(key, ttl, value)
            self.l3_cache.set(key, value, time=ttl)
        except Exception:
            pass

        return value

def cached(ttl=3600):
    """Decorator for automatic caching"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cache_manager = CacheManager()
            return cache_manager.cache_with_fallback(
                cache_key,
                lambda: func(*args, **kwargs),
                ttl
            )
        return wrapper
    return decorator

# Usage example

@cached(ttl=1800)  # Cache for 30 minutes
def get_user_profile(user_id):
    # Expensive database operation
    return database.get_user_with_preferences(user_id)
```markdown

#### Caching Performance Targets

- **Hit Rate**: >95% for frequently accessed data
- **Response Time**: <1ms for in-memory, <5ms for distributed cache
- **Memory Usage**: <2GB per application server
- **Cache Invalidation**: Real-time updates with <100ms propagation

### 5. Frontend Performance Optimization

#### Asset Optimization

```javascript
// Example: Webpack optimization configuration
module.exports = {
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          priority: 10,
          enforce: true,
        },
        common: {
          name: 'common',
          minChunks: 2,
          priority: 5,
          reuseExistingChunk: true,
        },
      },
    },
    usedExports: true,
    sideEffects: false,
  },
  plugins: [
    new CompressionPlugin({
      algorithm: 'gzip',
      test: /\.(js|css|html|svg)$/,
      threshold: 8192,
      minRatio: 0.8,
    }),
  ],
};
```markdown

#### Performance Monitoring

```javascript
// Example: Client-side performance monitoring
class PerformanceMonitor {
  constructor() {
    this.metrics = {};
    this.initializeObservers();
  }

  initializeObservers() {
    // Core Web Vitals monitoring
    if ('PerformanceObserver' in window) {
      // Largest Contentful Paint
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        this.metrics.lcp = lastEntry.startTime;
        this.sendMetric('lcp', lastEntry.startTime);
      }).observe({ entryTypes: ['largest-contentful-paint'] });

      // First Input Delay
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          this.metrics.fid = entry.processingStart - entry.startTime;
          this.sendMetric('fid', entry.processingStart - entry.startTime);
        });
      }).observe({ entryTypes: ['first-input'] });

      // Cumulative Layout Shift
      let clsValue = 0;
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
          }
        });
        this.metrics.cls = clsValue;
        this.sendMetric('cls', clsValue);
      }).observe({ entryTypes: ['layout-shift'] });
    }
  }

  measureResourceTiming() {
    const resources = performance.getEntriesByType('resource');
    const slowResources = resources.filter(resource =>
      resource.duration > 1000 // Resources taking >1 second
    );

    slowResources.forEach(resource => {
      console.warn(`Slow resource: ${resource.name} (${resource.duration}ms)`);
    });
  }

  sendMetric(name, value) {
    // Send to analytics service
    fetch('/api/metrics', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ metric: name, value, timestamp: Date.now() })
    });
  }
}
```markdown

#### Frontend Performance Targets

- **First Contentful Paint**: <1.5 seconds
- **Largest Contentful Paint**: <2.5 seconds
- **First Input Delay**: <100ms
- **Cumulative Layout Shift**: <0.1
- **Bundle Size**: Main bundle <250KB, total assets <1MB

### 6. API Performance Optimization

#### Request Optimization

```python
# Example: Efficient API implementation with batching

from dataclasses import dataclass
from typing import List, Dict, Any
import asyncio

@dataclass
class BatchRequest:
    operation: str
    params: Dict[str, Any]

class APIOptimizer:
    def __init__(self):
        self.batch_requests = []
        self.batch_timeout = 50  # 50ms batching window

    async def batch_execute(self, requests: List[BatchRequest]):
        """Execute multiple requests in a single batch"""

        # Group requests by operation type
        grouped_requests = {}
        for req in requests:
            if req.operation not in grouped_requests:
                grouped_requests[req.operation] = []
            grouped_requests[req.operation].append(req.params)

        # Execute batched operations
        results = {}
        for operation, params_list in grouped_requests.items():
            if operation == 'get_users':
                user_ids = [p['user_id'] for p in params_list]
                users = await self.get_users_batch(user_ids)
                results['get_users'] = users
            elif operation == 'get_posts':
                post_ids = [p['post_id'] for p in params_list]
                posts = await self.get_posts_batch(post_ids)
                results['get_posts'] = posts

        return results

    async def get_users_batch(self, user_ids: List[int]):
        """Efficient batch user retrieval"""
        # Single query instead of N queries
        query = """
        SELECT id, name, email, created_at
        FROM users
        WHERE id = ANY($1)
        """
        return await database.fetch_all(query, user_ids)

# Usage: API endpoint with automatic batching

@app.post("/api/batch")
async def batch_api(requests: List[BatchRequest]):
    optimizer = APIOptimizer()
    results = await optimizer.batch_execute(requests)
    return results
```markdown

#### API Performance Targets

- **Response Time**: 95th percentile <200ms
- **Throughput**: >1000 requests/second per server
- **Error Rate**: <0.1% for all endpoints
- **Payload Size**: Responses <100KB, use pagination for larger datasets

### 7. Infrastructure Optimization

#### Auto-scaling Configuration

```yaml
# Example: Kubernetes horizontal pod autoscaler

apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: app-deployment
  minReplicas: 3
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```markdown

### 8. Performance Testing Strategy

#### Load Testing Implementation

```python
# Example: Comprehensive load testing with Locust

from locust import HttpUser, task, between
import random

class PerformanceTestUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Authenticate user
        response = self.client.post("/auth/login", json={
            "username": f"testuser_{random.randint(1, 1000)}",
            "password": "testpass123"
        })
        self.token = response.json().get("access_token")
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    @task(10)
    def browse_products(self):
        """Simulate product browsing - high frequency"""
        with self.client.get("/api/products",
                           params={"page": random.randint(1, 10), "limit": 20},
                           catch_response=True) as response:
            if response.elapsed.total_seconds() > 0.5:
                response.failure(f"Request took {response.elapsed.total_seconds()}s")
            if response.status_code != 200:
                response.failure(f"Status code: {response.status_code}")

    @task(5)
    def search_products(self):
        """Simulate product search - medium frequency"""
        search_terms = ["laptop", "phone", "tablet", "headphones", "camera"]
        term = random.choice(search_terms)
        self.client.get(f"/api/products/search?q={term}")

    @task(3)
    def view_product_details(self):
        """Simulate product detail viewing - medium frequency"""
        product_id = random.randint(1, 1000)
        self.client.get(f"/api/products/{product_id}")

    @task(1)
    def add_to_cart(self):
        """Simulate add to cart - low frequency"""
        product_id = random.randint(1, 1000)
        quantity = random.randint(1, 3)
        self.client.post("/api/cart/add", json={
            "product_id": product_id,
            "quantity": quantity
        })

    @task(1)
    def checkout_simulation(self):
        """Simulate checkout process - low frequency"""
        # View cart
        self.client.get("/api/cart")

        # Proceed to checkout
        self.client.post("/api/checkout/initiate")

        # Simulate payment (mock)
        self.client.post("/api/checkout/payment", json={
            "payment_method": "credit_card",
            "amount": random.uniform(10.0, 500.0)
        })
```markdown

### 9. Performance Monitoring Dashboard

#### Key Performance Indicators

```json
{
  "performance_dashboard": {
    "response_times": {
      "api_p50": "120ms",
      "api_p95": "280ms",
      "api_p99": "450ms",
      "page_load_p95": "2.1s"
    },
    "throughput": {
      "requests_per_second": 2800,
      "concurrent_users": 1200,
      "peak_rps": 4500
    },
    "resource_utilization": {
      "cpu_average": "68%",
      "memory_usage": "5.2GB / 8GB",
      "disk_io": "42%",
      "network_bandwidth": "156 Mbps"
    },
    "cache_performance": {
      "l1_hit_rate": "97.2%",
      "l2_hit_rate": "94.8%",
      "cache_response_time": "2.1ms"
    },
    "database_performance": {
      "query_p95": "85ms",
      "connection_pool": "75/100",
      "slow_queries": 3,
      "cache_hit_rate": "96.1%"
    },
    "error_rates": {
      "4xx_errors": "0.12%",
      "5xx_errors": "0.03%",
      "timeout_errors": "0.01%"
    }
  }
}
```markdown

### 10. Performance Optimization Report Template

```markdown

# Performance Optimization Report - [System Name]


## Executive Summary

- **Review Date**: [Date]
- **Baseline Performance**: [Current metrics]
- **Optimization Target**: [Performance goals]
- **Overall Assessment**: [Performance rating]

## Current Performance Metrics

### Response Times
- API 95th percentile: XXXms (Target: <200ms)
- Page load 95th percentile: X.Xs (Target: <2.5s)
- Database query average: XXms (Target: <50ms)

### Throughput

- Requests per second: XXXX (Target: >1000)
- Concurrent users: XXXX (Target: >500)
- Error rate: X.XX% (Target: <0.1%)

## Identified Bottlenecks

### Critical Issues
1. **[Issue 1]**: [Description and impact]
2. **[Issue 2]**: [Description and impact]

### Performance Opportunities

1. **[Opportunity 1]**: [Description and potential improvement]
2. **[Opportunity 2]**: [Description and potential improvement]

## Optimization Recommendations

### Immediate Actions (0-1 week)
1. [High-impact, low-effort optimizations]
2. [Critical performance fixes]

### Short-term Actions (1-4 weeks)

1. [Medium-impact optimizations]
2. [Infrastructure improvements]

### Long-term Actions (1-3 months)

1. [Architectural improvements]
2. [Technology upgrades]

## Expected Performance Improvements

- Response time improvement: XX% faster
- Throughput increase: XX% more requests/second
- Resource efficiency: XX% reduction in server costs
- User experience: XX% improvement in Core Web Vitals

## Implementation Plan

1. **Phase 1**: [Immediate optimizations]
2. **Phase 2**: [Short-term improvements]
3. **Phase 3**: [Long-term architectural changes]

## Success Metrics

- Target response times achieved
- Throughput goals met
- Resource utilization optimized
- User satisfaction improved
```markdown

Remember: Performance optimization is an iterative process. Always measure before and after changes, and focus on optimizations that provide the biggest impact for your specific use case and user patterns.
