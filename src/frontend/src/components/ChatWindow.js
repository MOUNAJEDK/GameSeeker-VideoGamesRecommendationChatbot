import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { IconButton, Tooltip } from '@mui/material';
import { LogoutOutlined, DeleteSweep } from '@mui/icons-material';
import './ChatWindow.scss';

const ChatWindow = ({ token, setToken, userMessages, updateUserMessages }) => {
  const [loading, setLoading] = useState(false);
  const [isResponding, setIsResponding] = useState(false);
  const [username, setUsername] = useState('');
  const [threadId, setThreadId] = useState('');
  const navigate = useNavigate();
  const initialChatExecuted = useRef(false);

  const saveMessagesToLocalStorage = useCallback((messages) => {
    if (username) {
      const allMessages = JSON.parse(localStorage.getItem('all_chat_messages') || '{}');
      allMessages[username] = messages;
      localStorage.setItem('all_chat_messages', JSON.stringify(allMessages));
    }
  }, [username]);

  const loadMessagesFromLocalStorage = useCallback(() => {
    if (username) {
      const allMessages = JSON.parse(localStorage.getItem('all_chat_messages') || '{}');
      return allMessages[username] || null;
    }
    return null;
  }, [username]);

  const handleInitialChat = useCallback(async () => {
    if (initialChatExecuted.current || !username) return;

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
        const initialMessages = [
          { id: 1, text: 'Welcome to GameSeeker AI!', sender: 'bot' },
          { id: 2, text: data.output[0], sender: 'bot' },
        ];
        updateUserMessages(username, initialMessages);
        saveMessagesToLocalStorage(initialMessages);
        initialChatExecuted.current = true;
      } else {
        console.error('Failed to start a new chat');
      }
    } catch (error) {
      console.error('Error starting a new chat:', error);
    }
  }, [token, username, updateUserMessages, saveMessagesToLocalStorage]);

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
  }, [token, setToken, navigate]);

  useEffect(() => {
    if (username && !initialChatExecuted.current) {
      const savedMessages = loadMessagesFromLocalStorage();
      if (savedMessages) {
        updateUserMessages(username, savedMessages);
        initialChatExecuted.current = true;
      } else if (!userMessages[username]) {
        handleInitialChat();
      }
    }
  }, [username, userMessages, loadMessagesFromLocalStorage, updateUserMessages, handleInitialChat]);

  const handleSendMessage = async (message) => {
    if (!username) return;

    const newMessage = {
      id: (userMessages[username] || []).length + 1,
      text: message,
      sender: 'user',
    };
    const updatedMessages = [...(userMessages[username] || []), newMessage];
    updateUserMessages(username, updatedMessages);
    saveMessagesToLocalStorage(updatedMessages);
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
        text: data.output[0],
        sender: 'bot',
      };
      const newUpdatedMessages = [...updatedMessages, botMessage];
      updateUserMessages(username, newUpdatedMessages);
      saveMessagesToLocalStorage(newUpdatedMessages);
    } catch (error) {
      console.error('Error fetching response from the backend:', error);
    } finally {
      setLoading(false);
      setIsResponding(false);
    }
  };

  const handleLogout = () => {
    setToken('');
    localStorage.removeItem('token');
    navigate('/login');
  };

  const handleClearChat = () => {
    updateUserMessages(username, []);
    saveMessagesToLocalStorage([]);
    initialChatExecuted.current = false;
    handleInitialChat();
  };

  return (
    <div className="chat-window">
      <nav className="navbar">
        <h1 className="navbar-title">
          <span className="gameseeker-ai-text">GameSeeker AI</span>
        </h1>
        <div className="navbar-actions">
          <Tooltip title="Clear Chat">
            <IconButton onClick={handleClearChat} className="clear-chat-button">
              <DeleteSweep style={{ color: '#ff4d4d' }} />
            </IconButton>
          </Tooltip>
          <Tooltip title="Logout">
            <IconButton onClick={handleLogout} className="logout-button">
              <LogoutOutlined style={{ color: '#ff4d4d' }} />
            </IconButton>
          </Tooltip>
        </div>
      </nav>
      <MessageList messages={userMessages[username] || []} loading={loading} />
      <MessageInput onSendMessage={handleSendMessage} disabled={isResponding} />
    </div>
  );
};

export default ChatWindow;