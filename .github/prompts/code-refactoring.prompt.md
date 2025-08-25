# Code Refactoring Prompt

You are conducting systematic code refactoring to improve code quality, maintainability, and performance without changing external behavior.
Follow this comprehensive approach to identify refactoring opportunities and implement improvements safely.

## Refactoring Methodology

### 1. Pre-Refactoring Assessment

#### Code Quality Analysis

- [ ] **Cyclomatic Complexity**: Identify methods with complexity >10
- [ ] **Code Duplication**: Find repeated code blocks >5 lines
- [ ] **Method Length**: Flag methods >50 lines for potential extraction
- [ ] **Class Size**: Review classes >500 lines for single responsibility violations
- [ ] **Technical Debt**: Assess TODO comments, hack comments, deprecated code

#### Performance Profiling

```Python

## Example: Performance profiling before refactoring

import cProfile
import pstats
from functools import wraps

def profile_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()

        result = func(*args, **kwargs)

        profiler.disable()
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')

## Log performance data

        print(f"Performance profile for {func.**name**}:")
        stats.print_stats(10)  # Top 10 slowest operations

        return result
    return wrapper

## Usage: Profile methods before refactoring

@profile_performance
def complex_business_logic(data):

## Complex logic to be refactored

    pass

```Markdown

### Test Coverage Verification

```bash

## Ensure comprehensive test coverage before refactoring

pytest --cov=src --cov-report=HTML --cov-report=term-missing
coverage report --fail-under=85

## Generate baseline coverage report

coverage HTML -d coverage_baseline/

```Markdown

### 2. Refactoring Catalog

#### Extract Method Refactoring

```Python

## Before: Long method with multiple responsibilities

def process_user_registration(user_data):

## Email validation

    email = user_data.get('email', '').strip().lower()
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        raise ValueError('Invalid email format')

## Password validation

    password = user_data.get('password', '')
    if len(password) < 8:
        raise ValueError('Password too short')
    if not any(c.isupper() for c in password):
        raise ValueError('Password needs uppercase')
    if not any(c.islower() for c in password):
        raise ValueError('Password needs lowercase')
    if not any(c.isdigit() for c in password):
        raise ValueError('Password needs digit')

## Database operations

    if database.email_exists(email):
        raise ValueError('Email already exists')

    user_id = database.create_user({
        'email': email,
        'password': hash_password(password),
        'name': user_data.get('name', '').strip()
    })

## Email notification

    try:
        send_welcome_email(email, user_data.get('name', ''))
    except EmailError:
        logger.warning(f'Failed to send welcome email to {email}')

    return user_id

## After: Extracted methods with single responsibilities

def process_user_registration(user_data):
    """Process user registration with validation and notification"""
    validated_data = self._validate_registration_data(user_data)
    user_id = self._create_user_account(validated_data)
    self._send_welcome_notification(validated_data)
    return user_id

def _validate_registration_data(self, user_data):
    """Validate and normalize user registration data"""
    email = self._validate_and_normalize_email(user_data.get('email', ''))
    password = self._validate_password(user_data.get('password', ''))
    name = user_data.get('name', '').strip()

    return {
        'email': email,
        'password': password,
        'name': name
    }

def _validate_and_normalize_email(self, email):
    """Validate email format and normalize"""
    normalized_email = email.strip().lower()

    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', normalized_email):
        raise ValueError('Invalid email format')

    if self.database.email_exists(normalized_email):
        raise ValueError('Email already exists')

    return normalized_email

def _validate_password(self, password):
    """Validate password strength requirements"""
    requirements = [
        (len(password) >= 8, 'Password must be at least 8 characters'),
        (any(c.isupper() for c in password), 'Password must contain uppercase letter'),
        (any(c.islower() for c in password), 'Password must contain lowercase letter'),
        (any(c.isdigit() for c in password), 'Password must contain digit'),
    ]

    for is_valid, error_message in requirements:
        if not is_valid:
            raise ValueError(error_message)

    return password

def _create_user_account(self, user_data):
    """Create user account in database"""
    return self.database.create_user({
        'email': user_data['email'],
        'password': self._hash_password(user_data['password']),
        'name': user_data['name']
    })

def _send_welcome_notification(self, user_data):
    """Send welcome email notification"""
    try:
        self.email_service.send_welcome_email(
            user_data['email'],
            user_data['name']
        )
    except EmailError as e:
        self.logger.warning(f'Failed to send welcome email to {user_data["email"]}: {e}')

```Markdown

### Extract Class Refactoring

```Python

## Before: God class with multiple responsibilities

class UserManager:
    def **init**(self):
        self.database = Database()
        self.email_service = EmailService()
        self.logger = Logger()

    def register_user(self, user_data):

## User registration logic

        pass

    def authenticate_user(self, email, password):

## Authentication logic

        pass

    def update_user_profile(self, user_id, profile_data):

## Profile update logic

        pass

    def send_password_reset(self, email):

## Password reset logic

        pass

    def generate_user_report(self, filters):

## Reporting logic

        pass

    def export_user_data(self, format):

## Data export logic

        pass

## After: Extracted classes with single responsibilities

class UserRegistrationService:
    """Handles user registration and account creation"""

    def **init**(self, database, email_service, validator):
        self.database = database
        self.email_service = email_service
        self.validator = validator

    def register_user(self, user_data):
        validated_data = self.validator.validate_registration(user_data)
        user_id = self.database.create_user(validated_data)
        self.email_service.send_welcome_email(validated_data['email'])
        return user_id

class UserAuthenticationService:
    """Handles user authentication and session management"""

    def **init**(self, database, session_manager):
        self.database = database
        self.session_manager = session_manager

    def authenticate_user(self, email, password):
        user = self.database.get_user_by_email(email)
        if user and self._verify_password(password, user.password_hash):
            return self.session_manager.create_session(user.id)
        return None

class UserProfileService:
    """Handles user profile management"""

    def **init**(self, database, validator):
        self.database = database
        self.validator = validator

    def update_profile(self, user_id, profile_data):
        validated_data = self.validator.validate_profile_update(profile_data)
        return self.database.update_user_profile(user_id, validated_data)

class UserReportingService:
    """Handles user data reporting and analytics"""

    def **init**(self, database, report_generator):
        self.database = database
        self.report_generator = report_generator

    def generate_user_report(self, filters):
        user_data = self.database.get_users_by_filters(filters)
        return self.report_generator.create_report(user_data)

## Facade to maintain existing interface

class UserManager:
    """Facade for user management operations"""

    def **init**(self):

## Initialize all services

        self.database = Database()
        self.email_service = EmailService()
        self.validator = UserValidator()
        self.session_manager = SessionManager()
        self.report_generator = ReportGenerator()

## Initialize specialized services

        self.registration_service = UserRegistrationService(
            self.database, self.email_service, self.validator
        )
        self.auth_service = UserAuthenticationService(
            self.database, self.session_manager
        )
        self.profile_service = UserProfileService(
            self.database, self.validator
        )
        self.reporting_service = UserReportingService(
            self.database, self.report_generator
        )

    def register_user(self, user_data):
        return self.registration_service.register_user(user_data)

    def authenticate_user(self, email, password):
        return self.auth_service.authenticate_user(email, password)

    def update_user_profile(self, user_id, profile_data):
        return self.profile_service.update_profile(user_id, profile_data)

    def generate_user_report(self, filters):
        return self.reporting_service.generate_user_report(filters)

```Markdown

### Replace Conditional with Polymorphism

