# Database Optimization Prompt

You are optimizing database performance and design for scalability, reliability, and
maintainability. Apply systematic analysis to identify bottlenecks and implement comprehensive
optimization strategies across schema design, query performance, and infrastructure.

## Database Optimization Methodology

### 1. Performance Analysis and Profiling

### Query Performance Analysis

````SQL

-- PostgreSQL: Enable query timing and logging
SET log_statement = 'all';
SET log_min_duration_statement = 100; -- Log queries taking >100ms
SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,client=%h ';

-- Analyze slow queries
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 20;

-- Check table and index usage
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation,
    most_common_vals,
    most_common_freqs
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY tablename, attname;

-- Identify unused indexes
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY relname;

```Markdown

### MySQL Performance Analysis

```SQL

-- MySQL: Enable slow query log
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 0.1;  -- Log queries >100ms
SET GLOBAL log_queries_not_using_indexes = 'ON';

-- Analyze query performance
SELECT
    SCHEMA_NAME,
    DIGEST_TEXT,
    COUNT_STAR,
    AVG_TIMER_WAIT/1000000000000 as avg_time_sec,
    SUM_TIMER_WAIT/1000000000000 as total_time_sec,
    SUM_ROWS_EXAMINED,
    SUM_ROWS_SENT
FROM performance_schema.events_statements_summary_by_digest
WHERE SCHEMA_NAME IS NOT NULL
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 20;

-- Check index usage
SELECT
    object_schema,
    object_name,
    index_name,
    count_read,
    count_write,
    count_fetch,
    sum_timer_wait/1000000000000 as total_latency_sec
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE object_schema NOT IN ('mysql', 'performance_schema', 'information_schema')
ORDER BY sum_timer_wait DESC;

```Markdown

### Database Metrics Monitoring

```Python
import psycopg2
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    active_connections: int
    idle_connections: int
    waiting_connections: int
    cache_hit_ratio: float
    avg_query_time: float
    slow_queries_count: int
    deadlocks_count: int
    table_sizes: Dict[str, int]
    index_usage: Dict[str, float]

class DatabaseMonitor:
    """Monitor database performance metrics"""

    def **init**(self, connection_params):
        self.connection_params = connection_params

    def collect_metrics(self) -> DatabaseMetrics:
        """Collect comprehensive database metrics"""
        with psycopg2.connect(**self.connection_params) as conn:
            cursor = conn.cursor()

## Connection metrics

            cursor.execute("""
                SELECT
                    state,
                    COUNT(*)
                FROM pg_stat_activity
                WHERE datname = current_database()
                GROUP BY state
            """)
            connection_stats = dict(cursor.fetchall())

## Cache hit ratio

            cursor.execute("""
                SELECT
                    100.0 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read)) as cache_hit_ratio
                FROM pg_stat_database
                WHERE datname = current_database()
            """)
            cache_hit_ratio = cursor.fetchone()[0] or 0.0

## Query performance

            cursor.execute("""
                SELECT
                    avg(mean_time) as avg_query_time,
                    count(*) FILTER (WHERE mean_time > 1000) as slow_queries
                FROM pg_stat_statements
            """)
            query_stats = cursor.fetchone()

## Table sizes

            cursor.execute("""
                SELECT

                    schemaname||'.'||tablename as table_name,
|---|---|---|
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
|---|---|---|
                FROM pg_tables

                WHERE schemaname = 'public'
                ORDER BY size_bytes DESC
            """)
            table_sizes = dict(cursor.fetchall())

