import React, { useEffect, useRef } from 'react';
import { Box } from '@mui/material';
import ChatMessage from './ChatMessage';

const MessageDisplay = ({ messages }) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <Box
      sx={{
        flexGrow: 1,
        overflowY: 'auto',
        padding: 3,
        backgroundColor: '#0D0D0D',
        color: '#E0E0E0',
        borderRadius: '8px',
        margin: '10px',
        boxShadow: '0 0 10px rgba(0,0,0,0.5)',
        '&::-webkit-scrollbar': {
          width: '8px',
        },
        '&::-webkit-scrollbar-track': {
          background: '#2E2E2E',
        },
        '&::-webkit-scrollbar-thumb': {
          background: '#BB86FC',
          borderRadius: '8px',
        },
        '&::-webkit-scrollbar-thumb:hover': {
          background: '#9C6ADE',
        },
      }}
    >
      {messages.map((msg, index) => (
        <ChatMessage key={index} message={msg.message} sender={msg.sender} />
      ))}
      <div ref={messagesEndRef} />
    </Box>
  );
};

export default MessageDisplay;
