import React, { useState } from 'react';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import './ChatWindow.scss';

const ChatWindow = () => {
  const [messages, setMessages] = useState([
    { id: 1, text: 'Welcome to the chatbot!', sender: 'bot' },
    { id: 2, text: 'Hello! How can I assist you today?', sender: 'bot' },
  ]);

  const handleSendMessage = async (message) => {
    const newMessage = {
      id: messages.length + 1,
      text: message,
      sender: 'user',
    };
    setMessages([...messages, newMessage]);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ input: message }),
      });
      const data = await response.json();
      const botMessage = {
        id: messages.length + 2,
        text: data.output[0],
        sender: 'bot',
      };
      setMessages((prevMessages) => [...prevMessages, botMessage]);
    } catch (error) {
      console.error('Error fetching response from the backend:', error);
    }
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