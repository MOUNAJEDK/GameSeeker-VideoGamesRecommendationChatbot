import React, { useState } from 'react';
import { Box, TextField, IconButton, Paper } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import '@fontsource/montserrat'; // Import Montserrat font

const ChatBox = ({ onSendMessage, isDisabled }) => {
  const [message, setMessage] = useState('');

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      onSendMessage(message);
      setMessage('');
    }
  };

  return (
    <Paper sx={{ padding: 2, backgroundColor: '#1A1A1A', borderTop: '1px solid #2E2E2E' }}>
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <TextField
          variant="outlined"
          fullWidth
          multiline
          minRows={1}
          maxRows={5}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type a message..."
          disabled={isDisabled}
          sx={{
            backgroundColor: '#2E2E2E',
            color: '#E0E0E0',
            borderRadius: '8px',
            '& .MuiOutlinedInput-root': {
              '&.Mui-focused fieldset': {
                borderColor: '#BB86FC',
              },
            },
            '& .MuiInputBase-root': {
              color: '#E0E0E0',
              fontFamily: 'Montserrat, sans-serif',
            },
            '& .MuiInputBase-inputMultiline': {
              overflowY: 'auto',
            },
          }}
        />
        <IconButton
          color="primary"
          onClick={() => onSendMessage(message)}
          disabled={isDisabled}
          sx={{ marginLeft: 1 }}
        >
          <SendIcon sx={{ color: isDisabled ? '#666666' : '#BB86FC' }} />
        </IconButton>
      </Box>
    </Paper>
  );
};

export default ChatBox;
