#!/usr/bin/env python3
"""
Complete system seeding for the self-improving agent system.

This script implements the full seeding as specified in the launch plan:
1. All 9 core agents with proper instructions
2. All documentation from /docs as context documents
3. Additional context documents referenced by agents
4. All internal and external MCP tools

This creates the complete foundation for the self-improving system.
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import db_manager
from core.database_manager import database
from tools.base_tool import tool_registry
from tools.core_mcp.core_tools import register_core_tools
from tools.system_tools.mcp_integrations import register_system_tools
from tools.system_tools.internal_tools import register_internal_tools


async def init_database():
    """Initialize database connection and schema"""
    print("🔧 Initializing database...")
    
    try:
        await db_manager.connect()
        print("✅ Database connection established")
        
        # Create the basic schema for seeding
        schema_sql = """
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            instruction TEXT,
            context_documents TEXT DEFAULT '[]',
            available_tools TEXT DEFAULT '[]',
            permissions TEXT DEFAULT '[]',
            constraints TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS context_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            title TEXT,
            category TEXT DEFAULT 'general',
            content TEXT,
            format TEXT DEFAULT 'markdown',
            version TEXT DEFAULT '1.0.0'
        );
        
        CREATE TABLE IF NOT EXISTS tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            category TEXT DEFAULT 'system',
            implementation TEXT,
            parameters TEXT DEFAULT '{}',
            permissions TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_task_id INTEGER,
            tree_id INTEGER,
            agent_id INTEGER,
            instruction TEXT,
            status TEXT DEFAULT 'created',
            result TEXT DEFAULT '{}',
            metadata TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            message_type TEXT,
            content TEXT,
            metadata TEXT DEFAULT '{}',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        await db_manager.execute_script(schema_sql)
        print("✅ Database schema created")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


