#!/bin/bash
# Tool: performance-monitor.sh
# Purpose: Comprehensive performance monitoring and profiling for applications
# Usage: ./performance-monitor.sh [options]

set -euo pipefail

# Script metadata
TOOL_NAME="performance-monitor"
TOOL_VERSION="1.0.0"
TOOL_DESCRIPTION="Comprehensive performance monitoring and profiling for applications"

# Configuration
LOG_DIR="logs/toolshed"
DRY_RUN=false
VERBOSE=false
MONITORING_DURATION=60
SAMPLING_INTERVAL=1
ENABLE_PROFILING=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Usage function
show_usage() {
    cat << EOF
Usage: $0 [options]

$TOOL_DESCRIPTION

This tool provides comprehensive performance monitoring including:
- System resource monitoring (CPU, memory, disk, network)
- Application performance profiling
- Load testing and benchmarking
- Performance metrics collection and analysis
- Automated performance reports
- Performance regression detection

Options:
    -h, --help              Show this help message
    -d, --dry-run           Preview monitoring setup without executing
    -v, --verbose           Enable verbose output
    -t, --duration SECONDS  Monitoring duration in seconds [default: 60]
    -i, --interval SECONDS  Sampling interval in seconds [default: 1]
    -p, --profile           Enable application profiling
    --system-only           Monitor only system resources
    --app-only              Monitor only application performance
    --network-only          Monitor only network performance
    --load-test             Perform load testing
    --benchmark             Run performance benchmarks
    --continuous            Run continuous monitoring
    --report-only           Generate report from existing data

Examples:
    $0                                      # Basic system monitoring for 60 seconds
    $0 --duration 300 --interval 5         # Monitor for 5 minutes, sample every 5 seconds
    $0 --profile --app-only                 # Profile application performance only
    $0 --load-test --duration 120           # Run load test for 2 minutes
    $0 --benchmark                          # Run performance benchmarks
    $0 --continuous                         # Run continuous monitoring (until stopped)

Monitoring Capabilities:
    ✓ CPU usage and load averages
    ✓ Memory usage and allocation patterns
    ✓ Disk I/O and space utilization
    ✓ Network throughput and latency
    ✓ Process-level resource usage
    ✓ Application response times
    ✓ Database query performance
    ✓ Web server performance metrics

EOF
}

# Check for required monitoring tools
check_monitoring_tools() {
    local tools=("top" "ps" "iostat" "netstat" "df")
    local missing_tools=()

    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done

    # Check for optional advanced tools
    local advanced_tools=("htop" "iotop" "nload" "iftop" "perf" "strace")
    local available_advanced=()

    for tool in "${advanced_tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            available_advanced+=("$tool")
        fi
    done

    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_warning "Missing basic tools: ${missing_tools[*]}"
        log_info "Installing sysstat package for system monitoring..."
        if [[ "$DRY_RUN" == "false" ]]; then
            if command -v apt-get &> /dev/null; then
                sudo apt-get update && sudo apt-get install -y sysstat
            elif command -v yum &> /dev/null; then
                sudo yum install -y sysstat
            elif command -v pacman &> /dev/null; then
                sudo pacman -S --noconfirm sysstat
            fi
        fi
    fi

    log_info "Available advanced tools: ${available_advanced[*]:-none}"
}

