import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [message, setMessage] = useState('');
  const [history, setHistory] = useState([]);
  const [temperature, setTemperature] = useState(0.3);
  const [maxTokens, setMaxTokens] = useState(50);

  const sendMessage = async () => {
    if (!message.trim()) return;

    try {
      const response = await axios.post('http://localhost:5000/api/chat', {
        question: message,
        temperature,
        max_tokens: maxTokens,
        history
      });
      
      setHistory(response.data.history);
      setMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const clearHistory = async () => {
    try {
      await axios.post('http://localhost:5000/api/clear-history');
      setHistory([]);  // Clear the in-memory history on the frontend
    } catch (error) {
      console.error('Error clearing history:', error);
    }
  };

  return (
    <div className="App">
      <h1>🤖 AI ChatBot</h1>
      <div className="controls">
        <div>
          <label>Temperature: {temperature}</label>
          <input 
            type="range" 
            min="0" 
            max="1" 
            step="0.1"
            value={temperature}
            onChange={(e) => setTemperature(parseFloat(e.target.value))}
          />
        </div>

        <div>
          <label>Max Tokens: {maxTokens}</label>
          <input 
            type="range" 
            min="50" 
            max="500" 
            step="10"
            value={maxTokens}
            onChange={(e) => setMaxTokens(parseInt(e.target.value))}
          />
        </div>

        <button onClick={clearHistory}>Clear History</button>
      </div>

      <div className="chat-container">
        {history.map((msg, index) => (
          <div 
            key={index} 
            className={`message ${msg.role === 'user' ? 'user' : 'bot'}`}
          >
            <strong>{msg.role === 'user' ? '🧑‍💻 You: ' : '🤖 Bot: '}</strong>
            {msg.content}
          </div>
        ))}
      </div>

      <div className="input-container">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type your message..."
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}

export default App;