"""
Safe Expression Evaluator - AST-based Alternative to eval()

Replaces unsafe eval() calls with a secure AST parser that only allows
whitelisted operations. Prevents arbitrary code execution vulnerabilities.

Security Features:
- Whitelisted operators only (==, !=, <, >, <=, >=, and, or, not, in)
- Whitelisted functions only (len, str, int, float, bool)
- Context variable access only (no __import__, open(), exec())
- No attribute access except on context dict
- No lambda, comprehensions, or function definitions

Author: xanadOS Security Team
Date: 2025-12-17
"""

import ast
from typing import Any, Dict


class SafeExpressionEvaluator:
    """
    Safe expression evaluator using AST parsing.

    Prevents code injection by only allowing whitelisted operations.
    Use this instead of eval() for user-provided expressions.

    Example:
        >>> evaluator = SafeExpressionEvaluator()
        >>> context = {"status": "active", "count": 10}
        >>> evaluator.evaluate('status == "active" and count > 5', context)
        True
    """

    # Whitelisted comparison operators
    ALLOWED_OPS = {
        ast.Eq: lambda a, b: a == b,
        ast.NotEq: lambda a, b: a != b,
        ast.Lt: lambda a, b: a < b,
        ast.LtE: lambda a, b: a <= b,
        ast.Gt: lambda a, b: a > b,
        ast.GtE: lambda a, b: a >= b,
        ast.In: lambda a, b: a in b,
        ast.NotIn: lambda a, b: a not in b,
        ast.Is: lambda a, b: a is b,
        ast.IsNot: lambda a, b: a is not b,
    }

    # Whitelisted boolean operators
    ALLOWED_BOOL_OPS = {
        ast.And: all,
        ast.Or: any,
    }

    # Whitelisted unary operators
    ALLOWED_UNARY_OPS = {
        ast.Not: lambda x: not x,
        ast.USub: lambda x: -x,
        ast.UAdd: lambda x: +x,
    }

    # Whitelisted functions
    ALLOWED_FUNCTIONS = {
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
        "round": round,
    }

    def __init__(self):
        """Initialize the safe expression evaluator."""
        pass

    def evaluate(self, expression: str, context: Dict[str, Any]) -> Any:
        """
        Safely evaluate an expression with the given context.

        Args:
            expression: The expression to evaluate (e.g., "x > 5 and y == 'test'")
            context: Dictionary of variables available to the expression

        Returns:
            The result of evaluating the expression

        Raises:
            ValueError: If the expression contains disallowed operations
            SyntaxError: If the expression is malformed

        Example:
            >>> evaluator = SafeExpressionEvaluator()
            >>> evaluator.evaluate("count > 10", {"count": 15})
            True
        """
        if not expression or not isinstance(expression, str):
            raise ValueError("Expression must be a non-empty string")

        try:
            # Parse the expression into an AST
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as e:
            raise SyntaxError(f"Invalid expression syntax: {e}")

        # Validate and evaluate the AST
        return self._eval_node(tree.body, context)

    def _eval_node(self, node: ast.AST, context: Dict[str, Any]) -> Any:
        """
        Recursively evaluate an AST node.

        Args:
            node: The AST node to evaluate
            context: Dictionary of variables

        Returns:
            The result of evaluating the node

        Raises:
            ValueError: If the node type is not allowed
        """
        # Constant values (strings, numbers, None, True, False)
        if isinstance(node, ast.Constant):
            return node.value

        # For Python 3.7 compatibility (deprecated in 3.8+)
        if isinstance(node, (ast.Num, ast.Str, ast.NameConstant)):
            return (
                node.n
                if isinstance(node, ast.Num)
                else (node.s if isinstance(node, ast.Str) else node.value)
            )

        # Variable lookup (e.g., "status", "count")
        if isinstance(node, ast.Name):
            if node.id not in context:
                raise ValueError(f"Variable '{node.id}' not found in context")
            return context[node.id]

        # Comparison operations (e.g., "x > 5", "status == 'active'")
        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left, context)
            result = True

            for op, comparator in zip(node.ops, node.comparators):
                if type(op) not in self.ALLOWED_OPS:
                    raise ValueError(
                        f"Comparison operator {type(op).__name__} not allowed"
                    )

                right = self._eval_node(comparator, context)
                result = result and self.ALLOWED_OPS[type(op)](left, right)
                left = right  # Chain comparisons (e.g., "1 < x < 10")

            return result

        # Boolean operations (e.g., "x and y", "a or b")
        if isinstance(node, ast.BoolOp):
            if type(node.op) not in self.ALLOWED_BOOL_OPS:
                raise ValueError(
                    f"Boolean operator {type(node.op).__name__} not allowed"
                )

            # Evaluate all operands
            values = [self._eval_node(val, context) for val in node.values]

            # Apply the boolean operation
            if isinstance(node.op, ast.And):
                return all(values)
            else:  # ast.Or
                return any(values)

        # Unary operations (e.g., "not x", "-5")
        if isinstance(node, ast.UnaryOp):
            if type(node.op) not in self.ALLOWED_UNARY_OPS:
                raise ValueError(f"Unary operator {type(node.op).__name__} not allowed")

            operand = self._eval_node(node.operand, context)
            return self.ALLOWED_UNARY_OPS[type(node.op)](operand)

        # Function calls (e.g., "len(items)", "str(count)")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls are allowed")

            func_name = node.func.id
            if func_name not in self.ALLOWED_FUNCTIONS:
                raise ValueError(f"Function '{func_name}' not allowed")

            # Evaluate arguments
            args = [self._eval_node(arg, context) for arg in node.args]

            # Call the function
            return self.ALLOWED_FUNCTIONS[func_name](*args)

        # Subscript access (e.g., "items[0]", "data['key']")
        if isinstance(node, ast.Subscript):
            value = self._eval_node(node.value, context)
            key = self._eval_node(node.slice, context)
            return value[key]

        # List literals (e.g., "[1, 2, 3]")
        if isinstance(node, ast.List):
            return [self._eval_node(elem, context) for elem in node.elts]

        # Tuple literals (e.g., "(1, 2, 3)")
        if isinstance(node, ast.Tuple):
            return tuple(self._eval_node(elem, context) for elem in node.elts)

        # Dict literals (e.g., "{'key': 'value'}")
        if isinstance(node, ast.Dict):
            result: dict = {}  # type: ignore[assignment]
            for key_node, val_node in zip(node.keys, node.values):
                key = self._eval_node(key_node, context)
                val = self._eval_node(val_node, context)
                result[key] = val
            return result

        # Disallowed node types
        raise ValueError(
            f"Expression type '{type(node).__name__}' not allowed. "
            f"Only simple comparisons, boolean operations, and whitelisted functions are supported."
        )


