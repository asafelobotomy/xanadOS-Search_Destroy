# Bug Fixing & Error Resolution Instructions

## Copilot usage quick cues

- Ask: clarify the exact error and expected behavior; request minimal repro steps.
- Edit: add logging, guards, or small fixes; keep diffs tight and reversible.
- Agent: multi-file/root-cause hunts; require clear hypotheses and checkpoints.

### Model routing

- Reasoning model: intermittent bugs, concurrency, complex state flows.
- Claude Sonnet class: structured reviews of logs, stack traces, and diffs.
- Gemini Pro class: summarize long logs or correlate failures across files.
- Fast general model: quick log/print instrumentation and small patches.

### Token economy tips

- Share only the failing snippet, stack trace, and minimal repro, not full files.
- Prefer short checkpoints: what changed, what we tested, next hypothesis.

## 🎯 Purpose

This instruction set provides comprehensive guidance for systematically diagnosing,
debugging, and resolving bugs, conflicts, and errors in software development. It
incorporates modern best practices from Hugging Face, systematic debugging
methodologies, and advanced error handling patterns for 2024-2025.

## 🚀 Core Methodology: Systematic Debugging Approach

### Phase 1: Problem Analysis & Symptom Identification

#### 1. Symptom Documentation

- Document exact error messages, stack traces, and unexpected behaviors
- Record environmental context (OS, versions, dependencies, hardware)
- Capture reproduction steps with precise inputs and expected vs. actual outputs
- Note timing and frequency patterns of the issue

#### 2. Error Classification

- **Syntax Errors**: Code structure violations (immediate fixes)
- **Runtime Errors**: Execution failures (logic/resource issues)
- **Logic Errors**: Incorrect behavior (design/algorithm problems)
- **Integration Errors**: Component interaction failures
- **Performance Errors**: Resource exhaustion or inefficiency

### Phase 2: Reproduction & Environment Setup

#### 3. Reproduction Strategy

- Create minimal reproducible examples (MRE)
- Test across different environments to isolate environment-specific issues
- Use controlled inputs to verify consistent reproduction
- Document exact steps and conditions required for reproduction

#### 4. Environment Debugging

```bash

# For CUDA/GPU issues (Hugging Face best practice)

export CUDA_VISIBLE_DEVICES=""  # Test on CPU first
export CUDA_LAUNCH_BLOCKING="1"  # Better GPU tracebacks

# For dependency conflicts

pip list --verbose
conda list
python -c "import sys; print(sys.path)"
```markdown

### Phase 3: System Understanding & Hypothesis Formation

#### 5. System Architecture Analysis

- Map data flow and component interactions
- Identify critical paths and potential failure points
- Understand dependencies and their versions
- Review recent changes and their potential impact

#### 6. Binary Search Debugging

- Form hypotheses that eliminate ~50% of potential locations
- Test hypotheses systematically to narrow down problem areas
- Use logging and print statements strategically for visibility
- Validate assumptions at each step

## 🔧 Advanced Debugging Techniques

### Hugging Face Specific Debugging

#### CUDA Memory Issues

```python

# Memory management debugging

import torch
import gc

def debug_memory():
    if torch.cuda.is_available():
        print(f"GPU Memory: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
        print(f"GPU Cached: {torch.cuda.memory_reserved() / 1024**2:.2f} MB")
        print(f"Max Memory: {torch.cuda.max_memory_allocated() / 1024**2:.2f} MB")

    # Force cleanup
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

# Before problematic operations

debug_memory()
```markdown

#### Model Configuration Debugging

```python

# Validate model configurations

from transformers import AutoConfig, AutoModel

def validate_model_setup(model_name, task_type):
    try:
        config = AutoConfig.from_pretrained(model_name)
        print(f"Model architecture: {config.architectures}")
        print(f"Supported tasks: {config.task_specific_params}")

        # Verify task compatibility
        if task_type not in config.task_specific_params:
            print(f"Warning: {task_type} may not be supported")

    except Exception as e:
        print(f"Configuration error: {e}")
        return False
    return True
```markdown

### Systematic Error Isolation

#### 7. Component Isolation Testing

```python

# Test components individually

def test_component_isolation():
    # Test data pipeline
    assert validate_input_data(), "Input data validation failed"

    # Test model loading
    assert test_model_loading(), "Model loading failed"

    # Test preprocessing
    assert test_preprocessing(), "Preprocessing failed"

    # Test inference
    assert test_inference(), "Inference failed"
```markdown