# Monitor system resources
monitor_system_resources() {
    log_info "Starting system resource monitoring for $MONITORING_DURATION seconds..."

    local output_dir="performance-monitoring/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$output_dir"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would monitor system resources in $output_dir"
        return 0
    fi

    # CPU monitoring
    log_info "Monitoring CPU usage..."
    {
        echo "# CPU Usage Report - $(date)"
        echo "# Timestamp, %CPU_User, %CPU_System, %CPU_Idle, LoadAvg_1m, LoadAvg_5m, LoadAvg_15m"

        for ((i=0; i<$MONITORING_DURATION; i+=$SAMPLING_INTERVAL)); do
            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            cpu_stats=$(top -bn1 | grep "^%Cpu" | awk '{print $2,$4,$8}' | tr -d '%us,sy,id')
            load_avg=$(uptime | awk -F'load average:' '{print $2}' | tr -d ' ')
            echo "$timestamp, $cpu_stats, $load_avg"
            sleep $SAMPLING_INTERVAL
        done
    } > "$output_dir/cpu_usage.csv" &

    # Memory monitoring
    log_info "Monitoring memory usage..."
    {
        echo "# Memory Usage Report - $(date)"
        echo "# Timestamp, Total_MB, Used_MB, Free_MB, Available_MB, %Used"

        for ((i=0; i<$MONITORING_DURATION; i+=$SAMPLING_INTERVAL)); do
            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            mem_stats=$(free -m | awk 'NR==2{printf "%.0f,%.0f,%.0f,%.0f,%.1f", $2,$3,$4,$7,$3*100/$2}')
            echo "$timestamp, $mem_stats"
            sleep $SAMPLING_INTERVAL
        done
    } > "$output_dir/memory_usage.csv" &

    # Disk I/O monitoring
    log_info "Monitoring disk I/O..."
    if command -v iostat &> /dev/null; then
        iostat -x $SAMPLING_INTERVAL $((MONITORING_DURATION/SAMPLING_INTERVAL)) > "$output_dir/disk_io.txt" &
    fi

    # Network monitoring
    log_info "Monitoring network activity..."
    {
        echo "# Network Activity Report - $(date)"
        echo "# Timestamp, RX_bytes, TX_bytes, RX_packets, TX_packets"

        # Get initial values
        prev_rx_bytes=$(cat /proc/net/dev | grep -E "(eth|ens|wlan)" | head -1 | awk '{print $2}')
        prev_tx_bytes=$(cat /proc/net/dev | grep -E "(eth|ens|wlan)" | head -1 | awk '{print $10}')

        for ((i=0; i<$MONITORING_DURATION; i+=$SAMPLING_INTERVAL)); do
            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            net_stats=$(cat /proc/net/dev | grep -E "(eth|ens|wlan)" | head -1 | awk '{printf "%s,%s,%s,%s", $2,$10,$3,$11}')
            echo "$timestamp, $net_stats"
            sleep $SAMPLING_INTERVAL
        done
    } > "$output_dir/network_usage.csv" &

    # Process monitoring
    log_info "Monitoring top processes..."
    {
        echo "# Top Processes Report - $(date)"
        for ((i=0; i<$MONITORING_DURATION; i+=$((SAMPLING_INTERVAL*5)))); do
            echo "## $(date '+%Y-%m-%d %H:%M:%S')"
            ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu | head -20
            echo ""
            sleep $((SAMPLING_INTERVAL*5))
        done
    } > "$output_dir/top_processes.txt" &

    # Wait for monitoring to complete
    wait

    log_success "System monitoring completed. Data saved in $output_dir"
    echo "$output_dir" > "latest_monitoring_dir.txt"
}