## Index usage

            cursor.execute("""
                SELECT

                    schemaname||'.'||tablename as table_name,
|---|---|---|
                    CASE

                        WHEN seq_scan + idx_scan = 0 THEN 0
                        ELSE 100.0 * idx_scan / (seq_scan + idx_scan)
                    END as index_usage_percent
                FROM pg_stat_user_tables
            """)
            index_usage = dict(cursor.fetchall())

            return DatabaseMetrics(
                active_connections=connection_stats.get('active', 0),
                idle_connections=connection_stats.get('idle', 0),
                waiting_connections=connection_stats.get('waiting', 0),
                cache_hit_ratio=cache_hit_ratio,
                avg_query_time=query_stats[0] or 0.0,
                slow_queries_count=query_stats[1] or 0,
                deadlocks_count=0,  # TODO: Implement deadlock detection
                table_sizes=table_sizes,
                index_usage=index_usage
            )

    def generate_performance_report(self) -> str:
        """Generate comprehensive performance report"""
        metrics = self.collect_metrics()

        report = f"""

## Database Performance Report

Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Connection Status

- Active Connections: {metrics.active_connections}
- Idle Connections: {metrics.idle_connections}
- Waiting Connections: {metrics.waiting_connections}

## Query Performance 2

- Cache Hit Ratio: {metrics.cache_hit_ratio:.2f}%
- Average Query Time: {metrics.avg_query_time:.2f}ms
- Slow Queries (>1s): {metrics.slow_queries_count}

## Table Analysis

Top 10 Largest Tables:
"""

        for table, size in sorted(metrics.table_sizes.items(), key=lambda x: x[1], reverse=True)[:10]:
            size_mb = size / (1024 * 1024)
            report += f"- {table}: {size_mb:.2f} MB\n"

        report += "\nIndex Usage Analysis:\n"
        for table, usage in metrics.index_usage.items():
            status = "✓" if usage > 80 else "⚠️" if usage > 50 else "❌"
            report += f"- {table}: {usage:.1f}% {status}\n"

        return report

```Markdown

### 2. Index Optimization

### Strategic Index Design

```SQL

-- Composite index strategy for common query patterns
CREATE INDEX CONCURRENTLY idx_orders_user_status_date
ON orders (user_id, status, created_at DESC);

-- Partial indexes for common filtered queries
CREATE INDEX CONCURRENTLY idx_orders_pending
ON orders (created_at DESC)
WHERE status = 'pending';

CREATE INDEX CONCURRENTLY idx_users_active_email
ON users (email)
WHERE active = true;

-- Expression indexes for computed queries
CREATE INDEX CONCURRENTLY idx_users_lower_email
ON users (LOWER(email));

CREATE INDEX CONCURRENTLY idx_products_search_vector

ON products USING gin(to_tsvector('english', name || ' ' || description));
|---|---|---|

-- Covering indexes to avoid table lookups
CREATE INDEX CONCURRENTLY idx_orders_covering
ON orders (user_id, status)
INCLUDE (total_amount, created_at);

-- Hash indexes for equality checks (PostgreSQL)
CREATE INDEX CONCURRENTLY idx_sessions_token
ON user_sessions USING hash (session_token);

-- Prefix indexes for large text columns (MySQL)
CREATE INDEX idx_articles_content_prefix ON articles (content(100));

```Markdown

### Index Maintenance and Analysis

```Python
class IndexOptimizer:
    """Analyze and optimize database indexes"""

    def **init**(self, db_connection):
        self.db = db_connection

    def analyze_index_usage(self) -> Dict[str, Dict]:
        """Analyze index usage patterns"""
        cursor = self.db.cursor()

## PostgreSQL index usage analysis

        cursor.execute("""
            SELECT
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch,
                pg_size_pretty(pg_relation_size(indexname::regclass)) as size
            FROM pg_stat_user_indexes
            ORDER BY pg_relation_size(indexname::regclass) DESC
        """)

        indexes = cursor.fetchall()
        analysis = {}

        for index in indexes:
            schema, table, name, scans, reads, fetches, size = index

            analysis[name] = {
                'table': f"{schema}.{table}",
                'usage_score': scans + reads + fetches,
                'size': size,
                'efficiency': fetches / max(reads, 1) if reads > 0 else 0,
                'recommendation': self._get_index_recommendation(scans, reads, fetches)
            }

        return analysis

    def _get_index_recommendation(self, scans, reads, fetches) -> str:
        """Generate index optimization recommendation"""
        if scans == 0 and reads == 0:
            return "REMOVE - Unused index"
        elif scans < 10 and reads < 100:
            return "CONSIDER_REMOVAL - Low usage"
        elif fetches / max(reads, 1) < 0.1:
            return "OPTIMIZE - Low selectivity"
        elif scans > 1000 and fetches / reads > 0.8:
            return "EXCELLENT - High performance"
        else:
            return "MONITOR - Regular usage"

    def find_missing_indexes(self, slow_queries: List[str]) -> List[Dict]:
        """Suggest missing indexes based on slow queries"""
        suggestions = []

        for query in slow_queries:

## Parse query to identify potential index opportunities

            if 'WHERE' in query.upper():

## Extract WHERE conditions

                where_clause = query.upper().split[1]('WHERE').split[0]('ORDER BY')

