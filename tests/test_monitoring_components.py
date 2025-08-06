#!/usr/bin/env python3
"""
Simple demonstration of Phase 3 monitoring components
Tests individual components without full integration
"""
import sys
import os
import time
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

def test_file_watcher():
    """Test file watcher component."""
    print("Testing FileSystemWatcher...")
    
    try:
        from monitoring.file_watcher import FileSystemWatcher, WatchEventType
        
        watcher = FileSystemWatcher()
        print(f"✓ FileSystemWatcher created successfully")
        print(f"  - Polling available: {hasattr(watcher, '_polling_enabled')}")
        print(f"  - Statistics: {watcher.get_statistics()}")
        
        return True
    except Exception as e:
        print(f"✗ FileSystemWatcher test failed: {e}")
        return False

def test_event_processor():
    """Test event processor component."""
    print("\nTesting EventProcessor...")
    
    try:
        from monitoring.event_processor import EventProcessor, EventAction
        from monitoring.file_watcher import WatchEvent, WatchEventType
        
        processor = EventProcessor()
        print(f"✓ EventProcessor created successfully")
        
        # Test processing a mock event
        test_event = WatchEvent(
            file_path="/tmp/test.txt",
            event_type=WatchEventType.FILE_CREATED,
            timestamp=time.time()
        )
        
        processed = processor.process_event(test_event)
        if processed:
            print(f"✓ Event processed: {processed.action}")
        else:
            print("  Event filtered out")
        
        stats = processor.get_statistics()
        print(f"  - Statistics: {stats}")
        
        return True
    except Exception as e:
        print(f"✗ EventProcessor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_monitoring_imports():
    """Test that all monitoring components can be imported."""
    print("\nTesting monitoring imports...")
    
    try:
        from monitoring import (
            FileSystemWatcher, WatchEvent, WatchEventType,
            EventProcessor, EventAction,
            MonitorConfig, MonitorState
        )
        print("✓ All main monitoring components imported successfully")
        
        # Test creating basic objects
        config = MonitorConfig(watch_paths=["/tmp"])
        print(f"✓ MonitorConfig created: {len(config.watch_paths)} paths")
        
        return True
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_event_creation():
    """Test creating and validating events."""
    print("\nTesting event creation...")
    
    try:
        from monitoring.file_watcher import WatchEvent, WatchEventType
        
        # Create test file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            test_file = f.name
        
        try:
            # Test valid event
            event = WatchEvent(
                file_path=test_file,
                event_type=WatchEventType.FILE_CREATED,
                timestamp=time.time()
            )
            print(f"✓ Valid event created: {event.event_type.value}")
            
            # Test event with metadata
            event_with_meta = WatchEvent(
                file_path=test_file,
                event_type=WatchEventType.FILE_MODIFIED,
                timestamp=time.time(),
                is_directory=False
            )
            print(f"✓ Event with metadata created successfully")
            
            return True
        
        finally:
            # Clean up
            try:
                os.unlink(test_file)
            except:
                pass
        
    except Exception as e:
        print(f"✗ Event creation test failed: {e}")
        return False

def main():
    """Run all component tests."""
    print("Phase 3 Monitoring Components Test")
    print("=" * 40)
    
    tests = [
        test_monitoring_imports,
        test_event_creation,
        test_file_watcher,
        test_event_processor,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test_func.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 40)
    print("Test Results:")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All component tests passed!")
        return True
    else:
        print("⚠️  Some tests failed - components may have issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
