import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChatService } from '../../services/chat';
import { WebSocketService } from '../../services/websocket';
import { useAuth } from '../../contexts/AuthContext';

const ChatWindow = () => {
  const { chatId } = useParams();
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const [chat, setChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [ws, setWs] = useState(null);
  const [branches, setBranches] = useState([]);
  const [newBranchName, setNewBranchName] = useState('');
  const [activeBranchModal, setActiveBranchModal] = useState(null);
  
  const messagesEndRef = useRef(null);
  
  // Fetch chat data when component mounts or chatId changes
  useEffect(() => {
    fetchChatData();
    
    // Clean up WebSocket connection when component unmounts
    return () => {
      if (ws) {
        ws.disconnect();
      }
    };
  }, [chatId]);
  
  // Set up WebSocket connection
  useEffect(() => {
    if (chatId && currentUser) {
      const token = localStorage.getItem('token');
      
      if (token) {
        const socketService = new WebSocketService(
          chatId,
          token,
          handleWebSocketMessage
        );
        
        try {
          socketService.connect();
          setWs(socketService);
        } catch (err) {
          console.error('WebSocket connection failed:', err);
        }
      }
    }
  }, [chatId, currentUser]);
  
  // Scroll to bottom of messages when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);
  
  const fetchChatData = async () => {
    try {
      setLoading(true);
      
      // Get chat details
      const chatData = await ChatService.getChat(chatId);
      setChat(chatData);
      
      // Get chat messages
      const messagesData = await ChatService.getChatContent(chatId);
      setMessages(messagesData || []);
      
      // Get branches for this chat
      try {
        const branchesData = await ChatService.getBranches(chatId);
        setBranches(branchesData || []);
      } catch (err) {
        console.error('Error fetching branches:', err);
      }
      
      setError(null);
    } catch (err) {
      setError('Failed to load chat data. Please try again.');
      console.error('Error fetching chat data:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleWebSocketMessage = (data) => {
    if (data.type === 'message') {
      setMessages(prevMessages => [...prevMessages, data.data]);
    }
  };
  
  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!newMessage.trim()) return;
    
    try {
      if (ws && ws.isConnected) {
        // Send through WebSocket if connected
        ws.sendMessage(newMessage);
      } else {
        // Fallback to REST API
        await ChatService.addMessage(chatId, newMessage);
        // Refresh messages
        fetchChatData();
      }
      setNewMessage('');
    } catch (err) {
      setError('Failed to send message. Please try again.');
      console.error('Error sending message:', err);
    }
  };
  
  const handleCreateBranch = async (messageId) => {
    if (!newBranchName.trim()) {
      setError('Please enter a branch name');
      return;
    }
    
    try {
      const newBranch = await ChatService.createBranch(
        chatId,
        messageId,
        newBranchName
      );
      
      // Navigate to the new branch
      navigate(`/chat/${newBranch.id}`);
      
      setNewBranchName('');
      setActiveBranchModal(null);
    } catch (err) {
      setError('Failed to create branch. Please try again.');
      console.error('Error creating branch:', err);
    }
  };
  
  if (loading) return <div className="loading">Loading chat...</div>;
  
  if (!chat) return <div className="error">Chat not found</div>;
  
  return (
    <div className="chat-window">
      <div className="chat-header">
        <h2>{chat.name}</h2>
        <div className="chat-actions">
          <button onClick={() => navigate('/chats')} className="btn btn-secondary">
            Back to Chats
          </button>
        </div>
      </div>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="no-messages">No messages yet. Start the conversation!</div>
        ) : (
          messages.map((message, index) => (
            <div key={message.response_id} className="message-container">
              {message.question && (
                <div className="message user-message">
                  <div className="message-header">
                    <span>You</span>
                    <span>{new Date(message.timestamp).toLocaleString()}</span>
                  </div>
                  <div className="message-content">{message.question}</div>
                </div>
              )}
              
              {message.response && (
                <div className="message ai-message">
                  <div className="message-header">
                    <span>AI</span>
                    <span>{new Date(message.timestamp).toLocaleString()}</span>
                    <button 
                      className="branch-button"
                      onClick={() => setActiveBranchModal(message.response_id)}
                    >
                      Create Branch
                    </button>
                  </div>
                  <div className="message-content">{message.response}</div>
                  
                  {/* Branch modal */}
                  {activeBranchModal === message.response_id && (
                    <div className="branch-modal">
                      <input
                        type="text"
                        value={newBranchName}
                        onChange={(e) => setNewBranchName(e.target.value)}
                        placeholder="Enter branch name"
                      />
                      <div className="branch-modal-actions">
                        <button 
                          onClick={() => handleCreateBranch(message.response_id)}
                          className="btn btn-primary"
                        >
                          Create
                        </button>
                        <button 
                          onClick={() => {
                            setActiveBranchModal(null);
                            setNewBranchName('');
                          }}
                          className="btn btn-secondary"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                  
                  {/* Display branches for this message */}
                  {message.branches && message.branches.length > 0 && (
                    <div className="message-branches">
                      <span>Branches:</span>
                      {message.branches.map(branchId => {
                        const branch = branches.find(b => b.id === branchId);
                        return (
                          <button
                            key={branchId}
                            onClick={() => navigate(`/chat/${branchId}`)}
                            className="branch-link"
                          >
                            {branch ? branch.name : `Branch ${branchId}`}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={handleSendMessage} className="chat-input-form">
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Type your message..."
          className="chat-input"
        />
        <button type="submit" className="send-button">Send</button>
      </form>
    </div>
  );
};

export default ChatWindow; 