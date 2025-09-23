#!/usr/bin/env python3
"""
Test script for student signup functionality.
This script tests syntax and code structure without requiring Flask runtime.
"""

import sys
import os
import ast
import re

def test_auth_service_syntax():
    """Test that auth_service.py compiles without syntax errors."""
    try:
        with open('app/services/auth_service.py', 'r') as f:
            source = f.read()

        # Parse the AST to check syntax
        ast.parse(source)
        print("✓ auth_service.py syntax is valid")

        # Check if signup_student function exists
        if 'def signup_student(' in source:
            print("✓ signup_student function found")
            return True
        else:
            print("✗ signup_student function not found")
            return False

    except SyntaxError as e:
        print(f"✗ Syntax error in auth_service.py: {e}")
        return False
    except Exception as e:
        print(f"✗ Error reading auth_service.py: {e}")
        return False

def test_auth_routes_syntax():
    """Test that auth.py compiles without syntax errors."""
    try:
        with open('app/routes/auth.py', 'r') as f:
            source = f.read()

        # Parse the AST to check syntax
        ast.parse(source)
        print("✓ auth.py syntax is valid")

        # Check if signup route exists
        if '@auth_bp.route(\'/signup\'' in source:
            print("✓ signup route found")
            return True
        else:
            print("✗ signup route not found")
            return False

    except SyntaxError as e:
        print(f"✗ Syntax error in auth.py: {e}")
        return False
    except Exception as e:
        print(f"✗ Error reading auth.py: {e}")
        return False

def test_signup_function_structure():
    """Test that signup_student function has correct structure."""
    try:
        with open('app/services/auth_service.py', 'r') as f:
            source = f.read()

        # Extract function definition
        func_match = re.search(r'def signup_student\((.*?)\):', source, re.DOTALL)
        if not func_match:
            print("✗ Could not find signup_student function")
            return False

        params_str = func_match.group(1)
        params = [p.strip() for p in params_str.split(',')]

        expected_params = ['email', 'password', 'name=None', 'phone=None']
        if len(params) >= 2 and 'email' in params[0] and 'password' in params[1]:
            print("✓ signup_student function parameters look correct")
            return True
        else:
            print(f"✗ Unexpected parameters: {params}")
            return False

    except Exception as e:
        print(f"✗ Error analyzing function structure: {e}")
        return False

def test_imports_in_auth_service():
    """Test that required imports are present in auth_service.py."""
    try:
        with open('app/services/auth_service.py', 'r') as f:
            source = f.read()

        required_imports = [
            'from app.services.jwt_service import create_access_token, create_refresh_token'
        ]

        missing_imports = []
        for imp in required_imports:
            if imp not in source:
                missing_imports.append(imp)

        if not missing_imports:
            print("✓ Required imports found in auth_service.py")
            return True
        else:
            print(f"✗ Missing imports: {missing_imports}")
            return False

    except Exception as e:
        print(f"✗ Error checking imports: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing Student Signup Implementation (Syntax Only)")
    print("=" * 50)

    tests = [
        test_auth_service_syntax,
        test_auth_routes_syntax,
        test_signup_function_structure,
        test_imports_in_auth_service
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All syntax tests passed! Student signup implementation structure is correct.")
        print("\nNote: Runtime testing requires Flask and Supabase dependencies to be installed.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())