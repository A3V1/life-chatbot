import React, { useEffect, useState } from 'react';
import './InsuranceQuotationForm.css';
import { steps, options, getDynamicMaxCoverage } from '../config/formConfig';
import useMultiStepForm from '../hooks/useMultiStepForm';
import FormHeader from './form/FormHeader';
import StepNavigation from './form/StepNavigation';
import { Calendar, CreditCard, FileText } from 'lucide-react';

const InsuranceQuotationForm = ({ onQuoteGenerated, initialQuoteData, formData, setFormData }) => {
  const {
    currentStep,
    errors,
    handleInputChange,
    handleNext,
    handleBack,
  } = useMultiStepForm(formData, setFormData, onQuoteGenerated);

  const [quote, setQuote] = useState(null);

  useEffect(() => {
    if (initialQuoteData && initialQuoteData.quote_data) {
      setQuote(initialQuoteData.quote_data);
    }
  }, [initialQuoteData]);

  const renderStep = () => {
    const step = steps[currentStep];
    const StepIcon = step.icon;

    switch (step.id) {
      case 'dob':
        return (
          <div className="step-content">
            <div className="step-header">
              <Calendar className="step-icon" />
              <h2 className="step-title">Date of Birth</h2>
            </div>
            <p className="step-description">Please enter your date of birth to calculate your premium accurately.</p>
            <input
              type="date"
              value={formData?.dob || ''}
              onChange={(e) => handleInputChange('dob', e.target.value)}
              className={`input-field ${errors.dob ? 'error' : ''}`}
              max={new Date(new Date().setFullYear(new Date().getFullYear() - 18)).toISOString().split('T')[0]}
              min={new Date(new Date().setFullYear(new Date().getFullYear() - 65)).toISOString().split('T')[0]}
            />
            {errors.dob && <p className="error-message">{errors.dob}</p>}
          </div>
        );

      case 'coverage_required':
        const maxCoverage = getDynamicMaxCoverage(formData.policy_term);
        const coverageValue = formData?.coverage_required || 1000000;

        const handleCoverageChange = (e) => {
          let value = parseInt(e.target.value, 10);
          if (isNaN(value)) value = 50000;
          if (value > maxCoverage) value = maxCoverage;
          handleInputChange('coverage_required', value);
        };

        return (
          <div className="step-content">
            <div className="step-header">
              <CreditCard className="step-icon" />
              <h2 className="step-title">Coverage Amount</h2>
            </div>
            <div>
              <label className="step-description">
                Desired Coverage (Sum Assured)
              </label>
              <div className="coverage-input-sync">
                <input
                  type="range"
                  min="50000"
                  max={maxCoverage}
                  step="50000"
                  value={coverageValue}
                  onChange={handleCoverageChange}
                  className="range-slider"
                />
                <input
                  type="number"
                  min="50000"
                  max={maxCoverage}
                  step="50000"
                  value={coverageValue}
                  onChange={handleCoverageChange}
                  className="input-field coverage-input-box"
                />
              </div>
              <div className="range-value">
                ₹{coverageValue.toLocaleString()}
              </div>
            </div>
            {errors.coverage_required && (
              <p className="error-message text-center">{errors.coverage_required}</p>
            )}
          </div>
        );

      case 'terms':
        return (
          <div className="step-content">
            <div className="step-header">
              <FileText className="step-icon" />
              <h2 className="step-title">Policy & Payment Term</h2>
            </div>
            <div className="option-grid">
              <div>
                <label className="step-description">Policy Term (Years)</label>
                <div className="option-grid">
                  {options.policy_term.map((option) => (
                    <button
                      key={option}
                      onClick={() => handleInputChange('policy_term', option)}
                      className={`option-button ${formData?.policy_term === option ? 'selected' : ''}`}
                    >
                      {option}
                    </button>
                  ))}
                </div>
                {errors.policy_term && <p className="error-message">{errors.policy_term}</p>}
              </div>
              <div>
                <label className="step-description">Premium Payment Term (Years)</label>
                <div className="option-grid">
                  {options.premium_payment_term.map((option) => (
                    <button
                      key={option}
                      onClick={() => handleInputChange('premium_payment_term', option)}
                      className={`option-button ${formData?.premium_payment_term === option ? 'selected' : ''}`}
                    >
                      {option}
                    </button>
                  ))}
                </div>
                {errors.premium_payment_term && <p className="error-message">{errors.premium_payment_term}</p>}
              </div>
            </div>
          </div>
        );

      default:
        const fieldOptions = options[step.id];
        return (
          <div className="step-content">
            <div className="step-header">
              <StepIcon className="step-icon" />
              <h2 className="step-title">{step.title}</h2>
            </div>
            
            {step.id === 'nationality' ? (
              <div>
                <input
                  type="text"
                  placeholder="Enter your nationality"
                  value={formData?.[step.id] || ''}
                  onChange={(e) => handleInputChange(step.id, e.target.value)}
                  className={`input-field ${errors[step.id] ? 'error' : ''}`}
                  list="nationality-options"
                />
                <datalist id="nationality-options">
                  {fieldOptions.map(option => (
                    <option key={option} value={option} />
                  ))}
                </datalist>
              </div>
            ) : (
              <div className="option-grid">
                {fieldOptions.map((option) => (
                  <button
                    key={option}
                    onClick={() => handleInputChange(step.id, option === 'Yes' ? true : option === 'No' ? false : option)}
                    className={`option-button ${
                      formData?.[step.id] === option || 
                      (formData?.[step.id] === true && option === 'Yes') ||
                      (formData?.[step.id] === false && option === 'No')
                        ? 'selected'
                        : ''
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            )}
            
            {errors[step.id] && (
              <p className="error-message">{errors[step.id]}</p>
            )}
          </div>
        );
    }
  };

  return (
    <div className="insurance-quotation-form">
      <div className="form-container">
        <FormHeader currentStep={currentStep} steps={steps} />
        
        <div className="form-content">
          {renderStep()}
        </div>
        
        <StepNavigation 
          currentStep={currentStep}
          steps={steps}
          handleBack={handleBack}
          handleNext={handleNext}
        />
      </div>
    </div>
  );
};

export default InsuranceQuotationForm;
