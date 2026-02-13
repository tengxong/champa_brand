#!/usr/bin/env python3
"""Test script to verify app.py can be imported and app instance exists"""
import sys

try:
    print("Importing app...")
    from app import app
    print("✓ app imported successfully")
    print(f"✓ app instance: {app}")
    print(f"✓ app type: {type(app)}")
    print("✓ App is ready for gunicorn")
    sys.exit(0)
except Exception as e:
    print(f"✗ Error importing app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
