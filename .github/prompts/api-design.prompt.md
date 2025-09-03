---
title: "API Design Expert"
description:
  "Comprehensive RESTful API design assistant that follows industry best practices for scalability,
  security, and developer experience with OpenAPI specifications."
mode: "agent"
tools:
  [
    "codebase",
    "editFiles",
    "fetch",
    "githubRepo",
    "new",
    "openSimpleBrowser",
    "problems",
    "runCommands",
    "search",
    "searchResults",
    "usages",
    "vscodeAPI",
  ]
model: "GPT-4"
---

# API Design Expert

You are designing a RESTful API that follows industry best practices for scalability, security, and
developer experience. Create comprehensive API specifications with clear contracts, proper error
handling, and documentation.

## API Design Methodology

### 1. Resource-Based Design

#### Resource Identification

- [ ] **Primary Resources**: Identify main business entities (users, orders, products)
- [ ] **Resource Relationships**: Map parent-child and many-to-many relationships
- [ ] **Resource Hierarchies**: Define nested resource structures
- [ ] **Virtual Resources**: Identify computed or aggregated resources

#### RESTful URL Design

````YAML

## Example: E-commerce API resource structure

resources:
  users:
    path: /API/v1/users
    operations:

- GET /API/v1/users                    # List users
- POST /API/v1/users                   # Create user
- GET /API/v1/users/{userId}           # Get user
- PUT /API/v1/users/{userId}           # Update user
- DELETE /API/v1/users/{userId}        # Delete user

  nested_resources:
  orders:
  path: /API/v1/users/{userId}/orders
  operations:

- GET /API/v1/users/{userId}/orders                # List user orders
- POST /API/v1/users/{userId}/orders               # Create order for user
- GET /API/v1/users/{userId}/orders/{orderId}      # Get specific order
- PUT /API/v1/users/{userId}/orders/{orderId}      # Update order
- DELETE /API/v1/users/{userId}/orders/{orderId}   # Cancel order

  products:
  path: /API/v1/products
  operations:

- GET /API/v1/products                 # List products
- POST /API/v1/products                # Create product
- GET /API/v1/products/{productId}     # Get product
- PUT /API/v1/products/{productId}     # Update product
- DELETE /API/v1/products/{productId}  # Delete product

  search:
  path: /API/v1/products/search
  operations:

- GET /API/v1/products/search?q={query}&category={category}&price_min={min}&price_max={max}

  orders:
  path: /API/v1/orders
  operations:

- GET /API/v1/orders                   # List all orders (admin)
- GET /API/v1/orders/{orderId}         # Get order details
- PUT /API/v1/orders/{orderId}/status  # Update order status

```Markdown

### 2. HTTP Methods and Status Codes

#### Method Usage Guidelines

```Python

## HTTP Method selection guide

http_methods = {
    'GET': {
        'purpose': 'Retrieve resource(s)',
        'idempotent': True,
        'safe': True,
        'request_body': False,
        'examples': [
            'GET /API/v1/users/123',
            'GET /API/v1/users?page=1&limit=20'
        ]
    },
    'POST': {
        'purpose': 'Create new resource or non-idempotent operations',
        'idempotent': False,
        'safe': False,
        'request_body': True,
        'examples': [
            'POST /API/v1/users',
            'POST /API/v1/orders/123/payments'
        ]
    },
    'PUT': {
        'purpose': 'Create or completely replace resource',
        'idempotent': True,
        'safe': False,
        'request_body': True,
        'examples': [
            'PUT /API/v1/users/123',
            'PUT /API/v1/products/456'
        ]
    },
    'PATCH': {
        'purpose': 'Partial update of resource',
        'idempotent': True,
        'safe': False,
        'request_body': True,
        'examples': [
            'PATCH /API/v1/users/123',
            'PATCH /API/v1/orders/456/status'
        ]
    },
    'DELETE': {
        'purpose': 'Remove resource',
        'idempotent': True,
        'safe': False,
        'request_body': False,
        'examples': [
            'DELETE /API/v1/users/123',
            'DELETE /API/v1/orders/456'
        ]
    }
}

## Status code selection guide

status_codes = {
    'success': {
        200: 'OK - Successful GET, PUT, PATCH',
        201: 'Created - Successful POST with new resource',
        202: 'Accepted - Async operation started',
        204: 'No Content - Successful DELETE or PUT with no response body'
    },
    'client_error': {
        400: 'Bad Request - Invalid request syntax or data',
        401: 'Unauthorized - Authentication required',
        403: 'Forbidden - Authentication successful but insufficient permissions',
        404: 'Not Found - Resource does not exist',
        405: 'Method Not Allowed - HTTP method not supported for resource',
        409: 'Conflict - Resource state conflict (duplicate, constraint violation)',
        422: 'Unprocessable Entity - Valid syntax but semantic errors',
        429: 'Too Many Requests - Rate limit exceeded'
    },
    'server_error': {
        500: 'Internal Server Error - Generic server error',
        502: 'Bad Gateway - Invalid response from upstream server',
        503: 'Service Unavailable - Server temporarily unavailable',
        504: 'Gateway Timeout - Upstream server timeout'
    }
}