async def seed_all_agents():
    """Seed all 9 core agents as specified in the launch plan"""
    print("🤖 Seeding all 8 core agents...")
    
    from core.models import AgentPermissions
    
    agents_config = [
        {
            "name": "agent_selector",
            "instruction": """You are the system's intelligent entry point. Analyze each task and route it to the most appropriate agent, solve simple tasks directly, or request new capabilities when needed.

CORE DECISION PROCESS:
1. Can I solve this directly? → Do it immediately
2. Is this complex enough to require decomposition? → Route to task_breakdown
3. Does this match a specialized agent's domain? → Route to specialist
4. No existing agent fits well? → Request creation of new agent type

Always end with end_task().

Focus on enabling emergent intelligence through smart composition of capabilities rather than rigid categorization.""",
            "context_documents": ["agent_selector_guide", "system_overview", "agent_registry"],
            "available_tools": ["list_agents", "query_database"],
            "permissions": AgentPermissions(web_search=True, spawn_agents=True)
        },
        {
            "name": "task_breakdown",
            "instruction": """You are the system's recursive decomposition engine. Take complex tasks and break them into manageable, independently executable subtasks that enable parallel work and specialization.

CORE APPROACH:
1. Find the problem's natural structure and layers
2. Create subtasks with clear objectives and clean interfaces
3. Design for maximum independence and parallel execution
4. Match subtasks to agent specializations
5. Plan integration and coordination strategy

Focus on enabling emergence through composition rather than rigid control.""",
            "context_documents": ["task_breakdown_guide", "breakdown_guidelines", "system_architecture"],
            "available_tools": [],
            "permissions": AgentPermissions(spawn_agents=True)
        },
        {
            "name": "context_addition",
            "instruction": """You are the system's knowledge curator. Identify what context and domain expertise agents need to excel at their tasks, then research, synthesize, and provide that knowledge in actionable form.

CORE APPROACH:
1. Analyze knowledge gaps that limit agent effectiveness
2. Research and synthesize relevant domain expertise
3. Create context documents that enable better decisions and actions
4. Design knowledge for reusability across future tasks
5. Build the system's growing expertise systematically

Focus on knowledge that directly enables action, not just information.""",
            "context_documents": ["context_addition_guide", "available_context", "documentation_standards"],
            "available_tools": ["list_documents", "use_terminal", "query_database"],
            "permissions": AgentPermissions(web_search=True, database_write=True, file_system=True)
        },
        {
            "name": "tool_addition",
            "instruction": """You are the system's capability architect. Identify, create, and integrate the tools that agents need to accomplish their tasks, embodying the principle of dynamic capability discovery.

CORE APPROACH:
1. Assess capability gaps and tool requirements
2. Prefer integrating existing MCP tools over building custom
3. Build tools that enable emergence and composition
4. Design for reusability across multiple future needs
5. Create tools that become building blocks for capabilities you never anticipated

Focus on building capability patterns, not just individual tools.""",
            "context_documents": ["tool_addition_guide", "tool_registry", "mcp_documentation"],
            "available_tools": ["list_optional_tools", "github_operations", "use_terminal", "query_database"],
            "permissions": AgentPermissions(web_search=True, database_write=True, file_system=True, shell_access=True)
        },
        {
            "name": "task_evaluator",
            "instruction": """You are the system's quality guardian. Assess completed work across multiple quality dimensions to create feedback loops that enable continuous system improvement and learning.

CORE APPROACH:
1. Think in quality dimensions, not binary pass/fail
2. Focus on learning and insight extraction, not judgment
3. Balance standards with context and task requirements
4. Provide feedback that helps agents and system improve
5. Extract patterns that inform system evolution

Evaluate functional, completeness, craft, documentation, and integration quality.""",
            "context_documents": ["task_evaluator_guide", "evaluation_criteria", "quality_standards"],
            "available_tools": ["query_database"],
            "permissions": AgentPermissions(database_write=True)
        },
        {
            "name": "documentation_agent",
            "instruction": """You are the system's knowledge historian and transparency enabler. Capture insights, procedures, and learnings that emerge from task execution to ensure valuable knowledge isn't lost and the system becomes increasingly intelligent.

CORE APPROACH:
1. Think in knowledge flows, not static documents
2. Focus on knowledge that enables action, not just information
3. Design for discovery and evolution of knowledge
4. Capture emerging patterns and reusable insights
5. Build the system's institutional memory and expertise

Create documentation that makes agents more capable.""",
            "context_documents": ["documentation_agent_guide", "documentation_standards", "system_architecture"],
            "available_tools": ["list_documents", "query_database"],
            "permissions": AgentPermissions(database_write=True, file_system=True)
        },
        {
            "name": "summary_agent",
            "instruction": """You are the system's information synthesizer and communication facilitator. Distill complex task execution into clear, actionable insights that enable effective coordination and decision-making in the recursive architecture.

CORE APPROACH:
1. Think in information layers that serve different audiences
2. Focus on actionability, not completeness
3. Design for different cognitive loads and decision contexts
4. Extract strategic implications and coordination needs
5. Enable learning and knowledge transfer between agents

Create summaries that enable effective action by receiving agents.""",
            "context_documents": ["summary_agent_guide", "summarization_guidelines"],
            "available_tools": ["query_database"],
            "permissions": AgentPermissions()
        },
        {
            "name": "review_agent",
            "instruction": """You are the system's evolution architect. Analyze system performance patterns, identify improvement opportunities, and implement changes that enhance system capabilities, embodying the self-improving architecture principle.

CORE APPROACH:
1. Think in system evolution patterns, not isolated fixes
2. Focus on systematic improvement, not symptom treatment
3. Address root causes and strengthen fundamental capabilities
4. Balance innovation with stability during changes
5. Design improvements that enable accelerating evolution

Implement changes that make the system smarter and more capable over time.""",
            "context_documents": ["review_agent_guide", "improvement_guide", "system_architecture"],
            "available_tools": ["github_operations", "use_terminal", "query_database"],
            "permissions": AgentPermissions(web_search=True, database_write=True, file_system=True, shell_access=True, git_operations=True)
        }
    ]
    
    created_count = 0
    for agent_config in agents_config:
        try:
            # Check if agent already exists
            existing = await database.agents.get_by_name(agent_config["name"])
            if existing:
                print(f"  ⚠️  Agent '{agent_config['name']}' already exists, skipping")
                continue
            
            # Convert permissions to JSON string if it's an object
            permissions = agent_config.get("permissions", [])
            if hasattr(permissions, 'model_dump'):
                permissions = json.dumps(permissions.model_dump())
            elif isinstance(permissions, list):
                permissions = json.dumps(permissions)
            else:
                permissions = "[]"
            
            # Create agent
            agent_id = await database.agents.create(
                name=agent_config["name"],
                instruction=agent_config["instruction"],
                context_documents=json.dumps(agent_config["context_documents"]),
                available_tools=json.dumps(agent_config["available_tools"]),
                permissions=permissions,
                constraints=json.dumps(agent_config.get("constraints", []))
            )
            print(f"  ✅ Created agent '{agent_config['name']}' (ID: {agent_id})")
            created_count += 1
            
        except Exception as e:
            print(f"  ❌ Failed to create agent '{agent_config['name']}': {e}")
    
    print(f"✅ Created {created_count} agents")
    return True