#### 8. Logging Strategy

```python
import logging
import traceback
from datetime import datetime

def setup_debug_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )

def debug_checkpoint(checkpoint_name, variables=None):
    logger = logging.getLogger(__name__)
    logger.debug(f"Checkpoint: {checkpoint_name}")

    if variables:
        for var_name, var_value in variables.items():
            logger.debug(f"  {var_name}: {var_value}")

    # Memory usage
    if torch.cuda.is_available():
        logger.debug(f"  GPU Memory: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
```markdown

## 🔀 Git Conflict Resolution

### Advanced Conflict Resolution Strategies

#### 9. Three-Way Merge Analysis

```bash

# Understanding conflict context

git log --oneline --graph --all -10

# View conflict in detail

git diff HEAD...MERGE_HEAD  # Changes from common ancestor

# Advanced merge tools

git config merge.tool vimdiff  # or meld, kdiff3, vscode
git mergetool
```markdown

#### 10. Strategic Conflict Resolution

```bash

# Preserve both changes strategically

# For complex conflicts, use:
git checkout --ours file.py    # Keep current branch version
git checkout --theirs file.py  # Keep incoming branch version
git checkout --merge file.py   # Show conflict markers again

# Smart conflict resolution

git config merge.ours.driver true  # For generated files
git config merge.theirs.driver "git show %B:%A"  # For specific file types
```markdown

#### 11. Prevention Strategies

```bash

# Standardize formatting to reduce conflicts

# .gitattributes configuration
echo "*.py eol=lf" >> .gitattributes
echo "*.js eol=lf" >> .gitattributes

# Pre-commit hooks for consistency

pip install pre-commit
pre-commit install

# Rebase strategy for cleaner history

git config pull.rebase true
git config rebase.autoStash true
```markdown

## 🛡️ Error Handling Patterns

### Resilient Error Handling Architecture

#### 12. Circuit Breaker Pattern

```python
import time
from enum import Enum
from typing import Callable, Any

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self.reset()
            return result
        except Exception as e:
            self.record_failure()
            raise e

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def reset(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
```markdown

#### 13. Retry with Exponential Backoff

```python
import random
import time
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1, max_delay=60, backoff_factor=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        logging.error(f"Final attempt failed: {e}")
                        raise

                    delay = min(
                        base_delay * (backoff_factor ** attempt) + random.uniform(0, 1),
                        max_delay
                    )

                    logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s")
                    time.sleep(delay)

        return wrapper
    return decorator

# Usage

@retry_with_backoff(max_retries=3, base_delay=2)
def unreliable_api_call():
    # Your potentially failing function
    pass
```markdown

### Error Context & Recovery

#### 14. Comprehensive Error Context

```python
import sys
import traceback
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class ErrorContext:
    error_type: str
    error_message: str
    stack_trace: str
    function_name: str
    file_name: str
    line_number: int
    local_variables: Dict[str, Any]
    system_info: Dict[str, Any]
    timestamp: str

def capture_error_context(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            frame = sys.exc_info()[2].tb_frame

            context = ErrorContext(
                error_type=type(e).__name__,
                error_message=str(e),
                stack_trace=traceback.format_exc(),
                function_name=frame.f_code.co_name,
                file_name=frame.f_code.co_filename,
                line_number=frame.f_lineno,
                local_variables=dict(frame.f_locals),
                system_info={
                    'python_version': sys.version,
                    'platform': sys.platform,
                    'cuda_available': torch.cuda.is_available() if 'torch' in sys.modules else False
                },
                timestamp=datetime.now().isoformat()
            )

            # Log comprehensive context
            logging.error(f"Error context: {context}")

            # Re-raise with additional context
            error_msg = f"{str(e)} | Context: {context.function_name}:{context.line_number}"
            raise type(e)(error_msg) from e

    return wrapper
```markdown

## 📊 Modern Monitoring & Observability

### Real-time Error Tracking

#### 15. Health Checks & Monitoring

