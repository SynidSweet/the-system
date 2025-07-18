import React, { useState, useEffect } from 'react';
import './ToolBrowser.css';

function ToolBrowser({ apiBaseUrl }) {
  const [tools, setTools] = useState({});
  const [selectedTool, setSelectedTool] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTools();
  }, []);

  const fetchTools = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/system/tools`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      const tools = data.tools || {};
      setTools(tools);
      
      // Select first category and tool by default
      const categories = Object.keys(tools);
      if (categories.length > 0) {
        const firstCategory = categories[0];
        setSelectedCategory(firstCategory);
        if (tools[firstCategory] && tools[firstCategory].length > 0) {
          setSelectedTool(tools[firstCategory][0]);
        }
      }
      
      setLoading(false);
    } catch (err) {
      console.error('Error fetching tools:', err);
      setError('Failed to load tools');
      setTools({});
      setLoading(false);
    }
  };

  const selectTool = (tool, category) => {
    setSelectedTool(tool);
    setSelectedCategory(category);
  };

  const renderParameters = (parameters) => {
    if (!parameters || Object.keys(parameters).length === 0) {
      return <div className="no-params">No parameters</div>;
    }

    const required = parameters.required || [];
    const properties = parameters.properties || {};

    return (
      <div className="parameters">
        {Object.entries(properties).map(([name, schema]) => (
          <div key={name} className="parameter">
            <div className="param-header">
              <span className="param-name">{name}</span>
              <span className="param-type">{schema.type}</span>
              {required.includes(name) && <span className="param-required">required</span>}
            </div>
            {schema.description && (
              <div className="param-description">{schema.description}</div>
            )}
            {schema.enum && (
              <div className="param-enum">
                Allowed values: {schema.enum.join(', ')}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return <div className="tool-browser loading">Loading tools...</div>;
  }

  return (
    <div className="tool-browser">
      <div className="tool-categories">
        <h2>Tool Categories</h2>
        {Object.entries(tools).map(([category, categoryTools]) => (
          <div key={category} className="category-section">
            <h3 className="category-title">{category}</h3>
            <div className="tool-items">
              {categoryTools.map((tool, idx) => (
                <div
                  key={idx}
                  className={`tool-item ${selectedTool?.name === tool.name ? 'selected' : ''}`}
                  onClick={() => selectTool(tool, category)}
                >
                  <div className="tool-name">{tool.name}</div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="tool-details">
        {selectedTool ? (
          <>
            <div className="tool-header">
              <h2>{selectedTool.name}</h2>
              <span className="tool-category-badge">{selectedCategory}</span>
            </div>

            {error && <div className="error-message">{error}</div>}

            <div className="tool-info">
              <div className="field-group">
                <label>Description</label>
                <div className="tool-description">{selectedTool.description}</div>
              </div>

              <div className="field-group">
                <label>Parameters</label>
                {renderParameters(selectedTool.parameters)}
              </div>

                      {selectedTool.permissions && Array.isArray(selectedTool.permissions) && selectedTool.permissions.length > 0 && (
                <div className="field-group">
                  <label>Required Permissions</label>
                  <div className="permissions-list">
                    {selectedTool.permissions.map((perm, idx) => (
                      <span key={idx} className="permission-chip">{perm}</span>
                    ))}
                  </div>
                </div>
              )}

              <div className="field-group">
                <label>Usage Example</label>
                <pre className="usage-example">
{`await agent.call_tool("${selectedTool.name}", {${
  selectedTool.parameters?.properties 
    ? '\n' + Object.entries(selectedTool.parameters.properties)
        .map(([name, schema]) => `  ${name}: ${
          schema.type === 'string' ? '"example"' : 
          schema.type === 'number' ? '42' :
          schema.type === 'boolean' ? 'true' :
          schema.type === 'array' ? '[]' :
          '{}'
        }`)
        .join(',\n') + '\n'
    : ''
}})`}</pre>
              </div>
            </div>
          </>
        ) : (
          <div className="no-selection">Select a tool to view details</div>
        )}
      </div>
    </div>
  );
}

export default ToolBrowser;