async def seed_context_documents():
    """Seed context documents from /docs and additional required documents"""
    print("📚 Seeding context documents...")
    
    
    # First, add the existing docs files
    docs_dir = Path(__file__).parent.parent.parent / "docs"
    docs_added = 0
    
    if docs_dir.exists():
        for doc_file in docs_dir.glob("*.md"):
            try:
                content = doc_file.read_text(encoding='utf-8')
                name = doc_file.stem
                
                # Check if already exists
                existing = await database.context_documents.get_by_name(name)
                if existing:
                    print(f"  ⚠️  Document '{name}' already exists, skipping")
                    continue
                
                doc_id = await database.context_documents.create(
                    name=name,
                    title=doc_file.name.replace('_', ' ').title(),
                    category="system",
                    content=content,
                    format="markdown",
                    version="1.0.0"
                )
                print(f"  ✅ Added /docs/{doc_file.name} as '{name}' (ID: {doc_id})")
                docs_added += 1
                
            except Exception as e:
                print(f"  ❌ Failed to add {doc_file.name}: {e}")
    
    # Add additional context documents referenced by agents
    additional_docs = [
        # Agent-specific guides
        {
            "name": "agent_selector_guide",
            "title": "Agent Selector - Task Routing and Agent Selection Guide",
            "category": "agent_guide",
            "content": Path(__file__).parent.parent.parent.joinpath("docs/agent_contexts/agent_selector_guide.md").read_text()
        },
        {
            "name": "task_breakdown_guide", 
            "title": "Task Breakdown - Recursive Decomposition Guide",
            "category": "agent_guide",
            "content": Path(__file__).parent.parent.parent.joinpath("docs/agent_contexts/task_breakdown_guide.md").read_text()
        },
        {
            "name": "context_addition_guide",
            "title": "Context Addition - Knowledge Management and Enhancement Guide", 
            "category": "agent_guide",
            "content": Path(__file__).parent.parent.parent.joinpath("docs/agent_contexts/context_addition_guide.md").read_text()
        },
        {
            "name": "tool_addition_guide",
            "title": "Tool Addition - Capability Discovery and Enhancement Guide",
            "category": "agent_guide", 
            "content": Path(__file__).parent.parent.parent.joinpath("docs/agent_contexts/tool_addition_guide.md").read_text()
        },
        {
            "name": "task_evaluator_guide",
            "title": "Task Evaluator - Quality Assessment and Validation Guide",
            "category": "agent_guide",
            "content": Path(__file__).parent.parent.parent.joinpath("docs/agent_contexts/task_evaluator_guide.md").read_text()
        },
        {
            "name": "documentation_agent_guide",
            "title": "Documentation Agent - Knowledge Capture and System Transparency Guide",
            "category": "agent_guide",
            "content": Path(__file__).parent.parent.parent.joinpath("docs/agent_contexts/documentation_agent_guide.md").read_text()
        },
        {
            "name": "summary_agent_guide",
            "title": "Summary Agent - Information Synthesis and Communication Guide", 
            "category": "agent_guide",
            "content": Path(__file__).parent.parent.parent.joinpath("docs/agent_contexts/summary_agent_guide.md").read_text()
        },
        {
            "name": "review_agent_guide", 
            "title": "Review Agent - System Improvement and Evolution Guide",
            "category": "agent_guide",
            "content": Path(__file__).parent.parent.parent.joinpath("docs/agent_contexts/review_agent_guide.md").read_text()
        },
        # Existing system documents
        {
            "name": "agent_registry",
            "title": "Agent Registry and Capabilities",
            "category": "reference",
            "content": """# Agent Registry

## Available Agent Types

### agent_selector
**Purpose**: Task routing and agent selection
**Use when**: Need to determine the right agent for a task
**Capabilities**: Analyzes tasks, routes to appropriate agents, creates new agent types

### task_breakdown  
**Purpose**: Complex task decomposition
**Use when**: Tasks have multiple steps or complex requirements
**Capabilities**: Breaks down problems, creates subtasks, manages dependencies

### context_addition
**Purpose**: Knowledge and context management
**Use when**: Agents need domain knowledge or additional context
**Capabilities**: Creates documentation, gathers context, manages knowledge base

### tool_addition
**Purpose**: Capability expansion and tool development
**Use when**: Agents need new tools or integrations
**Capabilities**: Discovers tools, creates MCP integrations, builds custom tools

### task_evaluator
**Purpose**: Quality assessment and validation
**Use when**: Need to validate task completion and quality
**Capabilities**: Evaluates results, checks quality, provides feedback

### documentation_agent
**Purpose**: System documentation and knowledge capture
**Use when**: Need to document changes, procedures, or discoveries
**Capabilities**: Creates docs, updates knowledge base, maintains standards

### summary_agent
**Purpose**: Information synthesis and reporting
**Use when**: Need concise summaries for parent agents
**Capabilities**: Synthesizes information, creates reports, filters noise

### review_agent
**Purpose**: System improvement and optimization
**Use when**: Need to analyze and fix systemic issues
**Capabilities**: Analyzes problems, implements fixes, optimizes performance"""
        },
        {
            "name": "breakdown_guidelines",
            "title": "Task Breakdown Guidelines",
            "category": "process",
            "content": """# Task Breakdown Guidelines

## Principles
1. **Independence**: Each subtask should be executable independently
2. **Clarity**: Clear success criteria and expected outputs
3. **Granularity**: Right-sized chunks (not too big, not too small)
4. **Dependencies**: Minimize and clearly identify dependencies
5. **Parallelization**: Enable parallel execution where possible

## Process
1. **Analyze Scope**: Understand the full problem domain
2. **Identify Phases**: Major logical divisions or workflow steps
3. **Define Subtasks**: Specific, actionable items within each phase
4. **Map Dependencies**: Understand what must happen in order
5. **Assign Agents**: Match subtasks to appropriate agent capabilities
6. **Define Success**: Clear criteria for each subtask completion

## Best Practices
- Keep subtasks focused on single concerns
- Ensure each has measurable deliverables
- Include validation and testing steps
- Account for error handling and edge cases
- Document assumptions and constraints
- Plan for integration and assembly of results

## Common Patterns
- **Sequential**: Steps that must happen in order
- **Parallel**: Independent tasks that can run simultaneously
- **Conditional**: Tasks that depend on previous results
- **Iterative**: Tasks that may need multiple rounds
- **Validation**: Quality checks and testing tasks"""
        },
        {
            "name": "evaluation_criteria",
            "title": "Task Evaluation Criteria",
            "category": "process",
            "content": """# Task Evaluation Criteria

## Completeness Assessment
- All stated requirements addressed
- No missing functionality or deliverables
- Edge cases and error conditions handled
- Documentation and comments provided

## Correctness Validation
- Solution works as intended
- Produces expected outputs
- Handles inputs correctly
- No logical errors or bugs

## Quality Standards
- Code follows established conventions
- Proper error handling implemented
- Performance meets requirements
- Security considerations addressed
- Maintainable and readable implementation

## Testing and Validation
- Adequate test coverage provided
- Tests pass consistently
- Manual testing performed where needed
- Integration testing completed

## Documentation Quality
- Clear documentation provided
- Usage examples included
- Architecture and design explained
- Maintenance instructions available

## Evaluation Process
1. Review requirements vs. deliverables
2. Test functionality and edge cases
3. Assess code quality and standards
4. Validate documentation completeness
5. Check performance and efficiency
6. Provide specific feedback and scores"""
        },
        {
            "name": "documentation_standards",
            "title": "Documentation Standards",
            "category": "process",  
            "content": """# Documentation Standards

## Documentation Types
- **System Documentation**: Architecture, design, deployment
- **API Documentation**: Endpoints, parameters, examples
- **Process Documentation**: Workflows, procedures, guidelines
- **Reference Documentation**: Tools, configurations, specifications
- **User Documentation**: Guides, tutorials, FAQs

## Format Standards
- Use Markdown for all documentation
- Clear headings and structure
- Code examples with syntax highlighting
- Links to related documentation
- Version information and dates

## Content Requirements
- **Purpose**: What the component/process does
- **Usage**: How to use it with examples
- **Configuration**: Setup and configuration options
- **Dependencies**: Required tools, services, permissions
- **Troubleshooting**: Common issues and solutions
- **References**: Links to related documentation

## Maintenance Guidelines
- Keep documentation current with code changes
- Review and update quarterly
- Include change logs for major updates
- Archive obsolete documentation
- Maintain consistent style and format"""
        },
        {
            "name": "summarization_guidelines", 
            "title": "Summarization Guidelines",
            "category": "process",
            "content": """# Summarization Guidelines

## Purpose
Create concise, actionable summaries that provide parent agents with essential information without implementation noise.

## Summary Structure
1. **Objective**: What was the task trying to accomplish?
2. **Approach**: High-level approach taken
3. **Results**: Key deliverables and outcomes
4. **Decisions**: Important decisions made and rationale
5. **Insights**: Lessons learned or discoveries
6. **Status**: Current state and next steps
7. **Quality**: Assessment of result quality and validation

## Content Filtering
**Include:**
- Business outcomes and impacts
- Key technical decisions and rationale
- Blockers encountered and how resolved
- Quality metrics and validation results
- Recommendations for next steps

**Exclude:**
- Low-level implementation details
- Routine status updates
- Debugging information
- Tool-specific commands or output
- Verbose logs or traces

## Style Guidelines
- Use clear, concise language
- Focus on outcomes over activities
- Quantify results where possible
- Highlight important decisions
- Structure for easy scanning
- Include action items if relevant"""
        },
        {
            "name": "monitoring_guidelines",
            "title": "System Monitoring Guidelines", 
            "category": "process",
            "content": """# System Monitoring Guidelines

## Monitoring Scope
- **Task Execution**: Progress, duration, resource usage
- **Agent Behavior**: Response patterns, error rates
- **System Resources**: CPU, memory, disk, network
- **Queue Health**: Task backlog, processing rates
- **Error Patterns**: Failures, timeouts, exceptions

## Key Metrics
- Task completion times vs. expectations
- Agent resource consumption patterns
- Error rates and failure categories
- Queue depth and processing throughput
- System capacity utilization

## Alert Conditions
- Tasks exceeding timeout thresholds
- Agents consuming excessive resources
- High error rates or failure patterns
- System resource exhaustion
- Infinite loops or stuck processes
- Queue backlogs exceeding capacity

## Intervention Strategies
- **Graceful**: Allow completion with monitoring
- **Timeout**: Cancel tasks exceeding limits
- **Restart**: Restart stuck or failed agents
- **Escalate**: Flag for human review
- **Resource**: Adjust limits or add capacity

## Monitoring Tools
- System resource monitoring (CPU, memory)
- Database query analysis
- Log analysis and pattern detection
- Task queue health checks
- Agent communication monitoring"""
        },
        {
            "name": "system_limits",
            "title": "System Resource Limits",
            "category": "reference",
            "content": """# System Resource Limits

## Agent Execution Limits
- **Max Execution Time**: 300 seconds (5 minutes) default
- **Max Tool Calls**: 50 per task
- **Max Recursion Depth**: 10 levels
- **Memory Limit**: 512MB per agent
- **Concurrent Agents**: 3 maximum

## Task Management Limits  
- **Max Subtasks**: 20 per parent task
- **Queue Depth**: 100 pending tasks maximum
- **Message History**: 1000 messages per task
- **Task Tree Size**: 100 tasks per tree maximum

## Database Limits
- **Query Timeout**: 30 seconds
- **Result Set Size**: 1000 rows maximum
- **Transaction Size**: 10MB maximum
- **Connection Pool**: 10 connections

## Safety Mechanisms
- Automatic timeout enforcement
- Resource monitoring and alerts
- Recursion depth tracking
- Memory usage monitoring
- Queue overflow protection

## Override Procedures
- High-priority tasks can request limit increases
- System administrator approval required
- Temporary overrides with automatic revert
- Monitoring during override periods"""
        },
        {
            "name": "improvement_guide",
            "title": "System Improvement Guide",
            "category": "process",
            "content": """# System Improvement Guide

## Self-Modification Process
1. **Create Branch**: Always work in a separate git branch
2. **Analyze Issue**: Understand root cause and scope
3. **Design Solution**: Plan changes and impacts
4. **Implement**: Make code/config changes
5. **Test**: Validate changes work correctly
6. **Document**: Update relevant documentation
7. **Commit**: Create commit with clear description
8. **Deploy**: Merge to main and restart if needed
9. **Validate**: Confirm improvement works in production

## Types of Improvements
- **Bug Fixes**: Correct errors and edge cases
- **Performance**: Optimize speed and resource usage
- **Features**: Add new capabilities and tools
- **UX**: Improve user interface and experience
- **Architecture**: Refactor and improve design
- **Security**: Address vulnerabilities and hardening

## Safety Guidelines
- Always backup before changes
- Test changes thoroughly
- Use feature flags for risky changes
- Monitor after deployment
- Have rollback plan ready
- Document all changes

## Git Workflow
- Create descriptive branch names
- Make atomic commits with clear messages
- Include tests with changes
- Update documentation
- Review changes before merging
- Tag releases appropriately

## Testing Strategy
- Unit tests for individual components
- Integration tests for workflows
- Performance tests for optimization
- User acceptance tests for features
- Regression tests for bug fixes"""
        },
        {
            "name": "quality_standards",
            "title": "Quality Standards",
            "category": "reference",
            "content": """# Quality Standards

## Code Quality
- **Readability**: Clear, well-structured code
- **Documentation**: Comprehensive comments and docs
- **Testing**: Adequate test coverage (>80%)
- **Error Handling**: Proper exception handling
- **Performance**: Meets efficiency requirements
- **Security**: No vulnerabilities or security issues

## Process Quality
- **Requirements**: Clear, complete specifications
- **Design**: Well-architected solutions
- **Implementation**: Follows best practices
- **Validation**: Thorough testing and review
- **Documentation**: Complete and accurate
- **Deployment**: Reliable and repeatable

## Deliverable Quality
- **Completeness**: All requirements met
- **Correctness**: Works as specified
- **Reliability**: Stable and dependable
- **Maintainability**: Easy to update and extend
- **Usability**: User-friendly and intuitive
- **Performance**: Fast and efficient

## Quality Gates
- Code review required for all changes
- Automated testing must pass
- Documentation must be updated
- Performance benchmarks must be met
- Security scan must be clean
- User acceptance testing completed

## Continuous Improvement
- Regular quality metrics review
- Process improvement initiatives
- Training and skill development
- Tool and technology updates
- Best practice sharing"""
        },
        {
            "name": "tool_registry", 
            "title": "Tool Registry and MCP Documentation",
            "category": "reference",
            "content": """# Tool Registry and MCP Documentation

## Core MCP Tools (Always Available)
1. **break_down_task()** - Recursive task decomposition
2. **start_subtask()** - Spawn specialized agents
3. **request_context()** - Knowledge expansion  
4. **request_tools()** - Capability discovery
5. **end_task()** - Task completion
6. **flag_for_review()** - Human oversight
7. **think_out_loud()** - Transparent reasoning

## Internal System Tools
- **list_agents** - Query available agent configurations
- **list_documents** - Query context documents
- **list_optional_tools** - Query tools registry
- **query_database** - Direct database queries (read-only)

## External Integration Tools
- **use_terminal** - Execute shell commands (whitelisted)
- **github_operations** - Git operations and repository management
- **send_message_to_user** - Send messages to users for questions, updates, verification

## MCP Integration Guidelines
- Use official MCP implementations where available
- Follow MCP protocol specifications
- Implement proper error handling
- Add comprehensive logging
- Document tool capabilities and limitations
- Test thoroughly before deployment

## Tool Categories
- **System**: Database, file system, process management
- **Development**: Git, testing, deployment
- **Communication**: Notifications, reporting
- **Analysis**: Data processing, visualization
- **Integration**: External APIs, services

## Adding New Tools
1. Check existing tools for similar functionality
2. Research official MCP implementations
3. Design tool interface and parameters
4. Implement with proper error handling
5. Add to registry with documentation
6. Test integration thoroughly
7. Update agent configurations as needed"""
        },
        {
            "name": "mcp_documentation",
            "title": "MCP Protocol Documentation",
            "category": "reference", 
            "content": """# MCP Protocol Documentation

## Model Context Protocol Overview
MCP is an open protocol that enables seamless integration between LLM applications and external data sources and tools.

## Official MCP Tools Used
- **GitHub MCP Server**: Repository management and git operations
- **Shell Command MCP**: Secure terminal command execution
- **Database Query MCP**: Safe database operations

## Tool Development Guidelines
- Follow MCP protocol specifications
- Implement proper parameter validation
- Use structured error responses
- Add comprehensive logging
- Test with multiple scenarios
- Document thoroughly

## Security Considerations
- Validate all input parameters
- Restrict dangerous operations
- Use whitelist approach for commands
- Log all tool executions
- Implement timeout mechanisms
- Handle errors gracefully

## Integration Process
1. Identify tool requirements
2. Search for existing MCP implementations
3. Evaluate security and reliability
4. Configure and test integration
5. Add to internal tool registry
6. Update agent configurations
7. Monitor usage and performance

## Best Practices
- Use official implementations when available
- Implement consistent error handling
- Add comprehensive parameter validation
- Include usage examples in documentation
- Test edge cases and error conditions
- Monitor performance and reliability"""
        },
        {
            "name": "available_context",
            "title": "Available Context Documents",
            "category": "reference",
            "content": """# Available Context Documents

## System Documentation
- **agent_system_prd** - Complete product requirements and vision
- **architectural_schemas** - Technical schemas and interfaces  
- **development_launch_plan** - Implementation timeline and approach
- **project_principles** - Core principles and philosophy
- **system_overview** - High-level system description
- **system_architecture** - Component architecture and relationships

## Process Documentation
- **breakdown_guidelines** - Task decomposition best practices
- **evaluation_criteria** - Quality assessment standards
- **documentation_standards** - Documentation format and content
- **summarization_guidelines** - Summary creation process
- **monitoring_guidelines** - System monitoring procedures
- **improvement_guide** - Self-modification process

## Reference Documentation
- **agent_registry** - Available agent types and capabilities
- **tool_registry** - MCP tools and integration information
- **mcp_documentation** - MCP protocol and implementation
- **quality_standards** - Quality gates and requirements
- **system_limits** - Resource limits and safety mechanisms
- **available_context** - This document listing all contexts

## Usage Guidelines
- Check existing documents before creating new ones
- Update documents when making system changes
- Use consistent naming conventions
- Follow documentation standards
- Keep content current and accurate
- Cross-reference related documents"""
        }
    ]
    
    additional_added = 0
    for doc_config in additional_docs:
        try:
            # Check if document already exists
            existing = await database.context_documents.get_by_name(doc_config["name"])
            if existing:
                print(f"  ⚠️  Document '{doc_config['name']}' already exists, skipping")
                continue
            
            doc_id = await database.context_documents.create(
                name=doc_config["name"],
                title=doc_config["title"], 
                category=doc_config["category"],
                content=doc_config["content"],
                format="markdown",
                version="1.0.0"
            )
            print(f"  ✅ Created document '{doc_config['name']}' (ID: {doc_id})")
            additional_added += 1
            
        except Exception as e:
            print(f"  ❌ Failed to create document '{doc_config['name']}': {e}")
    
    print(f"✅ Added {docs_added} docs files and {additional_added} additional documents")
    return True