# Example usage and testing
if __name__ == "__main__":
    evaluator = SafeExpressionEvaluator()

    # Test cases
    test_cases = [
        # (expression, context, expected_result)
        ('status == "active"', {"status": "active"}, True),
        ("count > 10", {"count": 15}, True),
        ('count > 10 and status == "active"', {"count": 15, "status": "active"}, True),
        ("len(items) > 0", {"items": [1, 2, 3]}, True),
        ("not flag", {"flag": False}, True),
        ("x in [1, 2, 3]", {"x": 2}, True),
        ("1 < count < 100", {"count": 50}, True),
    ]

    print("Running test cases...")
    for expr, ctx, expected in test_cases:
        result = evaluator.evaluate(expr, ctx)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status}: {expr} => {result}")

    # Security tests (should raise ValueError)
    security_tests = [
        '__import__("os").system("ls")',  # Import attack
        'open("/etc/passwd")',  # File access
        'exec("print(1)")',  # Code execution
        "[x for x in range(10)]",  # List comprehension
        "lambda x: x + 1",  # Lambda
    ]

    print("\nRunning security tests (should all raise errors)...")
    for expr in security_tests:
        try:
            evaluator.evaluate(expr, {})
            print(f"❌ FAIL: {expr} (should have raised error)")
        except (ValueError, SyntaxError) as e:
            print(f"✅ PASS: {expr} blocked ({type(e).__name__})")
