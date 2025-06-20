#!/usr/bin/env python3
"""
Test script for Gemini 2.5 model series configuration.

This script verifies that:
1. The system can connect to Gemini 2.5 models
2. Model selection works correctly
3. Different models produce appropriate responses
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from config.model_config import GEMINI_25_MODELS, ModelSelector, AGENT_MODEL_PREFERENCES
from core.ai_models import GoogleProvider, ModelConfig


async def test_model_configuration():
    """Test that model configuration is set up correctly"""
    print("=== Testing Gemini 2.5 Model Configuration ===\n")
    
    # Check default model
    print(f"Default model: {settings.default_model_name}")
    print(f"Default provider: {settings.default_model_provider}")
    
    # Check available models
    print("\nAvailable Gemini 2.5 models:")
    for model_id, config in GEMINI_25_MODELS.items():
        print(f"  - {model_id}: {config['name']}")
        print(f"    Context: {config['context_window']:,} tokens")
        print(f"    Cost: {config['relative_cost']}x, Speed: {config['relative_speed']}x")
    
    # Check agent preferences
    print("\nAgent model preferences:")
    for agent, model in list(AGENT_MODEL_PREFERENCES.items())[:5]:
        print(f"  - {agent}: {model}")
    
    print("\n✓ Model configuration loaded successfully")


async def test_model_connection(model_name: str):
    """Test connection to a specific model"""
    print(f"\n=== Testing {model_name} ===")
    
    if not settings.google_api_key:
        print("❌ No Google API key found. Set GOOGLE_API_KEY environment variable.")
        return False
    
    try:
        # Create model config
        config = ModelConfig(
            provider="google",
            model_name=model_name,
            api_key=settings.google_api_key,
            temperature=0.1,
            max_tokens=100
        )
        
        # Initialize provider
        provider = GoogleProvider(config)
        await provider.initialize()
        
        # Test simple query
        messages = [
            {"role": "user", "content": "Say 'Hello from Gemini 2.5' and mention which model you are."}
        ]
        
        response = await provider.generate_response(messages)
        
        print(f"✓ Connected to {model_name}")
        print(f"Response: {response['content'][:200]}...")
        print(f"Tokens used: {response['usage']['total_tokens']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing {model_name}: {str(e)}")
        return False


async def test_model_selector():
    """Test the model selector logic"""
    print("\n=== Testing Model Selector ===")
    
    test_cases = [
        ("validation", "cost", "gemini-2.5-flash-lite"),
        ("architecture", "quality", "gemini-2.5-pro"),
        ("coding", "balanced", "gemini-2.5-flash"),
        ("simple", "speed", "gemini-2.5-flash-lite"),
    ]
    
    for task_type, priority, expected in test_cases:
        selected = ModelSelector.get_model_for_task(task_type, priority)
        status = "✓" if selected == expected else "❌"
        print(f"{status} Task: {task_type}, Priority: {priority} → {selected}")
    
    # Test cost estimation
    print("\nCost estimates (per 1M tokens):")
    for model in ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro"]:
        cost = ModelSelector.estimate_cost(model, 1_000_000)
        print(f"  - {model}: {cost:.1f} units")


async def main():
    """Run all tests"""
    print("Testing Gemini 2.5 Model Series Integration\n")
    
    # Test configuration
    await test_model_configuration()
    
    # Test model selector
    await test_model_selector()
    
    # Test model connections (only if API key is available)
    if settings.google_api_key:
        # Test each model
        models_to_test = [
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash",
            # "gemini-2.5-pro"  # Uncomment to test Pro model
        ]
        
        print("\n=== Testing Model Connections ===")
        print(f"(Testing with first {len(models_to_test)} models to save costs)")
        
        for model in models_to_test:
            success = await test_model_connection(model)
            if not success:
                print(f"\nNote: Model {model} may not be available yet or API key may be invalid.")
            await asyncio.sleep(1)  # Rate limiting
    else:
        print("\n⚠️  Skipping live model tests - no API key found")
        print("Set GOOGLE_API_KEY environment variable to test actual connections")
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(main())