async def seed_tools():
    """Seed all internal and external tools"""
    print("🔧 Seeding all MCP tools...")
    
    
    # Register tools with the registry first
    try:
        # Register core tools
        core_tools = register_core_tools(tool_registry)
        print(f"  ✅ Registered {len(core_tools)} core tools")
        
        # Register system tools (git, terminal)
        system_tools = register_system_tools(tool_registry) 
        print(f"  ✅ Registered {len(system_tools)} system tools")
        
        # Register internal tools (list_agents, etc)
        internal_tools = register_internal_tools(tool_registry)
        print(f"  ✅ Registered {len(internal_tools)} internal tools")
        
    except Exception as e:
        print(f"  ❌ Tool registration failed: {e}")
        return False
    
    # Add tools to database for persistence
    tools_config = [
        {
            "name": "list_agents",
            "description": "Query available agent configurations",
            "category": "system",
            "implementation": json.dumps({
                "type": "python_class",
                "module_path": "tools.system_tools.internal_tools",
                "class_name": "ListAgentsTool"
            }),
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["active", "deprecated", "testing", "all"]},
                    "include_details": {"type": "boolean"}
                }
            },
            "permissions": ["database_read"]
        },
        {
            "name": "list_documents", 
            "description": "Query available context documents",
            "category": "system",
            "implementation": json.dumps({
                "type": "python_class",
                "module_path":"tools.system_tools.internal_tools",
                "class_name":"ListDocumentsTool"
            }),
            "parameters": {
                "type": "object", 
                "properties": {
                    "category": {"type": "string"},
                    "search": {"type": "string"},
                    "include_content": {"type": "boolean"}
                }
            },
            "permissions": ["database_read"]
        },
        {
            "name": "list_optional_tools",
            "description": "Query tools registry",
            "category": "system", 
            "implementation": json.dumps({
                "type": "python_class",
                "module_path":"tools.system_tools.internal_tools", 
                "class_name":"ListOptionalToolsTool"
            }),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "status": {"type": "string"},
                    "include_config": {"type": "boolean"}
                }
            },
            "permissions": ["database_read"]
        },
        {
            "name": "use_terminal",
            "description": "Execute shell commands",
            "category": "system",
            "implementation": json.dumps({
                "type": "mcp_integration",
                "config":{"type": "shell_access", "permissions": "restricted"}
            }),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "args": {"type": "array"},
                    "working_directory": {"type": "string"}
                },
                "required": ["command"]
            },
            "permissions": ["shell_access"]
        },
        {
            "name": "github_operations",
            "description": "Git operations and repository management", 
            "category": "system",
            "implementation": json.dumps({
                "type": "mcp_integration",
                "config":{"type": "git_integration", "permissions": "full"}
            }),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string"},
                    "repository_path": {"type": "string"},
                    "args": {"type": "array"}
                },
                "required": ["operation"]
            },
            "permissions": ["git_operations"]
        },
        {
            "name": "query_database",
            "description": "Direct SQLite database queries",
            "category": "system",
            "implementation": json.dumps({
                "type": "python_class",
                "module_path":"tools.system_tools.internal_tools",
                "class_name":"QueryDatabaseTool" 
            }),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer"}
                },
                "required": ["query"]
            },
            "permissions": ["database_read"]
        },
        {
            "name": "send_message_to_user",
            "description": "Send messages directly to the user for questions, updates, verification, or communication",
            "category": "system",
            "implementation": json.dumps({
                "type": "python_class",
                "module_path":"tools.system_tools.user_communication",
                "class_name":"SendMessageToUserTool"
            }),
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message content to send to the user",
                        "minLength": 1,
                        "maxLength": 2000
                    },
                    "message_type": {
                        "type": "string",
                        "enum": ["question", "update", "verification", "error", "info", "warning", "success"],
                        "description": "Type of message for appropriate UI styling",
                        "default": "info"
                    },
                    "requires_response": {
                        "type": "boolean",
                        "description": "Whether this message requires a user response",
                        "default": False
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "normal", "high", "urgent"],
                        "description": "Message priority level",
                        "default": "normal"
                    },
                    "suggested_actions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Suggested actions or responses for the user",
                        "maxItems": 5
                    }
                },
                "required": ["message"]
            },
            "permissions": ["database_write", "websocket_broadcast"]
        }
    ]
    
    tools_added = 0
    for tool_config in tools_config:
        try:
            # Check if tool already exists in database
            existing = await database.tools.get_by_name(tool_config["name"])
            if existing:
                print(f"  ⚠️  Tool '{tool_config['name']}' already exists in DB, skipping")
                continue
            
            tool_id = await database.tools.create(
                name=tool_config["name"],
                description=tool_config["description"], 
                category=tool_config["category"],
                implementation=tool_config["implementation"],  # Already JSON string
                parameters=json.dumps(tool_config["parameters"]),
                permissions=json.dumps(tool_config["permissions"])
            )
            print(f"  ✅ Added tool '{tool_config['name']}' to database (ID: {tool_id})")
            tools_added += 1
            
        except Exception as e:
            print(f"  ❌ Failed to add tool '{tool_config['name']}' to database: {e}")
    
    print(f"✅ Added {tools_added} tools to database")
    return True


