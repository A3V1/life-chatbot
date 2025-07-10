import React, { useState, useEffect } from 'react';
import { Calendar, User, GraduationCap, Heart, Building, CreditCard, FileText, CheckCircle, ArrowRight, ArrowLeft } from 'lucide-react';
import './InsuranceQuotationForm.css';

const InsuranceQuotationForm = ({ onQuoteGenerated, initialQuoteData, formData, setFormData }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [quote, setQuote] = useState(null);
  const [errors, setErrors] = useState({});

  const steps = [
    { id: 'dob', title: 'Date of Birth', icon: Calendar },
    { id: 'gender', title: 'Gender', icon: User },
    { id: 'nationality', title: 'Nationality', icon: Building },
    { id: 'marital_status', title: 'Marital Status', icon: Heart },
    { id: 'education', title: 'Education', icon: GraduationCap },
    { id: 'existing_policy', title: 'Existing Policy', icon: FileText },
    { id: 'gst_applicable', title: 'GST Applicable', icon: FileText },
    { id: 'plan_option', title: 'Plan Type', icon: CreditCard },
    { id: 'coverage_or_premium', title: 'Coverage/Premium', icon: CreditCard },
    { id: 'policy_term', title: 'Policy Term', icon: FileText },
    { id: 'premium_payment_term', title: 'Payment Term', icon: CreditCard },
    { id: 'premium_frequency', title: 'Payment Frequency', icon: CreditCard },
    { id: 'income_payout_frequency', title: 'Payout Frequency', icon: CreditCard }
  ];

  const options = {
    gender: ['Male', 'Female', 'Other', 'Prefer not to say'],
    nationality: ['Indian', 'American', 'British', 'Canadian', 'Australian', 'German', 'French', 'Japanese', 'Chinese', 'Other'],
    marital_status: ['Single', 'Married', 'Divorced', 'Widowed', 'Separated'],
    education: [
      'High School',
      'Bachelor\'s Degree',
      'Master\'s Degree',
      'PhD/Doctorate',
      'Professional Degree',
      'Diploma/Certificate',
      'Other'
    ],
    existing_policy: ['Yes', 'No'],
    gst_applicable: ['Yes', 'No'],
    plan_option: [
      'Wealth Accumulation',
      'Child Education Plan',
      'Retirement Income Plan',
      'Monthly Income Plan',
      'Endowment / Lump Sum',
      'Tax Saving Plan',
      'Marriage Plan'
    ],
    policy_term: ['5', '10', '15', '20', '25', '30', '35'],
    premium_payment_term: ['5', '10', '12', '15', '20', 'Same as policy term'],
    premium_frequency: ['Monthly', 'Quarterly', 'Half-yearly', 'Annually'],
    income_payout_frequency: ['Monthly', 'Quarterly', 'Half-yearly', 'Yearly', 'At Maturity (Lump Sum)']
  };

  const isValidDate = (dateString) => {
    const regex = /^\d{4}-\d{2}-\d{2}$/;
    if (!regex.test(dateString)) return false;
    
    const date = new Date(dateString);
    const today = new Date();
    const age = today.getFullYear() - date.getFullYear();
    
    return date instanceof Date && !isNaN(date) && age >= 18 && age <= 65;
  };

  const validateStep = (stepId) => {
    const newErrors = {};
    
    switch (stepId) {
      case 'dob':
        if (!formData.dob) {
          newErrors.dob = 'Date of birth is required';
        } else if (!isValidDate(formData.dob)) {
          newErrors.dob = 'Please enter a valid date (age must be between 18-65)';
        }
        break;
      case 'coverage_or_premium':
        if (!formData.coverage_required && !formData.premium_budget) {
          newErrors.coverage_or_premium = 'Please specify either coverage amount or premium budget';
        }
        if (formData.premium_budget && formData.premium_budget < 1000) {
          newErrors.premium_budget = 'Minimum premium is ₹1,000';
        }
        break;
      default:
        if (!formData[stepId]) {
          newErrors[stepId] = 'This field is required';
        }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleNext = () => {
    const currentStepId = steps[currentStep].id;
    
    if (validateStep(currentStepId)) {
      if (currentStep === steps.length - 1) {
        onQuoteGenerated(formData);
      } else {
        setCurrentStep(prev => prev + 1);
      }
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };
  
  // This effect will be triggered when the parent component passes down the quote
  useEffect(() => {
    if (initialQuoteData && initialQuoteData.quote_data) {
      setQuote(initialQuoteData.quote_data);
      // setCurrentStep(steps.length - 1); // No longer needed
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

      case 'coverage_or_premium':
        return (
          <div className="step-content">
            <div className="step-header">
              <CreditCard className="step-icon" />
              <h2 className="step-title">Coverage & Premium</h2>
            </div>
            
            <div className="option-grid">
              <div>
                <label className="step-description">
                  Desired Coverage (Sum Assured)
                </label>
                <input
                  type="range"
                  min="50000"
                  max="10000000"
                  step="50000"
                  value={formData?.coverage_required || 1000000}
                  onChange={(e) => handleInputChange('coverage_required', parseInt(e.target.value))}
                  className="range-slider"
                />
                <div className="range-value">
                  ₹{(formData?.coverage_required || 1000000).toLocaleString()}
                </div>
              </div>
              
              <div>
                <label className="step-description">
                  OR Monthly Premium Budget
                </label>
                <input
                  type="number"
                  placeholder="Enter amount"
                  value={formData?.premium_budget || ''}
                  onChange={(e) => handleInputChange('premium_budget', parseInt(e.target.value))}
                  className="input-field"
                  min="1000"
                />
                {errors.premium_budget && <p className="error-message">{errors.premium_budget}</p>}
              </div>
            </div>
            
            {errors.coverage_or_premium && (
              <p className="error-message text-center">{errors.coverage_or_premium}</p>
            )}
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

  const progress = ((currentStep + 1) / steps.length) * 100;

  return (
    <div className="insurance-quotation-form">
      <div className="form-container">
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
        
        <div className="form-content">
          {renderStep()}
        </div>
        
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
      </div>
    </div>
  );
};

export default InsuranceQuotationForm;