```Python

## Before: Complex conditional logic

def calculate_shipping_cost(order, shipping_type):
    if shipping_type == 'standard':
        if order.total < 50:
            return 9.99
        elif order.total < 100:
            return 4.99
        else:
            return 0.00
    elif shipping_type == 'express':
        if order.weight < 2:
            return 14.99
        elif order.weight < 5:
            return 19.99
        else:
            return 24.99 + (order.weight - 5) * 2.50
    elif shipping_type == 'overnight':
        base_cost = 29.99
        if order.weight > 1:
            base_cost += (order.weight - 1) * 5.00
        if order.is_fragile:
            base_cost += 10.00
        return base_cost
    else:
        raise ValueError(f'Unknown shipping type: {shipping_type}')

## After: Polymorphic shipping calculators

from abc import ABC, abstractmethod

class ShippingCalculator(ABC):
    """Abstract base class for shipping cost calculation"""

    @abstractmethod
    def calculate_cost(self, order) -> float:
        pass

    @abstractmethod
    def get_estimated_delivery_days(self) -> int:
        pass

class StandardShippingCalculator(ShippingCalculator):
    """Standard shipping with total-based pricing"""

    def calculate_cost(self, order) -> float:
        if order.total < 50:
            return 9.99
        elif order.total < 100:
            return 4.99
        else:
            return 0.00  # Free shipping over $100

    def get_estimated_delivery_days(self) -> int:
        return 5

class ExpressShippingCalculator(ShippingCalculator):
    """Express shipping with weight-based pricing"""

    def calculate_cost(self, order) -> float:
        if order.weight < 2:
            return 14.99
        elif order.weight < 5:
            return 19.99
        else:
            return 24.99 + (order.weight - 5) * 2.50

    def get_estimated_delivery_days(self) -> int:
        return 2

class OvernightShippingCalculator(ShippingCalculator):
    """Overnight shipping with weight and fragility considerations"""

    def calculate_cost(self, order) -> float:
        base_cost = 29.99

## Weight surcharge

        if order.weight > 1:
            base_cost += (order.weight - 1) * 5.00

## Fragile item surcharge

        if order.is_fragile:
            base_cost += 10.00

        return base_cost

    def get_estimated_delivery_days(self) -> int:
        return 1

class ShippingService:
    """Service for calculating shipping costs using strategy pattern"""

    def **init**(self):
        self.calculators = {
            'standard': StandardShippingCalculator(),
            'express': ExpressShippingCalculator(),
            'overnight': OvernightShippingCalculator(),
        }

    def calculate_shipping_cost(self, order, shipping_type):
        calculator = self.calculators.get(shipping_type)
        if not calculator:
            raise ValueError(f'Unknown shipping type: {shipping_type}')

        return calculator.calculate_cost(order)

    def get_estimated_delivery(self, shipping_type):
        calculator = self.calculators.get(shipping_type)
        if not calculator:
            raise ValueError(f'Unknown shipping type: {shipping_type}')

        return calculator.get_estimated_delivery_days()

    def get_available_shipping_options(self, order):
        """Get all available shipping options with costs"""
        options = []
        for shipping_type, calculator in self.calculators.items():
            cost = calculator.calculate_cost(order)
            delivery_days = calculator.get_estimated_delivery_days()

            options.append({
                'type': shipping_type,
                'cost': cost,
                'delivery_days': delivery_days
            })

        return sorted(options, key=lambda x: x['cost'])

```Markdown

### Replace Magic Numbers/Strings with Constants

