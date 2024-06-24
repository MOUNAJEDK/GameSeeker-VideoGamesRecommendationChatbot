import React, { useState, useEffect } from 'react';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { IconButton } from '@mui/material';
import { Add } from '@mui/icons-material';
import './ChatWindow.scss';

const ChatWindow = () => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isResponding, setIsResponding] = useState(false);

  useEffect(() => {
    const savedMessages = localStorage.getItem('chatMessages');
    if (savedMessages) {
      setMessages(JSON.parse(savedMessages));
    } else {
      setMessages([
        { id: 1, text: 'Welcome to the chatbot!', sender: 'bot' },
        { id: 2, text: 'Hello! How can I assist you today?', sender: 'bot' },
      ]);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('chatMessages', JSON.stringify(messages));
  }, [messages]);

  const handleSendMessage = async (message) => {
    const newMessage = {
      id: messages.length + 1,
      text: message,
      sender: 'user',
    };
    setMessages([...messages, newMessage]);
    setLoading(true);
    setIsResponding(true);

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
          setIsResponding(false);
        }
      }, 5);  // Faster typing effect
    } catch (error) {
      console.error('Error fetching response from the backend:', error);
      setLoading(false);
      setIsResponding(false);
    }
  };

  const handleNewChat = () => {
    setMessages([
      { id: 1, text: 'Welcome to the chatbot!', sender: 'bot' },
      { id: 2, text: 'Hello! How can I assist you today?', sender: 'bot' },
    ]);
    localStorage.removeItem('chatMessages');
  };

  return (
    <div className="chat-window">
      <nav className="navbar">
        <h1 className="navbar-title">GameSeeker AI</h1>
        <IconButton className="new-chat-button" onClick={handleNewChat}>
          <Add />
        </IconButton>
      </nav>
      <MessageList messages={messages} loading={loading} />
      <MessageInput onSendMessage={handleSendMessage} disabled={isResponding} />
    </div>
  );
};

export default ChatWindow;