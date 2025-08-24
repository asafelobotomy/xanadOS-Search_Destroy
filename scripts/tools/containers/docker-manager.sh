#!/bin/bash
# Tool: docker-manager.sh
# Purpose: Comprehensive Docker container management and optimization
# Usage: ./docker-manager.sh [options]

set -euo pipefail

# Script metadata
TOOL_NAME="docker-manager"
TOOL_VERSION="1.0.0"
TOOL_DESCRIPTION="Comprehensive Docker container management and optimization"

# Configuration
LOG_DIR="logs/toolshed"
DRY_RUN=false
VERBOSE=false
AUTO_CLEANUP=false
SECURITY_SCAN=false

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

This tool provides comprehensive Docker management including:
- Container lifecycle management
- Image optimization and security scanning
- Resource monitoring and cleanup
- Docker Compose orchestration
- Performance analysis and tuning
- Security hardening and compliance

Options:
    -h, --help              Show this help message
    -d, --dry-run           Preview changes without executing
    -v, --verbose           Enable verbose output
    -c, --cleanup           Enable automatic cleanup of unused resources
    -s, --security-scan     Enable security scanning of images
    --build                 Build images from Dockerfile
    --run                   Run containers
    --stop                  Stop running containers
    --restart               Restart containers
    --logs                  Show container logs
    --stats                 Show container statistics
    --optimize              Optimize Docker setup
    --backup                Backup container data
    --restore               Restore container data
    --health-check          Check container health

Examples:
    $0                                      # Show Docker status and overview
    $0 --build --security-scan              # Build and scan images
    $0 --cleanup --dry-run                  # Preview cleanup operations
    $0 --stats --verbose                    # Show detailed container statistics
    $0 --optimize                           # Optimize Docker configuration
    $0 --backup                             # Backup container volumes

Docker Management Features:
    ✓ Container lifecycle management
    ✓ Image building and optimization
    ✓ Security scanning with Trivy
    ✓ Resource usage monitoring
    ✓ Automatic cleanup and maintenance
    ✓ Docker Compose management
    ✓ Volume and network management
    ✓ Health checking and monitoring

EOF
}

# Check Docker installation and status
check_docker_status() {
    log_info "Checking Docker installation and status..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi

    local docker_version=$(docker --version | awk '{print $3}' | tr -d ',')
    log_success "Docker version $docker_version is running"

    # Check Docker Compose
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        log_success "Docker Compose is available"
    else
        log_warning "Docker Compose is not available"
    fi
}

# Show Docker system overview
show_docker_overview() {
    log_info "Docker System Overview"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would show Docker overview"
        return 0
    fi

    echo ""
    echo "=== Docker System Information ==="
    docker system df

    echo ""
    echo "=== Running Containers ==="
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}"

    echo ""
    echo "=== Available Images ==="
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

    echo ""
    echo "=== Docker Networks ==="
    docker network ls

    echo ""
    echo "=== Docker Volumes ==="
    docker volume ls
}