```Python

## Before: Magic numbers and strings scattered throughout code

def validate_user_input(user_data):
    if len(user_data['password']) < 8:
        return False
    if len(user_data['username']) > 50:
        return False
    if user_data['role'] not in ['admin', 'user', 'guest']:
        return False
    return True

def calculate_subscription_price(plan, duration):
    if plan == 'basic':
        monthly_price = 9.99
    elif plan == 'premium':
        monthly_price = 19.99
    elif plan == 'enterprise':
        monthly_price = 49.99

    if duration == 12:
        discount = 0.15  # 15% annual discount
    elif duration == 6:
        discount = 0.10  # 10% semi-annual discount
    else:
        discount = 0.0

    return monthly_price _duration_ (1 - discount)

## After: Extracted constants and configuration

class UserValidationConstants:
    MIN_PASSWORD_LENGTH = 8
    MAX_USERNAME_LENGTH = 50
    VALID_ROLES = ['admin', 'user', 'guest']

class SubscriptionConfig:
    PLANS = {
        'basic': 9.99,
        'premium': 19.99,
        'enterprise': 49.99
    }

    DURATION_DISCOUNTS = {
        12: 0.15,  # 15% annual discount
        6: 0.10,   # 10% semi-annual discount
    }

    DEFAULT_DISCOUNT = 0.0

class UserValidator:
    """Centralized user validation with clear constants"""

    @staticmethod
    def validate_user_input(user_data):
        errors = []

## Password validation 2

        password = user_data.get('password', '')
        if len(password) < UserValidationConstants.MIN_PASSWORD_LENGTH:
            errors.append(f'Password must be at least {UserValidationConstants.MIN_PASSWORD_LENGTH} characters')

## Username validation

        username = user_data.get('username', '')
        if len(username) > UserValidationConstants.MAX_USERNAME_LENGTH:
            errors.append(f'Username cannot exceed {UserValidationConstants.MAX_USERNAME_LENGTH} characters')

## Role validation

        role = user_data.get('role', '')
        if role not in UserValidationConstants.VALID_ROLES:
            errors.append(f'Role must be one of: {", ".join(UserValidationConstants.VALID_ROLES)}')

        return len(errors) == 0, errors

class SubscriptionPricing:
    """Centralized subscription pricing logic"""

    @staticmethod
    def calculate_price(plan, duration_months):
        if plan not in SubscriptionConfig.PLANS:
            raise ValueError(f'Invalid plan: {plan}.
Available plans: {list(SubscriptionConfig.PLANS.keys())}')

        monthly_price = SubscriptionConfig.PLANS[plan]
        discount = SubscriptionConfig.DURATION_DISCOUNTS.get(duration_months, SubscriptionConfig.DEFAULT_DISCOUNT)

        subtotal = monthly_price * duration_months
        discount_amount = subtotal * discount

        return {
            'monthly_price': monthly_price,
            'duration_months': duration_months,
            'subtotal': subtotal,
            'discount_rate': discount,
            'discount_amount': discount_amount,
            'total': subtotal - discount_amount
        }

```Markdown

### 3. Refactoring Safety Measures

#### Automated Testing Safety Net

```Python

## Test suite to verify refactoring doesn't break functionality

import pytest
from unittest.mock import Mock

class TestRefactoringSafety:
    """Test suite to ensure refactoring maintains behavior"""

    def setup_method(self):
        self.original_behavior_tests = [
            self.test_user_registration_success,
            self.test_user_registration_duplicate_email,
            self.test_user_registration_invalid_data,
            self.test_shipping_calculation_accuracy,
            self.test_subscription_pricing_accuracy
        ]

    def test_refactoring_maintains_original_behavior(self):
        """Meta-test to ensure all original behavior tests still pass"""
        for test in self.original_behavior_tests:
            try:
                test()
            except Exception as e:
                pytest.fail(f"Refactoring broke original behavior in {test.**name**}: {e}")

    @pytest.mark.parametrize("test_data,expected_result", [
        (
            {'email': 'test@example.com', 'password': 'SecurePass123!', 'name': 'Test User'},
            {'success': True, 'user_id': 12345}
        ),

## Add more test cases

    ])
    def test_user_registration_behavior_preserved(self, test_data, expected_result):
        """Verify user registration behavior is preserved after refactoring"""

## Test both old and new implementations produce same results

        pass

## Regression testing framework

def create_regression_test_suite():
    """Create comprehensive regression test suite before refactoring"""

    test_cases = [

## Input/output pairs for all public methods

        {
            'method': 'register_user',
            'inputs': [
                {'email': 'test@example.com', 'password': 'SecurePass123!', 'name': 'Test User'},
                {'email': 'invalid-email', 'password': 'weak', 'name': ''},

## ... more test cases

            ],
            'expected_outputs': [
                {'success': True, 'user_id': 12345},
                {'success': False, 'error': 'Invalid email format'},

## ... corresponding expected outputs

            ]
        }
    ]

    return test_cases

```Markdown

### Code Metrics Monitoring

