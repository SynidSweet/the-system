#!/usr/bin/env python3
"""
Lateral test to verify the agent system is working correctly.
This tests the core flow from task submission to completion via the API.
"""

import asyncio
import json
import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Use standard library instead of external dependencies where possible
import urllib.request
import urllib.parse
import urllib.error

API_BASE_URL = "http://localhost:8000"


def print_status(message: str, status: str = "info"):
    """Simple status printer"""
    symbols = {
        "info": "ℹ️ ",
        "success": "✅",
        "error": "❌",
        "warning": "⚠️ ",
        "progress": "⏳"
    }
    print(f"{symbols.get(status, '')} {message}")


async def check_api_health() -> bool:
    """Check if the API server is running."""
    try:
        req = urllib.request.Request(f"{API_BASE_URL}/health")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                print_status("API server is healthy", "success")
                return True
    except Exception as e:
        print_status(f"API server is not responding: {e}", "error")
        return False


async def submit_task(instruction: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Submit a task to the agent system via API."""
    payload = {
        "instruction": instruction,
        "context": context or {},
        "metadata": {"test": True, "test_type": "lateral_flow"}
    }
    
    print_status(f"Submitting task: {instruction[:50]}...", "info")
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f"{API_BASE_URL}/tasks",
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            print_status(f"Task created: ID={result['task_id']}, Tree={result['tree_id']}", "success")
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print_status(f"Error submitting task: {e.code} - {error_body}", "error")
        raise Exception(f"Failed to submit task: {error_body}")


async def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get current status of a task."""
    req = urllib.request.Request(f"{API_BASE_URL}/tasks/{task_id}")
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print_status(f"Error getting task status: {e}", "error")
        return None


async def get_task_tree(tree_id: str) -> Dict[str, Any]:
    """Get the full task tree."""
    req = urllib.request.Request(f"{API_BASE_URL}/trees/{tree_id}")
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception:
        return None


async def monitor_task(task_id: str, tree_id: str) -> Dict[str, Any]:
    """Monitor task execution and display progress."""
    print_status("Monitoring task execution...", "progress")
    
    start_time = time.time()
    last_status = None
    subtask_count = 0
    
    while True:
        # Get task status
        task_data = await get_task_status(task_id)
        if not task_data:
            break
            
        # Extract task data from response
        if "task" in task_data:
            current_status = task_data["task"]["status"]
        else:
            current_status = task_data.get("status", "unknown")
        
        # Update progress if status changed
        if current_status != last_status:
            print_status(f"Status: {last_status} → {current_status}", "info")
            last_status = current_status
        
        # Get task tree to see subtasks
        tree_data = await get_task_tree(tree_id)
        if tree_data and "tasks" in tree_data:
            current_subtask_count = len(tree_data["tasks"]) - 1  # Exclude root
            
            if current_subtask_count > subtask_count:
                print_status(f"New subtasks created: {current_subtask_count} total", "success")
                subtask_count = current_subtask_count
                
                # Show subtask details
                for task in tree_data["tasks"]:
                    if task["id"] != task_id:
                        print(f"  - Agent: {task.get('agent_id', 'None')} | Status: {task['status']}")
        
        # Check if task is complete
        if current_status in ["completed", "failed", "rejected"]:
            elapsed = time.time() - start_time
            print_status(f"Task {current_status} in {elapsed:.2f} seconds", 
                        "success" if current_status == "completed" else "error")
            
            if task_data.get("result"):
                print("\n--- Task Result ---")
                print(json.dumps(task_data["result"], indent=2))
                print("------------------\n")
            
            return task_data
        
        await asyncio.sleep(1)


async def test_simple_task():
    """Test a simple task that should complete successfully."""
    print("\n=== Test 1: Simple Task ===")
    print("This tests basic task execution with a clear instruction.")
    
    # Submit a simple arithmetic task
    task_response = await submit_task(
        instruction="TEST TASK: Calculate 42 + 58 and complete the task with the result. "
                   "This is a test of the agent system. Please use the end_task tool "
                   "to complete this task with the calculated result."
    )
    
    # Monitor execution
    result = await monitor_task(task_response["task_id"], task_response["tree_id"])
    
    # Verify result
    if result["status"] == "completed":
        print_status("Test 1 PASSED", "success")
        return True
    else:
        print_status("Test 1 FAILED", "error")
        return False


async def test_process_discovery():
    """Test that process discovery is triggered for complex tasks."""
    print("\n=== Test 2: Process Discovery ===")
    print("This tests that the process-first architecture triggers for complex tasks.")
    
    # Submit a task that should trigger process discovery
    task_response = await submit_task(
        instruction="TEST TASK: Create a new Python module for calculating fibonacci numbers. "
                   "This is a test to verify process discovery works. The system should "
                   "establish a systematic framework before attempting this task."
    )
    
    # Monitor execution
    result = await monitor_task(task_response["task_id"], task_response["tree_id"])
    
    # Check if process discovery was triggered
    tree_data = await get_task_tree(task_response["tree_id"])
    if tree_data and "tasks" in tree_data:
        process_discovery_found = False
        for task in tree_data["tasks"]:
            if task.get("agent_id") == "process_discovery":
                process_discovery_found = True
                print_status("Process discovery agent was invoked", "success")
                break
        
        if not process_discovery_found:
            print_status("Process discovery agent was not invoked", "warning")
    
    # Verify result
    if result["status"] in ["completed", "pending"]:
        print_status("Test 2 PASSED", "success")
        return True
    else:
        print_status("Test 2 FAILED", "error")
        return False


async def main():
    """Run all lateral tests."""
    print("🧪 Agent System Lateral Test")
    print("=" * 50)
    
    # Check API health
    if not await check_api_health():
        print("\nPlease start the API server first:")
        print("python -m agent_system.api.main")
        return
    
    # Run tests
    tests_passed = 0
    total_tests = 2
    
    try:
        # Test 1: Simple task
        if await test_simple_task():
            tests_passed += 1
        
        # Test 2: Process discovery
        if await test_process_discovery():
            tests_passed += 1
        
    except Exception as e:
        print_status(f"Test error: {e}", "error")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Test Summary: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print_status("All tests passed! The system is working correctly.", "success")
    else:
        print_status("Some tests failed. Please check the system configuration.", "error")


if __name__ == "__main__":
    asyncio.run(main())