import React, { useState, useEffect } from 'react';
// @ts-ignore - react-tree-graph types are not fully compatible
import Tree from 'react-tree-graph';

interface TaskNode {
  task_id: number;
  instruction: string;
  status: string;
  agent_name?: string;
  parent_task_id?: number;
  created_at: string;
  completed_at?: string;
  children?: TaskNode[];
}

interface TaskTreeData {
  name: string;
  children?: TaskTreeData[];
  attributes?: {
    status: string;
    agent?: string;
    task_id: number;
  };
}

interface TaskTreeVisualizationProps {
  threadId: string;
  apiBaseUrl: string;
}

const TaskTreeVisualization: React.FC<TaskTreeVisualizationProps> = ({ 
  threadId, 
  apiBaseUrl 
}) => {
  const [treeData, setTreeData] = useState<TaskTreeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (threadId) {
      fetchTaskTree();
    }
  }, [threadId]);

  const fetchTaskTree = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${apiBaseUrl}/tasks/tree/${threadId}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch task tree: ${response.statusText}`);
      }
      
      const data = await response.json();
      const formattedTree = formatTasksForTree(data.tasks || []);
      setTreeData(formattedTree);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load task tree');
      console.error('Error fetching task tree:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatTasksForTree = (tasks: TaskNode[]): TaskTreeData | null => {
    if (!tasks.length) return null;

    // Build a map for quick lookup
    const taskMap = new Map<number, TaskNode>();
    tasks.forEach(task => taskMap.set(task.task_id, task));

    // Find the root task (task with no parent)
    const rootTask = tasks.find(task => !task.parent_task_id);
    if (!rootTask) return null;

    // Recursively build the tree structure
    const buildTree = (task: TaskNode): TaskTreeData => {
      const children = tasks
        .filter(t => t.parent_task_id === task.task_id)
        .map(buildTree);

      return {
        name: truncateText(task.instruction, 50),
        children: children.length > 0 ? children : undefined,
        attributes: {
          status: task.status,
          agent: task.agent_name || 'System',
          task_id: task.task_id
        }
      };
    };

    return buildTree(rootTask);
  };

  const truncateText = (text: string, maxLength: number): string => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const getNodeClassName = (node: any): string => {
    const status = node.attributes?.status?.toLowerCase() || 'unknown';
    return `tree-node tree-node-${status}`;
  };

  const getStatusIcon = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'completed': return '✅';
      case 'failed': return '❌';
      case 'running': return '🔄';
      case 'pending': return '⏳';
      case 'paused': return '⏸️';
      default: return '📋';
    }
  };

  if (loading) {
    return (
      <div className="task-tree-container">
        <div className="tree-loading">
          <div className="loading-spinner"></div>
          <p>Loading task tree...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="task-tree-container">
        <div className="tree-error">
          <p>❌ Error loading task tree: {error}</p>
          <button onClick={fetchTaskTree} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!treeData) {
    return (
      <div className="task-tree-container">
        <div className="tree-empty">
          <p>No task data available for this thread</p>
        </div>
      </div>
    );
  }

  return (
    <div className="task-tree-container">
      <div className="tree-header">
        <h3>📊 Task Tree Visualization</h3>
        <button onClick={fetchTaskTree} className="refresh-button">
          🔄 Refresh
        </button>
      </div>
      
      <div className="tree-legend">
        <span className="legend-item">
          ✅ Completed &nbsp;
        </span>
        <span className="legend-item">
          🔄 Running &nbsp;
        </span>
        <span className="legend-item">
          ⏳ Pending &nbsp;
        </span>
        <span className="legend-item">
          ❌ Failed
        </span>
      </div>

      <div className="tree-visualization">
        {/* @ts-ignore */}
        <Tree
          data={treeData}
          height={400}
          width={800}
          svgProps={{
            className: 'task-tree-svg'
          }}
          nodeProps={{
            className: getNodeClassName,
            r: 8
          }}
          textProps={{
            x: 12,
            y: 4,
            className: 'tree-node-text'
          }}
          pathProps={{
            className: 'tree-path'
          }}
          gProps={{
            className: 'tree-node-group'
          }}
          renderCustomNodeElement={(rd3tProps: any, appState: any) => {
            const { nodeDatum } = rd3tProps;
            const status = nodeDatum.attributes?.status || 'unknown';
            const agent = nodeDatum.attributes?.agent || 'System';
            const taskId = nodeDatum.attributes?.task_id;
            
            return (
              <g className={getNodeClassName(nodeDatum)}>
                <circle r="8" fill={getStatusColor(status)} />
                <text x="12" y="4" className="node-instruction">
                  {getStatusIcon(status)} {nodeDatum.name}
                </text>
                <text x="12" y="18" className="node-agent" fontSize="10">
                  {agent} (#{taskId})
                </text>
              </g>
            );
          }}
        />
      </div>
    </div>
  );
};

const getStatusColor = (status: string): string => {
  switch (status.toLowerCase()) {
    case 'completed': return '#4CAF50';
    case 'failed': return '#F44336';
    case 'running': return '#2196F3';
    case 'pending': return '#FF9800';
    case 'paused': return '#9C27B0';
    default: return '#757575';
  }
};

export default TaskTreeVisualization;