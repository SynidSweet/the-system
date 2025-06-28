#!/usr/bin/env python3
"""
Script to fix absolute imports in the agent_system codebase.
Converts 'from agent_system.x.y import z' to relative imports.
"""

import os
import re
import sys
from pathlib import Path

def get_relative_import_path(from_file: Path, import_parts: list) -> str:
    """Calculate the relative import path from one file to another."""
    from_parts = list(from_file.parts)
    
    # Find where we are in the agent_system hierarchy
    try:
        agent_idx = from_parts.index('agent_system')
        # Get the path from agent_system to the current file (excluding the filename)
        current_path_parts = from_parts[agent_idx+1:-1]
    except ValueError:
        return None
    
    # Get the target path from agent_system
    target_path_parts = import_parts[1:]  # Skip 'agent_system'
    
    # Find common prefix
    common_prefix_len = 0
    for i, (a, b) in enumerate(zip(current_path_parts, target_path_parts)):
        if a == b:
            common_prefix_len = i + 1
        else:
            break
    
    # Calculate dots needed (go up from current location)
    dots_needed = len(current_path_parts) - common_prefix_len
    if dots_needed == 0 and common_prefix_len < len(target_path_parts):
        # Same level import
        dots = '.'
    else:
        # Go up directories
        dots = '.' * (dots_needed + 1)
    
    # Get remaining path after common prefix
    remaining_parts = target_path_parts[common_prefix_len:]
    
    if remaining_parts:
        return f"from {dots}{'.'.join(remaining_parts)}"
    else:
        # Importing from parent
        return f"from {dots[:-1]}"

def fix_imports_in_file(filepath: Path, dry_run: bool = True):
    """Fix imports in a single file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False
    
    original_content = content
    changes = []
    
    # Pattern to match agent_system imports
    patterns = [
        (r'from agent_system\.([^\s]+) import ([^\n]+)', 'from'),
        (r'import agent_system\.([^\s\n]+)', 'import')
    ]
    
    for pattern, import_type in patterns:
        for match in re.finditer(pattern, content):
            full_match = match.group(0)
            
            if import_type == 'from':
                module_path = match.group(1)
                imported_items = match.group(2)
                
                # Split the module path
                parts = ['agent_system'] + module_path.split('.')
                
                # Get relative import
                relative_import = get_relative_import_path(filepath, parts)
                
                if relative_import:
                    new_import = f"{relative_import} import {imported_items}"
                    content = content.replace(full_match, new_import)
                    changes.append((full_match, new_import))
            
            else:  # import agent_system.x.y
                module_path = match.group(1)
                parts = ['agent_system'] + module_path.split('.')
                
                # For direct imports, we need to handle differently
                # Usually better to convert to 'from x import y' style
                module_name = parts[-1]
                parent_parts = parts[:-1]
                
                relative_import = get_relative_import_path(filepath, parent_parts)
                if relative_import:
                    new_import = f"{relative_import} import {module_name}"
                    content = content.replace(full_match, new_import)
                    changes.append((full_match, new_import))
    
    if changes:
        print(f"\n{filepath}:")
        for old, new in changes:
            print(f"  - {old}")
            print(f"  + {new}")
        
        if not dry_run and content != original_content:
            try:
                with open(filepath, 'w') as f:
                    f.write(content)
                print(f"  ✅ Fixed {len(changes)} imports")
                return True
            except Exception as e:
                print(f"  ❌ Error writing file: {e}")
                return False
    
    return False

def main():
    """Fix imports in all Python files."""
    if len(sys.argv) > 1 and sys.argv[1] == '--apply':
        dry_run = False
        print("🔧 Applying fixes...")
    else:
        dry_run = True
        print("🔍 Dry run mode. Use --apply to make changes.")
    
    agent_system_dir = Path(__file__).parent.parent
    fixed_count = 0
    
    # Files with agent_system imports
    files_to_fix = [
        "core/runtime/engine.py",
        "core/runtime/runtime_integration.py",
        "core/entities/entity_manager.py",
        "core/runtime/state_machine.py",
        "core/universal_agent_runtime.py",
        "core/processes/base.py",
        "core/processes/neutral_task_process.py",
        "core/processes/registry.py",
        "core/entities/task_entity.py",
        "core/entities/context_entity.py",
        "core/entities/event_entity.py",
        "core/entities/process_entity.py",
        "core/permissions/manager.py",
        "core/runtime/dependency_graph.py",
        "core/runtime/event_handler.py",
        "tools/mcp_servers/base.py",
        "tools/mcp_servers/entity_manager.py",
        "tools/mcp_servers/file_system.py",
        "tools/mcp_servers/github.py",
        "tools/mcp_servers/message_user.py",
        "tools/mcp_servers/sql_lite.py",
        "tools/mcp_servers/startup.py",
        "tools/mcp_servers/terminal.py",
        "core/processes/tool_processes/break_down_task.py",
        "core/processes/tool_processes/create_subtask.py",
        "core/processes/tool_processes/end_task.py",
        "core/processes/tool_processes/need_more_context.py",
        "core/processes/tool_processes/need_more_tools.py",
    ]
    
    for file_path in files_to_fix:
        full_path = agent_system_dir / file_path
        if full_path.exists():
            if fix_imports_in_file(full_path, dry_run):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n{'Would fix' if dry_run else 'Fixed'} {fixed_count} files")
    
    if dry_run:
        print("\nRun with --apply to make changes:")
        print("  python scripts/fix_imports.py --apply")

if __name__ == "__main__":
    main()