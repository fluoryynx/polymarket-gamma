#!/usr/bin/env python3
"""
Test script to verify CLOB API endpoints are working properly
"""
import requests
import time
from threading import Thread
from api import create_app

# Start the Flask app in a separate thread for testing
app = create_app()
server_thread = None

def start_server():
    app.run(debug=False, host='0.0.0.0', port=5001)

def test_clob_endpoints():
    """Test the CLOB API endpoints"""
    # Wait a moment for the server to start
    time.sleep(2)
    
    base_url = "http://localhost:5001"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health check: {response.status_code}, {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
    
    # Test /book endpoint (should return error since no token_id provided)
    try:
        response = requests.get(f"{base_url}/book")
        print(f"Book endpoint (no token_id): {response.status_code}, {response.json()}")
    except Exception as e:
        print(f"Book endpoint test failed: {e}")
    
    # Test /prices endpoint (should return error since no body provided)
    try:
        response = requests.post(f"{base_url}/prices", json={})
        print(f"Prices endpoint (empty body): {response.status_code}, {response.json()}")
    except Exception as e:
        print(f"Prices endpoint test failed: {e}")

if __name__ == "__main__":
    # Start server in background thread
    server_thread = Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Run tests
    test_clob_endpoints()
    
    print("Test completed. Server should still be running on another thread.")
