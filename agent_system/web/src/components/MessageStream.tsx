import React, { useEffect, useRef } from 'react';
import { MessageStreamProps, Message, MessageContent } from '../types';

const MessageStream: React.FC<MessageStreamProps> = ({ messages, threadId }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const autoScrollEnabled = useRef<boolean>(true);

  const scrollToBottom = (): void => {
    if (autoScrollEnabled.current && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(scrollToBottom, [messages]);

  const handleScroll = (): void => {
    const container = containerRef.current;
    if (container) {
      const isAtBottom = Math.abs(
        container.scrollHeight - container.scrollTop - container.clientHeight
      ) < 5; // Small threshold for floating point precision
      autoScrollEnabled.current = isAtBottom;
    }
  };

  const getMessageClass = (message: Message): string => {
    const baseClass = 'message';
    switch (message.type) {
      case 'agent_thinking':
        return `${baseClass} message-thinking`;
      case 'agent_tool_call':
        return `${baseClass} message-tool-call`;
      case 'agent_tool_result':
        return `${baseClass} message-tool-result`;
      case 'agent_error':
        return `${baseClass} message-error`;
      case 'system_message':
        return `${baseClass} message-system`;
      case 'user_message':
        return `${baseClass} message-user`;
      case 'step_mode_pause':
        return `${baseClass} message-pause`;
      case 'agent_started':
        return `${baseClass} message-started`;
      case 'agent_completed':
        return `${baseClass} message-completed`;
      default:
        return baseClass;
    }
  };

  const formatToolCall = (content: MessageContent): React.JSX.Element => {
    return (
      <div className="tool-call">
        <div className="tool-name">🔧 {content.tool_name}</div>
        {content.tool_input && (
          <pre className="tool-input">
            {JSON.stringify(content.tool_input, null, 2)}
          </pre>
        )}
      </div>
    );
  };

  const formatToolResult = (content: MessageContent): React.JSX.Element => {
    return (
      <div className="tool-result">
        <div className={`tool-status ${content.success ? 'success' : 'error'}`}>
          {content.success ? '✓' : '✗'} Result
        </div>
        {content.tool_output && (
          <pre className="tool-output">
            {typeof content.tool_output === 'string' 
              ? content.tool_output 
              : JSON.stringify(content.tool_output, null, 2)
            }
          </pre>
        )}
      </div>
    );
  };

  const renderMessageContent = (message: Message): React.JSX.Element => {
    const { content } = message;
    
    switch (message.type) {
      case 'agent_tool_call':
        return formatToolCall(content);
        
      case 'agent_tool_result':
        return formatToolResult(content);
        
      case 'agent_thinking':
        return (
          <div className="thinking">
            💭 {content.thought || content.message}
          </div>
        );
        
      case 'step_mode_pause':
        return (
          <div className="pause-message">
            ⏸️ {content.reason || content.message}
            <div className="pause-info">Waiting for continue command...</div>
          </div>
        );
        
      case 'agent_error':
        return (
          <div className="error-message">
            ❌ Error: {content.error || content.message}
          </div>
        );
        
      case 'agent_started':
        return (
          <div className="agent-started">
            🚀 Agent started: {content.instruction || content.message}
            {content.status && (
              <div className="agent-status">Status: {content.status}</div>
            )}
          </div>
        );
        
      case 'agent_completed':
        return (
          <div className="agent-completed">
            ✅ Agent completed: {content.message || content.instruction}
            {content.status && (
              <div className="agent-status">Final Status: {content.status}</div>
            )}
          </div>
        );
        
      default:
        const displayText = content.message || 
                          content.thought || 
                          content.instruction || 
                          (typeof content === 'string' ? content : JSON.stringify(content));
        
        return <div className="message-text">{displayText}</div>;
    }
  };

  const filteredMessages = messages.filter(m => m.tree_id === threadId);

  if (filteredMessages.length === 0) {
    return (
      <div className="message-stream empty">
        <div className="empty-state">
          <p>No messages yet for this thread</p>
          <p className="empty-hint">Messages will appear here as agents work on tasks</p>
        </div>
      </div>
    );
  }

  return (
    <div className="message-stream" ref={containerRef} onScroll={handleScroll}>
      {filteredMessages.map((message, index) => (
        <div key={`${message.task_id}-${message.timestamp}-${index}`} className={getMessageClass(message)}>
          <div className="message-header">
            <span className="message-agent">
              {message.agent_name || 'System'}
            </span>
            <span className="message-time">
              {new Date(message.timestamp).toLocaleTimeString()}
            </span>
            <span className="message-type">
              {message.type.replace('agent_', '').replace('_', ' ')}
            </span>
          </div>
          <div className="message-content">
            {renderMessageContent(message)}
          </div>
        </div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageStream;