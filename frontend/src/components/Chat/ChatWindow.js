import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import Message from './Message';
import MessageInput from './MessageInput';
import SearchBar from './SearchBar';
import BranchList from '../Branch/BranchList';
import CreateBranch from '../Branch/CreateBranch';
import { ChatService } from '../../services/chat';
import { WebSocketService } from '../../services/websocket';

const ChatWindow = () => {
  const { chatId } = useParams();
  const [chat, setChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateBranch, setShowCreateBranch] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [searchResults, setSearchResults] = useState(null);
  
  const socketRef = useRef(null);
  const messagesEndRef = useRef(null);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  const handleSearch = async (query) => {
    if (!query.trim()) {
      setSearchResults(null);
      return;
    }
    
    try {
      const results = await ChatService.searchMessages(chatId, query);
      setSearchResults(results);
    } catch (err) {
      console.error('Search failed:', err);
      setError('Failed to search messages');
    }
  };
  
  const handleWebSocketMessage = (data) => {
    if (data.type === 'message') {
      setMessages((prevMessages) => [...prevMessages, data.data]);
      scrollToBottom();
    }
  };
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch chat details
        const chatData = await ChatService.getChat(chatId);
        setChat(chatData);
        
        // Fetch chat messages
        const contentData = await ChatService.getChatContent(chatId);
        if (contentData && contentData.qa_pairs) {
          setMessages(contentData.qa_pairs);
        }
        
        // Fetch branches
        const branchesData = await ChatService.getBranches(chatId);
        setBranches(branchesData);
        
        // Setup WebSocket connection
        const token = localStorage.getItem('token');
        if (token) {
          socketRef.current = new WebSocketService(
            chatId,
            token,
            handleWebSocketMessage
          );
          socketRef.current.connect();
        }
        
      } catch (err) {
        console.error('Failed to load chat:', err);
        setError('Failed to load chat data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
    
    // Cleanup WebSocket connection
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, [chatId]);
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  const handleSendMessage = async (content, messageType) => {
    try {
      if (socketRef.current && socketRef.current.isConnected) {
        // Send via WebSocket
        socketRef.current.sendMessage(content, messageType);
      } else {
        // Fallback to REST API
        const message = await ChatService.addMessage(chatId, content, messageType);
        setMessages((prevMessages) => [...prevMessages, message]);
      }
    } catch (err) {
      console.error('Failed to send message:', err);
      setError('Failed to send message');
    }
  };
  
  const handleCreateBranch = async (name, messageId) => {
    try {
      const branch = await ChatService.createBranch(chatId, messageId, name);
      setBranches((prevBranches) => [...prevBranches, branch]);
      setShowCreateBranch(false);
      setSelectedMessage(null);
    } catch (err) {
      console.error('Failed to create branch:', err);
      setError('Failed to create branch');
    }
  };
  
  if (loading) {
    return <div className="loading">Loading chat...</div>;
  }
  
  if (error) {
    return <div className="error">{error}</div>;
  }
  
  return (
    <div className="chat-window">
      <div className="chat-header">
        <h2>{chat?.name || 'Chat'}</h2>
        <SearchBar onSearch={handleSearch} />
      </div>
      
      <div className="chat-branches">
        <BranchList branches={branches} />
      </div>
      
      <div className="chat-messages">
        {searchResults ? (
          <>
            <div className="search-results-header">
              <h3>Search Results</h3>
              <button onClick={() => setSearchResults(null)}>Clear</button>
            </div>
            {searchResults.map((message) => (
              <Message
                key={message.response_id}
                message={message}
                onBranch={() => {
                  setSelectedMessage(message);
                  setShowCreateBranch(true);
                }}
              />
            ))}
          </>
        ) : (
          <>
            {messages.map((message) => (
              <Message
                key={message.response_id}
                message={message}
                onBranch={() => {
                  setSelectedMessage(message);
                  setShowCreateBranch(true);
                }}
              />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
      
      <MessageInput onSendMessage={handleSendMessage} />
      
      {showCreateBranch && selectedMessage && (
        <CreateBranch
          message={selectedMessage}
          onClose={() => setShowCreateBranch(false)}
          onCreate={handleCreateBranch}
        />
      )}
    </div>
  );
};

export default ChatWindow; 