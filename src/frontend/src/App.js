import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import ChatWindow from './components/ChatWindow';
import LoginPage from './components/LoginPage';
import RegisterPage from './components/RegisterPage';
import ForgotPasswordPage from './components/ForgotPasswordPage';
import ResetPasswordPage from './components/ResetPasswordPage';
import './App.scss';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [userMessages, setUserMessages] = useState({});

  useEffect(() => {
    const checkToken = async () => {
      if (token) {
        try {
          const response = await fetch('http://localhost:8000/users/me', {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          if (!response.ok) {
            setToken('');
            localStorage.removeItem('token');
          }
        } catch (error) {
          console.error('Error checking token:', error);
          setToken('');
          localStorage.removeItem('token');
        }
      }
    };
    checkToken();
  }, [token]);

  const updateUserMessages = (username, messages) => {
    setUserMessages(prevState => ({
      ...prevState,
      [username]: messages
    }));
  };

  return (
    <Router>
      <div className="App">
        <div className="background-shapes">
          {[...Array(10)].map((_, i) => (
            <div key={i} className={`shape shape-${i + 1}`}></div>
          ))}
        </div>
        <div className="content">
          <Routes>
            <Route path="/login" element={<LoginPage setToken={setToken} />} />
            <Route path="/register" element={<RegisterPage setToken={setToken} />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route 
              path="/chat" 
              element={
                token ? 
                <ChatWindow 
                  token={token} 
                  setToken={setToken} 
                  userMessages={userMessages}
                  updateUserMessages={updateUserMessages}
                /> : 
                <Navigate to="/login" />
              } 
            />
            <Route path="*" element={<Navigate to="/chat" />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;