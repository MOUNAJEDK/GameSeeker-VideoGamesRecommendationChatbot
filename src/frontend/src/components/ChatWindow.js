import React, { useState } from 'react';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import './ChatWindow.scss';

const ChatWindow = () => {
  const [messages, setMessages] = useState([
    { id: 1, text: 'Welcome to the chatbot!', sender: 'bot' },
    { id: 2, text: 'Hello! How can I assist you today?', sender: 'bot' },
  ]);

  const handleSendMessage = (message) => {
    const newMessage = {
      id: messages.length + 1,
      text: message,
      sender: 'user',
    };
    setMessages([...messages, newMessage]);
  };

  return (
    <div className="chat-window">
      <nav className="navbar">
        <h1>GameSeeker AI</h1>
      </nav>
      <MessageList messages={messages} />
      <MessageInput onSendMessage={handleSendMessage} />
    </div>
  );
};

export default ChatWindow;
