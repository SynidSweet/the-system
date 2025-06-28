import React from 'react';
import { ThreadListProps, TaskThread } from '../types';

const ThreadList: React.FC<ThreadListProps> = ({ 
  threads, 
  selectedThread, 
  onSelectThread, 
  showCompleted 
}) => {
  const filteredThreads = threads.filter(thread => 
    showCompleted || !thread.root_task || thread.root_task.status !== 'completed'
  );

  const getThreadStatus = (thread: TaskThread): string => {
    if (thread.root_task?.status === 'completed') return '✓';
    if (thread.root_task?.status === 'failed') return '✗';
    if (thread.has_running_tasks) return '●';
    return '○';
  };

  const getThreadStatusClass = (thread: TaskThread): string => {
    if (thread.root_task?.status === 'completed') return 'status-completed';
    if (thread.root_task?.status === 'failed') return 'status-failed';
    if (thread.has_running_tasks) return 'status-running';
    return 'status-idle';
  };

  const formatThreadTitle = (thread: TaskThread): string => {
    const instruction = thread.root_task?.instruction || 'Unknown task';
    return instruction.length > 50 ? `${instruction.substring(0, 50)}...` : instruction;
  };

  const formatTimestamp = (timestamp: string): string => {
    try {
      return new Date(timestamp).toLocaleTimeString();
    } catch {
      return 'Unknown time';
    }
  };

  if (threads.length === 0) {
    return (
      <div className="thread-list">
        <div className="thread-list-header">
          <h3>Task Threads</h3>
        </div>
        <div className="thread-list-empty">
          <p>No task threads yet</p>
          <p className="empty-hint">Submit a task to get started</p>
        </div>
      </div>
    );
  }

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
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                onSelectThread(thread.tree_id, showCompleted);
              }
            }}
          >
            <span className={`thread-status ${getThreadStatusClass(thread)}`}>
              {getThreadStatus(thread)}
            </span>
            <div className="thread-info">
              <div className="thread-title" title={thread.root_task?.instruction}>
                {formatThreadTitle(thread)}
              </div>
              <div className="thread-meta">
                {thread.task_count} task{thread.task_count !== 1 ? 's' : ''} • {' '}
                {thread.root_task?.created_at 
                  ? formatTimestamp(thread.root_task.created_at)
                  : formatTimestamp(thread.last_activity)
                }
              </div>
            </div>
          </div>
        ))}
      </div>
      {filteredThreads.length === 0 && (
        <div className="thread-list-filtered-empty">
          <p>No {showCompleted ? '' : 'active '}threads to show</p>
          {!showCompleted && (
            <p className="empty-hint">Check "Show completed" to see all threads</p>
          )}
        </div>
      )}
    </div>
  );
};

export default ThreadList;