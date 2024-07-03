import React, { useState } from 'react';
import { TextField, Button, Typography, Container, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import './ForgotPasswordPage.scss';

const ForgotPasswordPage = () => {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    try {
      const response = await fetch('http://localhost:8000/request-password-reset', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });
      const data = await response.json();
      if (response.ok) {
        setMessage(data.message);
        setIsSubmitted(true);
        // In a real application, you wouldn't expose the token to the user.
        // This is just for demonstration purposes.
        if (data.reset_token) {
          setTimeout(() => {
            navigate(`/reset-password?token=${data.reset_token}`);
          }, 3000);
        }
      } else {
        setMessage(data.detail || 'An error occurred. Please try again.');
      }
    } catch (error) {
      console.error('Password reset request error:', error);
      setMessage('An error occurred. Please try again.');
    }
  };

  return (
    <Container component="main" maxWidth="xs" className="forgot-password-page">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Typography component="h1" variant="h5">
          Forgot Password - <span className="gameseeker-ai-text">GameSeeker AI</span>
        </Typography>
        {message && <Typography color="info" className="message">{message}</Typography>}
        {!isSubmitted ? (
          <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="email"
              label="Email Address"
              name="email"
              autoComplete="email"
              autoFocus
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
            >
              Reset Password
            </Button>
          </Box>
        ) : (
          <Button
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
            onClick={() => navigate('/login')}
          >
            Back to Login
          </Button>
        )}
      </Box>
    </Container>
  );
};

export default ForgotPasswordPage;