async def health_check():
    """Comprehensive health check for seeded system"""
    print("🏥 Performing comprehensive health check...")
    
    checks_passed = 0
    total_checks = 5
    
    # Database connectivity
    try:
        agents = await database.agents.get_all_active()
        print(f"  ✅ Database: {len(agents)} active agents found")
        checks_passed += 1
    except Exception as e:
        print(f"  ❌ Database check failed: {e}")
    
    # All 9 agents present
    try:
        expected_agents = [
            "agent_selector", "task_breakdown", "context_addition", "tool_addition",
            "task_evaluator", "documentation_agent", "summary_agent", "review_agent"
        ]
        missing_agents = []
        for agent_name in expected_agents:
            agent = await database.agents.get_by_name(agent_name)
            if not agent:
                missing_agents.append(agent_name)
        
        if not missing_agents:
            print(f"  ✅ Agents: All 8 core agents present")
            checks_passed += 1
        else:
            print(f"  ❌ Agents: Missing {missing_agents}")
    except Exception as e:
        print(f"  ❌ Agent check failed: {e}")
    
    # Context documents
    try:
        docs = await database.context_documents.get_by_names(["agent_registry", "breakdown_guidelines", "project_principles"])
        if len(docs) >= 3:
            print(f"  ✅ Context: Core documents available")
            checks_passed += 1
        else:
            print(f"  ❌ Context: Missing core documents")
    except Exception as e:
        print(f"  ❌ Context check failed: {e}")
    
    # Tool registry
    try:
        tools = tool_registry.list_tools()
        tool_count = sum(len(tools) for tools in tools.values())
        if tool_count >= 10:  # 7 core + 3+ system tools
            print(f"  ✅ Tools: {tool_count} tools registered")
            checks_passed += 1
        else:
            print(f"  ❌ Tools: Only {tool_count} tools registered")
    except Exception as e:
        print(f"  ❌ Tool registry check failed: {e}")
    
    # Database tools
    try:
        db_tools = await database.tools.get_all_active()
        if len(db_tools) >= 6:  # 6 optional tools
            print(f"  ✅ Database Tools: {len(db_tools)} tools in database")
            checks_passed += 1
        else:
            print(f"  ❌ Database Tools: Only {len(db_tools)} tools in database")
    except Exception as e:
        print(f"  ❌ Database tools check failed: {e}")
    
    success_rate = checks_passed / total_checks
    if success_rate >= 0.8:
        print(f"✅ Health check passed ({checks_passed}/{total_checks})")
        return True
    else:
        print(f"❌ Health check failed ({checks_passed}/{total_checks})")
        return False


