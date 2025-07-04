import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import './chatwidget.css';

const ChatWidget = () => {
  const [isOpen, setIsOpen] = useState(true);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showLogin, setShowLogin] = useState(true);
  const [phoneNumber, setPhoneNumber] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null); // New ref for the input field

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const focusInput = () => {
    inputRef.current?.focus();
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!phoneNumber) return;

    setIsTyping(true);
    try {
      const response = await axios.post('http://localhost:8000/chat', {
        phone_number: phoneNumber,
        query: "", // Send empty query to get history and welcome message
      });

      const formattedHistory = response.data.chat_history.map((msg, index) => ({
        id: `hist-${index}`,
        text: msg.text,
        sender: msg.type === 'user' ? 'user' : 'bot',
      }));
      
      const welcomeMessage = {
        id: 'welcome',
        text: response.data.answer,
        sender: 'bot',
        options: response.data.options,
      };

      // Avoid duplicating the welcome message if it's already in the history
      if (formattedHistory.length > 0 && formattedHistory[formattedHistory.length - 1].text === welcomeMessage.text) {
        setMessages(formattedHistory);
      } else {
        setMessages([...formattedHistory, welcomeMessage]);
      }
      
      setShowLogin(false);
      focusInput(); // Focus input after successful login
    } catch (error) {
      console.error('Error logging in:', error);
      // Optionally, show an error message to the user
    } finally {
      setIsTyping(false);
    }
  };

  const handleSendMessage = async (text) => {
    if (!phoneNumber) return;

    const userMessage = {
      id: `msg-${Date.now()}`,
      text: text,
      sender: 'user',
    };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setIsTyping(true);

    try {
      const response = await axios.post('http://localhost:8000/chat', {
        phone_number: phoneNumber,
        query: text,
      });

      const botResponse = {
        id: `resp-${Date.now()}`,
        text: response.data.answer,
        sender: 'bot',
        options: response.data.options,
      };
      setMessages((prevMessages) => {
        const updatedMessages = [...prevMessages, botResponse];
        // Ensure input is focused after bot response
        setTimeout(focusInput, 0); // Use setTimeout to ensure focus after state update
        return updatedMessages;
      });
    } catch (error) {
      console.error('Error sending message:', error);
      const botResponse = {
        id: `err-${Date.now()}`,
        text: 'Sorry, something went wrong. Please try again.',
        sender: 'bot',
      };
      setMessages((prevMessages) => [...prevMessages, botResponse]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleOptionClick = (option) => {
    if (option === 'Let me specify custom amount') {
      // Don't send a message, just show the input field
      const customAmountMessage = {
        id: messages.length + 1,
        text: "Please enter the custom amount.",
        sender: 'bot',
        customInput: true,
      };
      setMessages((prevMessages) => [...prevMessages, customAmountMessage]);
    } else {
      handleSendMessage(option);
    }
  };

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
  };

  const handleSendClick = () => {
    if (inputValue.trim()) {
      handleSendMessage(inputValue);
      setInputValue('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSendClick();
    }
  };

  const toggleChat = () => {
    if (isOpen) {
      // Reset state when closing the chat
      setMessages([]);
      setInputValue('');
      setIsTyping(false);
      setShowLogin(true);
      setPhoneNumber('');
    }
    setIsOpen(!isOpen);
  };

  if (!isOpen) {
    return (
      <div className="chatbot-fab" onClick={toggleChat}>
        <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 0 24 24" width="24px" fill="#FFFFFF"><path d="M0 0h24v24H0z" fill="none"/><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/></svg>
      </div>
    );
  }

  return (
    <div className="chatbot-container">
      <div className="chatbot-header">
        <div className="chatbot-avatar">
          <div className="avatar-circle" />
        </div>
        <div className="chatbot-title-group">
          <div className="chatbot-title">Cogno Life Assistant</div>
          {/* <div className="chatbot-subtitle">How can I help?</div> */}
        </div>
        <div className="chatbot-header-icons">
          <button className="icon-btn" onClick={toggleChat}>
            <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 0 24 24" width="24px" fill="#FFFFFF"><path d="M0 0h24v24H0z" fill="none"/><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
          </button>
        </div>
      </div>

      {showLogin ? (
        <div className="login-container">
          <form onSubmit={handleLogin} style={{ width: '100%' }}>
            <input
              type="tel"
              placeholder="Enter your phone number"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              className="chatbot-input"
              style={{ width: '100%', marginBottom: '10px' }}
            />
            <button type="submit" className="option-button" style={{ width: '100%' }}>
              Start Conversation
            </button>
          </form>
        </div>
      ) : (
        <>
          <div className="chatbot-messages">
            {messages.map((message) => (
              <div key={message.id} className={`message-container ${message.sender === 'user' ? 'user-message-container' : ''}`}>
                <div className={`message ${message.sender}-message`}>
                  <ReactMarkdown>{message.text}</ReactMarkdown>
                </div>
                {message.options && !message.customInput && (
                  <div className="options-container">
                    {message.options.map((option, index) => (
                      <button key={index} className="option-button" onClick={() => handleOptionClick(option)}>
                        {option}
                      </button>
                    ))}
                  </div>
                )}
                {message.customInput && (
                  <div className="chatbot-input-bar">
                    <input
                      className="chatbot-input"
                      type="text"
                      placeholder="Enter custom amount"
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          handleSendMessage(e.target.value);
                          e.target.value = '';
                        }
                      }}
                    />
                  </div>
                )}
                {message.policies && (
                  <div className="policies-container">
                    {message.policies.map((policy, index) => (
                      <div key={index} className="policy-card">
                        <div className="policy-card-body">
                          <ReactMarkdown>{policy}</ReactMarkdown>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {isTyping && (
              <div className="message-container">
                <div className="message bot-message typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="chatbot-input-bar">
            <input
              className="chatbot-input"
              type="text"
              placeholder={isTyping ? "Assistant is typing..." : "Type your message..."}
              value={inputValue}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              disabled={isTyping}
              ref={inputRef}
            />
            <button className="input-send-btn" title="Send" onClick={handleSendClick} disabled={isTyping}>
                <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 0 24 24" width="24px" fill="#FFFFFF"><path d="M0 0h24v24H0z" fill="none"/><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default ChatWidget;
