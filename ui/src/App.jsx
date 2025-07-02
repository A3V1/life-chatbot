
import './App.css'
import ChatWidget from './components/chatwidget';

function App() {
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
          <h2>Let's build a perfect life insurance cover for you</h2>
          <form>
            <div className="life-form-group">
              <label htmlFor="name">Your Name</label>
              <input id="name" name="name" type="text" placeholder="e.g John" />
            </div>
            <div className="life-form-group">
              <label>Your gender</label>
              <div className="life-form-row">
                <button type="button" className="life-form-btn">Male</button>
                <button type="button" className="life-form-btn">Female</button>
              </div>
            </div>
            <div className="life-form-group">
              <label>Have you smoked in the past 12 months?</label>
              <div className="life-form-row">
                <button type="button" className="life-form-btn">Yes</button>
                <button type="button" className="life-form-btn">No</button>
              </div>
            </div>
            <div className="life-form-row">
              <div className="life-form-group">
                <label>Your age</label>
                <input type="number" min="18" max="80" placeholder="e.g 30" />
              </div>
              <div className="life-form-group">
                <label>Your pin code</label>
                <input type="text" maxLength="6" placeholder="e.g 110001" />
              </div>
            </div>
            <button type="submit" className="life-btn life-btn-purple life-btn-block">Get Free Quote</button>
          </form>
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

export default App
