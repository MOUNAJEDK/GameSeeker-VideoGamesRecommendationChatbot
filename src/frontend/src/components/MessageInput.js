import React, { useState } from 'react';
import { TextField, IconButton } from '@mui/material';
import { Send } from '@mui/icons-material';
import './MessageInput.scss';

const MessageInput = ({ onSendMessage }) => {
  const [message, setMessage] = useState('');

  const handleSendMessage = () => {
    if (message.trim()) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="message-input-container">
      <div className="message-input">
        <TextField
          multiline
          minRows={1}
          maxRows={5}
          variant="outlined"
          placeholder="Type a message"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          className="message-textarea"
          InputProps={{
            style: {
              borderRadius: '50px',
              padding: '0.75rem 1.5rem',
              backgroundColor: 'rgba(30, 30, 30, 0.8)',
              color: '#fff',
            },
          }}
          sx={{
            '& .MuiOutlinedInput-root': {
              '& fieldset': {
                borderColor: '#333',
              },
              '&:hover fieldset': {
                borderColor: '#555',
              },
              '&.Mui-focused fieldset': {
                borderColor: '#ff4d4d',
              },
            },
            width: '100%',
          }}
        />
        <IconButton color="primary" onClick={handleSendMessage}>
          <Send />
        </IconButton>
      </div>
    </div>
  );
};

export default MessageInput;
