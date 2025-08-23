---
applyTo: "**/{src,lib,app,test,tests,spec}/**/*.{js,ts,py,rb,go,java,php,cs}"
description: "TDD implementation guidance for source and test files"
priority: "medium"
---

# Test-Driven Development (TDD) Prompt

You are implementing Test-Driven Development (TDD) methodology. Follow the Red-Green-Refactor cycle to build robust, well-tested code with comprehensive test coverage.

## TDD Core Principles

### The Red-Green-Refactor Cycle

1. **🔴 RED**: Write a failing test first
2. **🟢 GREEN**: Write minimal code to make the test pass
3. **🔵 REFACTOR**: Improve code while keeping tests green

### TDD Rules (Uncle Bob's Three Laws)

1. **First Law**: You may not write production code until you have written a failing unit test
2. **Second Law**: You may not write more of a unit test than is sufficient to fail
3. **Third Law**: You may not write more production code than is sufficient to pass the currently failing test

## TDD Implementation Framework

### 1. Test Planning Phase

#### Before Writing Code, Define:

- [ ] **User Story**: What functionality are we building?
- [ ] **Acceptance Criteria**: How do we know it's working correctly?
- [ ] **Test Scenarios**: What edge cases need to be covered?
- [ ] **Test Data**: What inputs and expected outputs are needed?

#### Example: User Registration Feature

```markdown
**User Story**: As a new user, I want to register an account so I can access the application.

**Acceptance Criteria**:
- User can register with email, password, and name
- Email must be unique and valid format
- Password must meet security requirements (12+ chars, complexity)
- Successful registration returns user ID and sends welcome email
- Invalid inputs return appropriate error messages

**Test Scenarios**:
- Valid registration data
- Duplicate email address
- Invalid email format
- Weak password
- Missing required fields
- Database connection failure
- Email service failure
```markdown

### 2. Red Phase: Write Failing Tests

#### Test Structure (Arrange-Act-Assert)

```python
# Example: User registration test

import pytest
from unittest.mock import Mock, patch
from user_service import UserService, UserAlreadyExistsError, InvalidEmailError

class TestUserRegistration:

    def setup_method(self):
        """Set up test dependencies"""
        self.mock_db = Mock()
        self.mock_email_service = Mock()
        self.user_service = UserService(self.mock_db, self.mock_email_service)

    def test_successful_user_registration(self):
        """Test successful user registration with valid data"""
        # Arrange
        user_data = {
            'email': 'john.doe@example.com',
            'password': 'SecurePassword123!',
            'name': 'John Doe'
        }
        expected_user_id = 12345

        self.mock_db.email_exists.return_value = False
        self.mock_db.create_user.return_value = expected_user_id
        self.mock_email_service.send_welcome_email.return_value = True

        # Act
        result = self.user_service.register_user(user_data)

        # Assert
        assert result['success'] is True
        assert result['user_id'] == expected_user_id
        assert result['message'] == 'User registered successfully'

        # Verify interactions
        self.mock_db.email_exists.assert_called_once_with('john.doe@example.com')
        self.mock_db.create_user.assert_called_once()
        self.mock_email_service.send_welcome_email.assert_called_once_with(
            'john.doe@example.com', 'John Doe'
        )

    def test_registration_with_duplicate_email(self):
        """Test registration fails when email already exists"""
        # Arrange
        user_data = {
            'email': 'existing@example.com',
            'password': 'SecurePassword123!',
            'name': 'Jane Doe'
        }

        self.mock_db.email_exists.return_value = True

        # Act & Assert
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            self.user_service.register_user(user_data)

        assert str(exc_info.value) == 'Email address already registered'

        # Verify database was checked but user not created
        self.mock_db.email_exists.assert_called_once_with('existing@example.com')
        self.mock_db.create_user.assert_not_called()
        self.mock_email_service.send_welcome_email.assert_not_called()

    def test_registration_with_invalid_email(self):
        """Test registration fails with invalid email format"""
        # Arrange
        user_data = {
            'email': 'invalid-email-format',
            'password': 'SecurePassword123!',
            'name': 'John Doe'
        }

        # Act & Assert
        with pytest.raises(InvalidEmailError) as exc_info:
            self.user_service.register_user(user_data)

        assert 'Invalid email format' in str(exc_info.value)

        # Verify no database operations occurred
        self.mock_db.email_exists.assert_not_called()
        self.mock_db.create_user.assert_not_called()

    @pytest.mark.parametrize("weak_password", [
        'short',           # Too short
        'nouppercase123!', # No uppercase
        'NOLOWERCASE123!', # No lowercase
        'NoNumbers!',      # No numbers
        'NoSpecialChars123' # No special characters
    ])
    def test_registration_with_weak_password(self, weak_password):
        """Test registration fails with weak passwords"""
        # Arrange
        user_data = {
            'email': 'test@example.com',
            'password': weak_password,
            'name': 'Test User'
        }

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.user_service.register_user(user_data)

        assert 'Password does not meet security requirements' in str(exc_info.value)

    def test_registration_with_database_failure(self):
        """Test registration handles database failures gracefully"""
        # Arrange
        user_data = {
            'email': 'test@example.com',
            'password': 'SecurePassword123!',
            'name': 'Test User'
        }

        self.mock_db.email_exists.return_value = False
        self.mock_db.create_user.side_effect = Exception('Database connection failed')

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            self.user_service.register_user(user_data)

        assert 'Database connection failed' in str(exc_info.value)

        # Verify email was not sent on failure
        self.mock_email_service.send_welcome_email.assert_not_called()
```markdown