## Simple pattern matching for common cases

                if 'AND' in where_clause:
                    suggestions.append({
                        'type': 'composite_index',
                        'query': query,
                        'recommendation': 'Consider composite index on multiple WHERE columns'
                    })

                if 'LIKE' in where_clause and '%' not in where_clause.split[1][:10]('LIKE'):
                    suggestions.append({
                        'type': 'prefix_index',
                        'query': query,
                        'recommendation': 'Consider prefix index for LIKE queries'
                    })

        return suggestions

    def optimize_index_maintenance(self) -> List[str]:
        """Generate index maintenance commands"""
        commands = []

## Reindex heavily used indexes

        cursor = self.db.cursor()
        cursor.execute("""
            SELECT indexname
            FROM pg_stat_user_indexes
            WHERE idx_scan > 10000
            ORDER BY idx_scan DESC
        """)

        heavy_indexes = [row[0] for row in cursor.fetchall()]

        for index in heavy_indexes:
            commands.append(f"REINDEX INDEX CONCURRENTLY {index};")

## Update table statistics

        cursor.execute("""
            SELECT schemaname, tablename
            FROM pg_stat_user_tables
            WHERE n_tup_ins + n_tup_upd + n_tup_del > 1000
        """)

        active_tables = cursor.fetchall()
        for schema, table in active_tables:
            commands.append(f"ANALYZE {schema}.{table};")

        return commands

```Markdown

### 3. Query Optimization

### Query Rewriting Strategies

```SQL

-- BEFORE: Inefficient subquery
SELECT u.*,
       (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) as order_count
FROM users u
WHERE u.active = true;

-- AFTER: Efficient JOIN with aggregation
SELECT u.*,
       COALESCE(o.order_count, 0) as order_count
FROM users u
LEFT JOIN (
    SELECT user_id, COUNT(*) as order_count
    FROM orders
    GROUP BY user_id
) o ON u.id = o.user_id
WHERE u.active = true;

-- BEFORE: Inefficient NOT IN with NULL possibility
SELECT * FROM products p
WHERE p.id NOT IN (
    SELECT order_item.product_id
    FROM order_items
    WHERE order_date > '2024-01-01'
);

-- AFTER: Efficient NOT EXISTS or LEFT JOIN
SELECT p.* FROM products p
WHERE NOT EXISTS (
    SELECT 1 FROM order_items oi
    WHERE oi.product_id = p.id
    AND oi.order_date > '2024-01-01'
);

-- Or using LEFT JOIN
SELECT p.* FROM products p
LEFT JOIN order_items oi ON p.id = oi.product_id
    AND oi.order_date > '2024-01-01'
WHERE oi.product_id IS NULL;

-- BEFORE: Inefficient function in WHERE clause
SELECT * FROM orders
WHERE YEAR(created_at) = 2024
AND MONTH(created_at) = 1;

-- AFTER: Sargable (index-friendly) range query
SELECT * FROM orders
WHERE created_at >= '2024-01-01'
AND created_at < '2024-02-01';

-- BEFORE: Inefficient wildcard search
SELECT * FROM products
WHERE name LIKE '%search_term%';

-- AFTER: Full-text search (PostgreSQL)
SELECT *, ts_rank_cd(search_vector, query) as rank
FROM products, to_tsquery('english', 'search_term') query
WHERE search_vector @@ query
ORDER BY rank DESC;

-- AFTER: Full-text search (MySQL)
SELECT *, MATCH(name, description) AGAINST('search_term' IN NATURAL LANGUAGE MODE) as score
FROM products
WHERE MATCH(name, description) AGAINST('search_term' IN NATURAL LANGUAGE MODE)
ORDER BY score DESC;

```Markdown

### Query Optimization Framework

```Python
class QueryOptimizer:
    """Analyze and optimize SQL queries"""

    def **init**(self, db_connection):
        self.db = db_connection

    def analyze_query_plan(self, query: str) -> Dict:
        """Analyze query execution plan"""
        cursor = self.db.cursor()

## Get execution plan with costs

        cursor.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
        plan = cursor.fetchone()[0][0]

        return {
            'total_cost': plan['Plan']['Total Cost'],
            'actual_time': plan['Plan']['Actual Total Time'],
            'rows_returned': plan['Plan']['Actual Rows'],
            'node_type': plan['Plan']['Node Type'],
            'optimization_opportunities': self._identify_optimizations(plan)
        }

    def _identify_optimizations(self, plan: Dict) -> List[str]:
        """Identify optimization opportunities from execution plan"""
        opportunities = []

        def analyze_node(node):

