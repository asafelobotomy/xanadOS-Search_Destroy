# Single Instance Implementation Summary

## Problem
The application could run multiple instances simultaneously, which could lead to:
- Resource conflicts
- Multiple system tray icons
- Configuration conflicts
- User confusion

## Solution Implemented

### 1. Single Instance Manager (`app/core/single_instance.py`)
- Uses file locking mechanism to detect existing instances
- Unix domain socket for inter-process communication
- Automatic cleanup of lock files and sockets on exit

### 2. Main Application Integration (`app/main.py`)
- Checks for existing instance before creating QApplication
- If existing instance found, notifies it and exits gracefully
- Sets up instance server to listen for new launch attempts

### 3. MainWindow Enhancement (`app/gui/main_window.py`)
- Added `bring_to_front()` method for graceful window restoration
- Handles hidden, minimized, and background states
- Shows notification when window is restored due to second launch

## How It Works

### First Instance Launch:
1. SingleInstanceManager tries to acquire exclusive lock file
2. If successful, creates Unix domain socket server
3. Application starts normally
4. Timer checks for incoming connections from other instances

### Second Instance Launch:
1. SingleInstanceManager tries to acquire lock file
2. Lock fails (first instance has it)
3. Connects to first instance's socket and sends "SHOW" message
4. Exits immediately with code 0

### Window Restoration:
1. First instance receives "SHOW" message
2. Calls MainWindow's `bring_to_front()` method
3. Window is restored from any state (hidden, minimized, background)
4. Notification shows user that window was restored

## Key Features

### ✅ Cross-Platform Compatibility
- Uses standard Unix file locking (works on Linux, macOS)
- Fallback mechanisms for edge cases

### ✅ Graceful Handling
- Second instance exits silently without error
- No disruptive error messages to user
- Smooth window restoration experience

### ✅ Robust Cleanup
- Automatic cleanup on normal exit
- Handles crashes and forced termination
- No leftover lock files or sockets

### ✅ User Experience
- Brings existing window to front when user tries to launch again
- Shows helpful notification about the restoration
- Works with minimize-to-tray functionality

## Files Modified

### New Files:
- `app/core/single_instance.py` - Single instance management logic

### Modified Files:
- `app/main.py` - Integration with single instance checking
- `app/gui/main_window.py` - Added `bring_to_front()` method

## Testing Results

✅ **First Instance**: Starts normally and acquires lock
✅ **Second Instance**: Detects existing instance and exits gracefully
✅ **Window Restoration**: Successfully brings existing window to front
✅ **Cleanup**: Properly releases locks when application exits
✅ **Restart**: Can start new instance after previous one exits

## Benefits

1. **Resource Efficiency**: No duplicate processes or resources
2. **User Experience**: Intuitive behavior when clicking app icon multiple times
3. **System Integration**: Works well with system tray minimize functionality
4. **Reliability**: Robust handling of edge cases and cleanup scenarios

The implementation ensures that only one instance of S&D - Search & Destroy can run at a time, while providing a smooth user experience when multiple launch attempts are made.