# Build Docker images
build_docker_images() {
    log_info "Building Docker images..."

    local dockerfile_dirs=()

    # Find Dockerfiles
    while IFS= read -r -d '' dockerfile; do
        dockerfile_dirs+=("$(dirname "$dockerfile")")
    done < <(find . -name "Dockerfile" -type f -print0)

    if [[ ${#dockerfile_dirs[@]} -eq 0 ]]; then
        log_warning "No Dockerfiles found"
        return 0
    fi

    log_info "Found Dockerfiles in: ${dockerfile_dirs[*]}"

    for dir in "${dockerfile_dirs[@]}"; do
        local image_name=$(basename "$dir")
        local image_tag="latest"

        if [[ -f "$dir/.dockerignore" ]]; then
            log_info "Found .dockerignore in $dir"
        else
            log_warning "No .dockerignore found in $dir - consider creating one"
        fi

        log_info "Building image $image_name:$image_tag from $dir"

        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] Would build: docker build -t $image_name:$image_tag $dir"
            continue
        fi

        if docker build -t "$image_name:$image_tag" "$dir"; then
            log_success "Successfully built $image_name:$image_tag"

            # Security scan if enabled
            if [[ "$SECURITY_SCAN" == "true" ]]; then
                scan_image_security "$image_name:$image_tag"
            fi
        else
            log_error "Failed to build $image_name:$image_tag"
        fi
    done
}

# Scan image security
scan_image_security() {
    local image=$1

    log_info "Scanning security for image: $image"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would scan image security"
        return 0
    fi

    # Use Trivy for security scanning
    if command -v trivy &> /dev/null; then
        local scan_output="security-scan-$(echo "$image" | tr '/:' '-').json"
        trivy image --format json --output "$scan_output" "$image" || true
        log_success "Security scan saved to $scan_output"
    else
        log_warning "Trivy not installed, skipping security scan"
        log_info "Install with: sudo apt-get install trivy"
    fi

    # Docker's built-in security scan (if available)
    if docker scan --help &> /dev/null; then
        docker scan "$image" || true
    fi
}

# Manage container operations
manage_containers() {
    local operation=$1

    case $operation in
        "start"|"run")
            start_containers
            ;;
        "stop")
            stop_containers
            ;;
        "restart")
            restart_containers
            ;;
        "logs")
            show_container_logs
            ;;
        "stats")
            show_container_stats
            ;;
    esac
}

# Start containers
start_containers() {
    log_info "Starting containers..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would start containers"
        return 0
    fi

    # Check for docker-compose files
    if [[ -f "docker-compose.yml" ]] || [[ -f "docker-compose.yaml" ]]; then
        log_info "Found Docker Compose file, starting services..."

        if command -v docker-compose &> /dev/null; then
            docker-compose up -d
        else
            docker compose up -d
        fi
    else
        log_info "No Docker Compose file found, starting individual containers..."

        # Start stopped containers
        local stopped_containers=$(docker ps -aq -f status=exited)
        if [[ -n "$stopped_containers" ]]; then
            echo "$stopped_containers" | xargs docker start
            log_success "Started stopped containers"
        else
            log_info "No stopped containers to start"
        fi
    fi
}

# Stop containers
stop_containers() {
    log_info "Stopping containers..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would stop containers"
        return 0
    fi

    # Check for docker-compose files
    if [[ -f "docker-compose.yml" ]] || [[ -f "docker-compose.yaml" ]]; then
        if command -v docker-compose &> /dev/null; then
            docker-compose down
        else
            docker compose down
        fi
    else
        # Stop all running containers
        local running_containers=$(docker ps -q)
        if [[ -n "$running_containers" ]]; then
            echo "$running_containers" | xargs docker stop
            log_success "Stopped running containers"
        else
            log_info "No running containers to stop"
        fi
    fi
}

# Restart containers
restart_containers() {
    log_info "Restarting containers..."

    stop_containers
    start_containers
}

# Show container logs
show_container_logs() {
    log_info "Showing container logs..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would show container logs"
        return 0
    fi

    local containers=$(docker ps --format "{{.Names}}")

    if [[ -z "$containers" ]]; then
        log_warning "No running containers found"
        return 0
    fi

    echo "$containers" | while read -r container; do
        echo ""
        echo "=== Logs for $container ==="
        docker logs --tail 50 "$container"
    done
}

# Show container statistics
show_container_stats() {
    log_info "Showing container statistics..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would show container statistics"
        return 0
    fi

    if docker ps -q | grep -q .; then
        docker stats --no-stream
    else
        log_warning "No running containers found"
    fi
}