## Check for sequential scans on large tables

            if node.get('Node Type') == 'Seq Scan' and node.get('Actual Rows', 0) > 10000:
                opportunities.append(f"Consider adding index to {node.get('Relation Name', 'table')}")

## Check for expensive sorts

            if node.get('Node Type') == 'Sort' and node.get('Actual Total Time', 0) > 1000:
                opportunities.append("Consider adding index to avoid expensive sort operation")

## Check for nested loop with high row counts

            if (node.get('Node Type') == 'Nested Loop' and
                node.get('Actual Rows', 0) > 1000):
                opportunities.append("Consider hash join instead of nested loop")

## Recursively analyze child nodes

            for child in node.get('Plans', []):
                analyze_node(child)

        analyze_node(plan['Plan'])
        return opportunities

    def suggest_query_rewrites(self, query: str) -> List[Dict]:
        """Suggest query rewrite options"""
        suggestions = []
        query_upper = query.upper()

## Detect common anti-patterns

        if 'SELECT *' in query_upper:
            suggestions.append({
                'type': 'column_selection',
                'message': 'Avoid SELECT * - specify only needed columns',
                'impact': 'Reduces I/O and network traffic'
            })

        if 'NOT IN' in query_upper:
            suggestions.append({
                'type': 'not_in_optimization',
                'message': 'Consider NOT EXISTS instead of NOT IN for better NULL handling',
                'impact': 'Improves performance and correctness'
            })

        if 'LIKE \'%' in query:
            suggestions.append({
                'type': 'full_text_search',
                'message': 'Consider full-text search instead of leading wildcard LIKE',
                'impact': 'Enables index usage for text searches'
            })

        if 'ORDER BY' in query_upper and 'LIMIT' in query_upper:
            suggestions.append({
                'type': 'index_optimization',
                'message': 'Ensure index exists on ORDER BY columns for efficient LIMIT queries',
                'impact': 'Avoids sorting entire result set'
            })

        return suggestions

    def optimize_batch_operations(self, operation_type: str, data: List[Dict]) -> str:
        """Generate optimized batch operation queries"""
        if operation_type == 'insert':

## Use bulk insert instead of individual INSERTs

            if len(data) > 1:
                columns = list(data[0].keys())
                values_list = []

                for row in data:
                    values = [f"'{row[col]}'" if isinstance(row[col], str) else str(row[col])
                             for col in columns]
                    values_list.append(f"({', '.join(values)})")

                return f"""
                INSERT INTO table_name ({', '.join(columns)})
                VALUES {', '.join(values_list)}
                ON CONFLICT (id) DO NOTHING;
                """

        elif operation_type == 'update':

## Use CASE statements for bulk updates

            if len(data) > 10:
                return """
                UPDATE table_name
                SET column1 = CASE
                    WHEN id = ? THEN ?
                    WHEN id = ? THEN ?

                    -- ... more cases
                    ELSE column1
                END
                WHERE id IN (?, ?, ...);
                """

        return "No optimization available for this operation type"

```Markdown

### 4. Schema Design Optimization

### Normalization and Denormalization Strategies

```SQL

-- Properly normalized schema for transactional integrity
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    bio TEXT,
    avatar_url VARCHAR(500),
    birth_date DATE,
    phone VARCHAR(20),
    address_id INTEGER REFERENCES addresses(id)
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    status order_status_enum NOT NULL DEFAULT 'pending',
    total_amount DECIMAL(10,2) NOT NULL,
    tax_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    shipping_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Strategic denormalization for read performance
CREATE TABLE order_summary (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    user_email VARCHAR(255) NOT NULL, -- Denormalized for reporting
    user_name VARCHAR(201) NOT NULL,   -- Denormalized: first_name + last_name
    status order_status_enum NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    item_count INTEGER NOT NULL,       -- Denormalized aggregate
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Maintain data consistency with triggers
    CONSTRAINT order_summary_amount_positive CHECK (total_amount >= 0),
    CONSTRAINT order_summary_items_positive CHECK (item_count > 0)
);

-- Materialized view for complex aggregations
CREATE MATERIALIZED VIEW user_analytics AS
SELECT
    u.id,
    u.email,

    u.first_name || ' ' || u.last_name as full_name,
