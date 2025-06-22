-- Migration: Add Process Discovery Agent for Process-First Architecture
-- This adds the process_discovery agent which is fundamental to the process-first approach

-- Add process_discovery to agent_base_permissions
INSERT INTO agent_base_permissions (agent_type, entity_permissions, base_tools) VALUES
('process_discovery', 
 '{"process": ["read", "write"], "document": ["read", "write"], "task": ["read"], "tool": ["read"], "agent": ["read"]}',
 '["entity_manager", "sql_lite", "file_system_listing"]'
)
ON CONFLICT (agent_type) DO UPDATE SET
    entity_permissions = EXCLUDED.entity_permissions,
    base_tools = EXCLUDED.base_tools;

-- Create the process_discovery agent
INSERT INTO agents (name, instruction, status, metadata) VALUES
('process_discovery',
'You are the Process Discovery Agent, responsible for analyzing task domains and establishing comprehensive systematic process frameworks before any task execution begins.

## Core Principle: Process-First Operation

Your primary responsibility is to ensure that EVERY task domain has a complete systematic framework established before any execution begins. You transform undefined problems into systematic domains with rules, regulations, and comprehensive context that enables isolated task success.

## Process-First Thinking Pattern

When analyzing any task, ask:
- "What systematic framework does this domain require?" (NOT "How do I solve this task?")
- "What processes need to exist for isolated subtasks to succeed?" (NOT "What''s the quickest solution?")
- "Is the structural foundation complete?" (NOT "Can I work around missing structure?")

Remember: The goal is not to solve tasks quickly, but to establish systematic frameworks that enable consistent, high-quality, isolated task execution across entire domains.',
'active',
'{"agent_type": "process_discovery", "version": "1.0", "process_first": true}'
)
ON CONFLICT (name) DO UPDATE SET
    instruction = EXCLUDED.instruction,
    status = EXCLUDED.status,
    metadata = EXCLUDED.metadata;

-- Add process_discovery_guide to documents if not exists
INSERT INTO documents (name, title, category, content, status, metadata) VALUES
('process_discovery_guide',
'Process Discovery Agent Guide',
'agent_guides',
'# Process Discovery Agent Guide

[Full content would be loaded from file]',
'active',
'{"version": "1.0", "process_first": true}'
)
ON CONFLICT (name) DO NOTHING;

-- Add process framework related documents
INSERT INTO documents (name, title, category, content, status, metadata) VALUES
('process_framework_guide',
'Process Framework Guide',
'process_guides',
'# Process Framework Guide

This guide describes how to establish and validate comprehensive systematic process frameworks.',
'active',
'{"version": "1.0"}'
),
('systematic_framework_guide',
'Systematic Framework Guide',
'process_guides',
'# Systematic Framework Guide

Guidelines for creating systematic frameworks that enable isolated task success.',
'active',
'{"version": "1.0"}'
),
('framework_validation_guide',
'Framework Validation Guide',
'process_guides',
'# Framework Validation Guide

How to validate that systematic frameworks are complete and enable isolated task success.',
'active',
'{"version": "1.0"}'
)
ON CONFLICT (name) DO NOTHING;

-- Add process_discovery_process to processes
INSERT INTO processes (name, description, status, metadata) VALUES
('process_discovery_process',
'Analyzes task domains and establishes comprehensive systematic frameworks before any execution',
'active',
'{"version": "1.0", "primary_process": true, "process_first": true}'
),
('domain_analysis_process',
'Analyzes domain requirements for systematic framework establishment',
'active',
'{"version": "1.0", "subprocess_of": "process_discovery_process"}'
)
ON CONFLICT (name) DO UPDATE SET
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    metadata = EXCLUDED.metadata;