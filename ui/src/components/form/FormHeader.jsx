import React from 'react';

const FormHeader = ({ currentStep, steps }) => {
  const progress = ((currentStep + 1) / steps.length) * 100;

  return (
    <>
      <div className="progress-bar-container">
        <div 
          className="progress-bar"
          style={{ width: `${progress}%` }}
        />
      </div>
      <div className="form-header">
        <h1>Insurance Quotation</h1>
        <p>
          Step {currentStep + 1} of {steps.length}
        </p>
      </div>
    </>
  );
};

export default FormHeader;
