import React, { useState } from 'react';
import { TextField, IconButton } from '@mui/material';
import { Send } from '@mui/icons-material';
import './MessageInput.scss';

const MessageInput = ({ onSendMessage, disabled }) => {
  const [message, setMessage] = useState('');

  const handleSendMessage = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !disabled) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className={`message-input-container ${disabled ? 'disabled' : ''}`}>
      <div className="message-input">
        <TextField
          multiline
          minRows={1}
          maxRows={5}
          variant="outlined"
          placeholder={disabled ? "AI is thinking..." : "Type a message"}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          className="message-textarea"
          disabled={disabled}
          InputProps={{
            style: {
              borderRadius: '50px',
              padding: '0.75rem 1.5rem',
              backgroundColor: disabled ? 'rgba(60, 60, 60, 0.8)' : 'rgba(30, 30, 30, 0.8)',
              color: disabled ? '#888' : '#fff',
            },
          }}
          sx={{
            '& .MuiOutlinedInput-root': {
              '& fieldset': {
                borderColor: disabled ? '#555' : '#333',
              },
              '&:hover fieldset': {
                borderColor: disabled ? '#666' : '#555',
              },
              '&.Mui-focused fieldset': {
                borderColor: disabled ? '#777' : '#ff4d4d',
              },
            },
            width: '100%',
          }}
        />
        <IconButton color="primary" onClick={handleSendMessage} disabled={disabled}>
          <Send />
        </IconButton>
      </div>
    </div>
  );
};

export default MessageInput;