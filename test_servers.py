#!/usr/bin/env python3
"""
Quick test script to verify servers can start correctly
"""

import sys
import os

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'srcs', 'server'))

print("Testing backend server initialization...")
try:
    from app_factory import create_app
    app = create_app()
    
    # Test a route
    with app.test_client() as client:
        response = client.get('/')
        print(f"✓ Backend server initialized successfully")
        print(f"✓ Root endpoint returned status: {response.status_code}")
        if response.status_code == 200:
            print(f"✓ Response: {response.get_json()}")
except Exception as e:
    print(f"✗ Backend server test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✓ All backend tests passed!")
print("\nYou can now start the servers:")
print("  1. Backend: cd srcs/server && python3 run.py")
print("  2. Frontend: cd frontend && npm run dev")