|---|---|---|
    COUNT(o.id) as total_orders,

    COALESCE(SUM(o.total_amount), 0) as lifetime_value,
    AVG(o.total_amount) as avg_order_value,
    MAX(o.created_at) as last_order_date,
    DATE_PART('day', CURRENT_DATE - MAX(o.created_at)) as days_since_last_order,
    CASE
        WHEN COUNT(o.id) = 0 THEN 'never_ordered'
        WHEN DATE_PART('day', CURRENT_DATE - MAX(o.created_at)) <= 30 THEN 'active'
        WHEN DATE_PART('day', CURRENT_DATE - MAX(o.created_at)) <= 90 THEN 'inactive'
        ELSE 'churned'
    END as customer_segment
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.email, u.first_name, u.last_name;

-- Create index on materialized view
CREATE INDEX idx_user_analytics_segment ON user_analytics (customer_segment);
CREATE INDEX idx_user_analytics_ltv ON user_analytics (lifetime_value DESC);

-- Refresh strategy for materialized view
CREATE OR REPLACE FUNCTION refresh_user_analytics()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY user_analytics;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Auto-refresh trigger (consider frequency based on business needs)
CREATE TRIGGER trigger_refresh_user_analytics
    AFTER INSERT OR UPDATE OR DELETE ON orders
    FOR EACH STATEMENT
    EXECUTE FUNCTION refresh_user_analytics();

```Markdown

### Data Type Optimization

```SQL

-- Optimized data types for storage and performance
CREATE TABLE optimized_products (
    id INTEGER NOT NULL,                    -- Use INTEGER instead of BIGINT if range sufficient
    sku VARCHAR(50) NOT NULL,              -- Exact size instead of TEXT
    name VARCHAR(200) NOT NULL,            -- Reasonable limit for product names
    description TEXT,                       -- Variable length for long content
    price DECIMAL(8,2) NOT NULL,           -- Sufficient precision for currency
    weight_grams SMALLINT,                 -- SMALLINT for weights under 32kg
    is_active BOOLEAN NOT NULL DEFAULT true,
    category_id SMALLINT NOT NULL,         -- SMALLINT for reasonable category count
    brand_id SMALLINT,                     -- SMALLINT for brand references
    created_at TIMESTAMP(0) NOT NULL,      -- Precision to seconds only
    updated_at TIMESTAMP(0) NOT NULL,

    -- Constraints for data integrity
    CONSTRAINT pk_products PRIMARY KEY (id),
    CONSTRAINT uk_products_sku UNIQUE (sku),
    CONSTRAINT ck_products_price_positive CHECK (price > 0),
    CONSTRAINT ck_products_weight_positive CHECK (weight_grams > 0),

    -- Foreign key constraints
    CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES categories(id),
    CONSTRAINT fk_products_brand FOREIGN KEY (brand_id) REFERENCES brands(id)
);

-- Enum types for better performance and data integrity
CREATE TYPE order_status AS ENUM ('pending', 'processing', 'shipped', 'delivered', 'cancelled');
CREATE TYPE payment_method AS ENUM ('credit_card', 'debit_card', 'paypal', 'bank_transfer', 'cash');
CREATE TYPE priority_level AS ENUM ('low', 'medium', 'high', 'urgent');

