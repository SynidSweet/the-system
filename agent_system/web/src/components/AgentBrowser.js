import React, { useState, useEffect } from 'react';
import './AgentBrowser.css';

function AgentBrowser({ apiBaseUrl }) {
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [editedAgent, setEditedAgent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/agents`);
      const data = await response.json();
      setAgents(data.agents);
      setLoading(false);
    } catch (err) {
      setError('Failed to load agents');
      setLoading(false);
    }
  };

  const selectAgent = async (agent) => {
    try {
      const response = await fetch(`${apiBaseUrl}/agents/${agent.name}`);
      const data = await response.json();
      setSelectedAgent(data);
      setEditedAgent(data);
      setEditMode(false);
    } catch (err) {
      setError('Failed to load agent details');
    }
  };

  const handleEdit = () => {
    setEditMode(true);
  };

  const handleCancel = () => {
    setEditMode(false);
    setEditedAgent(selectedAgent);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await fetch(`${apiBaseUrl}/agents/${selectedAgent.name}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          instruction: editedAgent.instruction,
          available_tools: editedAgent.available_tools,
          context_documents: editedAgent.context_documents,
          model_config: editedAgent.model_config,
          permissions: editedAgent.permissions,
        }),
      });

      if (response.ok) {
        setSelectedAgent(editedAgent);
        setEditMode(false);
        fetchAgents(); // Refresh the list
      } else {
        throw new Error('Failed to save');
      }
    } catch (err) {
      setError('Failed to save agent');
    } finally {
      setSaving(false);
    }
  };

  const handleFieldChange = (field, value) => {
    setEditedAgent(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleArrayFieldChange = (field, value) => {
    try {
      const arrayValue = JSON.parse(value);
      if (Array.isArray(arrayValue)) {
        setEditedAgent(prev => ({
          ...prev,
          [field]: arrayValue
        }));
      }
    } catch (e) {
      // Invalid JSON, ignore
    }
  };

  const handleObjectFieldChange = (field, value) => {
    try {
      const objectValue = JSON.parse(value);
      if (typeof objectValue === 'object') {
        setEditedAgent(prev => ({
          ...prev,
          [field]: objectValue
        }));
      }
    } catch (e) {
      // Invalid JSON, ignore
    }
  };

  if (loading) {
    return <div className="agent-browser loading">Loading agents...</div>;
  }

  return (
    <div className="agent-browser">
      <div className="agent-list">
        <h2>Agents</h2>
        <div className="agent-items">
          {agents.map(agent => (
            <div
              key={agent.id}
              className={`agent-item ${selectedAgent?.id === agent.id ? 'selected' : ''}`}
              onClick={() => selectAgent(agent)}
            >
              <div className="agent-name">{agent.name}</div>
              <div className="agent-status">{agent.status}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="agent-details">
        {selectedAgent ? (
          <>
            <div className="agent-header">
              <h2>{selectedAgent.name}</h2>
              <div className="agent-actions">
                {!editMode ? (
                  <button onClick={handleEdit} className="edit-button">Edit</button>
                ) : (
                  <>
                    <button 
                      onClick={handleSave} 
                      className="save-button"
                      disabled={saving}
                    >
                      {saving ? 'Saving...' : 'Save'}
                    </button>
                    <button 
                      onClick={handleCancel} 
                      className="cancel-button"
                      disabled={saving}
                    >
                      Cancel
                    </button>
                  </>
                )}
              </div>
            </div>

            {error && <div className="error-message">{error}</div>}

            <div className="agent-fields">
              <div className="field-group">
                <label>Instruction</label>
                {editMode ? (
                  <textarea
                    value={editedAgent.instruction}
                    onChange={(e) => handleFieldChange('instruction', e.target.value)}
                    className="instruction-input"
                    rows={10}
                  />
                ) : (
                  <div className="instruction-display">{selectedAgent.instruction}</div>
                )}
              </div>

              <div className="field-group">
                <label>Available Tools</label>
                {editMode ? (
                  <textarea
                    value={JSON.stringify(editedAgent.available_tools, null, 2)}
                    onChange={(e) => handleArrayFieldChange('available_tools', e.target.value)}
                    className="json-input"
                    rows={5}
                  />
                ) : (
                  <div className="tools-list">
                    {selectedAgent.available_tools.map((tool, idx) => (
                      <span key={idx} className="tool-chip">{tool}</span>
                    ))}
                  </div>
                )}
              </div>

              <div className="field-group">
                <label>Context Documents</label>
                {editMode ? (
                  <textarea
                    value={JSON.stringify(editedAgent.context_documents, null, 2)}
                    onChange={(e) => handleArrayFieldChange('context_documents', e.target.value)}
                    className="json-input"
                    rows={5}
                  />
                ) : (
                  <div className="docs-list">
                    {selectedAgent.context_documents.map((doc, idx) => (
                      <span key={idx} className="doc-chip">{doc}</span>
                    ))}
                  </div>
                )}
              </div>

              <div className="field-group">
                <label>Model Configuration</label>
                {editMode ? (
                  <textarea
                    value={JSON.stringify(editedAgent.model_config, null, 2)}
                    onChange={(e) => handleObjectFieldChange('model_config', e.target.value)}
                    className="json-input"
                    rows={4}
                  />
                ) : (
                  <pre className="json-display">
                    {JSON.stringify(selectedAgent.model_config, null, 2)}
                  </pre>
                )}
              </div>

              <div className="field-group">
                <label>Permissions</label>
                {editMode ? (
                  <textarea
                    value={JSON.stringify(editedAgent.permissions, null, 2)}
                    onChange={(e) => handleObjectFieldChange('permissions', e.target.value)}
                    className="json-input"
                    rows={4}
                  />
                ) : (
                  <pre className="json-display">
                    {JSON.stringify(selectedAgent.permissions, null, 2)}
                  </pre>
                )}
              </div>

              <div className="field-group">
                <label>Metadata</label>
                <div className="metadata">
                  <div>ID: {selectedAgent.id}</div>
                  <div>Version: {selectedAgent.version}</div>
                  <div>Status: {selectedAgent.status}</div>
                  <div>Created: {new Date(selectedAgent.created_at).toLocaleString()}</div>
                  <div>Updated: {new Date(selectedAgent.updated_at).toLocaleString()}</div>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="no-selection">Select an agent to view details</div>
        )}
      </div>
    </div>
  );
}

export default AgentBrowser;