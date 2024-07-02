import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { IconButton, Button } from '@mui/material';
import { Add, ExitToApp } from '@mui/icons-material';
import './ChatWindow.scss';

const ChatWindow = ({ token, setToken, userMessages, updateUserMessages }) => {
  const [loading, setLoading] = useState(false);
  const [isResponding, setIsResponding] = useState(false);
  const [username, setUsername] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUsername = async () => {
      try {
        const response = await fetch('http://localhost:8000/users/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (response.ok) {
          const data = await response.json();
          setUsername(data.username);
          if (!userMessages[data.username]) {
            updateUserMessages(data.username, [
              { id: 1, text: 'Welcome to GameSeeker AI!', sender: 'bot' },
              { id: 2, text: 'How can I assist you with video game recommendations today?', sender: 'bot' },
            ]);
          }
        } else {
          throw new Error('Failed to fetch username');
        }
      } catch (error) {
        console.error('Error fetching username:', error);
        setToken('');
        localStorage.removeItem('token');
        navigate('/login');
      }
    };

    fetchUsername();
  }, [token, setToken, navigate, userMessages, updateUserMessages]);

  const handleSendMessage = async (message) => {
    const newMessage = {
      id: (userMessages[username] || []).length + 1,
      text: message,
      sender: 'user',
    };
    const updatedMessages = [...(userMessages[username] || []), newMessage];
    updateUserMessages(username, updatedMessages);
    setLoading(true);
    setIsResponding(true);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ input: message }),
      });
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      const botMessage = {
        id: updatedMessages.length + 1,
        text: '',
        sender: 'bot',
      };
      updateUserMessages(username, [...updatedMessages, botMessage]);
      setLoading(false);

      // Simulate typing effect
      let index = 0;
      const interval = setInterval(() => {
        if (index < data.output[0].length) {
          botMessage.text += data.output[0][index];
          updateUserMessages(username, [...updatedMessages, botMessage]);
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

  const handleNewChat = async () => {
    try {
      const response = await fetch('http://localhost:8000/new-chat', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
      });
      if (response.ok) {
        await response.json();  // We don't need to do anything with the response
        updateUserMessages(username, [
          { id: 1, text: 'Welcome to GameSeeker AI!', sender: 'bot' },
          { id: 2, text: 'How can I assist you with video game recommendations today?', sender: 'bot' },
        ]);
      } else {
        console.error('Failed to start a new chat');
      }
    } catch (error) {
      console.error('Error starting a new chat:', error);
    }
  };

  const handleLogout = () => {
    setToken('');
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <div className="chat-window">
      <nav className="navbar">
        <h1 className="navbar-title">
          <span className="gameseeker-ai-text">GameSeeker AI</span>
        </h1>
        <IconButton className="new-chat-button" onClick={handleNewChat}>
          <Add />
        </IconButton>
        <Button className="logout-button" onClick={handleLogout} startIcon={<ExitToApp />}>
          Logout
        </Button>
      </nav>
      <MessageList messages={userMessages[username] || []} loading={loading} />
      <MessageInput onSendMessage={handleSendMessage} disabled={isResponding} />
    </div>
  );
};

export default ChatWindow;