```python
from typing import NamedTuple
import psutil
import time

class SystemHealth(NamedTuple):
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    gpu_memory_percent: Optional[float]
    timestamp: float

def monitor_system_health():
    health = SystemHealth(
        cpu_percent=psutil.cpu_percent(interval=1),
        memory_percent=psutil.virtual_memory().percent,
        disk_percent=psutil.disk_usage('/').percent,
        gpu_memory_percent=get_gpu_memory_percent() if torch.cuda.is_available() else None,
        timestamp=time.time()
    )

    # Alert on critical thresholds
    if health.cpu_percent > 90:
        logging.warning(f"High CPU usage: {health.cpu_percent}%")
    if health.memory_percent > 85:
        logging.warning(f"High memory usage: {health.memory_percent}%")

    return health

def get_gpu_memory_percent():
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated()
        total = torch.cuda.max_memory_allocated()
        return (allocated / total) * 100 if total > 0 else 0
    return None
```markdown

## 🛠️ Automated Debugging Tools Integration

### Pre-Built Debugging and Monitoring Tools

Before creating custom debugging scripts, GitHub Copilot agents MUST use the
comprehensive debugging and monitoring tools available in the toolshed:

#### Performance Monitoring and Profiling

```bash
# Comprehensive performance monitoring and profiling
./scripts/tools/monitoring/performance-monitor.sh --duration 300
./scripts/tools/monitoring/performance-monitor.sh --benchmark --report-only
./scripts/tools/monitoring/performance-monitor.sh --help  # View all options
```

#### Security and Vulnerability Analysis

```bash
# Security scanning for debugging security-related issues
./scripts/tools/security/security-scan.sh --all
./scripts/tools/security/security-scan.sh --secrets-only  # Credential leak detection
```

#### Container Debugging

```bash
# Docker container debugging and optimization
./scripts/tools/containers/docker-manager.sh --health-check
./scripts/tools/containers/docker-manager.sh --logs --container app
```

#### Database Health and Debugging

```bash
# Database debugging and health monitoring
./scripts/tools/database/database-manager.sh --health-check --type postgresql
./scripts/tools/database/database-manager.sh --performance-analysis --type mysql
```

#### Dependency Analysis

```bash
# Dependency conflict and vulnerability debugging
./scripts/tools/dependencies/dependency-manager.sh --audit
./scripts/tools/dependencies/dependency-manager.sh --conflict-analysis
```

#### Repository Structure Validation

```bash
# Repository structure and quality debugging
./scripts/tools/validation/validate-structure.sh --verbose
./scripts/tools/quality/check-quality.sh --debug --fix
```

### Tool Benefits for Debugging

- **Comprehensive Coverage**: Multi-system monitoring and analysis
- **Automated Detection**: Proactive issue identification before they become problems
- **Performance Profiling**: Resource usage analysis and optimization recommendations
- **Security Analysis**: Vulnerability detection and credential leak prevention
- **Health Monitoring**: Real-time system health assessment and alerting

### Integration with Debugging Workflow

1. **System Health Check**: Start with `performance-monitor.sh` and `validate-structure.sh`
2. **Security Analysis**: Use `security-scan.sh` for security-related debugging
3. **Dependency Issues**: Run `dependency-manager.sh --audit` for package conflicts
4. **Container Problems**: Use `docker-manager.sh --health-check` for containerized apps
5. **Database Issues**: Apply `database-manager.sh --health-check` for data problems

**Reference**: See `scripts/tools/README.md` for complete debugging tool catalog.

## 🎯 Best Practices Summary

### Development Workflow Integration

#### 16. Pre-Development Checks

- Set up comprehensive logging before starting development
- Configure monitoring and health checks
- Establish error context capture mechanisms
- Set up debugging environment variables

#### 17. During Development

- Use systematic debugging approach for any issues
- Implement circuit breakers for external dependencies
- Add retry mechanisms for transient failures
- Document error patterns in knowledge base

#### 18. Post-Resolution

- Conduct post-debugging reflection
- Update documentation with lessons learned
- Share insights with team members
- Update error handling patterns based on new findings

### Team Collaboration

#### 19. Knowledge Sharing

- Maintain debugging knowledge base with categorized solutions
- Conduct post-mortem reviews for complex bugs
- Share debugging techniques and tools across team
- Document common error patterns and their solutions

#### 20. Continuous Improvement

- Regularly update debugging tools and techniques
- Monitor industry best practices and new methodologies
- Implement automated error detection and reporting
- Conduct training sessions on advanced debugging techniques

---

**Remember**: Effective debugging is 70% systematic methodology and 30% technical
tools. Focus on understanding the system, forming testable hypotheses, and
maintaining comprehensive documentation of your debugging process.