async def main():
    """Main seeding function"""
    print("🚀 Seeding Complete Self-Improving Agent System...")
    print("=" * 60)
    print("Building the full foundation as specified in the launch plan")
    print("=" * 60)
    
    # Initialize database
    if not await init_database():
        print("💥 Database initialization failed, aborting")
        return False
    
    # Initialize database manager
    await database.initialize()
    
    # Seed all components
    if not await seed_all_agents():
        print("💥 Agent seeding failed, aborting")
        return False
        
    if not await seed_context_documents():
        print("💥 Context seeding failed, aborting")
        return False
    
    if not await seed_tools():
        print("💥 Tool seeding failed, aborting")
        return False
    
    # Health check
    if not await health_check():
        print("💥 Health check failed")
        return False
    
    print("=" * 60)
    print("🎉 Complete system seeding successful!")
    print("🤖 All 8 core agents, context documents, and tools are ready.")
    print("")
    print("System includes:")
    print("  • 8 specialized agents with detailed instructions")
    print("  • Complete documentation from /docs + additional contexts")
    print("  • Core MCP toolkit (7 essential tools)")
    print("  • Internal tools (list_agents, list_documents, etc.)")
    print("  • External integrations (git, terminal)")
    print("")
    print("Next steps:")
    print("  1. Start the API server: python -m api.main")
    print("  2. Open web interface: http://localhost:8000/app")
    print("  3. Submit complex tasks and watch the agents collaborate!")
    print("")
    print("The self-improving agent system is fully operational! 🚀")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Seeding cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Seeding failed: {e}")
        sys.exit(1)