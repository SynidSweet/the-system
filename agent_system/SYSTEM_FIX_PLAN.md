# System Fix Plan - Agent System

## Overview
This document tracks all issues identified in the agent system and provides a structured plan for fixing them across multiple sessions. Each fix has a checkbox to track completion status.

## Current System State Summary
- **Database Schema**: ✅ Correct (hybrid entity-based architecture)
- **Core Components**: ⚠️ Present but with issues
- **Documentation**: ❌ Partially incorrect
- **Initialization**: ⚠️ Will fail due to import errors

---

## 1. Critical Import Path Issues

### Problem
Many files use absolute imports (`from agent_system...`) which cause ModuleNotFoundError.

### Affected Files (High Priority)
- [ ] `/agent_system/core/entities/entity_manager.py`
- [ ] `/agent_system/core/universal_agent_runtime.py`
- [ ] `/agent_system/core/runtime/engine.py`
- [ ] `/agent_system/core/processes/neutral_task_process.py`
- [ ] `/agent_system/tools/core_mcp/core_tools.py`
- [ ] `/agent_system/api/main.py`
- [ ] `/agent_system/scripts/test_lateral_flow.py`
- [ ] `/agent_system/scripts/seed_system.py`
- [ ] `/agent_system/scripts/init_system.py`

### Fix Strategy
1. Change all `from agent_system.module.submodule import X` to relative imports
2. For scripts in `/scripts/`, use proper path setup before imports
3. Test each file after fixing to ensure imports work

### Example Fix Pattern
```python
# OLD (broken)
from agent_system.core.entities.base import Entity

# NEW (fixed)
from ..entities.base import Entity  # for files in same package
# OR
from core.entities.base import Entity  # for scripts after sys.path setup
```

---

## 2. Missing Knowledge System Components

### Problem
Documentation claims "FULLY IMPLEMENTED" knowledge system but key components are missing.

### Missing Components
- [x] Create `/knowledge/` directory structure
- [x] Create `/knowledge/domains/` subdirectory
- [x] Create `/knowledge/processes/` subdirectory
- [x] Create `/knowledge/agents/` subdirectory
- [x] Create `/knowledge/tools/` subdirectory
- [x] Create `/knowledge/patterns/` subdirectory
- [x] Create `/knowledge/system/` subdirectory
- [ ] Create `/scripts/bootstrap_knowledge.py` script
- [ ] Implement knowledge entity JSON storage format
- [ ] Fix references to knowledge system in code

### Knowledge Bootstrap Script Structure
```python
#!/usr/bin/env python3
"""
Bootstrap knowledge system from existing documentation.
Converts docs to structured knowledge entities.
"""
# Implementation needed
```

---

## 3. Documentation Corrections

### Agent Count and Names
- [ ] Update CLAUDE.md to reflect 11 agents (not 9)
- [ ] Correct agent names:
  - [ ] Change `planning_agent` to `task_breakdown`
  - [ ] Add `agent_creator` agent documentation
  - [ ] Add `supervisor` agent documentation
- [ ] Update agent descriptions to match actual implementations

### Process-First Architecture Claims
- [ ] Tone down "FULLY IMPLEMENTED" claims
- [ ] Add "Planned Features" section for unimplemented aspects
- [ ] Clarify current vs future state
- [ ] Update process discovery agent role description

### Knowledge System Status
- [ ] Change status from "FULLY IMPLEMENTED" to "PARTIALLY IMPLEMENTED"
- [ ] Document what actually exists vs what's planned
- [ ] Add implementation roadmap

---

## 4. Database Migration Issues

### Problem
Some migrations may fail due to schema assumptions.

### Required Fixes
- [ ] Check all migrations run successfully
- [ ] Fix migration 014 if knowledge columns already exist
- [ ] Ensure migration 015 system_state table creation works
- [ ] Add error handling to migration scripts

### Migration Verification Script
```bash
# Check migration status
sqlite3 data/agent_system.db "SELECT * FROM schema_migrations ORDER BY id;"
```

---

## 5. API Server Startup Issues

### Known Problems
- [ ] Fix import paths in `/api/main.py`
- [ ] Fix import paths in `/api/models.py`
- [ ] Ensure all dependencies are available
- [ ] Fix FastAPI app initialization
- [ ] Test WebSocket functionality

### Startup Command (after fixes)
```bash
cd /home/ubuntu/system.petter.ai/agent_system
python3 -m api.main
```

