import React from 'react';
import { Box, Typography } from '@mui/material';
import '@fontsource/montserrat'; // Import Montserrat font

const ChatMessage = ({ message, sender }) => {
  const isBot = sender === 'bot';

  return (
    <Box sx={{ display: 'flex', justifyContent: isBot ? 'flex-start' : 'flex-end', marginBottom: 2 }}>
      <Box
        sx={{
          maxWidth: '60%',
          padding: 2,
          backgroundColor: isBot ? '#333333' : '#BB86FC',
          borderRadius: '12px',
          boxShadow: '0px 0px 10px rgba(0,0,0,0.5)',
          whiteSpace: 'pre-line', // This ensures that new lines in the message are preserved
        }}
      >
        <Typography variant="body1" sx={{ color: isBot ? '#E0E0E0' : '#121212', fontFamily: 'Montserrat, sans-serif' }}>
          {message}
        </Typography>
      </Box>
    </Box>
  );
};

export default ChatMessage;
