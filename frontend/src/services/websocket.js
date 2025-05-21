export class WebSocketService {
  constructor(chatId, token, onMessageCallback) {
    this.chatId = chatId;
    this.token = token;
    this.onMessageCallback = onMessageCallback;
    this.socket = null;
    this.isConnected = false;
  }
  
  connect() {
    if (this.isConnected) {
      return;
    }
    
    // Create WebSocket connection
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host.replace('3000', '8000')}/ws/${this.chatId}/${this.token}`;
    
    this.socket = new WebSocket(wsUrl);
    
    this.socket.onopen = () => {
      console.log('WebSocket connection established');
      this.isConnected = true;
    };
    
    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (this.onMessageCallback) {
        this.onMessageCallback(data);
      }
    };
    
    this.socket.onclose = () => {
      console.log('WebSocket connection closed');
      this.isConnected = false;
      
      // Attempt to reconnect after a delay
      setTimeout(() => {
        this.connect();
      }, 5000);
    };
    
    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.socket.close();
    };
  }
  
  sendMessage(content, messageType = 'text') {
    if (!this.isConnected) {
      throw new Error('WebSocket is not connected');
    }
    
    const message = {
      content,
      message_type: messageType,
      timestamp: new Date().toISOString()
    };
    
    this.socket.send(JSON.stringify(message));
  }
  
  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.isConnected = false;
    }
  }
} 