-- Use enums in table definitions
CREATE TABLE orders_optimized (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    status order_status NOT NULL DEFAULT 'pending',
    payment_method payment_method NOT NULL,
    priority priority_level NOT NULL DEFAULT 'medium',
    total_amount DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP(0) NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- JSON/JSONB for flexible schema parts (PostgreSQL)
CREATE TABLE product_attributes (
    product_id INTEGER NOT NULL REFERENCES products(id),
    attributes JSONB NOT NULL,

    -- Index on JSON fields for fast queries
    CONSTRAINT pk_product_attributes PRIMARY KEY (product_id)
);

-- Create GIN index for JSONB queries
CREATE INDEX idx_product_attributes_gin ON product_attributes USING gin (attributes);

-- Example queries on JSON data
-- Find products with specific attribute
SELECT p.*, pa.attributes
FROM products p
JOIN product_attributes pa ON p.id = pa.product_id
WHERE pa.attributes @> '{"color": "red"}';

-- Find products with attribute existence
SELECT p.*, pa.attributes
FROM products p
JOIN product_attributes pa ON p.id = pa.product_id
WHERE pa.attributes ? 'warranty_years';

```Markdown

### 5. Partitioning Strategies

### Table Partitioning Implementation

```SQL

-- Range partitioning by date (PostgreSQL)
CREATE TABLE orders_partitioned (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (order_date);

-- Create monthly partitions
CREATE TABLE orders_2024_01 PARTITION OF orders_partitioned
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE orders_2024_02 PARTITION OF orders_partitioned
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

CREATE TABLE orders_2024_03 PARTITION OF orders_partitioned
FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

-- Create default partition for future dates
CREATE TABLE orders_default PARTITION OF orders_partitioned DEFAULT;

-- Hash partitioning for even distribution
CREATE TABLE user_sessions_partitioned (
    id BIGINT NOT NULL,
    user_id INTEGER NOT NULL,
    session_token VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) PARTITION BY HASH (user_id);

-- Create hash partitions
CREATE TABLE user_sessions_p0 PARTITION OF user_sessions_partitioned
FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE user_sessions_p1 PARTITION OF user_sessions_partitioned
FOR VALUES WITH (MODULUS 4, REMAINDER 1);

CREATE TABLE user_sessions_p2 PARTITION OF user_sessions_partitioned
FOR VALUES WITH (MODULUS 4, REMAINDER 2);

CREATE TABLE user_sessions_p3 PARTITION OF user_sessions_partitioned
FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- List partitioning by category
CREATE TABLE products_partitioned (
    id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(8,2) NOT NULL
) PARTITION BY LIST (category_id);

CREATE TABLE products_electronics PARTITION OF products_partitioned
FOR VALUES IN (1, 2, 3);

CREATE TABLE products_clothing PARTITION OF products_partitioned
FOR VALUES IN (4, 5, 6);

CREATE TABLE products_books PARTITION OF products_partitioned
FOR VALUES IN (7, 8);

```Markdown

### Automated Partition Management

```Python
import psycopg2
from datetime import datetime, timedelta
from typing import List

class PartitionManager:
    """Manage database partitions automatically"""

    def **init**(self, connection_params):
        self.connection_params = connection_params

    def create_monthly_partitions(self, table_name: str, months_ahead: int = 3) -> List[str]:
        """Create monthly partitions for the next N months"""
        commands = []
        current_date = datetime.now().replace(day=1)

        with psycopg2.connect(**self.connection_params) as conn:
            cursor = conn.cursor()

            for i in range(months_ahead):
                partition_date = current_date + timedelta(days=32*i)
                partition_date = partition_date.replace(day=1)
                next_month = (partition_date + timedelta(days=32)).replace(day=1)

                partition_name = f"{table_name}_{partition_date.strftime('%Y_%m')}"

## Check if partition already exists

                cursor.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = %s
                    )
                """, (partition_name,))

                if not cursor.fetchone()[0]:
                    command = f"""
                    CREATE TABLE {partition_name} PARTITION OF {table_name}
                    FOR VALUES FROM ('{partition_date.strftime('%Y-%m-%d')}')
                                TO ('{next_month.strftime('%Y-%m-%d')}')
                    """
                    commands.append(command)
                    cursor.execute(command)

            conn.commit()

        return commands

    def drop_old_partitions(self, table_name: str, retain_months: int = 12) -> List[str]:
        """Drop partitions older than retain_months"""
        commands = []
        cutoff_date = datetime.now() - timedelta(days=30 * retain_months)

        with psycopg2.connect(**self.connection_params) as conn:
            cursor = conn.cursor()

## Find old partitions

            cursor.execute("""
                SELECT schemaname, tablename
                FROM pg_tables
                WHERE tablename LIKE %s
                AND tablename < %s
            """, (f"{table_name}_%", f"{table_name}_{cutoff_date.strftime('%Y_%m')}"))

            old_partitions = cursor.fetchall()

            for schema, partition_name in old_partitions:

## Optionally backup before dropping

                backup_command = f"pg_dump -t {schema}.{partition_name} > {partition_name}_backup.SQL"
                commands.append(f"-- Backup: {backup_command}")

## Drop partition

                drop_command = f"DROP TABLE {schema}.{partition_name}"
                commands.append(drop_command)
                cursor.execute(drop_command)

            conn.commit()

        return commands

    def analyze_partition_usage(self, table_name: str) -> Dict[str, Dict]:
        """Analyze partition usage and performance"""
        with psycopg2.connect(**self.connection_params) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,

                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
|---|---|---|
                    n_tup_ins,

                    n_tup_upd,
                    n_tup_del,
                    n_live_tup,
                    n_dead_tup
                FROM pg_stat_user_tables
                WHERE tablename LIKE %s
                ORDER BY tablename
            """, (f"{table_name}_%",))

            partitions = {}
            for row in cursor.fetchall():
                schema, name, size, ins, upd, del_, live, dead = row
                partitions[name] = {
                    'size': size,
                    'inserts': ins,
                    'updates': upd,
                    'deletes': del_,
                    'live_tuples': live,
                    'dead_tuples': dead,
                    'health_score': live / (live + dead) if (live + dead) > 0 else 1.0
                }

            return partitions

