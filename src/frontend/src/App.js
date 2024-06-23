import React from 'react';
import ChatWindow from './components/ChatWindow';
import './App.scss';

function App() {
  return (
    <div className="App">
      <div className="background-shapes">
        {[...Array(10)].map((_, i) => (
          <div key={i} className={`shape shape-${i + 1}`}></div>
        ))}
      </div>
      <ChatWindow />
    </div>
  );
}

export default App;