#### JavaScript/TypeScript Example

```typescript
// Example: E-commerce cart functionality
import { Cart, Product, CartItem } from '../src/cart';
import { expect } from 'chai';

describe('Shopping Cart', () => {
  let cart: Cart;

  beforeEach(() => {
    cart = new Cart();
  });

  describe('Adding items to cart', () => {
    it('should add a new item to empty cart', () => {
      // Arrange
      const product: Product = {
        id: 1,
        name: 'Laptop',
        price: 999.99,
        category: 'Electronics'
      };

      // Act
      cart.addItem(product, 1);

      // Assert
      expect(cart.getItemCount()).to.equal(1);
      expect(cart.getTotal()).to.equal(999.99);
      expect(cart.hasItem(1)).to.be.true;
    });

    it('should increase quantity when adding existing item', () => {
      // Arrange
      const product: Product = {
        id: 1,
        name: 'Laptop',
        price: 999.99,
        category: 'Electronics'
      };

      // Act
      cart.addItem(product, 1);
      cart.addItem(product, 2);

      // Assert
      expect(cart.getItemCount()).to.equal(1); // Still one unique item
      expect(cart.getItemQuantity(1)).to.equal(3);
      expect(cart.getTotal()).to.equal(2999.97);
    });

    it('should throw error when adding item with invalid quantity', () => {
      // Arrange
      const product: Product = {
        id: 1,
        name: 'Laptop',
        price: 999.99,
        category: 'Electronics'
      };

      // Act & Assert
      expect(() => cart.addItem(product, 0)).to.throw('Quantity must be greater than 0');
      expect(() => cart.addItem(product, -1)).to.throw('Quantity must be greater than 0');
    });

    it('should apply discount when adding eligible items', () => {
      // Arrange
      const product: Product = {
        id: 1,
        name: 'Laptop',
        price: 1000.00,
        category: 'Electronics',
        discount: 0.1 // 10% discount
      };

      // Act
      cart.addItem(product, 1);

      // Assert
      expect(cart.getSubtotal()).to.equal(1000.00);
      expect(cart.getDiscountAmount()).to.equal(100.00);
      expect(cart.getTotal()).to.equal(900.00);
    });
  });

  describe('Removing items from cart', () => {
    it('should remove item completely when quantity becomes zero', () => {
      // Arrange
      const product: Product = { id: 1, name: 'Laptop', price: 999.99, category: 'Electronics' };
      cart.addItem(product, 2);

      // Act
      cart.removeItem(1, 2);

      // Assert
      expect(cart.getItemCount()).to.equal(0);
      expect(cart.hasItem(1)).to.be.false;
      expect(cart.getTotal()).to.equal(0);
    });

    it('should decrease quantity when removing partial amount', () => {
      // Arrange
      const product: Product = { id: 1, name: 'Laptop', price: 999.99, category: 'Electronics' };
      cart.addItem(product, 3);

      // Act
      cart.removeItem(1, 1);

      // Assert
      expect(cart.getItemQuantity(1)).to.equal(2);
      expect(cart.getTotal()).to.equal(1999.98);
    });

    it('should throw error when removing non-existent item', () => {
      // Act & Assert
      expect(() => cart.removeItem(999, 1)).to.throw('Item not found in cart');
    });
  });

  describe('Cart calculations', () => {
    it('should calculate correct total with multiple items and tax', () => {
      // Arrange
      const laptop: Product = { id: 1, name: 'Laptop', price: 1000.00, category: 'Electronics' };
      const mouse: Product = { id: 2, name: 'Mouse', price: 25.00, category: 'Electronics' };

      cart.setTaxRate(0.08); // 8% tax

      // Act
      cart.addItem(laptop, 1);
      cart.addItem(mouse, 2);

      // Assert
      expect(cart.getSubtotal()).to.equal(1050.00);
      expect(cart.getTaxAmount()).to.equal(84.00);
      expect(cart.getTotal()).to.equal(1134.00);
    });

    it('should handle free shipping threshold', () => {
      // Arrange
      const product: Product = { id: 1, name: 'Laptop', price: 100.00, category: 'Electronics' };
      cart.setFreeShippingThreshold(150.00);
      cart.setShippingCost(15.00);

      // Act - Below threshold
      cart.addItem(product, 1);

      // Assert
      expect(cart.getShippingCost()).to.equal(15.00);
      expect(cart.getTotal()).to.equal(115.00);

      // Act - Above threshold
      cart.addItem(product, 1); // Total now $200

      // Assert
      expect(cart.getShippingCost()).to.equal(0.00);
      expect(cart.getTotal()).to.equal(200.00);
    });
  });
});
```markdown

