import React from 'react';

const ThreadList = ({ threads, selectedThread, onSelectThread, showCompleted }) => {
  const filteredThreads = threads.filter(thread => 
    showCompleted || thread.status !== 'completed'
  );

  const getThreadStatus = (thread) => {
    if (thread.status === 'completed') return '✓';
    if (thread.status === 'failed') return '✗';
    if (thread.has_running_tasks) return '●';
    return '○';
  };

  const getThreadStatusClass = (thread) => {
    if (thread.status === 'completed') return 'status-completed';
    if (thread.status === 'failed') return 'status-failed';
    if (thread.has_running_tasks) return 'status-running';
    return 'status-idle';
  };

  return (
    <div className="thread-list">
      <div className="thread-list-header">
        <h3>Task Threads</h3>
        <label className="show-completed">
          <input
            type="checkbox"
            checked={showCompleted}
            onChange={(e) => onSelectThread(selectedThread, e.target.checked)}
          />
          Show completed
        </label>
      </div>
      <div className="thread-list-items">
        {filteredThreads.map(thread => (
          <div
            key={thread.tree_id}
            className={`thread-item ${selectedThread === thread.tree_id ? 'selected' : ''}`}
            onClick={() => onSelectThread(thread.tree_id, showCompleted)}
          >
            <span className={`thread-status ${getThreadStatusClass(thread)}`}>
              {getThreadStatus(thread)}
            </span>
            <div className="thread-info">
              <div className="thread-title">
                {thread.root_instruction?.substring(0, 50)}...
              </div>
              <div className="thread-meta">
                {thread.task_count} tasks • {new Date(thread.created_at).toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ThreadList;