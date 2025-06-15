#!/usr/bin/env python3
"""
Fix corrupted model_config values in the agents table.
Updates all agents to use the default model configuration.
"""

import sqlite3
import json
import os

def fix_agent_model_configs():
    """Update all agents to use proper default model configuration"""
    
    # Create default model config matching the ModelConfig defaults
    config_dict = {
        "provider": "google",
        "model_name": "gemini-2.5-flash-preview-05-20",
        "temperature": 0.1,
        "max_tokens": 4000,
        "api_key": None
    }
    config_json = json.dumps(config_dict)
    
    # Connect to database
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'agent_system.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # First, let's check current values
        cursor.execute("SELECT id, name, model_config FROM agents")
        agents = cursor.fetchall()
        
        print(f"Found {len(agents)} agents to update")
        print("\nCurrent model configurations:")
        for agent_id, name, current_config in agents:
            print(f"  {name}: {current_config}")
        
        # Update all agents with proper model config
        cursor.execute(
            "UPDATE agents SET model_config = ?, updated_at = CURRENT_TIMESTAMP",
            (config_json,)
        )
        
        rows_updated = cursor.rowcount
        conn.commit()
        
        print(f"\nUpdated {rows_updated} agents with default model configuration:")
        print(f"  Provider: {config_dict['provider']}")
        print(f"  Model: {config_dict['model_name']}")
        print(f"  Temperature: {config_dict['temperature']}")
        print(f"  Max Tokens: {config_dict['max_tokens']}")
        
        # Verify the update
        cursor.execute("SELECT name, model_config FROM agents LIMIT 3")
        updated_agents = cursor.fetchall()
        print("\nVerification (first 3 agents):")
        for name, config in updated_agents:
            print(f"  {name}: {config}")
        
    except Exception as e:
        print(f"Error updating agents: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
    
    print("\nModel configuration update completed successfully!")

if __name__ == "__main__":
    fix_agent_model_configs()