```Markdown

### 3. Request/Response Format Design

#### Request Structure

```JSON
// POST /API/v1/users - Create user request
{
  "data": {
    "type": "user",
    "attributes": {
      "email": "john.doe@example.com",
      "firstName": "John",
      "lastName": "Doe",
      "dateOfBirth": "1990-05-15",
      "preferences": {
        "newsletter": true,
        "notifications": {
          "email": true,
          "sms": false
        }
      }
    }
  },
  "meta": {
    "source": "web-app",
    "version": "1.2.3"
  }
}

// PATCH /API/v1/products/123 - Partial update request
{
  "data": {
    "type": "product",
    "id": "123",
    "attributes": {
      "price": 29.99,
      "inStock": true
    }
  }
}

// GET /API/v1/orders?status=pending&page=2&limit=20 - Query parameters
// Query parameters for filtering, pagination, sorting, and field selection

```Markdown

#### Response Structure

```JSON
// GET /API/v1/users/123 - Single resource response
{
  "data": {
    "type": "user",
    "id": "123",
    "attributes": {
      "email": "john.doe@example.com",
      "firstName": "John",
      "lastName": "Doe",
      "dateOfBirth": "1990-05-15",
      "createdAt": "2024-01-15T10:30:00Z",
      "updatedAt": "2024-01-20T14:45:00Z"
    },
    "relationships": {
      "orders": {
        "links": {
          "self": "/API/v1/users/123/relationships/orders",
          "related": "/API/v1/users/123/orders"
        },
        "meta": {
          "count": 5
        }
      }
    },
    "links": {
      "self": "/API/v1/users/123"
    }
  },
  "meta": {
    "responseTime": 45,
    "apiVersion": "1.0"
  }
}

// GET /API/v1/users - Collection response
{
  "data": [
    {
      "type": "user",
      "id": "123",
      "attributes": {
        "email": "john.doe@example.com",
        "firstName": "John",
        "lastName": "Doe"
      },
      "links": {
        "self": "/API/v1/users/123"
      }
    }
    // ... more users
  ],
  "meta": {
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 150,
      "totalPages": 8
    },
    "responseTime": 120
  },
  "links": {
    "self": "/API/v1/users?page=1&limit=20",
    "first": "/API/v1/users?page=1&limit=20",
    "prev": null,
    "next": "/API/v1/users?page=2&limit=20",
    "last": "/API/v1/users?page=8&limit=20"
  }
}

// Error response format
{
  "errors": [
    {
      "id": "ERR_VALIDATION_001",
      "status": "422",
      "code": "INVALID_EMAIL",
      "title": "Invalid email format",
      "detail": "The email address 'invalid-email' does not conform to RFC 5322 standards",
      "source": {
        "pointer": "/data/attributes/email"
      },
      "meta": {
        "timestamp": "2024-01-20T15:30:00Z",
        "requestId": "req_abc123def456"
      }
    }
  ],
  "meta": {
    "requestId": "req_abc123def456",
    "responseTime": 15
  }
}

```Markdown

### 4. Authentication and Authorization

#### Authentication Schemes

```Python

## JWT-based authentication implementation

from datetime import datetime, timedelta
import jwt
from functools import wraps

