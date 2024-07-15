import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { Button } from '@mui/material';
import { ExitToApp } from '@mui/icons-material';
import './ChatWindow.scss';

const ChatWindow = ({ token, setToken, userMessages, updateUserMessages }) => {
  const [loading, setLoading] = useState(false);
  const [isResponding, setIsResponding] = useState(false);
  const [username, setUsername] = useState('');
  const [threadId, setThreadId] = useState('');
  const navigate = useNavigate();

  const handleInitialChat = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ input: 'Hello', thread_id: '' }),
      });
      if (response.ok) {
        const data = await response.json();
        setThreadId(data.thread_id);
        updateUserMessages(username, [
          { id: 1, text: 'Welcome to GameSeeker AI!', sender: 'bot' },
          { id: 2, text: data.output[0], sender: 'bot' },
        ]);
      } else {
        console.error('Failed to start a new chat');
      }
    } catch (error) {
      console.error('Error starting a new chat:', error);
    }
  }, [token, username, updateUserMessages]);

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
            handleInitialChat();
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
  }, [token, setToken, navigate, userMessages, handleInitialChat]);

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
        body: JSON.stringify({ input: message, thread_id: threadId || '' }),
      });
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      if (data.thread_id) {
        setThreadId(data.thread_id);
      }
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