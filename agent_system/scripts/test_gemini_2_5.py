#!/usr/bin/env python3
"""
Test that the system can connect to and use Gemini 2.5 Flash
"""

import os
import sys

# Simple test without dependencies
def test_gemini_connection():
    """Test connection to Gemini 2.5 Flash API"""
    
    try:
        # Check if Google API key is set
        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            print("❌ GOOGLE_API_KEY environment variable not set")
            print("   Please set it to test the Gemini 2.5 Flash connection")
            return False
        
        print("✅ GOOGLE_API_KEY is set")
        
        # Try importing the Google generativeai library
        try:
            import google.generativeai as genai
            print("✅ google-generativeai package is installed")
        except ImportError:
            print("❌ google-generativeai package not installed")
            print("   Run: pip install google-generativeai")
            return False
        
        # Configure and test the API
        genai.configure(api_key=api_key)
        
        # Test with Gemini 2.5 Flash
        model_name = "gemini-2.5-flash-preview-05-20"
        print(f"\nTesting connection to {model_name}...")
        
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Say 'Hello from Gemini 2.5 Flash!' in exactly those words.")
            print(f"✅ Successfully connected to {model_name}")
            print(f"   Response: {response.text.strip()}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to {model_name}")
            print(f"   Error: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_database_config():
    """Check that agents are configured with Gemini 2.5 Flash"""
    import sqlite3
    import json
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'agent_system.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name, model_config FROM agents LIMIT 3")
    agents = cursor.fetchall()
    
    print("\nDatabase Configuration Check:")
    all_correct = True
    for name, config_str in agents:
        config = json.loads(config_str)
        is_correct = (config.get('provider') == 'google' and 
                     config.get('model_name') == 'gemini-2.5-flash-preview-05-20')
        status = "✅" if is_correct else "❌"
        print(f"{status} {name}: {config.get('model_name')}")
        all_correct = all_correct and is_correct
    
    conn.close()
    return all_correct

if __name__ == "__main__":
    print("=== Testing Gemini 2.5 Flash Configuration ===\n")
    
    # Check database configuration
    db_ok = check_database_config()
    
    # Test API connection
    api_ok = test_gemini_connection()
    
    print("\n=== Summary ===")
    print(f"Database Configuration: {'✅ PASS' if db_ok else '❌ FAIL'}")
    print(f"API Connection: {'✅ PASS' if api_ok else '❌ FAIL'}")
    
    if db_ok and api_ok:
        print("\n🎉 All tests passed! The system is configured to use Gemini 2.5 Flash.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")