class APIAuthentication:
    """Handle API authentication and authorization"""

    def **init**(self, secret_key, algorithm='HS256'):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def generate_access_token(self, user_id, permissions, expires_in=3600):
        """Generate JWT access token"""
        payload = {
            'user_id': user_id,
            'permissions': permissions,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def generate_refresh_token(self, user_id, expires_in=604800):  # 7 days
        """Generate JWT refresh token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token):
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")

## Authorization decorators

def require_auth(permissions=None):
    """Decorator to require authentication and optional permissions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = extract_token_from_request()
            user = authenticate_token(token)

            if permissions and not user.has_permissions(permissions):
                raise ForbiddenError("Insufficient permissions")

## Add user to request context

            request.current_user = user
            return func(*args, **kwargs)
        return wrapper
    return decorator

## Usage examples

@require_auth(permissions=['user:read'])
def get_user(user_id):
    """Get user by ID - requires user:read permission"""
    pass

@require_auth(permissions=['user:write'])
def update_user(user_id):
    """Update user - requires user:write permission"""
    pass

@require_auth(permissions=['admin:read'])
def get_all_users():
    """Get all users - requires admin:read permission"""
    pass

```Markdown

### API Key Authentication

```Python

## API Key-based authentication for service-to-service communication

class APIKeyAuthentication:
    """Handle API key authentication for external services"""

    def **init**(self, api_key_service):
        self.api_key_service = api_key_service

    def generate_api_key(self, service_name, permissions, expires_at=None):
        """Generate new API key for service"""
        api_key = {
            'key': self._generate_secure_key(),
            'service_name': service_name,
            'permissions': permissions,
            'created_at': datetime.utcnow(),
            'expires_at': expires_at,
            'active': True
        }

        return self.api_key_service.store_api_key(api_key)

    def authenticate_api_key(self, key):
        """Authenticate API key and return service info"""
        api_key_info = self.api_key_service.get_api_key(key)

        if not api_key_info:
            raise AuthenticationError("Invalid API key")

        if not api_key_info['active']:
            raise AuthenticationError("API key is deactivated")

        if api_key_info['expires_at'] and datetime.utcnow() > api_key_info['expires_at']:
            raise AuthenticationError("API key has expired")

        return api_key_info

    def _generate_secure_key(self):
        """Generate cryptographically secure API key"""
        import secrets
        return f"ak_{secrets.token_urlsafe(32)}"

## Rate limiting per API key

@require_api_key
@rate_limit(requests_per_minute=100)
def api_endpoint():
    """API endpoint with rate limiting per API key"""
    pass

```Markdown

### 5. Pagination and Filtering

#### Pagination Implementation

```Python

## Cursor-based pagination for large datasets

class CursorPagination:
    """Implement cursor-based pagination for APIs"""

    def **init**(self, page_size=20, max_page_size=100):
        self.page_size = page_size
        self.max_page_size = max_page_size

    def paginate_queryset(self, queryset, cursor=None, page_size=None):
        """Apply cursor-based pagination to queryset"""
        page_size = min(page_size or self.page_size, self.max_page_size)

        if cursor:

## Decode cursor to get last item's sort key

            last_id = self._decode_cursor(cursor)
            queryset = queryset.filter(id__gt=last_id)

## Get one extra item to determine if there's a next page

        items = list[:page_size + 1](queryset.order_by('id'))

        has_next = len(items) > page_size
        if has_next:
            items = items[:-1]  # Remove the extra item

        next_cursor = None
        if has_next and items:
            next_cursor = self._encode_cursor(items[-1].id)

        return {
            'items': items,
            'pagination': {
                'page_size': page_size,
                'has_next': has_next,
                'next_cursor': next_cursor
            }
        }

    def _encode_cursor(self, item_id):
        """Encode cursor for pagination"""
        import base64
        return base64.b64encode(f"cursor:{item_id}".encode()).decode()

    def _decode_cursor(self, cursor):
        """Decode cursor to get item ID"""
        import base64
        try:
            decoded = base64.b64decode(cursor).decode()
            return int[1](decoded.split('cursor:'))
        except (ValueError, IndexError):
            raise ValidationError("Invalid cursor format")

## Offset-based pagination for smaller datasets

class OffsetPagination:
    """Implement offset-based pagination for APIs"""

    def **init**(self, page_size=20, max_page_size=100):
        self.page_size = page_size
        self.max_page_size = max_page_size

    def paginate_queryset(self, queryset, page=1, page_size=None):
        """Apply offset-based pagination to queryset"""
        page_size = min(page_size or self.page_size, self.max_page_size)
        offset = (page - 1) * page_size

        total_count = queryset.count()
        items = queryset[offset:offset + page_size]

        total_pages = (total_count + page_size - 1) // page_size

        return {
            'items': list(items),
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        }

```Markdown

### Advanced Filtering

```Python

## Query parameter filtering system

class APIFilterSet:
    """Handle complex filtering for API endpoints"""

    def **init**(self, model_class):
        self.model_class = model_class
        self.filters = {}

    def add_filter(self, param_name, field_name, filter_type='exact'):
        """Add a filter to the filter set"""
        self.filters[param_name] = {
            'field': field_name,
            'type': filter_type
        }

    def apply_filters(self, queryset, query_params):
        """Apply filters from query parameters to queryset"""
        for param_name, param_value in query_params.items():
            if param_name in self.filters:
                filter_config = self.filters[param_name]
                field_name = filter_config['field']
                filter_type = filter_config['type']

## Build filter expression

                if filter_type == 'exact':
                    filter_expr = {field_name: param_value}
                elif filter_type == 'icontains':
                    filter_expr = {f"{field_name}__icontains": param_value}
                elif filter_type == 'gte':
                    filter_expr = {f"{field_name}__gte": param_value}
                elif filter_type == 'lte':
                    filter_expr = {f"{field_name}__lte": param_value}
                elif filter_type == 'in':
                    values = param_value.split(',')
                    filter_expr = {f"{field_name}__in": values}
                elif filter_type == 'range':
                    min_val, max_val = param_value.split(',')
                    filter_expr = {
                        f"{field_name}__gte": min_val,
                        f"{field_name}__lte": max_val
                    }

                queryset = queryset.filter(**filter_expr)

        return queryset

## Example usage

class ProductFilterSet(APIFilterSet):
    """Filter set for product API endpoint"""

    def **init**(self):
        super().**init**(Product)
        self.add_filter('name', 'name', 'icontains')
        self.add_filter('category', 'category_id', 'exact')
        self.add_filter('price_min', 'price', 'gte')
        self.add_filter('price_max', 'price', 'lte')
        self.add_filter('price_range', 'price', 'range')
        self.add_filter('tags', 'tags__name', 'in')
        self.add_filter('created_after', 'created_at', 'gte')

## API endpoint with filtering

@app.route('/API/v1/products')
def get_products():
    """Get products with filtering, sorting, and pagination"""
    filter_set = ProductFilterSet()
    queryset = Product.objects.all()

## Apply filters

    queryset = filter_set.apply_filters(queryset, request.args)

## Apply sorting

    sort_by = request.args.get('sort', 'name')
    order = request.args.get('order', 'asc')
    if order == 'desc':
        sort_by = f'-{sort_by}'
    queryset = queryset.order_by(sort_by)

## Apply pagination

    paginator = OffsetPagination()
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))

    result = paginator.paginate_queryset(queryset, page, page_size)

    return jsonify({
        'data': [serialize_product(product) for product in result['items']],
        'meta': result['pagination'],
        'links': build_pagination_links(request.URL, result['pagination'])
    })

