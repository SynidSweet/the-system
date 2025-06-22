-- Add system initialization process and related configuration

-- Add initialization process
INSERT OR REPLACE INTO processes (name, description, category, steps, parameters, permissions, status, metadata)
VALUES (
    'system_initialization_process',
    'Complete system initialization including knowledge bootstrap and framework establishment',
    'system_management',
    json_array(
        'Bootstrap knowledge system from documentation',
        'Execute Phase 1: Bootstrap Validation',
        'Execute Phase 2: Framework Establishment',
        'Execute Phase 3: Capability Validation',
        'Execute Phase 4: Self-Improvement Setup',
        'Validate system readiness for autonomous operation'
    ),
    json_object(
        'manual_mode', true,
        'phase_timeout', 3600,
        'validation_required', true
    ),
    json_object(
        'required', json_array('system_admin', 'task_create', 'knowledge_write'),
        'optional', json_array('process_modify')
    ),
    'active',
    json_object(
        'created_by', 'migration_015',
        'initialization_process', true,
        'execution_order', 'sequential'
    )
);

-- Add sub-processes for initialization
INSERT OR REPLACE INTO processes (name, description, category, steps, parameters, permissions, status, metadata)
VALUES 
(
    'knowledge_bootstrap_process',
    'Convert documentation to knowledge entities',
    'knowledge_management',
    json_array(
        'Scan documentation directories',
        'Convert agent guides to knowledge entities',
        'Convert architecture docs to system knowledge',
        'Convert principles to foundational knowledge',
        'Establish initial relationships',
        'Validate knowledge base completeness'
    ),
    json_object(
        'docs_dir', '.',
        'knowledge_dir', 'knowledge',
        'validate_relationships', true
    ),
    json_object(
        'required', json_array('file_read', 'knowledge_write')
    ),
    'active',
    json_object('initialization_subprocess', true)
),
(
    'framework_establishment_process',
    'Establish systematic process frameworks',
    'process_management',
    json_array(
        'Analyze domain requirements',
        'Create process templates',
        'Define execution boundaries',
        'Establish validation criteria',
        'Document framework specifications'
    ),
    json_object(
        'framework_type', 'systematic',
        'validation_required', true
    ),
    json_object(
        'required', json_array('process_create', 'document_write')
    ),
    'active',
    json_object('initialization_subprocess', true)
),
(
    'context_system_validation',
    'Validate context assembly functionality',
    'testing',
    json_array(
        'Test context assembly for all agent types',
        'Validate completeness scoring',
        'Test knowledge gap detection',
        'Verify isolation requirements',
        'Generate validation report'
    ),
    json_object(
        'test_all_agents', true,
        'min_completeness_score', 0.8
    ),
    json_object(
        'required', json_array('knowledge_read', 'test_execute')
    ),
    'active',
    json_object('initialization_subprocess', true)
);

-- Add initialization state tracking
CREATE TABLE IF NOT EXISTS system_state (
    id INTEGER PRIMARY KEY,
    state VARCHAR(50) NOT NULL, -- 'uninitialized', 'initializing', 'ready', 'maintenance'
    initialized_at TIMESTAMP,
    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT -- JSON for additional state info
);

-- Insert initial state
INSERT INTO system_state (id, state, metadata)
VALUES (
    1,
    'uninitialized',
    json_object(
        'version', '1.0.0',
        'requires_initialization', true
    )
);

-- Add initialization tracking to tasks
ALTER TABLE tasks ADD COLUMN initialization_task BOOLEAN DEFAULT FALSE;

-- Log the initialization process addition
INSERT INTO events (event_type, primary_entity_type, primary_entity_id, event_data, metadata)
VALUES (
    'PROCESS_CREATED',
    'process',
    (SELECT entity_id FROM entities WHERE entity_type = 'process' AND name = 'system_initialization_process'),
    json_object(
        'action', 'initialization_process_added',
        'description', 'Added complete system initialization process'
    ),
    json_object(
        'migration', '015_add_initialization_process',
        'includes_subprocesses', true,
        'phases', 4
    )
);