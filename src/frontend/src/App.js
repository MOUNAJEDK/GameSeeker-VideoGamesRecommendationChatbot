import React, { useState } from 'react';
import { Box, CssBaseline } from '@mui/material';
import NavBar from './components/NavBar';
import MessageDisplay from './components/MessageDisplay';
import ChatBox from './components/ChatBox';
import axios from 'axios';

function App() {
  const [messages, setMessages] = useState([
    { message: "Hello! How can I assist you today?", sender: "bot" },
  ]);
  const [isSending, setIsSending] = useState(false);

  const handleSendMessage = async (message) => {
    if (message.trim() !== "") {
      setMessages((prevMessages) => [...prevMessages, { message, sender: "user" }]);
      setIsSending(true);

      try {
        const response = await axios.post('http://localhost:8000/chat', { input: message });
        const responseId = response.data.response_id;
        const eventSource = new EventSource(`http://localhost:8000/stream_response/${responseId}`);

        eventSource.onmessage = (event) => {
          if (event.data === "[DONE]") {
            console.log("Received done signal");
            eventSource.close();
            setIsSending(false);
          } else {
            console.log("Received chunk:", event.data);  // Debug statement
            setMessages((prevMessages) => {
              const lastMessage = prevMessages[prevMessages.length - 1];
              if (lastMessage.sender === 'bot') {
                return [...prevMessages.slice(0, -1), { ...lastMessage, message: lastMessage.message + event.data }];
              } else {
                return [...prevMessages, { message: event.data, sender: "bot" }];
              }
            });
          }
        };

        eventSource.onerror = (error) => {
          console.error("Error receiving messages:", error);
          eventSource.close();
          setIsSending(false);
        };

      } catch (error) {
        console.error("Error sending message:", error);
        setIsSending(false);
      }
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#0D0D0D' }}>
      <CssBaseline />
      <NavBar />
      <MessageDisplay messages={messages} />
      <ChatBox onSendMessage={handleSendMessage} isDisabled={isSending} />
    </Box>
  );
}

export default App;
