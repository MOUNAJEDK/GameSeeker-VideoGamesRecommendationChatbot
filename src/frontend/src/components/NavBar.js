import React from 'react';
import { AppBar, Toolbar, Typography, Box } from '@mui/material';
import favicon from '../assets/favicon.png';

const NavBar = () => {
  return (
    <AppBar position="static" sx={{ backgroundColor: '#1A1A1A', padding: '0 20px' }}>
      <Toolbar>
        <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center' }}>
          <img src={favicon} alt="GameSeeker AI Logo" style={{ height: 40, marginRight: 10 }} />
          <Typography variant="h6" sx={{ color: '#BB86FC', fontWeight: 'bold', fontFamily: 'Montserrat, sans-serif' }}>
            GameSeeker AI
          </Typography>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default NavBar;
