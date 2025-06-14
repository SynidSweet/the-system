import React, { useState } from 'react';

const ControlPanel = ({ 
  systemConfig, 
  onUpdateConfig, 
  selectedThread, 
  pausedTasks,
  onContinueTask 
}) => {
  const [localConfig, setLocalConfig] = useState(systemConfig);

  const handleMaxTasksChange = (value) => {
    const newConfig = { ...localConfig, max_parallel_tasks: parseInt(value) };
    setLocalConfig(newConfig);
    onUpdateConfig(newConfig);
  };

  const handleStepModeToggle = (enabled) => {
    const newConfig = { ...localConfig, step_mode: enabled };
    setLocalConfig(newConfig);
    onUpdateConfig(newConfig);
  };

  const handleThreadStepMode = (enabled) => {
    const newThreads = enabled 
      ? [...localConfig.step_mode_threads, selectedThread]
      : localConfig.step_mode_threads.filter(id => id !== selectedThread);
    
    const newConfig = { ...localConfig, step_mode_threads: newThreads };
    setLocalConfig(newConfig);
    onUpdateConfig(newConfig);
  };

  const isThreadInStepMode = selectedThread && (
    localConfig.step_mode || localConfig.step_mode_threads.includes(selectedThread)
  );

  return (
    <div className="control-panel">
      <h3>System Controls</h3>
      
      <div className="control-section">
        <label className="control-label">
          Max Parallel Tasks
          <input
            type="range"
            min="1"
            max="10"
            value={localConfig.max_parallel_tasks}
            onChange={(e) => handleMaxTasksChange(e.target.value)}
            className="slider"
          />
          <span className="slider-value">{localConfig.max_parallel_tasks}</span>
        </label>
      </div>

      <div className="control-section">
        <label className="control-toggle">
          <input
            type="checkbox"
            checked={localConfig.step_mode}
            onChange={(e) => handleStepModeToggle(e.target.checked)}
          />
          <span>Global Step Mode</span>
        </label>
        
        {selectedThread && !localConfig.step_mode && (
          <label className="control-toggle">
            <input
              type="checkbox"
              checked={localConfig.step_mode_threads.includes(selectedThread)}
              onChange={(e) => handleThreadStepMode(e.target.checked)}
            />
            <span>Step Mode for Current Thread</span>
          </label>
        )}
      </div>

      {pausedTasks.length > 0 && (
        <div className="control-section paused-tasks">
          <h4>Paused Tasks</h4>
          {pausedTasks.map(task => (
            <div key={task.task_id} className="paused-task">
              <span className="task-info">
                Task {task.task_id} - {task.agent_name}
              </span>
              <button 
                className="continue-button"
                onClick={() => onContinueTask(task.task_id)}
              >
                Continue ▶
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="control-info">
        {isThreadInStepMode && (
          <div className="info-item step-active">
            ⏸️ Step mode active for this thread
          </div>
        )}
        <div className="info-item">
          Press <kbd>Ctrl+Enter</kbd> to submit new task
        </div>
      </div>
    </div>
  );
};

export default ControlPanel;