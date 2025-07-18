import React from 'react';
import { ArrowLeft, ArrowRight } from 'lucide-react';

const StepNavigation = ({ currentStep, steps, handleBack, handleNext }) => {
  return (
    <div className="step-navigation">
      <button
        onClick={handleBack}
        disabled={currentStep === 0}
        className="nav-button back-button"
      >
        <ArrowLeft className="w-5 h-5" />
        <span>Back</span>
      </button>
      
      <div className="step-dots">
        {steps.map((_, index) => (
          <div
            key={index}
            className={`step-dot ${
              index <= currentStep ? 'active' : 'inactive'
            }`}
          />
        ))}
      </div>
      
      <button
        onClick={handleNext}
        className="nav-button next-button"
      >
        <span>{currentStep === steps.length - 1 ? 'Generate Quote' : 'Next'}</span>
        <ArrowRight className="w-5 h-5" />
      </button>
    </div>
  );
};

export default StepNavigation;
