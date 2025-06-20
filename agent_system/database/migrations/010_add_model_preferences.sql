-- Add model preferences to agent entities
-- This migration updates agent metadata to include model configuration

-- Update existing agents with model preferences
UPDATE entities
SET metadata = json_set(
    COALESCE(metadata, '{}'),
    '$.model_preference',
    CASE name
        WHEN 'agent_selector' THEN 'gemini-2.5-flash-lite'
        WHEN 'task_breakdown' THEN 'gemini-2.5-flash'
        WHEN 'context_addition' THEN 'gemini-2.5-flash'
        WHEN 'tool_addition' THEN 'gemini-2.5-flash'
        WHEN 'task_evaluator' THEN 'gemini-2.5-flash-lite'
        WHEN 'documentation_agent' THEN 'gemini-2.5-flash'
        WHEN 'summary_agent' THEN 'gemini-2.5-flash-lite'
        WHEN 'review_agent' THEN 'gemini-2.5-pro'
        WHEN 'planning_agent' THEN 'gemini-2.5-flash'
        WHEN 'investigator_agent' THEN 'gemini-2.5-pro'
        WHEN 'optimizer_agent' THEN 'gemini-2.5-flash'
        WHEN 'feedback_agent' THEN 'gemini-2.5-flash'
        WHEN 'recovery_agent' THEN 'gemini-2.5-flash'
        ELSE 'gemini-2.5-flash-lite'
    END,
    '$.model_config', json_object(
        'provider', 'google',
        'temperature', 0.1,
        'max_tokens', 4000
    )
)
WHERE entity_type = 'agent'
  AND status = 'active';

-- Add system configuration for available models
INSERT OR REPLACE INTO entities (entity_type, entity_id, name, metadata, status)
VALUES (
    'document',
    (SELECT COALESCE(MAX(entity_id), 0) + 1 FROM entities WHERE entity_type = 'document'),
    'gemini_model_config',
    json_object(
        'title', 'Gemini 2.5 Model Configuration',
        'category', 'system',
        'content', json_object(
            'available_models', json_object(
                'gemini-2.5-flash-lite', json_object(
                    'name', 'Gemini 2.5 Flash-Lite',
                    'description', 'Fastest and most cost-efficient',
                    'context_window', 1000000,
                    'relative_cost', 1,
                    'relative_speed', 10
                ),
                'gemini-2.5-flash', json_object(
                    'name', 'Gemini 2.5 Flash',
                    'description', 'Balanced performance',
                    'context_window', 1000000,
                    'relative_cost', 3,
                    'relative_speed', 5
                ),
                'gemini-2.5-pro', json_object(
                    'name', 'Gemini 2.5 Pro',
                    'description', 'Highest capability',
                    'context_window', 2000000,
                    'relative_cost', 10,
                    'relative_speed', 2
                )
            ),
            'default_model', 'gemini-2.5-flash-lite',
            'selection_strategy', 'Agents can request specific models based on task complexity'
        )
    ),
    'active'
);

-- Log the model update
INSERT INTO events (event_type, primary_entity_type, primary_entity_id, event_data, metadata)
VALUES (
    'SYSTEM_UPDATE',
    'system',
    0,
    json_object(
        'action', 'model_configuration_update',
        'description', 'Updated to Gemini 2.5 model series'
    ),
    json_object(
        'default_model', 'gemini-2.5-flash-lite',
        'available_models', json_array('gemini-2.5-flash-lite', 'gemini-2.5-flash', 'gemini-2.5-pro'),
        'migration', '010_add_model_preferences'
    )
);