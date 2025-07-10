
import React, { useState } from 'react';
import './App.css';
import ChatWidget from './components/chatwidget';
import InsuranceQuotationForm from './components/InsuranceQuotationForm';

function App() {
  const [quoteData, setQuoteData] = useState(null);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [isFormStarted, setIsFormStarted] = useState(false);
  const [phoneError, setPhoneError] = useState('');

  const handlePhoneSubmit = (e) => {
    e.preventDefault();
    if (phoneNumber.trim().length >= 10) {
      setIsFormStarted(true);
      setPhoneError('');
    } else {
      setPhoneError('Please enter a valid phone number.');
    }
  };

  // const handleQuoteGenerated = async (formData) => {
  //   try {
  //     const response = await fetch('http://localhost:8000/api/update_user_and_get_quote', {
  //       method: 'POST',
  //       headers: {
  //         'Content-Type': 'application/json',
  //       },
  //       body: JSON.stringify({ ...formData, phone_number: phoneNumber }),
  //     });

  //     if (!response.ok) {
  //       throw new Error('Failed to get quote');
  //     }

  //     const data = await response.json();
  //     setQuoteData(data);
  //   } catch (error) {
  //     console.error('Error getting quote:', error);
  //   }
  // };

  return (
    <div className="life-bg">
      {/* Top Navigation */}
      <header className="life-header">
        <div className="life-header-inner">
          <div className="life-logo-wrap">
            <div className="life-logo-text">
              <svg width="38" height="38" viewBox="0 0 38 38" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ marginRight: 8 }}>
                <circle cx="19" cy="19" r="19" fill="#e6ecf7" />
                <path d="M10 19L19 10V28L10 19Z" fill="#5b3df5" />
              </svg>
              LifeSecure
            </div>
          </div>
          <nav className="life-nav">
            <a href="#">Products</a>
            <a href="#">Renewals</a>
            <a href="#">Claims</a>
            <a href="#">Resources</a>
            <a href="#">Enterprise</a>
          </nav>
          <div className="life-header-actions">
            <button className="life-btn life-btn-outline">Login</button>
            <button className="life-btn life-btn-green">Sign Up</button>
          </div>
        </div>
      </header>

      {/* Banner Info */}
      <div className="life-banner">
        BEST LIFE INSURANCE POLICY IN INDIA 2025 @₹18/DAY* | LifeSecure™
        <div className="life-banner-desc">
          It’s great to stay positive, but being prepared never hurts. Life doesn’t always go as planned, and that’s where life insurance comes in. A life insurance plan can offer financial support. It gives your family the security they deserve.
        </div>
      </div>

      {/* Hero Section */}
      <section className="life-hero">
        <div className="life-hero-left">
          <h1>
            Term Life Insurance that Welcomes Change
          </h1>
          <div className="life-hero-sub">
            Life Cover Starting @ just ₹18/day*
          </div>
          <ul className="life-hero-list">
            <li>
              <span className="life-hero-icon">
                <svg width="32" height="32" fill="none" viewBox="0 0 32 32"><circle cx="16" cy="16" r="16" fill="#e6ecf7"/><path d="M10 16l6-6v12l-6-6z" fill="#5b3df5"/></svg>
              </span>
              <span>
                <b>Change Your Policy Term</b><br />
                <span className="life-hero-list-desc">As per your life stage and commitments</span>
              </span>
            </li>
            <li>
              <span className="life-hero-icon">
                <svg width="32" height="32" fill="none" viewBox="0 0 32 32"><circle cx="16" cy="16" r="16" fill="#e6ecf7"/><path d="M10 22l12-12v12H10z" fill="#5b3df5"/></svg>
              </span>
              <span>
                <b>Hassle-Free Claim Settlement</b><br />
                <span className="life-hero-list-desc">99.38% Claim settlement ratio*</span>
              </span>
            </li>
            <li>
              <span className="life-hero-icon">
                <svg width="32" height="32" fill="none" viewBox="0 0 32 32"><circle cx="16" cy="16" r="16" fill="#e6ecf7"/><path d="M16 10v12M10 16h12" stroke="#5b3df5" strokeWidth="2" strokeLinecap="round"/></svg>
              </span>
              <span>
                <b>Smart Income Tax Savings</b><br />
                <span className="life-hero-list-desc">Save up to ₹54,600* on your taxes</span>
              </span>
            </li>
          </ul>
        </div>
        {/* Form Card */}
        <div className="life-hero-form-card">
          {/* {!isFormStarted ? (
            <>
              <h2>Let's build a perfect life insurance cover for you</h2>
              <form onSubmit={handlePhoneSubmit}>
                <div className="life-form-group">
                  <label htmlFor="phone">Your Phone Number</label>
                  <input
                    id="phone"
                    name="phone"
                    type="tel"
                    placeholder="Enter your 10-digit phone number"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                  />
                  {phoneError && <p className="error-message" style={{color: 'red', fontSize: '12px', marginTop: '4px'}}>{phoneError}</p>}
                </div>
                <button type="submit" className="life-btn life-btn-purple life-btn-block">
                  Get Free Quote
                </button>
              </form>
            </>
          ) : (
            <InsuranceQuotationForm
              onQuoteGenerated={handleQuoteGenerated}
              initialQuoteData={quoteData}
            />
          )} */}
        </div>
      </section>

      {/* Hero Image */}
      <div className="life-hero-img-wrap">
        <img src="https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=900&q=80" alt="Happy family enjoying outdoors" className="life-hero-img" />
      </div>

      {/* Footer */}
      <footer className="life-footer">
        &copy; {new Date().getFullYear()} LifeSecure Insurance. All rights reserved.
      </footer>

      {/* Chat Widget Bottom Left */}
      <div className="chatbot-fixed-bl">
        <ChatWidget />
      </div>
    </div>
  )
}

export default App;