# Cleanup Docker resources
cleanup_docker_resources() {
    log_info "Cleaning up Docker resources..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would perform Docker cleanup:"
        log_info "  - Remove unused containers"
        log_info "  - Remove unused images"
        log_info "  - Remove unused volumes"
        log_info "  - Remove unused networks"
        return 0
    fi

    # Remove stopped containers
    local stopped_containers=$(docker ps -aq -f status=exited)
    if [[ -n "$stopped_containers" ]]; then
        echo "$stopped_containers" | xargs docker rm
        log_success "Removed stopped containers"
    fi

    # Remove dangling images
    local dangling_images=$(docker images -qf dangling=true)
    if [[ -n "$dangling_images" ]]; then
        echo "$dangling_images" | xargs docker rmi
        log_success "Removed dangling images"
    fi

    # Remove unused volumes
    docker volume prune -f
    log_success "Removed unused volumes"

    # Remove unused networks
    docker network prune -f
    log_success "Removed unused networks"

    # System prune (careful with this)
    if [[ "$AUTO_CLEANUP" == "true" ]]; then
        docker system prune -f
        log_success "Performed system cleanup"
    fi
}

# Optimize Docker setup
optimize_docker_setup() {
    log_info "Optimizing Docker setup..."

    local optimization_report="docker-optimization-report.md"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would optimize Docker setup"
        return 0
    fi

    cat > "$optimization_report" << EOF
# Docker Optimization Report

**Generated**: $(date)
**Docker Version**: $(docker --version)

## Current Configuration

### System Information
\`\`\`
$(docker system info | head -20)
\`\`\`

### Resource Usage
\`\`\`
$(docker system df)
\`\`\`

## Optimization Recommendations

### Image Optimization
$(analyze_image_optimization)

### Container Performance
$(analyze_container_performance)

### Resource Management
$(analyze_resource_management)

### Security Recommendations
$(analyze_security_recommendations)

## Action Items

1. **Implement Multi-stage Builds**: Reduce image sizes
2. **Use .dockerignore**: Exclude unnecessary files
3. **Optimize Base Images**: Use Alpine or scratch images where possible
4. **Resource Limits**: Set appropriate CPU and memory limits
5. **Health Checks**: Implement container health monitoring

EOF

    log_success "Optimization report generated: $optimization_report"
}

# Analyze image optimization opportunities
analyze_image_optimization() {
    local large_images=$(docker images --format "{{.Repository}}:{{.Tag}} {{.Size}}" | sort -k2 -hr | head -5)

    echo "**Large Images (Top 5):**"
    echo "\`\`\`"
    echo "$large_images"
    echo "\`\`\`"
    echo ""
    echo "**Recommendations:**"
    echo "- Use multi-stage builds to reduce final image size"
    echo "- Choose smaller base images (alpine, scratch)"
    echo "- Remove unnecessary packages and files"
    echo "- Combine RUN commands to reduce layers"
}

# Analyze container performance
analyze_container_performance() {
    echo "**Container Resource Usage:**"
    if docker ps -q | grep -q .; then
        echo "\`\`\`"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
        echo "\`\`\`"
    else
        echo "No running containers"
    fi
    echo ""
    echo "**Recommendations:**"
    echo "- Set resource limits for containers"
    echo "- Monitor CPU and memory usage patterns"
    echo "- Optimize application code for better performance"
}

# Analyze resource management
analyze_resource_management() {
    local volume_count=$(docker volume ls -q | wc -l)
    local network_count=$(docker network ls -q | wc -l)

    echo "**Resource Summary:**"
    echo "- Volumes: $volume_count"
    echo "- Networks: $network_count"
    echo ""
    echo "**Recommendations:**"
    echo "- Regular cleanup of unused resources"
    echo "- Use named volumes for persistent data"
    echo "- Implement backup strategies for important volumes"
}

# Analyze security recommendations
analyze_security_recommendations() {
    echo "**Security Analysis:**"
    echo "- Image scanning: $(command -v trivy &> /dev/null && echo "Available" || echo "Not installed")"
    echo "- Docker daemon: $(docker info --format '{{.SecurityOptions}}' 2>/dev/null || echo "Unknown")"
    echo ""
    echo "**Recommendations:**"
    echo "- Regularly scan images for vulnerabilities"
    echo "- Use non-root users in containers"
    echo "- Implement secrets management"
    echo "- Keep Docker daemon updated"
    echo "- Use read-only root filesystems where possible"
}

# Backup container data
backup_container_data() {
    log_info "Backing up container data..."

    local backup_dir="docker-backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would backup container data to $backup_dir"
        return 0
    fi

    # Backup volumes
    local volumes=$(docker volume ls -q)
    if [[ -n "$volumes" ]]; then
        log_info "Backing up Docker volumes..."
        echo "$volumes" | while read -r volume; do
            log_info "Backing up volume: $volume"
            docker run --rm -v "$volume:/data" -v "$(pwd)/$backup_dir:/backup" alpine tar czf "/backup/$volume.tar.gz" -C /data .
        done
        log_success "Volume backups completed"
    fi

    # Backup container configurations
    log_info "Backing up container configurations..."
    docker ps -a --format "{{.Names}}" | while read -r container; do
        docker inspect "$container" > "$backup_dir/$container-config.json"
    done

    # Backup images list
    docker images --format "{{.Repository}}:{{.Tag}}" > "$backup_dir/images-list.txt"

    log_success "Container data backup completed in $backup_dir"
}

# Health check containers
health_check_containers() {
    log_info "Performing container health checks..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would perform health checks"
        return 0
    fi

    local health_report="docker-health-report.md"

    cat > "$health_report" << EOF
# Docker Health Check Report

**Generated**: $(date)

## Container Health Status

EOF

    # Check running containers
    docker ps --format "{{.Names}}" | while read -r container; do
        echo "### $container" >> "$health_report"

        # Get container health status
        local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no-healthcheck")
        echo "**Health Status**: $health_status" >> "$health_report"

        # Get container stats
        local stats=$(docker stats --no-stream --format "{{.CPUPerc}} {{.MemUsage}} {{.MemPerc}}" "$container")
        echo "**Resource Usage**: $stats" >> "$health_report"

        # Check if container is responding
        local ports=$(docker port "$container" 2>/dev/null || echo "no-ports")
        if [[ "$ports" != "no-ports" ]]; then
            echo "**Exposed Ports**: $ports" >> "$health_report"
        fi

        echo "" >> "$health_report"
    done

    log_success "Health check report generated: $health_report"
}

# Main execution function
main() {
    local operation="overview"

    # Create log directory
    mkdir -p "$LOG_DIR"

    log_info "Starting Docker management operations..."

    # Check Docker status
    check_docker_status

    # Execute based on operation
    case $operation in
        "overview")
            show_docker_overview
            ;;
        "build")
            build_docker_images
            ;;
        "cleanup")
            cleanup_docker_resources
            ;;
        "optimize")
            optimize_docker_setup
            ;;
        "backup")
            backup_container_data
            ;;
        "health-check")
            health_check_containers
            ;;
        *)
            manage_containers "$operation"
            ;;
    esac

    echo ""
    log_success "Docker management operations completed!"
    echo ""
    echo "Available operations:"
    echo "- Overview: $0"
    echo "- Build: $0 --build"
    echo "- Cleanup: $0 --cleanup"
    echo "- Optimize: $0 --optimize"
    echo "- Stats: $0 --stats"
    echo "- Health check: $0 --health-check"
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
        -c|--cleanup)
            AUTO_CLEANUP=true
            operation="cleanup"
            shift
            ;;
        -s|--security-scan)
            SECURITY_SCAN=true
            shift
            ;;
        --build)
            operation="build"
            shift
            ;;
        --run)
            operation="run"
            shift
            ;;
        --stop)
            operation="stop"
            shift
            ;;
        --restart)
            operation="restart"
            shift
            ;;
        --logs)
            operation="logs"
            shift
            ;;
        --stats)
            operation="stats"
            shift
            ;;
        --optimize)
            operation="optimize"
            shift
            ;;
        --backup)
            operation="backup"
            shift
            ;;
        --health-check)
            operation="health-check"
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