```Markdown

### 6. Error Handling and Validation

#### Comprehensive Error Response System

```Python

## Error handling framework

class APIError(Exception):
    """Base API error class"""

    def **init**(self, message, status_code=500, error_code=None, details=None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or 'INTERNAL_ERROR'
        self.details = details or {}
        super().**init**(message)

class ValidationError(APIError):
    """Validation error with field-specific details"""

    def **init**(self, message="Validation failed", field_errors=None):
        self.field_errors = field_errors or {}
        super().**init**(
            message=message,
            status_code=422,
            error_code='VALIDATION_ERROR',
            details={'field_errors': self.field_errors}
        )

class NotFoundError(APIError):
    """Resource not found error"""

    def **init**(self, resource_type, resource_id):
        message = f"{resource_type} with ID '{resource_id}' not found"
        super().**init**(
            message=message,
            status_code=404,
            error_code='RESOURCE_NOT_FOUND',
            details={'resource_type': resource_type, 'resource_id': resource_id}
        )

class RateLimitError(APIError):
    """Rate limit exceeded error"""

    def **init**(self, limit, window_seconds, retry_after):
        message = f"Rate limit exceeded: {limit} requests per {window_seconds} seconds"
        super().**init**(
            message=message,
            status_code=429,
            error_code='RATE_LIMIT_EXCEEDED',
            details={
                'limit': limit,
                'window_seconds': window_seconds,
                'retry_after': retry_after
            }
        )

## Global error handler

@app.errorhandler(APIError)
def handle_api_error(error):
    """Global API error handler"""
    response_data = {
        'errors': [{
            'id': generate_error_id(),
            'status': str(error.status_code),
            'code': error.error_code,
            'title': error.message,
            'detail': error.message,
            'meta': {
                'timestamp': datetime.utcnow().isoformat(),
                'request_id': get_request_id()
            }
        }]
    }

## Add field-specific errors for validation errors

    if isinstance(error, ValidationError):
        response_data['errors'][0]['source'] = {
            'field_errors': error.field_errors
        }

## Add details if available

    if error.details:
        response_data['errors'][0]['meta'].update(error.details)

    response = jsonify(response_data)
    response.status_code = error.status_code

## Add rate limiting headers

    if isinstance(error, RateLimitError):
        response.headers['Retry-After'] = str(error.details['retry_after'])

    return response

```Markdown

### Input Validation Framework

```Python

## Schema-based validation

from marshmallow import Schema, fields, validate, ValidationError as MarshmallowValidationError

class UserCreateSchema(Schema):
    """Schema for user creation validation"""

    email = fields.Email(required=True, validate=validate.Length(max=255))
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    date_of_birth = fields.Date(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8, max=128))
    phone = fields.Str(allow_none=True, validate=validate.Regexp(r'^\+?1?\d{9,15}$'))

    @validates('password')
    def validate_password_strength(self, password):
        """Custom password strength validation"""
        if not any(c.isupper() for c in password):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in password):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in password):
            raise ValidationError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            raise ValidationError('Password must contain at least one special character')

