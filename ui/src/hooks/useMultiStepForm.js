import { useState } from 'react';
import { steps } from '../config/formConfig';

const useMultiStepForm = (initialFormData, setFormData, onQuoteGenerated) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [errors, setErrors] = useState({});

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
    const formData = initialFormData;

    switch (stepId) {
      case 'dob':
        if (!formData.dob) {
          newErrors.dob = 'Date of birth is required';
        } else if (!isValidDate(formData.dob)) {
          newErrors.dob = 'Please enter a valid date (age must be between 18-65)';
        }
        break;
      case 'coverage_required':
        if (!formData.coverage_required) {
          newErrors.coverage_required = 'Please specify a coverage amount';
        }
        break;
      case 'terms':
        if (!formData.policy_term) newErrors.policy_term = 'Policy term is required.';
        if (!formData.premium_payment_term) newErrors.premium_payment_term = 'Premium payment term is required.';
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
        onQuoteGenerated(initialFormData);
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

  return {
    currentStep,
    errors,
    handleInputChange,
    handleNext,
    handleBack,
  };
};

export default useMultiStepForm;
