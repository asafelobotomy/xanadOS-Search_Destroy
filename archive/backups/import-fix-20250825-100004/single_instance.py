#!/usr/bin/env python3
"""
Single Instance Manager for S&D - Search & Destroy
Ensures only one instance of the application can run at a time.
"""
import os
import fcntl
import tempfile
import socket
from PyQt6.QtCore import QTimer


class SingleInstanceManager:
    """Manages single instance enforcement for the application."""
    
    def __init__(self, app_name="search-and-destroy"):
        self.app_name = app_name
        self.lock_fd = None
        self.socket_server = None
        
        # Create lock file path in temp directory
        temp_dir = tempfile.gettempdir()
        self.lock_file_path = os.path.join(temp_dir, f"{app_name}.lock")
        self.socket_file_path = os.path.join(temp_dir, f"{app_name}.sock")
        
    def is_already_running(self):
        """Check if another instance is already running."""
        try:
            # Try to acquire lock file
            self.lock_fd = os.open(self.lock_file_path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Write PID to lock file
            os.write(self.lock_fd, str(os.getpid()).encode())
            os.fsync(self.lock_fd)
            
            return False  # Not already running, we got the lock
            
        except (OSError, IOError):
            # Lock file is already locked by another process
            if self.lock_fd:
                try:
                    os.close(self.lock_fd)
                except:
                    pass
                self.lock_fd = None
            return True  # Already running
    
    def notify_existing_instance(self):
        """Notify the existing instance to show itself."""
        try:
            # Try to connect to the existing instance's socket
            client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client_socket.connect(self.socket_file_path)
            client_socket.send(b"SHOW")
            client_socket.close()
            return True
        except Exception as e:
            print(f"Could not notify existing instance: {e}")
            return False
    
    def setup_instance_server(self, main_window):
        """Set up socket server to listen for other instances."""
        try:
            # Remove old socket file if it exists
            if os.path.exists(self.socket_file_path):
                os.unlink(self.socket_file_path)
            
            # Create Unix domain socket
            self.socket_server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.socket_server.bind(self.socket_file_path)
            self.socket_server.listen(1)
            self.socket_server.setblocking(False)
            
            # Set up timer to check for incoming connections
            self.connection_timer = QTimer()
            self.connection_timer.timeout.connect(lambda: self._check_connections(main_window))
            self.connection_timer.start(500)  # Check every 500ms
            
            return True
        except Exception as e:
            print(f"Failed to setup instance server: {e}")
            return False
    
    def _check_connections(self, main_window):
        """Check for incoming connections from other instances."""
        try:
            client_socket, _ = self.socket_server.accept()
            data = client_socket.recv(1024)
            client_socket.close()
            
            if data == b"SHOW":
                # Another instance wants us to show the window
                self._bring_to_front(main_window)
                
        except socket.error:
            # No connection waiting, which is normal
            pass
        except Exception as e:
            print(f"Error handling connection: {e}")
    
    def _bring_to_front(self, main_window):
        """Bring the main window to the front."""
        try:
            # Use the main window's own method for bringing to front
            if hasattr(main_window, 'bring_to_front'):
                main_window.bring_to_front()
            else:
                # Fallback to basic method
                if not main_window.isVisible():
                    main_window.show()
                
                if main_window.isMinimized():
                    main_window.showNormal()
                
                main_window.raise_()
                main_window.activateWindow()
            
            print("✅ Brought existing instance to front")
                    
        except Exception as e:
            print(f"❌ Error bringing window to front: {e}")
    
    def cleanup(self):
        """Clean up resources when application exits."""
        try:
            # Stop the connection timer
            if hasattr(self, 'connection_timer'):
                self.connection_timer.stop()
            
            # Close socket server
            if self.socket_server:
                self.socket_server.close()
                
            # Remove socket file
            if self.socket_file_path and os.path.exists(self.socket_file_path):
                os.unlink(self.socket_file_path)
                
            # Release lock
            if self.lock_fd:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                os.close(self.lock_fd)
                
            # Remove lock file
            if self.lock_file_path and os.path.exists(self.lock_file_path):
                os.unlink(self.lock_file_path)
                
        except Exception as e:
            print(f"Error during cleanup: {e}")
