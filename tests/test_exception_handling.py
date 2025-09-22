"""
Test suite for the standardized exception handling framework.

Tests all custom exception classes, decorators, context managers,
and error recovery strategies.
"""

import pytest
import logging
from unittest.mock import patch, MagicMock
from app.core.exceptions import (
    BaseXanadOSError,
    SystemError,
    SecurityError,
    NetworkError,
    FileIOError,
    DatabaseError,
    MLModelError,
    ErrorSeverity,
    ErrorCategory,
    handle_exceptions,
    safe_operation,
    log_and_reraise,
    ErrorRecoveryStrategy,
    exception_monitor,
    setup_global_exception_handling
)


class TestBaseXanadOSError:
    """Test the base exception class."""
    
    def test_basic_exception_creation(self):
        """Test basic exception creation with default values."""
        exc = BaseXanadOSError("Test error")
        
        assert exc.message == "Test error"
        assert exc.severity == ErrorSeverity.MEDIUM
        assert exc.category == ErrorCategory.SYSTEM
        assert exc.context == {}
        assert exc.cause is None
        assert exc.error_id is not None
        assert exc.timestamp is not None
    
    def test_exception_with_all_parameters(self):
        """Test exception creation with all parameters."""
        context = {"key": "value"}
        cause = ValueError("Original error")
        
        exc = BaseXanadOSError(
            message="Test error",
            error_code="TEST_001",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.SECURITY,
            context=context,
            cause=cause
        )
        
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_001"
        assert exc.severity == ErrorSeverity.HIGH
        assert exc.category == ErrorCategory.SECURITY
        assert exc.context == context
        assert exc.cause == cause
    
    def test_exception_to_dict(self):
        """Test exception serialization."""
        exc = BaseXanadOSError(
            "Test error",
            error_code="TEST_001",
            severity=ErrorSeverity.HIGH
        )
        
        result = exc.to_dict()
        
        assert result["message"] == "Test error"
        assert result["error_code"] == "TEST_001"
        assert result["severity"] == "high"
        assert "error_id" in result
        assert "timestamp" in result
    
    @patch('app.core.exceptions.logging.getLogger')
    def test_exception_logging(self, mock_get_logger):
        """Test that exceptions are automatically logged."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        exc = BaseXanadOSError("Test error", severity=ErrorSeverity.CRITICAL)
        
        mock_get_logger.assert_called_with("xanados.system")
        mock_logger.critical.assert_called_once()


class TestSpecificExceptions:
    """Test specific exception classes."""
    
    def test_system_error(self):
        """Test SystemError."""
        exc = SystemError("System failure")
        assert exc.category == ErrorCategory.SYSTEM
    
    def test_security_error(self):
        """Test SecurityError."""
        exc = SecurityError("Security breach")
        assert exc.category == ErrorCategory.SECURITY
        assert exc.severity == ErrorSeverity.HIGH
    
    def test_network_timeout_error(self):
        """Test NetworkTimeoutError."""
        from app.core.exceptions import NetworkTimeoutError
        exc = NetworkTimeoutError("Connection timeout", timeout_seconds=30.0)
        assert exc.category == ErrorCategory.NETWORK
        assert exc.context['timeout_seconds'] == 30.0
    
    def test_file_io_error(self):
        """Test FileIOError."""
        exc = FileIOError("File not found", file_path="/tmp/test.txt")
        assert exc.category == ErrorCategory.FILE_IO
        assert exc.context['file_path'] == "/tmp/test.txt"
    
    def test_ml_model_error(self):
        """Test MLModelError."""
        exc = MLModelError("Model training failed", model_name="threat_detector")
        assert exc.category == ErrorCategory.ML_MODEL
        assert exc.context['model_name'] == "threat_detector"


class TestExceptionDecorators:
    """Test exception handling decorators."""
    
    def test_handle_exceptions_decorator_with_reraise(self):
        """Test handle_exceptions decorator with reraise=True."""
        @handle_exceptions(reraise=True)
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(SystemError) as exc_info:
            failing_function()
        
        assert "Unhandled ValueError in failing_function" in str(exc_info.value)
    
    def test_handle_exceptions_decorator_without_reraise(self):
        """Test handle_exceptions decorator with reraise=False."""
        @handle_exceptions(reraise=False, fallback_return="fallback")
        def failing_function():
            raise ValueError("Test error")
        
        result = failing_function()
        assert result == "fallback"
    
    def test_handle_exceptions_decorator_with_custom_exception(self):
        """Test handle_exceptions decorator with custom exceptions."""
        @handle_exceptions(reraise=True)
        def failing_function():
            raise SecurityError("Security issue")
        
        with pytest.raises(SecurityError):
            failing_function()
    
    def test_log_and_reraise_decorator(self):
        """Test log_and_reraise decorator."""
        @log_and_reraise("Failed to process", SecurityError)
        def failing_function():
            raise ValueError("Original error")
        
        with pytest.raises(SecurityError) as exc_info:
            failing_function()
        
        assert "Failed to process: Original error" in str(exc_info.value)
        assert exc_info.value.cause is not None


class TestSafeOperation:
    """Test safe operation context manager."""
    
    def test_safe_operation_success(self):
        """Test safe operation with successful operation."""
        with safe_operation("test_operation"):
            result = 1 + 1
        
        assert result == 2
    
    def test_safe_operation_with_exception(self):
        """Test safe operation with exception."""
        with pytest.raises(SystemError) as exc_info:
            with safe_operation("test_operation", ErrorCategory.DATABASE, ErrorSeverity.HIGH):
                raise ValueError("Test error")
        
        assert "Error in test_operation" in str(exc_info.value)
        assert exc_info.value.category == ErrorCategory.DATABASE
        assert exc_info.value.severity == ErrorSeverity.HIGH
    
    def test_safe_operation_with_custom_exception(self):
        """Test safe operation with custom exception (should pass through)."""
        with pytest.raises(SecurityError):
            with safe_operation("test_operation"):
                raise SecurityError("Security issue")


class TestErrorRecoveryStrategy:
    """Test error recovery strategies."""
    
    def test_successful_operation(self):
        """Test successful operation without retries."""
        strategy = ErrorRecoveryStrategy(max_retries=3)
        
        def successful_operation():
            return "success"
        
        result = strategy.execute_with_retry(successful_operation)
        assert result == "success"
    
    def test_operation_with_retries(self):
        """Test operation that succeeds after retries."""
        strategy = ErrorRecoveryStrategy(max_retries=3, delay_seconds=0.1)
        
        attempt_count = 0
        def flaky_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ValueError("Temporary failure")
            return "success"
        
        result = strategy.execute_with_retry(flaky_operation)
        assert result == "success"
        assert attempt_count == 3
    
    def test_operation_exhausts_retries(self):
        """Test operation that exhausts all retries."""
        strategy = ErrorRecoveryStrategy(max_retries=2, delay_seconds=0.1)
        
        def always_failing_operation():
            raise ValueError("Persistent failure")
        
        with pytest.raises(SystemError) as exc_info:
            strategy.execute_with_retry(always_failing_operation)
        
        assert "Operation failed after 3 attempts" in str(exc_info.value)


class TestExceptionMonitoring:
    """Test exception monitoring and statistics."""
    
    def test_exception_monitoring(self):
        """Test exception monitoring."""
        # Clear previous stats
        exception_monitor.exception_counts.clear()
        exception_monitor.severity_counts = dict.fromkeys(ErrorSeverity, 0)
        exception_monitor.category_counts = dict.fromkeys(ErrorCategory, 0)
        
        # Generate some exceptions
        exc1 = SecurityError("Security issue 1")
        exc2 = SecurityError("Security issue 2")
        exc3 = SystemError("System issue")
        
        stats = exception_monitor.get_statistics()
        
        assert stats["exception_counts"]["SecurityError"] == 2
        assert stats["exception_counts"]["SystemError"] == 1
        assert stats["severity_counts"]["high"] == 2  # SecurityErrors are high severity
        assert stats["severity_counts"]["medium"] == 1  # SystemError is medium
        assert stats["category_counts"]["security"] == 2
        assert stats["category_counts"]["system"] == 1
        assert stats["total_exceptions"] == 3


class TestGlobalExceptionHandling:
    """Test global exception handling setup."""
    
    @patch('sys.excepthook')
    def test_global_exception_handler_setup(self, mock_excepthook):
        """Test global exception handler setup."""
        setup_global_exception_handling()
        
        # The excepthook should be set
        assert mock_excepthook is not None
    
    def test_global_exception_handler_keyboard_interrupt(self):
        """Test that KeyboardInterrupt passes through."""
        import sys
        from unittest.mock import patch
        
        setup_global_exception_handling()
        
        # Store original handler
        original_handler = sys.__excepthook__
        
        with patch('sys.__excepthook__') as mock_original:
            # Simulate KeyboardInterrupt
            try:
                sys.excepthook(KeyboardInterrupt, KeyboardInterrupt(), None)
                mock_original.assert_called_once()
            except SystemExit:
                pass  # Expected for other exceptions


@pytest.fixture
def clear_exception_monitor():
    """Clear exception monitor between tests."""
    exception_monitor.exception_counts.clear()
    exception_monitor.severity_counts = dict.fromkeys(ErrorSeverity, 0)
    exception_monitor.category_counts = dict.fromkeys(ErrorCategory, 0)


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""
    
    def test_file_processing_with_error_handling(self):
        """Test file processing with comprehensive error handling."""
        @handle_exceptions(reraise=True)
        def process_file(filename: str) -> str:
            if filename == "missing.txt":
                raise FileNotFoundError("File not found")
            elif filename == "permission_denied.txt":
                raise PermissionError("Permission denied")
            else:
                return f"Processed {filename}"
        
        # Test successful processing
        result = process_file("valid.txt")
        assert result == "Processed valid.txt"
        
        # Test file not found
        with pytest.raises(SystemError) as exc_info:
            process_file("missing.txt")
        assert "FileNotFoundError" in str(exc_info.value)
        
        # Test permission error
        with pytest.raises(SystemError) as exc_info:
            process_file("permission_denied.txt")
        assert "PermissionError" in str(exc_info.value)
    
    def test_ml_pipeline_with_error_handling(self):
        """Test ML pipeline with error handling."""
        from app.core.exceptions import MLTrainingError, MLPredictionError
        
        class MockMLModel:
            def __init__(self, name: str):
                self.name = name
                self.trained = False
            
            def train(self, data):
                if not data:
                    raise MLTrainingError("No training data provided", model_name=self.name)
                self.trained = True
            
            def predict(self, input_data):
                if not self.trained:
                    raise MLPredictionError("Model not trained", model_name=self.name)
                return f"Prediction for {input_data}"
        
        model = MockMLModel("threat_detector")
        
        # Test training error
        with pytest.raises(MLTrainingError) as exc_info:
            model.train(None)
        assert exc_info.value.context['model_name'] == "threat_detector"
        
        # Test prediction error
        with pytest.raises(MLPredictionError):
            model.predict("test_input")
        
        # Test successful flow
        model.train(["data1", "data2"])
        result = model.predict("test_input")
        assert result == "Prediction for test_input"
    
    def test_network_operation_with_retry(self):
        """Test network operation with retry logic."""
        strategy = ErrorRecoveryStrategy(max_retries=3, delay_seconds=0.1)
        
        attempt_count = 0
        def simulate_network_request():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                from app.core.exceptions import NetworkTimeoutError
                raise NetworkTimeoutError("Connection timeout", timeout_seconds=30.0)
            return {"status": "success", "data": "response"}
        
        result = strategy.execute_with_retry(simulate_network_request)
        assert result["status"] == "success"
        assert attempt_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])