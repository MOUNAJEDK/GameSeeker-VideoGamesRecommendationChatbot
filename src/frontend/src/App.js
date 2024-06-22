import React from 'react';
import ChatWindow from './components/ChatWindow';
import './App.scss'; // Import App-specific styles

function App() {
  return (
    <div className="App">
      <div className="background-shapes">
        <div className="shape1"></div>
        <div className="shape2"></div>
      </div>
      <ChatWindow />
    </div>
  );
}

export default App;
