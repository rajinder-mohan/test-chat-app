import React from 'react';
import { formatDateTime } from '../../utils/formatters';

// Component to handle different message types
const MessageContent = ({ content, type }) => {
  switch (type) {
    case 'code':
      return (
        <pre className="message-code">
          <code>{content}</code>
        </pre>
      );
    case 'link':
      return (
        <a 
          href={content.startsWith('http') ? content : `https://${content}`}
          target="_blank"
          rel="noopener noreferrer"
          className="message-link"
        >
          {content}
        </a>
      );
    default:
      return <p>{content}</p>;
  }
};

const Message = ({ message, onBranch }) => {
  const hasQuestion = message.question && message.question.trim() !== '';
  const hasResponse = message.response && message.response.trim() !== '';
  
  return (
    <div className="message-container">
      {hasQuestion && (
        <div className="message user-message">
          <div className="message-header">
            <span className="message-sender">You</span>
            <span className="message-timestamp">{formatDateTime(message.timestamp)}</span>
          </div>
          <div className="message-content">
            <MessageContent content={message.question} type={message.message_type || 'text'} />
          </div>
        </div>
      )}
      
      {hasResponse && (
        <div className="message ai-message">
          <div className="message-header">
            <span className="message-sender">AI</span>
            <span className="message-timestamp">{formatDateTime(message.timestamp)}</span>
            <button className="branch-button" onClick={() => onBranch(message.response_id)}>
              Branch from here
            </button>
          </div>
          <div className="message-content">
            <MessageContent content={message.response} type={message.message_type || 'text'} />
          </div>
          {message.branches && message.branches.length > 0 && (
            <div className="message-branches">
              <span className="branches-label">Branches: {message.branches.length}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Message; 