### 3. Green Phase: Write Minimal Implementation

#### Implementation Guidelines

- **Write simplest code** that makes tests pass
- **Don't over-engineer** - implement only what's needed for current test
- **Focus on functionality** - optimization comes later in refactor phase

#### Example: Initial Implementation

```python
# user_service.py - Initial implementation to make tests pass

import re
from typing import Dict, Any

class UserAlreadyExistsError(Exception):
    pass

class InvalidEmailError(Exception):
    pass

class UserService:
    def __init__(self, database, email_service):
        self.database = database
        self.email_service = email_service

    def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user - minimal implementation"""

        # Validate email format
        if not self._is_valid_email(user_data['email']):
            raise InvalidEmailError('Invalid email format')

        # Validate password strength
        if not self._is_strong_password(user_data['password']):
            raise ValueError('Password does not meet security requirements')

        # Check if email already exists
        if self.database.email_exists(user_data['email']):
            raise UserAlreadyExistsError('Email address already registered')

        # Create user in database
        user_id = self.database.create_user(user_data)

        # Send welcome email
        self.email_service.send_welcome_email(user_data['email'], user_data['name'])

        return {
            'success': True,
            'user_id': user_id,
            'message': 'User registered successfully'
        }

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format - minimal implementation"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _is_strong_password(self, password: str) -> bool:
        """Validate password strength - minimal implementation"""
        if len(password) < 12:
            return False

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)

        return has_upper and has_lower and has_digit and has_special
```markdown

### 4. Refactor Phase: Improve Code Quality

#### Refactoring Guidelines

- **Improve code structure** without changing functionality
- **Eliminate duplication** (DRY principle)
- **Improve readability** and maintainability
- **Extract methods/classes** for better organization
- **All tests must continue to pass**

#### Example: Refactored Implementation

```python
# user_service.py - Refactored version

import re
from typing import Dict, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Value Objects

@dataclass
class UserRegistrationData:
    email: str
    password: str
    name: str

    def __post_init__(self):
        self._validate()

    def _validate(self):
        if not self.email or not self.password or not self.name:
            raise ValueError('All fields are required')

# Custom Exceptions

class UserRegistrationError(Exception):
    """Base exception for user registration errors"""
    pass

class UserAlreadyExistsError(UserRegistrationError):
    pass

class InvalidEmailError(UserRegistrationError):
    pass

class WeakPasswordError(UserRegistrationError):
    pass

# Validation Services

class EmailValidator:
    @staticmethod
    def is_valid(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

class PasswordValidator:
    MIN_LENGTH = 12
    REQUIRED_CHARS = {
        'uppercase': str.isupper,
        'lowercase': str.islower,
        'digit': str.isdigit,
        'special': lambda c: c in '!@#$%^&*()_+-=[]{}|;:,.<>?'
    }

    @classmethod
    def is_strong(cls, password: str) -> bool:
        if len(password) < cls.MIN_LENGTH:
            return False

        return all(
            any(check(c) for c in password)
            for check in cls.REQUIRED_CHARS.values()
        )

    @classmethod
    def get_strength_requirements(cls) -> str:
        return (
            f"Password must be at least {cls.MIN_LENGTH} characters long and contain "
            f"uppercase, lowercase, numbers, and special characters."
        )

# Interfaces

class DatabaseInterface(ABC):
    @abstractmethod
    def email_exists(self, email: str) -> bool:
        pass

    @abstractmethod
    def create_user(self, user_data: Dict[str, Any]) -> int:
        pass

class EmailServiceInterface(ABC):
    @abstractmethod
    def send_welcome_email(self, email: str, name: str) -> bool:
        pass

# Main Service

class UserService:
    def __init__(self, database: DatabaseInterface, email_service: EmailServiceInterface):
        self.database = database
        self.email_service = email_service

    def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user with comprehensive validation"""

        # Create validated user data object
        registration_data = UserRegistrationData(**user_data)

        # Validate email format
        self._validate_email(registration_data.email)

        # Validate password strength
        self._validate_password(registration_data.password)

        # Check for existing user
        self._check_email_uniqueness(registration_data.email)

        # Create user
        user_id = self._create_user_account(registration_data)

        # Send notification
        self._send_welcome_notification(registration_data)

        return self._create_success_response(user_id)

    def _validate_email(self, email: str) -> None:
        if not EmailValidator.is_valid(email):
            raise InvalidEmailError(f'Invalid email format: {email}')

    def _validate_password(self, password: str) -> None:
        if not PasswordValidator.is_strong(password):
            raise WeakPasswordError(
                f'Password does not meet security requirements. '
                f'{PasswordValidator.get_strength_requirements()}'
            )

    def _check_email_uniqueness(self, email: str) -> None:
        if self.database.email_exists(email):
            raise UserAlreadyExistsError('Email address already registered')

    def _create_user_account(self, registration_data: UserRegistrationData) -> int:
        try:
            return self.database.create_user({
                'email': registration_data.email,
                'password': registration_data.password,
                'name': registration_data.name
            })
        except Exception as e:
            raise UserRegistrationError(f'Failed to create user account: {str(e)}')

    def _send_welcome_notification(self, registration_data: UserRegistrationData) -> None:
        try:
            self.email_service.send_welcome_email(
                registration_data.email,
                registration_data.name
            )
        except Exception as e:
            # Log error but don't fail registration
            print(f'Warning: Failed to send welcome email: {str(e)}')

    def _create_success_response(self, user_id: int) -> Dict[str, Any]:
        return {
            'success': True,
            'user_id': user_id,
            'message': 'User registered successfully'
        }
```markdown

### 5. TDD Best Practices

#### Test Organization

```python
# conftest.py - Shared test fixtures

import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_database():
    """Mock database for testing"""
    db = Mock()
    db.email_exists.return_value = False
    db.create_user.return_value = 12345
    return db

@pytest.fixture
def mock_email_service():
    """Mock email service for testing"""
    email_service = Mock()
    email_service.send_welcome_email.return_value = True
    return email_service

@pytest.fixture
def user_service(mock_database, mock_email_service):
    """User service with mocked dependencies"""
    return UserService(mock_database, mock_email_service)

@pytest.fixture
def valid_user_data():
    """Valid user registration data"""
    return {
        'email': 'test@example.com',
        'password': 'SecurePassword123!',
        'name': 'Test User'
    }
```markdown

#### Test Coverage Monitoring

```bash
# Coverage configuration (.coveragerc)

[run]
source = src/
omit =
    */tests/*
    */venv/*
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError

# Run tests with coverage

pytest --cov=src --cov-report=html --cov-report=term-missing
coverage report --fail-under=90
```markdown

#### Continuous Integration Integration

```yaml
# .github/workflows/tdd.yml

name: TDD Workflow

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests with coverage
      run: |
        pytest --cov=src --cov-report=xml --cov-fail-under=90

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```markdown

### 6. TDD Anti-Patterns to Avoid

#### Common Mistakes

- **Writing tests after code** - defeats the purpose of TDD
- **Testing implementation details** - tests should focus on behavior
- **Large, complex tests** - break down into smaller, focused tests
- **Mocking everything** - only mock external dependencies
- **Ignoring refactor phase** - leads to technical debt accumulation

#### Better Approaches

```python
# Anti-pattern: Testing implementation

def test_password_validation_implementation():
    # Don't test internal regex pattern
    assert user_service._password_regex.match('password123!')

# Better: Testing behavior

def test_password_validation_behavior():
    # Test what the function should do, not how it does it
    assert user_service.is_valid_password('SecurePassword123!')
    assert not user_service.is_valid_password('weak')
```markdown

### 7. TDD Metrics and Quality Gates

#### Quality Metrics

- **Test Coverage**: >90% line coverage, >85% branch coverage
- **Test Speed**: Unit tests <5 minutes, integration tests <15 minutes
- **Test Reliability**: <1% flaky test rate
- **Code Quality**: Cyclomatic complexity <10 per method

#### Definition of Done Checklist

- [ ] All tests pass (100% success rate)
- [ ] Code coverage meets minimum thresholds
- [ ] No code smells or technical debt introduced
- [ ] All edge cases covered with tests
- [ ] Documentation updated for new functionality
- [ ] Performance requirements met
- [ ] Security considerations addressed

Remember: TDD is not just about testing - it's a design methodology that leads to better code architecture, higher quality, and more maintainable software. The tests are a byproduct of good design practices.
