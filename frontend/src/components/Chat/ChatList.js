import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ChatService } from '../../services/chat';

const ChatList = () => {
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newChatName, setNewChatName] = useState('');

  useEffect(() => {
    // Fetch chats when component mounts
    fetchChats();
  }, []);

  const fetchChats = async () => {
    try {
      setLoading(true);
      const chatsData = await ChatService.getChats();
      setChats(chatsData);
      setError(null);
    } catch (err) {
      setError('Failed to load chats. Please try again.');
      console.error('Error fetching chats:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateChat = async (e) => {
    e.preventDefault();
    if (!newChatName.trim()) return;
    
    try {
      const newChat = await ChatService.createChat(newChatName);
      setChats([...chats, newChat]);
      setNewChatName('');
    } catch (err) {
      setError('Failed to create chat. Please try again.');
      console.error('Error creating chat:', err);
    }
  };

  if (loading) return <div className="loading">Loading chats...</div>;
  
  return (
    <div className="chat-list-container">
      <h2>Your Chats</h2>
      
      {error && <div className="error-message">{error}</div>}
      
      <form onSubmit={handleCreateChat} className="create-chat-form">
        <input
          type="text"
          value={newChatName}
          onChange={(e) => setNewChatName(e.target.value)}
          placeholder="Enter new chat name"
          className="chat-input"
        />
        <button type="submit" className="btn create-chat-btn">Create Chat</button>
      </form>
      
      <div className="chat-list">
        {chats.length === 0 ? (
          <p className="no-chats">No chats yet. Create your first chat above!</p>
        ) : (
          chats.map(chat => (
            <Link to={`/chat/${chat.id}`} key={chat.id} className="chat-link">
              <div className="chat-card">
                <h3>{chat.name}</h3>
                {chat.created_at && (
                  <p>Created: {new Date(chat.created_at).toLocaleString()}</p>
                )}
                <p>Type: {chat.chat_type}</p>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
};

export default ChatList; 