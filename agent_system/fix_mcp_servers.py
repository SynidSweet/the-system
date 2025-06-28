#!/usr/bin/env python3
"""Fix MCP server classes to add missing register_tools method."""

import os
import re

mcp_servers = {
    "sql_lite.py": """
    def register_tools(self):
        \"\"\"Register all SQL tools.\"\"\"
        self.register_tool("execute_query", self.execute_query)
        self.register_tool("list_tables", self.list_tables)
        self.register_tool("describe_table", self.describe_table)
        self.register_tool("execute_raw_query", self.execute_raw_query)
""",
    "terminal.py": """
    def register_tools(self):
        \"\"\"Register all terminal tools.\"\"\"
        self.register_tool("execute_command", self.execute_command)
        self.register_tool("list_allowed_commands", self.list_allowed_commands)
        self.register_tool("get_working_directory", self.get_working_directory)
        self.register_tool("change_directory", self.change_directory)
""",
    "github.py": """
    def register_tools(self):
        \"\"\"Register all GitHub tools.\"\"\"
        self.register_tool("get_status", self.get_status)
        self.register_tool("get_diff", self.get_diff)
        self.register_tool("get_log", self.get_log)
        self.register_tool("create_branch", self.create_branch)
        self.register_tool("commit", self.commit)
        self.register_tool("push", self.push)
        self.register_tool("pull", self.pull)
""",
    "message_user.py": """
    def register_tools(self):
        \"\"\"Register all message tools.\"\"\"
        self.register_tool("send_message", self.send_message)
        self.register_tool("ask_user", self.ask_user)
        self.register_tool("show_progress", self.show_progress)
""",
    "entity_manager.py": """
    def register_tools(self):
        \"\"\"Register all entity manager tools.\"\"\"
        self.register_tool("create_entity", self.create_entity)
        self.register_tool("get_entity", self.get_entity)
        self.register_tool("update_entity", self.update_entity)
        self.register_tool("delete_entity", self.delete_entity)
        self.register_tool("list_entities", self.list_entities)
        self.register_tool("create_agent", self.create_agent)
        self.register_tool("create_task", self.create_task)
        self.register_tool("update_task", self.update_task)
        self.register_tool("create_document", self.create_document)
"""
}

# Also fix the __init__ methods to add server_name
init_fixes = {
    "sql_lite.py": ("super().__init__(permission_manager)", 'super().__init__("sqlite", permission_manager)'),
    "terminal.py": ("super().__init__(permission_manager)", 'super().__init__("terminal", permission_manager)'),
    "github.py": ("super().__init__(permission_manager)", 'super().__init__("github", permission_manager)'),
    "message_user.py": ("super().__init__(permission_manager)", 'super().__init__("message_user", permission_manager)'),
    "entity_manager.py": ("super().__init__(permission_manager)", 'super().__init__("entity_manager", permission_manager)'),
}

base_dir = "/home/ubuntu/system.petter.ai/agent_system/tools/mcp_servers"

for filename, register_method in mcp_servers.items():
    filepath = os.path.join(base_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check if register_tools already exists
        if "def register_tools" not in content:
            # Find where to insert it (after __init__)
            init_match = re.search(r'(def __init__.*?\n(?:.*?\n)*?.*?)\n\n', content, re.DOTALL)
            if init_match:
                insert_pos = init_match.end()
                content = content[:insert_pos] + register_method + "\n" + content[insert_pos:]
                print(f"Added register_tools to {filename}")
            else:
                print(f"Could not find __init__ in {filename}")
        
        # Fix the super().__init__ call
        if filename in init_fixes:
            old_call, new_call = init_fixes[filename]
            if old_call in content:
                content = content.replace(old_call, new_call)
                print(f"Fixed super().__init__ in {filename}")
        
        # Write back
        with open(filepath, 'w') as f:
            f.write(content)