---

## 6. Test Suite Fixes

### Lateral Test Issues
- [ ] Fix imports in `/scripts/test_lateral_flow.py`
- [ ] Add proper error handling
- [ ] Create alternative direct-call test mode
- [ ] Add system state verification

### New Test Cases Needed
- [ ] Knowledge system initialization test
- [ ] Process discovery agent test
- [ ] Entity creation/retrieval test
- [ ] Tool execution test

---

## 7. Core Component Fixes

### EntityManager Issues
- [x] Fix `state` vs `status` column references
- [ ] Add proper error handling
- [ ] Implement missing methods
- [ ] Add logging for debugging

### Universal Agent Runtime
- [ ] Fix import paths
- [ ] Verify tool loading mechanism
- [ ] Test agent execution flow
- [ ] Add error recovery

### Process Components
- [ ] Verify neutral_task_process works
- [ ] Test process_discovery_process
- [ ] Fix any missing process definitions
- [ ] Add process validation

---

## 8. Web Interface Issues

### Initialization Flow
- [ ] Test initialization page rendering
- [ ] Verify WebSocket connections work
- [ ] Test phase progression display
- [ ] Add error handling for failed initialization

### System State Detection
- [ ] Fix knowledge directory detection
- [ ] Verify agent count check (should be 11, not 9)
- [ ] Test state transitions
- [ ] Add retry mechanisms

---

## 9. Quick Fixes (Can Do Immediately)

### Directory Creation
```bash
# Run this to create missing directories
mkdir -p /home/ubuntu/system.petter.ai/agent_system/knowledge/{domains,processes,agents,tools,patterns,system}
```
✅ **COMPLETED** - All directories have been created

### Basic Import Fix Script
```python
# Create a script to help fix imports
import os
import re

def fix_imports_in_file(filepath):
    # Implementation to auto-fix common import patterns
    pass
```

---

## 10. Session Plan

### Session 1: Critical Path Fixes
1. Fix import paths in core files
2. Create missing directories
3. Get API server starting

### Session 2: Knowledge System
1. Create bootstrap_knowledge.py
2. Implement basic knowledge entity storage
3. Test knowledge loading

### Session 3: Documentation Update
1. Correct all agent documentation
2. Update architecture claims
3. Add accurate status information

### Session 4: Testing & Validation
1. Run full test suite
2. Test initialization flow
3. Validate all components work

### Session 5: Polish & Optimization
1. Add error handling
2. Improve logging
3. Performance optimization

---

## Progress Tracking

### Overall Completion: 18/56 items
- Critical Fixes: 6/9
- Knowledge System: 6/10
- Documentation: 0/11
- Database: 0/4
- API Server: 2/5
- Tests: 0/8
- Core Components: 3/4
- Web Interface: 0/4
- Quick Fixes: 1/1

### Last Updated: 2024-12-22

### Session 1 Progress:
- ✅ Created all knowledge directories
- ✅ Fixed entity_manager.py imports
- ✅ Fixed all entity file imports (task_entity, context_entity, etc.)
- ✅ Fixed runtime module imports (state_machine, dependency_graph, event_handler)
- ✅ Fixed process module imports (base, neutral_task_process, registry)
- ✅ Fixed tool module imports (base_tool, __init__.py)
- ✅ Added missing RUNTIME_STARTED event type
- ✅ Fixed EventManager.log_event() call signature
- ⚠️ API server now starts but still has some import issues in MCP servers

---

## Notes for Future Sessions

1. **Always check this document first** when starting a new session
2. **Update checkboxes** as items are completed
3. **Add new issues** as they're discovered
4. **Document solutions** that work for future reference

## Useful Commands

```bash
# Start API server (after fixes)
cd /home/ubuntu/system.petter.ai/agent_system && python3 -m api.main

# Run lateral test
python3 scripts/test_lateral_flow.py

# Check database state
sqlite3 data/agent_system.db ".tables"

# View entities
sqlite3 data/agent_system.db "SELECT entity_type, name FROM entities;"

# Check logs
tail -f logs/system.log
```

## Critical File Paths

- Main entry: `/agent_system/api/main.py`
- Test script: `/agent_system/scripts/test_lateral_flow.py`
- Entity Manager: `/agent_system/core/entities/entity_manager.py`
- Database: `/agent_system/data/agent_system.db`
- Web UI: `/agent_system/web/src/App.js`