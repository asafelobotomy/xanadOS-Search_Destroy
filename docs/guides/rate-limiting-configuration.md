# Rate Limiting Configuration Guide

This document explains how to configure rate limiting for xanadOS Search & Destroy to
optimize performance for different scan types while maintaining security protection.

## Overview

The rate limiting system protects against resource exhaustion and provides different
limits for different types of operations:

- **Quick Scan**: User-initiated fast scans with higher limits
- **Full Scan**: User-initiated comprehensive scans with moderate limits
- **Background Scan**: Automated monitoring with conservative limits
- **Real-time Scan**: File system monitoring with highest limits

## Configuration File Location

Rate limiting configuration is stored in your main configuration file under the
`rate_limiting` section.

## Configuration Format

```json
{
  "rate_limiting": {
    "quick_scan": {
      "calls": 500,
      "period": 60.0,
      "burst": 100
    },
    "full_scan": {
      "calls": 200,
      "period": 60.0,
      "burst": 50
    },
    "background_scan": {
      "calls": 50,
      "period": 60.0,
      "burst": 10
    },
    "real_time_scan": {
      "calls": 1000,
      "period": 60.0,
      "burst": 200
    },
    "file_scan": {
      "calls": 100,
      "period": 60.0,
      "burst": 20
    },
    "directory_scan": {
      "calls": 10,
      "period": 60.0,
      "burst": 5
    },
    "quick_directory_scan": {
      "calls": 30,
      "period": 60.0,
      "burst": 15
    },
    "virus_db_update": {
      "calls": 1,
      "period": 3600.0,
      "burst": null
    },
    "network_request": {
      "calls": 50,
      "period": 60.0,
      "burst": 10
    },
    "quarantine_action": {
      "calls": 20,
      "period": 60.0,
      "burst": null
    },
    "system_command": {
      "calls": 5,
      "period": 60.0,
      "burst": null
    }
  }
}
```

## Rate Limit Parameters

### calls

The maximum number of operations allowed within the specified period.

### period

The time window in seconds for the rate limit (typically 60.0 for per-minute limits).

### burst

Optional burst allowance - additional operations allowed for brief spikes.
Set to `null` to disable burst capacity.

## Operation Types

### Scan Operations

| Operation | Purpose | Default Limits |
|-----------|---------|----------------|
| `quick_scan` | User-initiated quick scans | 500/min, burst 100 |
| `full_scan` | User-initiated full system scans | 200/min, burst 50 |
| `background_scan` | Automated background monitoring | 50/min, burst 10 |
| `real_time_scan` | Real-time file system protection | 1000/min, burst 200 |
| `file_scan` | General file scanning operations | 100/min, burst 20 |

### Directory Operations

| Operation | Purpose | Default Limits |
|-----------|---------|----------------|
| `directory_scan` | Standard directory scanning | 10/min, burst 5 |
| `quick_directory_scan` | Quick scan directory operations | 30/min, burst 15 |

### System Operations

| Operation | Purpose | Default Limits |
|-----------|---------|----------------|
| `virus_db_update` | Virus definition updates | 1/hour |
| `network_request` | Network API requests | 50/min, burst 10 |
| `quarantine_action` | File quarantine operations | 20/min |
| `system_command` | System command execution | 5/min |

## Configuration Examples

### High-Performance System

For systems with high CPU and memory resources:

```json
{
  "rate_limiting": {
    "quick_scan": {
      "calls": 1000,
      "period": 60.0,
      "burst": 200
    },
    "full_scan": {
      "calls": 500,
      "period": 60.0,
      "burst": 100
    }
  }
}
```

### Resource-Constrained System

For systems with limited resources:

```json
{
  "rate_limiting": {
    "quick_scan": {
      "calls": 200,
      "period": 60.0,
      "burst": 50
    },
    "full_scan": {
      "calls": 100,
      "period": 60.0,
      "burst": 25
    }
  }
}
```

### Disable Rate Limiting

To disable rate limiting for specific operations, remove them from the configuration
or set very high limits:

```json
{
  "rate_limiting": {
    "quick_scan": {
      "calls": 999999,
      "period": 60.0,
      "burst": 999999
    }
  }
}
```

## Troubleshooting

### Quick Scan Hitting Rate Limits

**Symptom**: Quick Scan stops with "Rate limit exceeded" message.

**Solutions**:

1. Increase `quick_scan` limits:

   ```json
   "quick_scan": {
     "calls": 1000,
     "period": 60.0,
     "burst": 200
   }
   ```

2. Increase burst capacity for temporary spikes:

   ```json
   "quick_scan": {
     "calls": 500,
     "period": 60.0,
     "burst": 300
   }
   ```

### System Performance Issues

**Symptom**: System becomes slow during scans.

**Solutions**:

1. Reduce scan limits:

   ```json
   "quick_scan": {
     "calls": 250,
     "period": 60.0,
     "burst": 50
   }
   ```

2. Increase the period for longer windows:

   ```json
   "quick_scan": {
     "calls": 500,
     "period": 120.0,
     "burst": 100
   }
   ```

## Monitoring Rate Limits

The application logs rate limiting events. Monitor these logs to understand if limits
need adjustment:

```log
WARNING: Rate limit exceeded for quick_scan. Wait time: 15.2 seconds
INFO: Applied custom rate limit for quick_scan: RateLimit(calls=500, period=60.0, burst=100)
```

## Dynamic Configuration Updates

Rate limits can be updated without restarting the application by modifying the
configuration file. The system will automatically reload the configuration for
new operations.

## Security Considerations

- **Don't disable all rate limiting**: This can lead to resource exhaustion
- **Monitor system resources**: Adjust limits based on actual system capacity
- **Test changes gradually**: Increase limits incrementally and monitor performance
- **Consider scan scope**: Quick scans of limited directories may need higher burst capacity

## Best Practices

1. **Start with defaults**: Use the default configuration and adjust based on actual usage patterns
2. **Monitor performance**: Watch system resources during scans to find optimal limits
3. **Consider user experience**: Balance security with usability - users shouldn't wait
   excessively for Quick Scans
4. **Document changes**: Keep track of configuration changes and their impact
5. **Test thoroughly**: Verify that changes don't negatively impact system stability

## API Access

For programmatic access to rate limiting configuration:

```python
from app.core.rate_limiting import rate_limit_manager

# Get current limits
limits = rate_limit_manager.get_current_limits()

# Update a specific limit
rate_limit_manager.update_rate_limit("quick_scan", calls=750, period=60.0, burst=150)

# Check operation status
status = rate_limit_manager.get_operation_status("quick_scan")

# Reload configuration
rate_limit_manager.reload_configuration()
```

This configuration system ensures that your security scanning remains both effective
and responsive to your system's capabilities.
