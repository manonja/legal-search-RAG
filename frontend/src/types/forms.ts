// Types related to form inputs and validation

// Login form data structure
export interface LoginFormData {
  email: string;
  password: string;
}

// Signup form data structure
export interface SignupFormData {
  email: string;
  password: string;
  // Add confirmPassword if handled client-side, or other fields like displayName
}

// Reset Password form data structure
export interface ResetPasswordFormData {
  email: string;
}

// Add other form data types as needed (e.g., ResetPasswordFormData)
