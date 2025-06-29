import React, { useState, useEffect, useCallback } from 'react';
import './ToolBrowser.css';
import { Tool, ToolBrowserProps } from '../types';

function ToolBrowser({ apiBaseUrl }: ToolBrowserProps) {
  const [tools, setTools] = useState<Record<string, Tool[]>>({});
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTools = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/system/tools`);
      const data = await response.json();
      setTools(data.tools);
      
      // Select first category and tool by default
      const categories = Object.keys(data.tools);
      if (categories.length > 0) {
        const firstCategory = categories[0];
        setSelectedCategory(firstCategory);
        if (data.tools[firstCategory].length > 0) {
          setSelectedTool(data.tools[firstCategory][0]);
        }
      }
      
      setLoading(false);
    } catch (err) {
      setError('Failed to load tools');
      setLoading(false);
    }
  }, [apiBaseUrl]);

  useEffect(() => {
    fetchTools();
  }, [fetchTools]);

  const selectTool = useCallback((tool: Tool, category: string) => {
    setSelectedTool(tool);
    setSelectedCategory(category);
  }, []);

  const renderParameters = useCallback((parameters: Tool['parameters']) => {
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
  }, []);

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

              {selectedTool.permissions && selectedTool.permissions.length > 0 && (
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