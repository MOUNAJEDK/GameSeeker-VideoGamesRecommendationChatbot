import React, { useState } from 'react';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import './ChatWindow.scss';

const ChatWindow = () => {
  const [messages, setMessages] = useState([
    { id: 1, text: 'Welcome to the chatbot!', sender: 'bot' },
    { id: 2, text: 'Hello! How can I assist you today?', sender: 'bot' },
  ]);
  const [loading, setLoading] = useState(false);

  const handleSendMessage = async (message) => {
    const newMessage = {
      id: messages.length + 1,
      text: message,
      sender: 'user',
    };
    setMessages([...messages, newMessage]);
    setLoading(true);

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
        text: '',
        sender: 'bot',
      };
      setMessages((prevMessages) => [...prevMessages, botMessage]);
      setLoading(false);

      // Simulate typing effect
      let index = 0;
      const interval = setInterval(() => {
        if (index < data.output[0].length) {
          botMessage.text += data.output[0][index];
          setMessages((prevMessages) => [
            ...prevMessages.slice(0, -1),
            botMessage,
          ]);
          index++;
        } else {
          clearInterval(interval);
        }
      }, 5);  // Faster typing effect
    } catch (error) {
      console.error('Error fetching response from the backend:', error);
      setLoading(false);
    }
  };

  return (
    <div className="chat-window">
      <nav className="navbar">
        <h1 className="navbar-title">GameSeeker AI</h1>
      </nav>
      <MessageList messages={messages} loading={loading} />
      <MessageInput onSendMessage={handleSendMessage} />
    </div>
  );
};

export default ChatWindow;
