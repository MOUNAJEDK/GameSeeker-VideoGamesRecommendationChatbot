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

  return (
    <div className="message-input">
      <TextField
        variant="outlined"
        placeholder="Type a message..."
        fullWidth
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyPress={(e) => {
          if (e.key === 'Enter') handleSendMessage();
        }}
        InputProps={{
          endAdornment: (
            <IconButton color="primary" onClick={handleSendMessage}>
              <Send />
            </IconButton>
          ),
        }}
      />
    </div>
  );
};

export default MessageInput;