```Python

## Code quality metrics monitoring

import ast
import os
from typing import Dict, List

class CodeMetrics:
    """Monitor code quality metrics during refactoring"""

    def **init**(self, source_directory):
        self.source_directory = source_directory

    def calculate_cyclomatic_complexity(self, file_path) -> Dict[str, int]:
        """Calculate cyclomatic complexity for all functions in file"""
        with open(file_path, 'r') as file:
            tree = ast.parse(file.read())

        complexity_map = {}

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._calculate_complexity(node)
                complexity_map[node.name] = complexity

        return complexity_map

    def _calculate_complexity(self, node) -> int:
        """Calculate cyclomatic complexity for a function"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1

        return complexity

    def measure_code_duplication(self) -> Dict[str, List[str]]:
        """Identify potential code duplication"""

## Implementation for duplicate code detection

        pass

    def generate_metrics_report(self) -> Dict:
        """Generate comprehensive code metrics report"""
        report = {
            'complexity': {},
            'duplication': {},
            'file_sizes': {},
            'test_coverage': {}
        }

        for root, dirs, files in os.walk(self.source_directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    report['complexity'][file] = self.calculate_cyclomatic_complexity(file_path)

        return report

## Usage: Monitor metrics before and after refactoring

def monitor_refactoring_impact():
    metrics = CodeMetrics('src/')

## Baseline metrics

    baseline_report = metrics.generate_metrics_report()

## ... perform refactoring 

## Post-refactoring metrics

    post_refactoring_report = metrics.generate_metrics_report()

## Compare and validate improvements

    return compare_metrics(baseline_report, post_refactoring_report)

```Markdown

### 4. Refactoring Checklist

#### Pre-Refactoring Checklist

- [ ] **Comprehensive test suite** exists with >85% coverage
- [ ] **Baseline metrics** captured (complexity, performance, size)
- [ ] **Version control** state is clean (all changes committed)
- [ ] **Backup strategy** in place for rollback if needed
- [ ] **Stakeholder notification** of refactoring plans

#### During Refactoring Checklist

- [ ] **Small, incremental changes** - refactor in small steps
- [ ] **Run tests frequently** - after each refactoring step
- [ ] **Maintain external behavior** - no functional changes
- [ ] **Update documentation** as code structure changes
- [ ] **Commit regularly** with descriptive messages

#### Post-Refactoring Checklist

- [ ] **All tests pass** with same or better coverage
- [ ] **Performance metrics** maintained or improved
- [ ] **Code metrics improved** (complexity, duplication, readability)
- [ ] **Documentation updated** to reflect new structure
- [ ] **Code review completed** by team members
- [ ] **Integration testing** passes in all environments

### 5. Refactoring Report Template

```Markdown

## Code Refactoring Report - [Module/Component Name]

## Summary

- **Refactoring Date**: [Date]
- **Modules Affected**: [List of modified files/classes]
- **Refactoring Type**: [Extract Method, Extract Class, etc.]
- **Rationale**: [Why refactoring was needed]

## Metrics Comparison

### Before Refactoring

- **Cyclomatic Complexity**: Average X, Max Y
- **Lines of Code**: X lines
- **Test Coverage**: X%
- **Code Duplication**: X instances
- **Performance**: X ms average response time

### After Refactoring

- **Cyclomatic Complexity**: Average X, Max Y (±Z change)
- **Lines of Code**: X lines (±Z change)
- **Test Coverage**: X% (±Z change)
- **Code Duplication**: X instances (±Z change)
- **Performance**: X ms average response time (±Z change)

## Changes Made

### Structural Changes

1. **Extracted Methods**: [List of new methods]
2. **Extracted Classes**: [List of new classes]
3. **Eliminated Duplication**: [Description of removed duplicates]
4. **Improved Naming**: [Renamed variables/methods/classes]

### Quality Improvements

- **Readability**: [How code is more readable]
- **Maintainability**: [How code is easier to maintain]
- **Testability**: [How code is easier to test]
- **Performance**: [Any performance improvements]

## Risk Assessment

- **Breaking Changes**: None (refactoring maintains external behavior)
- **Compatibility**: All existing tests pass
- **Dependencies**: No new external dependencies introduced
- **Rollback Plan**: Git commit SHA for rollback if needed

## Future Improvements

1. [Additional refactoring opportunities identified]
2. [Technical debt items to address next]
3. [Performance optimization opportunities]

## Validation

- [ ] All existing tests pass
- [ ] New tests added for extracted methods/classes
- [ ] Code review completed
- [ ] Performance testing passed
- [ ] Documentation updated

```Markdown

Remember: Refactoring is an ongoing process of continuous improvement.
Small, frequent refactoring efforts are more effective and less risky than large, infrequent refactoring projects
Always maintain test coverage and measure the impact of your changes.
