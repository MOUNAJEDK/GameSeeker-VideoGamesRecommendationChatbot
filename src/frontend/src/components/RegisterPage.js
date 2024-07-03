import React, { useState } from 'react';
import { TextField, Button, Typography, Container, Box, Grid } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import './RegisterPage.scss';

const RegisterPage = ({ setToken }) => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [verificationKey, setVerificationKey] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [isKeyRequested, setIsKeyRequested] = useState(false);
  const navigate = useNavigate();

  const isUsernameValid = (username) => {
    const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/;
    return usernameRegex.test(username);
  };

  const isEmailValid = (email) => {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailRegex.test(email);
  };

  const isPasswordStrong = (password) => {
    const minLength = 8;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumbers = /\d/.test(password);
    const hasNonalphas = /\W/.test(password);
    return password.length >= minLength && hasUpperCase && hasLowerCase && hasNumbers && hasNonalphas;
  };

  const handleRequestKey = async () => {
    if (!isEmailValid(email)) {
      setError('Please enter a valid email address.');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/request-verification-key', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });
      const data = await response.json();
      if (response.ok) {
        setMessage(data.message);
        setIsKeyRequested(true);
        setError(''); // Clear any previous errors
      } else {
        setError(data.detail || 'Failed to send verification key. Please try again.');
        setMessage(''); // Clear any previous messages
      }
    } catch (error) {
      console.error('Verification key request error:', error);
      setError('An error occurred. Please try again.');
      setMessage(''); // Clear any previous messages
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    if (!isUsernameValid(username)) {
      setError('Username must be 3-20 characters long and can only contain letters, numbers, and underscores.');
      return;
    }

    if (!isEmailValid(email)) {
      setError('Please enter a valid email address.');
      return;
    }

    if (!isPasswordStrong(password)) {
      setError('Password must be at least 8 characters long and contain uppercase, lowercase, number, and special character');
      return;
    }

    if (!verificationKey) {
      setError('Please enter the verification key sent to your email.');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          email,
          password,
          verification_key: verificationKey,
        }),
      });
      const data = await response.json();
      if (response.ok) {
        setToken(data.access_token);
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('refreshToken', data.refresh_token);
        navigate('/chat');
      } else {
        if (typeof data.detail === 'string') {
          setError(data.detail);
        } else if (Array.isArray(data.detail)) {
          setError(data.detail.map(err => err.msg).join(', '));
        } else {
          setError('Registration failed. Please try again.');
        }
      }
    } catch (error) {
      console.error('Registration error:', error);
      setError('An error occurred. Please try again.');
    }
  };

  return (
    <Container component="main" maxWidth="xs" className="register-page">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Typography component="h1" variant="h5">
          Register for <span className="gameseeker-ai-text">GameSeeker AI</span>
        </Typography>
        {error && <Typography color="error" className="error-message">{error}</Typography>}
        {message && (
          <Typography 
            className="verification-message"
            sx={{ color: '#ff6b6b', marginBottom: '1rem' }}
          >
            {message}
          </Typography>
        )}
        <Box component="form" onSubmit={handleRegister} noValidate sx={{ mt: 1, width: '100%' }}>
          <TextField
            margin="normal"
            required
            fullWidth
            id="username"
            label="Username"
            name="username"
            autoComplete="username"
            autoFocus
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <Grid container spacing={2}>
            <Grid item xs={8}>
              <TextField
                margin="normal"
                required
                fullWidth
                id="email"
                label="Email Address"
                name="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </Grid>
            <Grid item xs={4}>
              <Button
                fullWidth
                variant="contained"
                onClick={handleRequestKey}
                disabled={isKeyRequested}
                sx={{ mt: 3, mb: 2 }}
              >
                {isKeyRequested ? 'Sent' : 'Get Key'}
              </Button>
            </Grid>
          </Grid>
          <TextField
            margin="normal"
            required
            fullWidth
            id="verificationKey"
            label="Verification Key"
            name="verificationKey"
            value={verificationKey}
            onChange={(e) => setVerificationKey(e.target.value)}
          />
          <TextField
            margin="normal"
            required
            fullWidth
            name="password"
            label="Password"
            type="password"
            id="password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
          >
            Sign Up
          </Button>
          <Button
            fullWidth
            variant="text"
            onClick={() => navigate('/login')}
          >
            Already have an account? Sign In
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default RegisterPage;