class UserUpdateSchema(Schema):
    """Schema for user update validation (partial updates allowed)"""

    first_name = fields.Str(validate=validate.Length(min=1, max=100))
    last_name = fields.Str(validate=validate.Length(min=1, max=100))
    phone = fields.Str(allow_none=True, validate=validate.Regexp(r'^\+?1?\d{9,15}$'))
    preferences = fields.Dict()

## Validation decorator

def validate_json(schema_class):
    """Decorator to validate JSON request body against schema"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                schema = schema_class()
                validated_data = schema.load(request.get_json() or {})
                request.validated_data = validated_data
                return func(*args, **kwargs)
            except MarshmallowValidationError as e:
                raise ValidationError(field_errors=e.messages)
        return wrapper
    return decorator

## Usage in API endpoints

@app.route('/API/v1/users', methods=['POST'])
@validate_json(UserCreateSchema)
def create_user():
    """Create new user with validation"""
    user_data = request.validated_data

## Check if email already exists

    if User.objects.filter(email=user_data['email']).exists():
        raise ValidationError(
            field_errors={'email': ['Email address already in use']}
        )

## Create user

    user = User.objects.create(**user_data)
    return jsonify(serialize_user(user)), 201

@app.route('/API/v1/users/<int:user_id>', methods=['PATCH'])
@validate_json(UserUpdateSchema)
def update_user(user_id):
    """Update user with partial validation"""
    user_data = request.validated_data

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise NotFoundError('User', user_id)

## Update user fields

    for field, value in user_data.items():
        setattr(user, field, value)

    user.save()
    return jsonify(serialize_user(user))

```Markdown

### 7. API Documentation

#### OpenAPI/Swagger Specification

```YAML

## openapi.YAML - Comprehensive API specification

openapi: 3.0.3
info:
  title: E-commerce API
  description: |
    Comprehensive e-commerce API providing user management, product catalog,
    order processing, and payment integration capabilities.

## Authentication

    This API uses JWT tokens for authentication. Include the token in the
    Authorization header: `Authorization: Bearer <token>`

## Rate Limiting

- Authenticated requests: 1000 requests per hour
- Unauthenticated requests: 100 requests per hour

## Pagination

  Collections use cursor-based pagination for performance. Use the `cursor`
  parameter to navigate through results.
  version: 1.0.0
  contact:
  name: API Support
  email: API-support@example.com
  URL: <HTTPS://example.com/API-support>
  license:
  name: MIT
  URL: <HTTPS://opensource.org/licenses/MIT>

servers:

- URL: <HTTPS://API.example.com/v1>

  description: Production server

- URL: <HTTPS://staging-API.example.com/v1>

  description: Staging server

- URL: <HTTP://localhost:8000/v1>

  description: Local development server

paths:
  /users:
    get:
      summary: List users
      description: Retrieve a paginated list of users with optional filtering
      parameters:

- name: cursor

  in: query
  description: Pagination cursor for next page
  schema:
  type: string

- name: page_size

  in: query
  description: Number of items per page (max 100)
  schema:
  type: integer
  minimum: 1
  maximum: 100
  default: 20

- name: email

  in: query
  description: Filter by email address (partial match)
  schema:
  type: string

- name: created_after

  in: query
  description: Filter users created after date
  schema:
  type: string
  format: date
  responses:
  200:
  description: Successful response
  content:
  application/JSON:
  schema:
  $ref: '#/components/schemas/UserListResponse'
  401:
  $ref: '#/components/responses/UnauthorizedError'
  429:
  $ref: '#/components/responses/RateLimitError'
  security:

- bearerAuth: ['user:read']

  post:
  summary: Create user
  description: Create a new user account
  requestBody:
  required: true
  content:
  application/JSON:
  schema:
  $ref: '#/components/schemas/UserCreateRequest'
  responses:
  201:
  description: User created successfully
  content:
  application/JSON:
  schema:
  $ref: '#/components/schemas/UserResponse'
  400:
  $ref: '#/components/responses/ValidationError'
  409:
  description: Email already exists
  content:
  application/JSON:
  schema:
  $ref: '#/components/schemas/ErrorResponse'
  security:

- bearerAuth: ['user:write']

  /users/{userId}:
  parameters:

- name: userId

  in: path
  required: true
  description: Unique identifier for the user
  schema:
  type: integer
  format: int64

  get:
  summary: Get user by ID
  description: Retrieve detailed information about a specific user
  responses:
  200:
  description: User found
  content:
  application/JSON:
  schema:
  $ref: '#/components/schemas/UserResponse'
  404:
  $ref: '#/components/responses/NotFoundError'
  security:

- bearerAuth: ['user:read']

  patch:
  summary: Update user
  description: Partially update user information
  requestBody:
  required: true
  content:
  application/JSON:
  schema:
  $ref: '#/components/schemas/UserUpdateRequest'
  responses:
  200:
  description: User updated successfully
  content:
  application/JSON:
  schema:
  $ref: '#/components/schemas/UserResponse'
  404:
  $ref: '#/components/responses/NotFoundError'
  422:
  $ref: '#/components/responses/ValidationError'
  security:

- bearerAuth: ['user:write']

components:
  schemas:
    User:
      type: object
      required:

- id
- email
- firstName
- lastName
- createdAt

  properties:
  id:
  type: integer
  format: int64
  example: 123
  email:
  type: string
  format: email
  example: john.doe@example.com
  firstName:
  type: string
  minLength: 1
  maxLength: 100
  example: John
  lastName:
  type: string
  minLength: 1
  maxLength: 100
  example: Doe
  dateOfBirth:
  type: string
  format: date
  example: '1990-05-15'
  phone:
  type: string
  pattern: '^\+?1?\d{9,15}$'
  example: '+1234567890'
  createdAt:
  type: string
  format: date-time
  example: '2024-01-15T10:30:00Z'
  updatedAt:
  type: string
  format: date-time
  example: '2024-01-20T14:45:00Z'

  UserCreateRequest:
  type: object
  required:

- email
- firstName
- lastName
- password
- dateOfBirth

  properties:
  email:
  type: string
  format: email
  maxLength: 255
  firstName:
  type: string
  minLength: 1
  maxLength: 100
  lastName:
  type: string
  minLength: 1
  maxLength: 100
  password:
  type: string
  minLength: 8
  maxLength: 128
  description: |
  Password must contain:

- At least 8 characters
- One uppercase letter
- One lowercase letter
- One digit
- One special character

  dateOfBirth:
  type: string
  format: date
  phone:
  type: string
  pattern: '^\+?1?\d{9,15}$'

  UserUpdateRequest:
  type: object
  properties:
  firstName:
  type: string
  minLength: 1
  maxLength: 100
  lastName:
  type: string
  minLength: 1
  maxLength: 100
  phone:
  type: string
  pattern: '^\+?1?\d{9,15}$'
  preferences:
  type: object
  description: User preferences object

  UserResponse:
  type: object
  properties:
  data:
  $ref: '#/components/schemas/User'
  meta:
  type: object
  properties:
  responseTime:
  type: integer
  description: Response time in milliseconds

  UserListResponse:
  type: object
  properties:
  data:
  type: array
  items:
  $ref: '#/components/schemas/User'
  meta:
  type: object
  properties:
  pagination:
  $ref: '#/components/schemas/CursorPagination'
  responseTime:
  type: integer
  links:
  $ref: '#/components/schemas/PaginationLinks'

  CursorPagination:
  type: object
  properties:
  pageSize:
  type: integer
  hasNext:
  type: boolean
  nextCursor:
  type: string
  nullable: true

  PaginationLinks:
  type: object
  properties:
  self:
  type: string
  format: URI
  next:
  type: string
  format: URI
  nullable: true

  ErrorResponse:
  type: object
  properties:
  errors:
  type: array
  items:
  $ref: '#/components/schemas/Error'
  meta:
  type: object
  properties:
  requestId:
  type: string
  responseTime:
  type: integer

  Error:
  type: object
  required:

- id
- status
- code
- title

  properties:
  id:
  type: string
  description: Unique error identifier
  status:
  type: string
  description: HTTP status code
  code:
  type: string
  description: Application-specific error code
  title:
  type: string
  description: Short error summary
  detail:
  type: string
  description: Detailed error description
  source:
  type: object
  description: Error source information
  meta:
  type: object
  description: Additional error metadata

  responses:
  UnauthorizedError:
  description: Authentication required
  content:
  application/JSON:
  schema:
  $ref: '#/components/schemas/ErrorResponse'

  ValidationError:
  description: Validation failed
  content:
  application/JSON:
  schema:
  $ref: '#/components/schemas/ErrorResponse'

  NotFoundError:
  description: Resource not found
  content:
  application/JSON:
  schema:
  $ref: '#/components/schemas/ErrorResponse'

  RateLimitError:
  description: Rate limit exceeded
  headers:
  Retry-After:
  description: Seconds until rate limit resets
  schema:
  type: integer
  content:
  application/JSON:
  schema:
  $ref: '#/components/schemas/ErrorResponse'

  securitySchemes:
  bearerAuth:
  type: HTTP
  scheme: bearer
  bearerFormat: JWT
  description: |
  JWT token authentication. Include the token in the Authorization header:
  `Authorization: Bearer <token>`

security:

- bearerAuth: []

```Markdown

### 8. API Testing Strategy

#### Comprehensive Test Suite

```Python

## API testing framework

import pytest
import requests
from unittest.mock import Mock, patch

class APITestClient:
    """Test client for API testing"""

    def **init**(self, base_url, auth_token=None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

        if auth_token:
            self.session.headers.update({
                'Authorization': f'Bearer {auth_token}'
            })

    def get(self, endpoint, **kwargs):
        """Make GET request"""
        URL = f"{self.base_url}{endpoint}"
        return self.session.get(URL, **kwargs)

    def post(self, endpoint, JSON=None, **kwargs):
        """Make POST request"""
        URL = f"{self.base_url}{endpoint}"
        return self.session.post(URL, JSON=JSON, **kwargs)

    def patch(self, endpoint, JSON=None, **kwargs):
        """Make PATCH request"""
        URL = f"{self.base_url}{endpoint}"
        return self.session.patch(URL, JSON=JSON, **kwargs)

    def delete(self, endpoint, **kwargs):
        """Make DELETE request"""
        URL = f"{self.base_url}{endpoint}"
        return self.session.delete(URL, **kwargs)

class TestUserAPI:
    """Comprehensive user API tests"""

    @pytest.fixture
    def api_client(self):
        """Create authenticated API client"""
        return APITestClient(
            base_url='<HTTP://localhost:8000/API/v1',>
            auth_token='test_token_with_user_permissions'
        )

    @pytest.fixture
    def admin_client(self):
        """Create admin API client"""
        return APITestClient(
            base_url='<HTTP://localhost:8000/API/v1',>
            auth_token='test_token_with_admin_permissions'
        )

    def test_create_user_success(self, api_client):
        """Test successful user creation"""
        user_data = {
            'email': 'test@example.com',
            'firstName': 'Test',
            'lastName': 'User',
            'password': 'SecurePassword123!',
            'dateOfBirth': '1990-01-01'
        }

        response = api_client.post('/users', JSON=user_data)

        assert response.status_code == 201

        response_data = response.JSON()
        assert 'data' in response_data
        assert response_data['data']['email'] == user_data['email']
        assert response_data['data']['firstName'] == user_data['firstName']
        assert 'id' in response_data['data']
        assert 'password' not in response_data['data']  # Password should not be returned

    def test_create_user_validation_errors(self, api_client):
        """Test user creation with validation errors"""
        invalid_user_data = {
            'email': 'invalid-email',
            'firstName': '',
            'lastName': 'User',
            'password': 'weak',
            'dateOfBirth': 'invalid-date'
        }

        response = api_client.post('/users', JSON=invalid_user_data)

        assert response.status_code == 422

        response_data = response.JSON()
        assert 'errors' in response_data

        error = response_data['errors'][0]
        assert error['code'] == 'VALIDATION_ERROR'
        assert 'source' in error
        assert 'field_errors' in error['source']

        field_errors = error['source']['field_errors']
        assert 'email' in field_errors
        assert 'firstName' in field_errors
        assert 'password' in field_errors
        assert 'dateOfBirth' in field_errors

    def test_create_user_duplicate_email(self, api_client):
        """Test user creation with duplicate email"""

## Create first user

        user_data = {
            'email': 'duplicate@example.com',
            'firstName': 'First',
            'lastName': 'User',
            'password': 'SecurePassword123!',
            'dateOfBirth': '1990-01-01'
        }

        response1 = api_client.post('/users', JSON=user_data)
        assert response1.status_code == 201

## Try to create second user with same email

        user_data['firstName'] = 'Second'
        response2 = api_client.post('/users', JSON=user_data)

        assert response2.status_code == 409

        response_data = response2.JSON()
        assert response_data['errors'][0]['code'] == 'EMAIL_ALREADY_EXISTS'

    def test_get_user_success(self, api_client):
        """Test successful user retrieval"""

## Create user first

        user_data = {
            'email': 'gettest@example.com',
            'firstName': 'Get',
            'lastName': 'Test',
            'password': 'SecurePassword123!',
            'dateOfBirth': '1990-01-01'
        }

        create_response = api_client.post('/users', JSON=user_data)
        user_id = create_response.JSON()['data']['id']

## Get user

        response = api_client.get(f'/users/{user_id}')

        assert response.status_code == 200

        response_data = response.JSON()
        assert response_data['data']['id'] == user_id
        assert response_data['data']['email'] == user_data['email']

    def test_get_user_not_found(self, api_client):
        """Test user retrieval with non-existent ID"""
        response = api_client.get('/users/99999')

        assert response.status_code == 404

        response_data = response.JSON()
        assert response_data['errors'][0]['code'] == 'RESOURCE_NOT_FOUND'

    def test_list_users_pagination(self, admin_client):
        """Test user listing with pagination"""

## Create multiple users for pagination testing

        for i in range(25):
            user_data = {
                'email': f'pagtest{i}@example.com',
                'firstName': f'User{i}',
                'lastName': 'Test',
                'password': 'SecurePassword123!',
                'dateOfBirth': '1990-01-01'
            }
            admin_client.post('/users', JSON=user_data)

## Test first page

        response = admin_client.get('/users?page_size=10')

        assert response.status_code == 200

        response_data = response.JSON()
        assert len(response_data['data']) == 10
        assert 'meta' in response_data
        assert 'pagination' in response_data['meta']
        assert 'links' in response_data
        assert response_data['links']['next'] is not None

    @pytest.mark.parametrize("filter_param,filter_value,expected_count", [
        ('email', 'filtertest', 2),
        ('firstName', 'Filter', 2),
        ('created_after', '2024-01-01', 2)
    ])
    def test_list_users_filtering(self, admin_client, filter_param, filter_value, expected_count):
        """Test user listing with various filters"""

## Create test users

        for i in range(2):
            user_data = {
                'email': f'filtertest{i}@example.com',
                'firstName': f'FilterUser{i}',
                'lastName': 'Test',
                'password': 'SecurePassword123!',
                'dateOfBirth': '1990-01-01'
            }
            admin_client.post('/users', JSON=user_data)

## Test filtering

        response = admin_client.get(f'/users?{filter_param}={filter_value}')

        assert response.status_code == 200

        response_data = response.JSON()
        assert len(response_data['data']) >= expected_count

    def test_update_user_success(self, api_client):
        """Test successful user update"""

## Create user first 2

        user_data = {
            'email': 'updatetest@example.com',
            'firstName': 'Original',
            'lastName': 'Name',
            'password': 'SecurePassword123!',
            'dateOfBirth': '1990-01-01'
        }

        create_response = api_client.post('/users', JSON=user_data)
        user_id = create_response.JSON()['data']['id']

## Update user

        update_data = {
            'firstName': 'Updated',
            'phone': '+1234567890'
        }

        response = api_client.patch(f'/users/{user_id}', JSON=update_data)

        assert response.status_code == 200

        response_data = response.JSON()
        assert response_data['data']['firstName'] == 'Updated'
        assert response_data['data']['phone'] == '+1234567890'
        assert response_data['data']['lastName'] == 'Name'  # Unchanged

    def test_rate_limiting(self, api_client):
        """Test API rate limiting"""

## Make many requests quickly

        responses = []
        for i in range(10):
            response = api_client.get('/users/1')
            responses.append(response)

## Check if any request was rate limited

        rate_limited = any(r.status_code == 429 for r in responses)

        if rate_limited:
            rate_limited_response = next(r for r in responses if r.status_code == 429)
            assert 'Retry-After' in rate_limited_response.headers

            response_data = rate_limited_response.JSON()
            assert response_data['errors'][0]['code'] == 'RATE_LIMIT_EXCEEDED'

## Integration testing

class TestAPIIntegration:
    """Integration tests for API workflows"""

    def test_complete_user_lifecycle(self, api_client):
        """Test complete user CRUD lifecycle"""

## 1. Create user

        user_data = {
            'email': 'lifecycle@example.com',
            'firstName': 'Lifecycle',
            'lastName': 'Test',
            'password': 'SecurePassword123!',
            'dateOfBirth': '1990-01-01'
        }

        create_response = api_client.post('/users', JSON=user_data)
        assert create_response.status_code == 201
        user_id = create_response.JSON()['data']['id']

## 2. Read user

        get_response = api_client.get(f'/users/{user_id}')
        assert get_response.status_code == 200
        assert get_response.JSON()['data']['email'] == user_data['email']

## 3. Update user

        update_data = {'firstName': 'Updated'}
        update_response = api_client.patch(f'/users/{user_id}', JSON=update_data)
        assert update_response.status_code == 200
        assert update_response.JSON()['data']['firstName'] == 'Updated'

## 4. Delete user

        delete_response = api_client.delete(f'/users/{user_id}')
        assert delete_response.status_code == 204

## 5. Verify deletion

        get_deleted_response = api_client.get(f'/users/{user_id}')
        assert get_deleted_response.status_code == 404

## Load testing setup

def test_api_performance():
    """Basic performance test"""
    import time
    import concurrent.futures

    def make_request():
        client = APITestClient('<HTTP://localhost:8000/API/v1>')
        start_time = time.time()
        response = client.get('/users')
        end_time = time.time()
        return {
            'status_code': response.status_code,
            'response_time': end_time - start_time
        }

## Test concurrent requests

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(100)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]

## Analyze results

    successful_requests = [r for r in results if r['status_code'] == 200]
    avg_response_time = sum(r['response_time'] for r in successful_requests) / len(successful_requests)

    assert len(successful_requests) >= 95  # 95% success rate
    assert avg_response_time < 1.0  # Average response time under 1 second

```Markdown

Remember: API design is about creating intuitive, consistent, and scalable interfaces.
Focus on developer experience, clear documentation, comprehensive error handling, and robust testing
Always version your APIs and maintain backward compatibility when possible.
````
