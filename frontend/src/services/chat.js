import api from './api';

export const ChatService = {
  getChats: async () => {
    const response = await api.get('/chats/list-chats');
    return response.data;
  },
  
  createChat: async (name, chatType = 'direct') => {
    const response = await api.post('/chats/create-chat', {
      name,
      chat_type: chatType,
    });
    return response.data;
  },
  
  getChat: async (chatId) => {
    const response = await api.get(`/chats/get-chat?chat_id=${chatId}`);
    return response.data;
  },
  
  getChatContent: async (chatId) => {
    const response = await api.get(`/chats/get-chat-content?chat_id=${chatId}`);
    return response.data;
  },
  
  addMessage: async (chatId, content, messageType = 'text') => {
    const response = await api.post('/messages/add-message', {
      chat_id: chatId,
      content,
      message_type: messageType,
    });
    return response.data;
  },
  
  searchMessages: async (chatId, query) => {
    const response = await api.get(`/messages/search?chat_id=${chatId}&query=${query}`);
    return response.data;
  },
  
  createBranch: async (parentChatId, parentMessageId, name) => {
    const response = await api.post('/branches/create-branch', {
      parent_chat_id: parentChatId,
      parent_message_id: parentMessageId,
      name,
    });
    return response.data;
  },
  
  getBranches: async (chatId) => {
    const response = await api.get(`/branches/get-branches?chat_id=${chatId}`);
    return response.data;
  },
  
  getBranchTree: async (chatId) => {
    const response = await api.get(`/branches/get-branch-tree?chat_id=${chatId}`);
    return response.data;
  },
  
  setActiveBranch: async (chatId, branchId) => {
    const response = await api.put('/branches/set-active-branch', null, {
      params: { chat_id: chatId, branch_id: branchId },
    });
    return response.data;
  },
}; 