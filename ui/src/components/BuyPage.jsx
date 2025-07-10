import React from 'react';

const BuyPage = ({ onBack }) => {
  return (
    <div className="buy-page-container">
      <div className="buy-page-header">
        <button className="back-button" onClick={onBack}>
          &larr; Back
        </button>
        <h2>Complete Your Purchase</h2>
      </div>
      <div className="buy-page-content">
        <p>This is the buy page. Please fill in the details below to complete your purchase.</p>
        {/* Add form fields for the purchase process here */}
      </div>
    </div>
  );
};

export default BuyPage;
