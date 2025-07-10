import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import InsuranceQuotationForm from './InsuranceQuotationForm'; // Import the new component
import BuyPage from './BuyPage'; // Import the new BuyPage component
import './chatwidget.css';

const ChatWidget = () => {
  const [isOpen, setIsOpen] = useState(true);
  const [showQuotationForm, setShowQuotationForm] = useState(false); // New state
  const [showBuyPage, setShowBuyPage] = useState(false); // New state for the buy page
  const [isFormVisible, setIsFormVisible] = useState(true);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showLogin, setShowLogin] = useState(true);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [sliderValues, setSliderValues] = useState({});
  const [quoteDataForForm, setQuoteDataForForm] = useState(null); // To pass quote data to the form
  const [formData, setFormData] = useState({});
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null); // New ref for the input field
  const fileInputRef = useRef(null);

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
    if (!phoneNumber || !name) return;

    setIsTyping(true);
    try {
      const response = await axios.post('http://localhost:8000/chat', {
        phone_number: phoneNumber,
        name: name,
        email: email,
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
        input_type: response.data.input_type,
        slider_config: response.data.slider_config,
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

      const botResponse = response.data;

      // Check if the backend wants to show the multi-step form
      if (botResponse.input_type === 'multi_step_form') {
        setShowQuotationForm(true);
        setIsFormVisible(true);
        // Add a message to inform the user
        const formMessage = {
          id: `form-msg-${Date.now()}`,
          text: botResponse.answer,
          sender: 'bot',
        };
        setMessages((prevMessages) => [...prevMessages, formMessage]);
      } else {
        const message = {
          id: `resp-${Date.now()}`,
          text: botResponse.answer,
          sender: 'bot',
          options: botResponse.options,
          input_type: botResponse.input_type,
          slider_config: botResponse.slider_config,
        };
        setMessages((prevMessages) => {
          const updatedMessages = [...prevMessages, message];
          setTimeout(focusInput, 0);
          return updatedMessages;
        });
      }
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

  // This function is called by the InsuranceQuotationForm component when the user clicks "Generate Quote"
  const handleQuoteRequest = async (currentFormData) => {
    try {
      const response = await axios.post('http://localhost:8000/api/update_user_and_get_quote', {
        ...currentFormData,
        phone_number: phoneNumber,
      });

      const quote = response.data;
      const quoteMessageText = `
### Your Insurance Quote

**Quote Number:** ${quote.quote_number}
**Sum Assured:** ₹${quote.sum_assured.toLocaleString()}
**Policy Term:** ${quote.policy_term} years
**Payment Term:** ${quote.premium_payment_term} years
**Base Premium:** ₹${quote.base_premium.toLocaleString()}
**GST (18%):** ₹${quote.gst.toLocaleString()}
**Total Premium (${quote.premium_frequency}):** ₹${quote.total_premium.toLocaleString()}

**Note:** This is an estimate. Final premium depends on underwriting and medical examination.
      `;
      const botMessage = {
        id: `resp-${Date.now()}`,
        text: quoteMessageText,
        sender: 'bot',
        actions: quote.actions, // Pass actions to the message
      };
      setMessages((prevMessages) => [...prevMessages, botMessage]);
      setShowQuotationForm(false);
      setFormData({}); // Reset form data
    } catch (error) {
      console.error('Error getting quote:', error);
      const botResponse = {
        id: `err-${Date.now()}`,
        text: 'Sorry, something went wrong while generating your quote. Please try again.',
        sender: 'bot',
      };
      setMessages((prevMessages) => [...prevMessages, botResponse]);
    }
  };

  const handleActionClick = (action) => {
    if (action === 'Proceed to Buy') {
      setShowBuyPage(true);
    }
  };

  const handleSliderChange = (messageId, value) => {
    setSliderValues(prev => ({ ...prev, [messageId]: value }));
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

  const handleFileAttach = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    console.log("Selected file:", file.name);
    // Here you can add logic to upload the file or display it in the chat
    const reader = new FileReader();
    reader.onload = (event) => {
      const fileMessage = {
        id: `msg-${Date.now()}`,
        text: `Attached file: ${file.name}`,
        sender: 'user',
        file: {
          name: file.name,
          type: file.type,
          size: file.size,
          dataUrl: event.target.result,
        },
      };
      setMessages((prevMessages) => [...prevMessages, fileMessage]);
    };
    reader.readAsDataURL(file);
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
      setShowQuotationForm(false); // Reset form visibility
      setIsFormVisible(true);
      setQuoteDataForForm(null); // Reset quote data
      setFormData({}); // Reset form data
      setShowBuyPage(false); // Reset buy page visibility
      setPhoneNumber('');
      setName('');
      setEmail('');
    }
    setIsOpen(!isOpen);
  };

  if (!isOpen) {
    return (
      <div className="chatbot-fab" onClick={toggleChat}>
        <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 0 24 24" width="24px"><path d="M0 0h24v24H0z" fill="none"/><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/></svg>
      </div>
    );
  }

  if (showBuyPage) {
    return (
      <div className="chatbot-container">
        <BuyPage onBack={() => setShowBuyPage(false)} />
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
            <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 0 24 24" width="24px"><path d="M0 0h24v24H0z" fill="none"/><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
          </button>
        </div>
      </div>

      {showLogin ? (
        <div className="login-container">
          <form onSubmit={handleLogin} style={{ width: '100%' }}>
            <input
              type="text"
              placeholder="Enter your name *"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="chatbot-input"
              style={{ width: '100%', marginBottom: '10px' }}
              required
            />
            <input
              type="tel"
              placeholder="Enter your phone number *"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              className="chatbot-input"
              style={{ width: '100%', marginBottom: '10px' }}
              required
            />
            <input
              type="email"
              placeholder="Enter your email "
              value={email}
              onChange={(e) => setEmail(e.target.value)}
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
          {showQuotationForm && (
            <div className="form-section">
              <div className="form-header" onClick={() => setIsFormVisible(!isFormVisible)}>
                <span>Insurance Quotation</span>
                <button className="icon-btn">
                  <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 0 24 24" width="24px">
                    <path d="M0 0h24v24H0z" fill="none"/>
                    <path d={isFormVisible ? "M7.41 15.41L12 10.83l4.59 4.58L18 14l-6-6-6 6z" : "M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6z"}/>
                  </svg>
                </button>
              </div>
              <div
                className="form-container-collapsible"
                style={{ display: isFormVisible ? 'block' : 'none' }}
              >
                <InsuranceQuotationForm
                  onQuoteGenerated={handleQuoteRequest}
                  initialQuoteData={quoteDataForForm}
                  formData={formData}
                  setFormData={setFormData}
                />
              </div>
            </div>
          )}
          <div className="chatbot-messages">
            {messages.map((message) => (
              <div key={message.id} className={`message-container ${message.sender === 'user' ? 'user-message-container' : ''}`}>
                <div className={`message ${message.sender}-message`}>
                  <ReactMarkdown>{message.text}</ReactMarkdown>
                </div>
                {message.actions && (
                  <div className="options-container">
                    {message.actions.map((action, index) => (
                      <button key={index} className="option-button" onClick={() => handleActionClick(action)}>
                        {action}
                      </button>
                    ))}
                  </div>
                )}
                {message.input_type === 'slider' && message.slider_config && (
                  <div className="slider-container">
                    <div className="slider-label">
                      {message.slider_config.label}: <strong>₹{Number(sliderValues[message.id] || message.slider_config.default).toLocaleString('en-IN')}</strong>
                    </div>
                    <input
                      type="range"
                      min={message.slider_config.min}
                      max={message.slider_config.max}
                      step={message.slider_config.step}
                      defaultValue={sliderValues[message.id] || message.slider_config.default}
                      onChange={(e) => handleSliderChange(message.id, e.target.value)}
                      className="chatbot-slider"
                    />
                    <button
                      className="option-button"
                      onClick={() => handleSendMessage(sliderValues[message.id] || message.slider_config.default)}
                    >
                      Confirm Amount
                    </button>
                  </div>
                )}
                {message.options && message.input_type === 'dropdown' && (
                  <div className="options-container">
                    <select
                      className="chatbot-input"
                      onChange={(e) => handleOptionClick(e.target.value)}
                      style={{ width: '100%', marginBottom: '10px' }}
                    >
                      <option value="">Select an option</option>
                      {message.options.map((option, index) => (
                        <option key={index} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
                {message.options && message.input_type !== 'dropdown' && !message.customInput && (
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
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              onChange={handleFileChange}
            />
            <button className="input-attach-btn" title="Attach File" onClick={handleFileAttach}>
              <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 0 24 24" width="24px"><path d="M0 0h24v24H0V0z" fill="none"/><path d="M16.5 6v11.5c0 2.21-1.79 4-4 4s-4-1.79-4-4V5c0-1.38 1.12-2.5 2.5-2.5s2.5 1.12 2.5 2.5v10.5c0 .55-.45 1-1 1s-1-.45-1-1V6H10v9.5c0 1.38 1.12 2.5 2.5 2.5s2.5-1.12 2.5-2.5V5c0-2.21-1.79-4-4-4S7 2.79 7 5v12.5c0 3.04 2.46 5.5 5.5 5.5s5.5-2.46 5.5-5.5V6h-1.5z"/></svg>
            </button>
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
                <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 0 24 24" width="24px"><path d="M0 0h24v24H0z" fill="none"/><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default ChatWidget;
