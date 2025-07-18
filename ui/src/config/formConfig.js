import { Calendar, User, GraduationCap, Heart, Building, CreditCard, FileText } from 'lucide-react';

export const steps = [
  { id: 'dob', title: 'Date of Birth', icon: Calendar },
  { id: 'gender', title: 'Gender', icon: User },
  { id: 'nationality', title: 'Nationality', icon: Building },
  { id: 'marital_status', title: 'Marital Status', icon: Heart },
  { id: 'education', title: 'Education', icon: GraduationCap },
  { id: 'existing_policy', title: 'Existing Policy', icon: FileText },
  { id: 'gst_applicable', title: 'GST Applicable', icon: FileText },
  { id: 'plan_option', title: 'Plan Type', icon: CreditCard },
  { id: 'terms', title: 'Policy & Payment Term', icon: FileText },
  { id: 'coverage_required', title: 'Coverage Amount', icon: CreditCard },
  { id: 'premium_frequency', title: 'Payment Frequency', icon: CreditCard },
  { id: 'income_payout_frequency', title: 'Payout Frequency', icon: CreditCard }
];

export const options = {
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

export const getDynamicMaxCoverage = (term) => {
  if (!term) return 10000000; // Default max
  // Example logic: Higher term allows higher coverage
  return 10000000 + (parseInt(term, 10) * 100000);
};