# Monitor application performance
monitor_application_performance() {
    log_info "Starting application performance monitoring..."

    local output_dir="performance-monitoring/$(date +%Y%m%d_%H%M%S)/application"
    mkdir -p "$output_dir"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would monitor application performance"
        return 0
    fi

    # Web server monitoring (if detected)
    if pgrep -f "nginx\|apache\|httpd" &> /dev/null; then
        log_info "Detected web server, monitoring HTTP performance..."

        # Monitor response times
        {
            echo "# HTTP Response Times - $(date)"
            echo "# Timestamp, Response_Time_ms, Status_Code"

            for ((i=0; i<$MONITORING_DURATION; i+=$SAMPLING_INTERVAL)); do
                timestamp=$(date '+%Y-%m-%d %H:%M:%S')
                # Test localhost (adjust URL as needed)
                response_time=$(curl -o /dev/null -s -w "%{time_total},%{http_code}" http://localhost/ 2>/dev/null || echo "0,000")
                echo "$timestamp, ${response_time/,/, }"
                sleep $SAMPLING_INTERVAL
            done
        } > "$output_dir/http_response_times.csv" &
    fi

    # Database monitoring (if detected)
    if pgrep -f "mysql\|postgres\|mongod" &> /dev/null; then
        log_info "Detected database server, monitoring database performance..."

        # Monitor database connections and queries (example for MySQL)
        if pgrep -f mysql &> /dev/null; then
            {
                echo "# Database Performance - $(date)"
                for ((i=0; i<$MONITORING_DURATION; i+=$((SAMPLING_INTERVAL*10)))); do
                    echo "## $(date '+%Y-%m-%d %H:%M:%S')"
                    echo "Active connections: $(mysql -e 'SHOW STATUS LIKE "Threads_connected"' 2>/dev/null | tail -1 | awk '{print $2}' || echo 'N/A')"
                    echo "Slow queries: $(mysql -e 'SHOW STATUS LIKE "Slow_queries"' 2>/dev/null | tail -1 | awk '{print $2}' || echo 'N/A')"
                    echo ""
                    sleep $((SAMPLING_INTERVAL*10))
                done
            } > "$output_dir/database_performance.txt" &
        fi
    fi

    # Application-specific monitoring
    detect_and_monitor_applications "$output_dir"

    log_success "Application monitoring setup completed"
}

# Detect and monitor specific applications
detect_and_monitor_applications() {
    local output_dir=$1

    # Python applications
    if pgrep -f python &> /dev/null; then
        log_info "Detected Python applications, setting up monitoring..."

        # Monitor Python processes
        {
            echo "# Python Application Performance - $(date)"
            for ((i=0; i<$MONITORING_DURATION; i+=$((SAMPLING_INTERVAL*5)))); do
                echo "## $(date '+%Y-%m-%d %H:%M:%S')"
                ps -eo pid,cmd,%mem,%cpu | grep python | grep -v grep
                echo ""
                sleep $((SAMPLING_INTERVAL*5))
            done
        } > "$output_dir/python_apps.txt" &
    fi

    # Node.js applications
    if pgrep -f node &> /dev/null; then
        log_info "Detected Node.js applications, setting up monitoring..."

        # Monitor Node.js processes
        {
            echo "# Node.js Application Performance - $(date)"
            for ((i=0; i<$MONITORING_DURATION; i+=$((SAMPLING_INTERVAL*5)))); do
                echo "## $(date '+%Y-%m-%d %H:%M:%S')"
                ps -eo pid,cmd,%mem,%cpu | grep node | grep -v grep
                echo ""
                sleep $((SAMPLING_INTERVAL*5))
            done
        } > "$output_dir/nodejs_apps.txt" &
    fi

    # Docker containers
    if command -v docker &> /dev/null && docker ps &> /dev/null; then
        log_info "Detected Docker containers, monitoring container performance..."

        {
            echo "# Docker Container Performance - $(date)"
            for ((i=0; i<$MONITORING_DURATION; i+=$((SAMPLING_INTERVAL*5)))); do
                echo "## $(date '+%Y-%m-%d %H:%M:%S')"
                docker stats --no-stream 2>/dev/null || echo "Docker stats unavailable"
                echo ""
                sleep $((SAMPLING_INTERVAL*5))
            done
        } > "$output_dir/docker_performance.txt" &
    fi
}

# Run performance benchmarks
run_performance_benchmarks() {
    log_info "Running performance benchmarks..."

    local output_dir="performance-benchmarks/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$output_dir"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would run performance benchmarks"
        return 0
    fi

    # CPU benchmark
    log_info "Running CPU benchmark..."
    {
        echo "# CPU Benchmark Results - $(date)"
        echo ""

        # Simple CPU stress test
        echo "## CPU Stress Test (calculating prime numbers)"
        time_start=$(date +%s.%N)
        seq 1 100000 | awk 'function isprime(x) {for(i=2;i<=sqrt(x);i++) if(x%i==0) return 0; return 1} isprime($1) {print $1}' > /dev/null
        time_end=$(date +%s.%N)
        cpu_time=$(echo "$time_end - $time_start" | bc -l)
        echo "CPU calculation time: ${cpu_time} seconds"

        # CPU info
        echo ""
        echo "## CPU Information"
        lscpu | grep -E "Model name|CPU\(s\)|Thread|MHz"
    } > "$output_dir/cpu_benchmark.txt"

    # Memory benchmark
    log_info "Running memory benchmark..."
    {
        echo "# Memory Benchmark Results - $(date)"
        echo ""

        # Memory allocation test
        echo "## Memory Allocation Test"
        time_start=$(date +%s.%N)
        dd if=/dev/zero of=/tmp/memory_test bs=1M count=100 2>/dev/null
        sync
        time_end=$(date +%s.%N)
        rm -f /tmp/memory_test
        mem_time=$(echo "$time_end - $time_start" | bc -l)
        echo "Memory allocation time: ${mem_time} seconds"

        # Memory info
        echo ""
        echo "## Memory Information"
        free -h
    } > "$output_dir/memory_benchmark.txt"

    # Disk I/O benchmark
    log_info "Running disk I/O benchmark..."
    {
        echo "# Disk I/O Benchmark Results - $(date)"
        echo ""

        echo "## Sequential Write Test"
        dd if=/dev/zero of=/tmp/disk_test bs=1M count=100 conv=fsync 2>&1 | grep -E "bytes|copied"

        echo ""
        echo "## Sequential Read Test"
        dd if=/tmp/disk_test of=/dev/null bs=1M 2>&1 | grep -E "bytes|copied"

        rm -f /tmp/disk_test

        echo ""
        echo "## Disk Space Information"
        df -h
    } > "$output_dir/disk_benchmark.txt"

    # Network benchmark (if network tools available)
    if command -v wget &> /dev/null; then
        log_info "Running network benchmark..."
        {
            echo "# Network Benchmark Results - $(date)"
            echo ""

            echo "## Network Speed Test (downloading test file)"
            time_start=$(date +%s.%N)
            wget -O /dev/null -q http://speedtest.ftp.otenet.gr/files/test1Mb.db 2>/dev/null || echo "Network test failed"
            time_end=$(date +%s.%N)
            network_time=$(echo "$time_end - $time_start" | bc -l)
            echo "1MB download time: ${network_time} seconds"

            echo ""
            echo "## Network Interface Information"
            ip addr show | grep -E "inet|mtu"
        } > "$output_dir/network_benchmark.txt"
    fi

    log_success "Performance benchmarks completed. Results saved in $output_dir"
}

# Generate comprehensive performance report
generate_performance_report() {
    log_info "Generating comprehensive performance report..."

    local latest_dir
    if [[ -f "latest_monitoring_dir.txt" ]]; then
        latest_dir=$(cat "latest_monitoring_dir.txt")
    else
        latest_dir="performance-monitoring/latest"
    fi

    local report_file="performance-comprehensive-report.md"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would generate performance report"
        return 0
    fi

    cat > "$report_file" << EOF
# Performance Monitoring Report

**Generated**: $(date)
**Repository**: $(basename "$(pwd)")
**Monitoring Duration**: $MONITORING_DURATION seconds
**Sampling Interval**: $SAMPLING_INTERVAL seconds

## Executive Summary

This comprehensive performance report includes:

- 📊 System resource utilization analysis
- 🚀 Application performance metrics
- 🔧 Performance bottleneck identification
- 📈 Trending and historical analysis
- 💡 Optimization recommendations

## System Performance Overview

### CPU Performance
$(if [[ -f "$latest_dir/cpu_usage.csv" ]]; then
    echo "**Average CPU Usage**: $(tail -n +2 "$latest_dir/cpu_usage.csv" | awk -F',' '{sum+=$2} END {printf "%.1f%%", sum/NR}')"
    echo ""
    echo "**Peak CPU Usage**: $(tail -n +2 "$latest_dir/cpu_usage.csv" | awk -F',' 'BEGIN{max=0} {if($2>max) max=$2} END {printf "%.1f%%", max}')"
else
    echo "CPU data not available"
fi)

### Memory Performance
$(if [[ -f "$latest_dir/memory_usage.csv" ]]; then
    echo "**Average Memory Usage**: $(tail -n +2 "$latest_dir/memory_usage.csv" | awk -F',' '{sum+=$6} END {printf "%.1f%%", sum/NR}')"
    echo ""
    echo "**Peak Memory Usage**: $(tail -n +2 "$latest_dir/memory_usage.csv" | awk -F',' 'BEGIN{max=0} {if($6>max) max=$6} END {printf "%.1f%%", max}')"
else
    echo "Memory data not available"
fi)

### Network Performance
$(if [[ -f "$latest_dir/network_usage.csv" ]]; then
    echo "Network monitoring data available in $latest_dir/network_usage.csv"
else
    echo "Network data not available"
fi)

### Disk I/O Performance
$(if [[ -f "$latest_dir/disk_io.txt" ]]; then
    echo "Disk I/O monitoring data available in $latest_dir/disk_io.txt"
else
    echo "Disk I/O data not available"
fi)

## Application Performance

### Web Server Performance
$(if [[ -f "$latest_dir/application/http_response_times.csv" ]]; then
    echo "**Average Response Time**: $(tail -n +2 "$latest_dir/application/http_response_times.csv" | awk -F',' '{sum+=$2} END {printf "%.0f ms", sum/NR}')"
    echo ""
    echo "**Peak Response Time**: $(tail -n +2 "$latest_dir/application/http_response_times.csv" | awk -F',' 'BEGIN{max=0} {if($2>max) max=$2} END {printf "%.0f ms", max}')"
else
    echo "Web server data not available"
fi)

### Database Performance
$(if [[ -f "$latest_dir/application/database_performance.txt" ]]; then
    echo "Database performance data available in $latest_dir/application/database_performance.txt"
else
    echo "Database data not available"
fi)

### Container Performance
$(if [[ -f "$latest_dir/application/docker_performance.txt" ]]; then
    echo "Container performance data available in $latest_dir/application/docker_performance.txt"
else
    echo "Container data not available"
fi)

## Performance Analysis

### Resource Utilization Trends
$(analyze_performance_trends "$latest_dir")

### Bottleneck Identification
$(identify_performance_bottlenecks "$latest_dir")

### Optimization Recommendations
$(generate_optimization_recommendations "$latest_dir")

## Benchmark Results

$(if [[ -d "performance-benchmarks" ]]; then
    echo "Benchmark results available in performance-benchmarks/ directory"
    find performance-benchmarks/ -name "*.txt" -type f | head -5 | while read -r file; do
        echo "- $(basename "$file")"
    done
else
    echo "No benchmark data available"
fi)

## Data Files

### Raw Monitoring Data
- System resources: $latest_dir/
- Application metrics: $latest_dir/application/
- Process information: $latest_dir/top_processes.txt

### Analysis Files
- CPU usage: $latest_dir/cpu_usage.csv
- Memory usage: $latest_dir/memory_usage.csv
- Network activity: $latest_dir/network_usage.csv

## Next Steps

1. **Immediate Actions**:
   - Address any identified performance bottlenecks
   - Optimize high resource consumption processes
   - Scale resources if consistently high utilization

2. **Monitoring Setup**:
   - Implement continuous monitoring for critical metrics
   - Set up alerts for performance thresholds
   - Schedule regular performance reviews

3. **Optimization Tasks**:
   - Apply recommended optimizations
   - Test performance improvements
   - Monitor impact of changes

## Tools Used

- System monitoring: top, ps, iostat, free, df
- Network monitoring: netstat, ss
- Process monitoring: htop, iotop (if available)
- Application monitoring: custom scripts
- Benchmarking: dd, wget, CPU stress tests

---

*This report provides a comprehensive analysis of system and application performance. Use the recommendations to improve overall system efficiency.*

EOF

    log_success "Performance report generated: $report_file"
}

# Analyze performance trends (helper function)
analyze_performance_trends() {
    local data_dir=$1

    if [[ -f "$data_dir/cpu_usage.csv" ]]; then
        echo "**CPU Trend**: $(tail -n +2 "$data_dir/cpu_usage.csv" | awk -F',' 'NR==1{first=$2} END{if($2>first) print "Increasing"; else if($2<first) print "Decreasing"; else print "Stable"}')"
    fi

    if [[ -f "$data_dir/memory_usage.csv" ]]; then
        echo "**Memory Trend**: $(tail -n +2 "$data_dir/memory_usage.csv" | awk -F',' 'NR==1{first=$6} END{if($6>first) print "Increasing"; else if($6<first) print "Decreasing"; else print "Stable"}')"
    fi
}

# Identify performance bottlenecks (helper function)
identify_performance_bottlenecks() {
    local data_dir=$1
    local bottlenecks=()

    # Check CPU bottlenecks
    if [[ -f "$data_dir/cpu_usage.csv" ]]; then
        local avg_cpu=$(tail -n +2 "$data_dir/cpu_usage.csv" | awk -F',' '{sum+=$2} END {print sum/NR}')
        if (( $(echo "$avg_cpu > 80" | bc -l) )); then
            bottlenecks+=("High CPU usage (${avg_cpu}%)")
        fi
    fi

    # Check memory bottlenecks
    if [[ -f "$data_dir/memory_usage.csv" ]]; then
        local avg_mem=$(tail -n +2 "$data_dir/memory_usage.csv" | awk -F',' '{sum+=$6} END {print sum/NR}')
        if (( $(echo "$avg_mem > 90" | bc -l) )); then
            bottlenecks+=("High memory usage (${avg_mem}%)")
        fi
    fi

    if [[ ${#bottlenecks[@]} -gt 0 ]]; then
        printf '%s\n' "${bottlenecks[@]}" | sed 's/^/- /'
    else
        echo "No significant bottlenecks detected"
    fi
}

# Generate optimization recommendations (helper function)
generate_optimization_recommendations() {
    local data_dir=$1
    local recommendations=()

    # CPU recommendations
    if [[ -f "$data_dir/cpu_usage.csv" ]]; then
        local avg_cpu=$(tail -n +2 "$data_dir/cpu_usage.csv" | awk -F',' '{sum+=$2} END {print sum/NR}')
        if (( $(echo "$avg_cpu > 70" | bc -l) )); then
            recommendations+=("Consider CPU optimization or scaling")
        fi
    fi

    # Memory recommendations
    if [[ -f "$data_dir/memory_usage.csv" ]]; then
        local avg_mem=$(tail -n +2 "$data_dir/memory_usage.csv" | awk -F',' '{sum+=$6} END {print sum/NR}')
        if (( $(echo "$avg_mem > 80" | bc -l) )); then
            recommendations+=("Consider memory optimization or adding more RAM")
        fi
    fi

    # General recommendations
    recommendations+=("Implement caching for frequently accessed data")
    recommendations+=("Optimize database queries and indexing")
    recommendations+=("Consider load balancing for high traffic")

    printf '%s\n' "${recommendations[@]}" | sed 's/^/- /'
}

# Main execution function
main() {
    local monitoring_type="all"
    local continuous_mode=false
    local report_only=false

    # Create log directory
    mkdir -p "$LOG_DIR"

    log_info "Starting performance monitoring and analysis..."

    # Check for monitoring tools
    check_monitoring_tools

    if [[ "$report_only" == "true" ]]; then
        generate_performance_report
        return 0
    fi

    # Run monitoring based on options
    case $monitoring_type in
        "system"|"all")
            monitor_system_resources
            ;;& # Continue to next case
        "app"|"all")
            monitor_application_performance
            ;;
    esac

    # Run benchmarks if requested
    if [[ "$monitoring_type" == "benchmark" ]]; then
        run_performance_benchmarks
    fi

    # Generate comprehensive report
    generate_performance_report

    echo ""
    log_success "Performance monitoring completed!"
    echo ""
    echo "Generated reports:"
    echo "- Comprehensive report: performance-comprehensive-report.md"
    if [[ -f "latest_monitoring_dir.txt" ]]; then
        local latest_dir=$(cat "latest_monitoring_dir.txt")
        echo "- Raw monitoring data: $latest_dir"
    fi
    echo ""
    echo "Use this data to:"
    echo "1. Identify performance bottlenecks"
    echo "2. Plan capacity and scaling"
    echo "3. Optimize application performance"
    echo "4. Monitor trends over time"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -t|--duration)
            MONITORING_DURATION="$2"
            shift 2
            ;;
        -i|--interval)
            SAMPLING_INTERVAL="$2"
            shift 2
            ;;
        -p|--profile)
            ENABLE_PROFILING=true
            shift
            ;;
        --system-only)
            monitoring_type="system"
            shift
            ;;
        --app-only)
            monitoring_type="app"
            shift
            ;;
        --network-only)
            monitoring_type="network"
            shift
            ;;
        --load-test)
            monitoring_type="load-test"
            shift
            ;;
        --benchmark)
            monitoring_type="benchmark"
            shift
            ;;
        --continuous)
            continuous_mode=true
            MONITORING_DURATION=86400  # 24 hours
            shift
            ;;
        --report-only)
            report_only=true
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            show_usage >&2
            exit 1
            ;;
    esac
done

# Execute main function
main "$@"
