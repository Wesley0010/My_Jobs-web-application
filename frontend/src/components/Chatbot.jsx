import { useState } from 'react';
import './Chatbot.css';

export default function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([{ text: "Hi! I'm your AI career assistant. How can I help you today?", sender: 'ai' }]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input;
    setMessages(prev => [...prev, { text: userMsg, sender: 'user' }]);
    setInput('');
    setIsLoading(true);

    const token = localStorage.getItem('token');

    try {
      const response = await fetch('http://localhost:8000/api/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}`
        },
        body: JSON.stringify({ message: userMsg })
      });

      const data = await response.json();
      if (response.ok) {
        setMessages(prev => [...prev, { text: data.reply, sender: 'ai' }]);
      } else {
        setMessages(prev => [...prev, { text: "Sorry, I couldn't connect to the AI.", sender: 'ai' }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { text: "Server error.", sender: 'ai' }]);
    }
    setIsLoading(false);
  };

  return (
    <>
      {/* Floating Button */}
      <button className="chat-toggle-btn" onClick={() => setIsOpen(!isOpen)}>
        {isOpen ? '✕' : '💬'}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="chat-window">
          <div className="chat-header">
            <strong>My_Jobs AI Assistant</strong>
          </div>
          
          <div className="chat-messages">
            {messages.map((msg, index) => (
              <div key={index} className={`message ${msg.sender}`}>
                {msg.text}
              </div>
            ))}
            {isLoading && <div className="message ai">Typing...</div>}
          </div>

          <form className="chat-input-area" onSubmit={sendMessage}>
            <input 
              type="text" 
              value={input} 
              onChange={(e) => setInput(e.target.value)} 
              placeholder="Ask me anything..."
            />
            <button type="submit">Send</button>
          </form>
        </div>
      )}
    </>
  );
}