## Automated partition maintenance script

def maintain_partitions():
    """Daily partition maintenance routine"""
    connection_params = {
        'host': 'localhost',
        'database': 'myapp',
        'user': 'postgres',
        'password': 'password'
    }

    manager = PartitionManager(connection_params)

## Create future partitions

    future_partitions = manager.create_monthly_partitions('orders_partitioned', months_ahead=3)
    print(f"Created {len(future_partitions)} future partitions")

## Drop old partitions (keep 12 months)

    dropped_partitions = manager.drop_old_partitions('orders_partitioned', retain_months=12)
    print(f"Dropped {len(dropped_partitions)} old partitions")

## Analyze partition health

    partition_stats = manager.analyze_partition_usage('orders_partitioned')
    for partition, stats in partition_stats.items():
        if stats['health_score'] < 0.8:
            print(f"⚠️  Partition {partition} needs maintenance (health: {stats['health_score']:.2f})")
        print(f"📊 {partition}: {stats['size']}, {stats['live_tuples']} live rows")

if **name** == '**main**':
    maintain_partitions()

```Markdown

## 6. Connection Pooling and Caching

### Connection Pool Configuration

```Python

## Advanced connection pooling with PostgreSQL

import psycopg2.pool
from contextlib import contextmanager
from typing import Optional
import threading
import time

class DatabaseConnectionPool:
    """Advanced database connection pool with monitoring"""

    def **init**(self, connection_params, min_connections=5, max_connections=20):
        self.connection_params = connection_params
        self.min_connections = min_connections
        self.max_connections = max_connections

## Create connection pool

        self.pool = psycopg2.pool.ThreadedConnectionPool(
            min_connections,
            max_connections,

            **connection_params
        )

## Monitoring

        self.active_connections = 0
        self.total_requests = 0
        self.failed_requests = 0
        self.lock = threading.Lock()

    @contextmanager
    def get_connection(self, timeout=30):
        """Get connection from pool with timeout and monitoring"""
        connection = None
        start_time = time.time()

        try:
            with self.lock:
                self.total_requests += 1

## Get connection from pool

            connection = self.pool.getconn()

            if connection is None:
                raise Exception("Failed to get connection from pool")

            with self.lock:
                self.active_connections += 1

## Test connection health

            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()

            yield connection

        except Exception as e:
            with self.lock:
                self.failed_requests += 1
            raise e

        finally:
            if connection:
                with self.lock:
                    self.active_connections -= 1

## Return connection to pool

                self.pool.putconn(connection)

    def get_pool_stats(self) -> dict:
        """Get connection pool statistics"""
        return {
            'active_connections': self.active_connections,
            'total_requests': self.total_requests,
            'failed_requests': self.failed_requests,
            'success_rate': (self.total_requests - self.failed_requests) / max(self.total_requests, 1),
            'pool_size': len(self.pool._pool),
            'min_connections': self.min_connections,
            'max_connections': self.max_connections
        }

    def close_all_connections(self):
        """Close all connections in pool"""
        self.pool.closeall()

## Database caching layer

import redis
import JSON
import hashlib
from functools import wraps

class DatabaseCache:
    """Database query caching with Redis"""

    def **init**(self, redis_client, default_ttl=300):
        self.redis = redis_client
        self.default_ttl = default_ttl

    def cache_query(self, ttl=None):
        """Decorator to cache database query results"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):

## Generate cache key from function name and parameters

                cache_key = self._generate_cache_key(func.**name**, args, kwargs)

## Try to get from cache

                cached_result = self.redis.get(cache_key)
                if cached_result:
                    return JSON.loads(cached_result)

## Execute query

                result = func(*args, **kwargs)

## Cache result

                ttl_seconds = ttl or self.default_ttl
                self.redis.setex(
                    cache_key,
                    ttl_seconds,
                    JSON.dumps(result, default=str)
                )

                return result
            return wrapper
        return decorator

    def _generate_cache_key(self, func_name, args, kwargs) -> str:
        """Generate consistent cache key"""
        key_data = {
            'function': func_name,
            'args': args,
            'kwargs': kwargs
        }
        key_string = JSON.dumps(key_data, sort_keys=True, default=str)
        return f"db_cache:{hashlib.md5(key_string.encode()).hexdigest()}"

    def invalidate_pattern(self, pattern: str):
        """Invalidate all cache keys matching pattern"""
        keys = self.redis.keys(f"db_cache:{pattern}*")
        if keys:
            self.redis.delete(*keys)

    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        info = self.redis.info()
        return {
            'used_memory': info.get('used_memory_human'),
            'keyspace_hits': info.get('keyspace_hits', 0),
            'keyspace_misses': info.get('keyspace_misses', 0),
            'hit_rate': info.get('keyspace_hits', 0) / max(
                info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1
            ),
            'connected_clients': info.get('connected_clients', 0)
        }

## Usage example

connection_pool = DatabaseConnectionPool({
    'host': 'localhost',
    'database': 'myapp',
    'user': 'postgres',
    'password': 'password'
})

redis_client = redis.Redis(host='localhost', port=6379, db=0)
cache = DatabaseCache(redis_client)

@cache.cache_query(ttl=600)  # Cache for 10 minutes
def get_user_orders(user_id, status=None):
    """Get user orders with caching"""
    with connection_pool.get_connection() as conn:
        cursor = conn.cursor()

        if status:
            cursor.execute(
                "SELECT * FROM orders WHERE user_id = %s AND status = %s",
                (user_id, status)
            )
        else:
            cursor.execute(
                "SELECT * FROM orders WHERE user_id = %s",
                (user_id,)
            )

        return cursor.fetchall()

## Cache invalidation on data changes

def update_order_status(order_id, new_status):
    """Update order status and invalidate related cache"""
    with connection_pool.get_connection() as conn:
        cursor = conn.cursor()

## Get user_id for cache invalidation

        cursor.execute("SELECT user_id FROM orders WHERE id = %s", (order_id,))
        user_id = cursor.fetchone()[0]

## Update order

        cursor.execute(
            "UPDATE orders SET status = %s WHERE id = %s",
            (new_status, order_id)
        )
        conn.commit()

## Invalidate cache

        cache.invalidate_pattern(f"_user_id_{user_id}*")

```Markdown

## 7. Database Optimization Checklist

### Performance Optimization Checklist

- [ ] **Query Analysis**
- [ ] Identify slow queries (>100ms)
- [ ] Analyze execution plans for all critical queries
- [ ] Profile query performance under load
- [ ] Monitor query frequency and resource usage
- [ ] **Index Optimization**
- [ ] Create indexes for all WHERE clause columns
- [ ] Add composite indexes for multi-column filters
- [ ] Implement covering indexes to avoid table lookups
- [ ] Remove unused indexes to reduce write overhead
- [ ] Monitor index usage statistics
- [ ] **Schema Design**
- [ ] Normalize to eliminate data redundancy
- [ ] Strategically denormalize for read performance
- [ ] Use appropriate data types for storage efficiency
- [ ] Implement proper constraints for data integrity
- [ ] Consider partitioning for large tables
- [ ] **Connection Management**
- [ ] Implement connection pooling
- [ ] Configure optimal pool sizes
- [ ] Monitor connection usage patterns
- [ ] Set appropriate connection timeouts
- [ ] **Caching Strategy**
- [ ] Implement query result caching
- [ ] Cache frequently accessed reference data
- [ ] Set appropriate cache TTLs
- [ ] Implement cache invalidation strategies
- [ ] **Maintenance Tasks**
- [ ] Regular VACUUM and ANALYZE operations
- [ ] Monitor table bloat and fragmentation
- [ ] Reindex heavily used indexes
- [ ] Update table statistics regularly
- [ ] Archive old data

Remember: Database optimization is an iterative process.
Start with the biggest bottlenecks, measure the impact of changes, and continuously monitor performance
Always test optimizations in a staging environment before applying to production.
````
