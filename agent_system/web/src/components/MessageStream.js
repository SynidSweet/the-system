import React, { useEffect, useRef } from 'react';

const MessageStream = ({ messages, threadId }) => {
  const messagesEndRef = useRef(null);
  const containerRef = useRef(null);
  const autoScrollEnabled = useRef(true);

  const scrollToBottom = () => {
    if (autoScrollEnabled.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(scrollToBottom, [messages]);

  const handleScroll = () => {
    const container = containerRef.current;
    if (container) {
      const isAtBottom = container.scrollHeight - container.scrollTop === container.clientHeight;
      autoScrollEnabled.current = isAtBottom;
    }
  };

  const getMessageClass = (message) => {
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
      default:
        return baseClass;
    }
  };

  const formatToolCall = (content) => {
    return (
      <div className="tool-call">
        <div className="tool-name">🔧 {content.tool_name}</div>
        <pre className="tool-input">{JSON.stringify(content.tool_input, null, 2)}</pre>
      </div>
    );
  };

  const formatToolResult = (content) => {
    return (
      <div className="tool-result">
        <div className={`tool-status ${content.success ? 'success' : 'error'}`}>
          {content.success ? '✓' : '✗'} Result
        </div>
        <pre className="tool-output">{
          typeof content.tool_output === 'string' 
            ? content.tool_output 
            : JSON.stringify(content.tool_output, null, 2)
        }</pre>
      </div>
    );
  };

  const renderMessageContent = (message) => {
    switch (message.type) {
      case 'agent_tool_call':
        return formatToolCall(message.content);
      case 'agent_tool_result':
        return formatToolResult(message.content);
      case 'agent_thinking':
        return <div className="thinking">💭 {message.content.thought}</div>;
      case 'step_mode_pause':
        return (
          <div className="pause-message">
            ⏸️ {message.content.reason}
            <div className="pause-info">Waiting for continue command...</div>
          </div>
        );
      case 'agent_error':
        return (
          <div className="error-message">
            ❌ Error: {message.content.error}
          </div>
        );
      case 'agent_started':
        return (
          <div className="agent-started">
            🚀 Agent started: {message.content.instruction}
            <div className="agent-status">Status: {message.content.status}</div>
          </div>
        );
      default:
        return <div>{message.content.message || message.content.thought || message.content.instruction || JSON.stringify(message.content)}</div>;
    }
  };

  return (
    <div className="message-stream" ref={containerRef} onScroll={handleScroll}>
      {messages.filter(m => m.tree_id === threadId).map((message, index) => (
        <div key={`${message.task_id}-${index}`} className={getMessageClass(message)}>
          <div className="message-header">
            <span className="message-agent">{message.agent_name || 'System'}</span>
            <span className="message-time">{new Date(message.timestamp).toLocaleTimeString()}</span>
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