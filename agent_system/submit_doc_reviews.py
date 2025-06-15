#!/usr/bin/env python3
"""Submit documentation review tasks to the agent system"""

import requests
import json
from typing import List, Dict, Any

# Documentation files to review
DOCUMENTATION_FILES = [
    {
        "file": "agent_system_prd.md",
        "description": "Product Requirements Document"
    },
    {
        "file": "architectural_schemas.md", 
        "description": "Architectural schemas and system design"
    },
    {
        "file": "development_launch_plan.md",
        "description": "Development and launch plan"
    },
    {
        "file": "project_principles.md",
        "description": "Core project principles and philosophy"
    },
    {
        "file": "self_improvement_guide.md",
        "description": "Guide for system self-improvement"
    },
    {
        "file": "service_management.md",
        "description": "Service management and deployment"
    },
    {
        "file": "ui_browser_features.md",
        "description": "UI and browser feature documentation"
    }
]

API_URL = "http://localhost:8000"


def submit_task(instruction: str) -> Dict[str, Any]:
    """Submit a task to the agent system"""
    payload = {
        "instruction": instruction,
        "priority": 1
    }
    
    response = requests.post(f"{API_URL}/tasks", json=payload)
    response.raise_for_status()
    return response.json()


def submit_documentation_reviews():
    """Submit all documentation review tasks"""
    submitted_tasks = []
    
    # First, verify the API is available
    try:
        response = requests.get(f"{API_URL}/health")
        health = response.json()
        print(f"✅ API is healthy: {health['status']}")
    except Exception as e:
        print(f"❌ API is not available: {e}")
        return
    
    # Submit each documentation review task
    for doc in DOCUMENTATION_FILES:
        instruction = f"""Review the documentation file /home/ubuntu/system.petter.ai/docs/{doc['file']} and compare it against the current system implementation.

Your task:
1. Read and analyze the documentation file: {doc['file']} ({doc['description']})
2. Compare the documentation against the current implementation in /home/ubuntu/system.petter.ai/agent_system/
3. Identify any outdated, inaccurate, or missing information
4. Note any discrepancies between documented features and actual implementation
5. Provide a detailed summary of findings including:
   - What is accurate and up-to-date
   - What needs to be updated
   - What is missing from the documentation
   - What is documented but not implemented
   - Specific recommendations for updates

Focus on accuracy and completeness. Be thorough in your analysis."""
            
        try:
            print(f"\n📄 Submitting review task for {doc['file']}...")
            result = submit_task(instruction)
            submitted_tasks.append({
                "file": doc['file'],
                "task_id": result["task_id"],
                "tree_id": result["tree_id"]
            })
            print(f"✅ Submitted - Task ID: {result['task_id']}, Tree ID: {result['tree_id']}")
        except Exception as e:
            print(f"❌ Failed to submit task for {doc['file']}: {e}")
    
    # Submit final summary task
    summary_instruction = f"""Create a comprehensive summary report of all documentation reviews that have been completed.

The following documentation files were reviewed:
{chr(10).join([f"- {doc['file']} ({doc['description']})" for doc in DOCUMENTATION_FILES])}

Your task:
1. Wait for all documentation review tasks to complete
2. Gather all the review findings from the completed tasks
3. Create a comprehensive summary report that includes:
   - Overall state of the documentation (accuracy percentage, completeness)
   - Common themes across all documentation files
   - High-priority updates needed across multiple files
   - Consistency issues between different documentation files
   - Recommendations for documentation maintenance process
   - Prioritized action items for documentation updates

Format the report clearly with sections for each documentation file and an executive summary at the beginning.

Related task trees: {', '.join([str(task['tree_id']) for task in submitted_tasks])}"""
        
    try:
        print(f"\n📊 Submitting summary task...")
        result = submit_task(summary_instruction)
        print(f"✅ Summary task submitted - Task ID: {result['task_id']}, Tree ID: {result['tree_id']}")
        
        # Save task information for reference
        all_tasks = submitted_tasks + [{
            "file": "SUMMARY_REPORT", 
            "task_id": result["task_id"],
            "tree_id": result["tree_id"]
        }]
        
        with open("/home/ubuntu/system.petter.ai/agent_system/doc_review_tasks.json", "w") as f:
            json.dump(all_tasks, f, indent=2)
        
        print(f"\n✅ All tasks submitted successfully!")
        print(f"📝 Task information saved to doc_review_tasks.json")
        
    except Exception as e:
        print(f"❌ Failed to submit summary task: {e}")


if __name__ == "__main__":
    submit_documentation_reviews()