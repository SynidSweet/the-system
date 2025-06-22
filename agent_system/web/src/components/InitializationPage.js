import React, { useState } from 'react';
import './InitializationPage.css';

function InitializationPage({ onInitialize }) {
  const [settings, setSettings] = useState({
    manualStepMode: true,
    maxConcurrentAgents: 1,
    enableLogging: true
  });

  const handleInitialize = () => {
    onInitialize(settings);
  };

  return (
    <div className="initialization-page">
      <div className="init-container">
        <div className="init-header">
          <h1>🚀 Agent System MVP</h1>
          <p className="tagline">Process-First Recursive Agent System</p>
        </div>

        <div className="init-content">
          <div className="welcome-section">
            <h2>Welcome to the Agent System</h2>
            <p>This is your first time running the system. The initialization process will:</p>
            <ul>
              <li>Bootstrap the knowledge system from documentation</li>
              <li>Validate core system components</li>
              <li>Establish process frameworks</li>
              <li>Test system capabilities</li>
              <li>Prepare for autonomous operation</li>
            </ul>
          </div>

          <div className="settings-section">
            <h3>Initialization Settings</h3>
            
            <div className="setting-group">
              <label>
                <input
                  type="checkbox"
                  checked={settings.manualStepMode}
                  onChange={(e) => setSettings({...settings, manualStepMode: e.target.checked})}
                />
                <span className="setting-label">Manual Step Mode</span>
                <span className="setting-description">
                  Require manual approval for each agent execution (recommended for first run)
                </span>
              </label>
            </div>

            <div className="setting-group">
              <label>
                <span className="setting-label">Max Concurrent Agents</span>
                <input
                  type="number"
                  min="1"
                  max="5"
                  value={settings.maxConcurrentAgents}
                  onChange={(e) => setSettings({...settings, maxConcurrentAgents: parseInt(e.target.value)})}
                  className="number-input"
                />
                <span className="setting-description">
                  Limit the number of agents that can run simultaneously
                </span>
              </label>
            </div>

            <div className="setting-group">
              <label>
                <input
                  type="checkbox"
                  checked={settings.enableLogging}
                  onChange={(e) => setSettings({...settings, enableLogging: e.target.checked})}
                />
                <span className="setting-label">Enable Detailed Logging</span>
                <span className="setting-description">
                  Log all system operations for debugging
                </span>
              </label>
            </div>
          </div>

          <div className="phases-section">
            <h3>Initialization Phases</h3>
            <div className="phases-grid">
              <div className="phase">
                <div className="phase-number">1</div>
                <div className="phase-info">
                  <h4>Bootstrap Validation</h4>
                  <p>Convert documentation to knowledge base</p>
                </div>
              </div>
              <div className="phase">
                <div className="phase-number">2</div>
                <div className="phase-info">
                  <h4>Framework Establishment</h4>
                  <p>Create systematic process frameworks</p>
                </div>
              </div>
              <div className="phase">
                <div className="phase-number">3</div>
                <div className="phase-info">
                  <h4>Capability Validation</h4>
                  <p>Test system components and integration</p>
                </div>
              </div>
              <div className="phase">
                <div className="phase-number">4</div>
                <div className="phase-info">
                  <h4>Self-Improvement Setup</h4>
                  <p>Initialize optimization mechanisms</p>
                </div>
              </div>
            </div>
          </div>

          <div className="warning-section">
            <div className="warning-icon">⚠️</div>
            <div className="warning-content">
              <p><strong>Important:</strong> The initialization process will execute approximately 15 tasks and may take 20-30 minutes.</p>
              <p>With manual step mode enabled, you'll have full control over the process.</p>
            </div>
          </div>

          <button className="initialize-button" onClick={handleInitialize}>
            Initialize System
          </button>
        </div>

        <div className="init-footer">
          <p>Ready to transform undefined problems into systematic solutions</p>
        </div>
      </div>
    </div>
  );
}

export default InitializationPage;