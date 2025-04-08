'use client';

import React, { useState } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useAuth } from '@/contexts/AuthContext';
import { SignupFormData } from '@/types/forms'; // Ensure this type includes necessary fields
import { useRouter } from 'next/navigation';

// Define validation schema using Zod, including password confirmation
const signupSchema = z.object({
  email: z.string().email({ message: 'Invalid email address' }).min(1, { message: 'Email is required' }),
  password: z.string().min(6, { message: 'Password must be at least 6 characters' }),
  confirmPassword: z.string().min(1, { message: 'Please confirm your password' }),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"], // Error attached to the confirmPassword field
});

// Infer the type from the schema if needed, though SignupFormData should match
// type SignupFormInputs = z.infer<typeof signupSchema>;

const SignupForm: React.FC = () => {
  const { signup } = useAuth();
  const router = useRouter();
  const [formError, setFormError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupFormData & { confirmPassword: string }>({ // Include confirmPassword for validation
    resolver: zodResolver(signupSchema),
  });

  const onSubmit: SubmitHandler<SignupFormData> = async (data) => {
    setIsLoading(true);
    setFormError(null);
    try {
      console.log("Attempting to sign up with Firebase...");
      // Only pass necessary fields (email, password) to the actual signup function
      const userCredential = await signup({ email: data.email, password: data.password });
      console.log("Firebase signup successful, getting ID token...");

      // After Firebase signup, get the ID token to establish a session
      const idToken = await userCredential.user.getIdToken();
      console.log("ID token retrieved, setting up session...");

      // Send the ID token to the server to set up a session cookie
      const response = await fetch('/api/auth/session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ idToken }),
      });

      const responseData = await response.json();
      console.log("Session API response:", responseData);

      if (!response.ok) {
        throw new Error(`Session setup failed: ${responseData.error || response.statusText}`);
      }

      console.log("Session cookie set successfully, redirecting...");

      // Force a page reload to ensure Firebase auth state syncs with the session cookie
      // This is necessary because the client-side Firebase SDK doesn't automatically
      // detect the server-side session cookie without a page refresh
      window.location.href = '/';
      // Don't use router.push here as it won't cause a full page refresh
    } catch (error: any) {
      console.error("Signup failed:", error);
      let errorMessage = 'Signup failed. Please try again.';
      if (error.code === 'auth/email-already-in-use') {
        errorMessage = 'This email address is already registered.';
      } else if (error.code === 'auth/weak-password') {
        errorMessage = 'Password is too weak. Please choose a stronger password.';
      } else if (error.message) {
        // Show the actual error message for debugging
        errorMessage = `Error: ${error.message}`;
      }
      setFormError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {formError && (
        <div className="p-4 mb-4 text-sm text-red-800 rounded-lg bg-red-50" role="alert">
          {formError}
        </div>
      )}
      <div>
        <label htmlFor="email-signup" className="block text-sm font-medium leading-6 text-gray-700">
          Email address
        </label>
        <div className="mt-2">
          <input
            id="email-signup"
            type="email"
            autoComplete="email"
            required
            {...register('email')}
            className={`block w-full rounded-md border border-gray-300 py-1.5 px-3 text-gray-900 shadow-sm placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 sm:text-sm sm:leading-6 ${errors.email ? 'border-red-500 focus:ring-red-500' : ''}`}
          />
          {errors.email && <p className="mt-2 text-sm text-red-600">{errors.email.message}</p>}
        </div>
      </div>

      <div>
        <label htmlFor="password-signup" className="block text-sm font-medium leading-6 text-gray-700">
          Password
        </label>
        <div className="mt-2">
          <input
            id="password-signup"
            type="password"
            autoComplete="new-password"
            required
            {...register('password')}
            className={`block w-full rounded-md border border-gray-300 py-1.5 px-3 text-gray-900 shadow-sm placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 sm:text-sm sm:leading-6 ${errors.password ? 'border-red-500 focus:ring-red-500' : ''}`}
          />
          {errors.password && <p className="mt-2 text-sm text-red-600">{errors.password.message}</p>}
        </div>
      </div>

      <div>
        <label htmlFor="confirmPassword-signup" className="block text-sm font-medium leading-6 text-gray-700">
          Confirm Password
        </label>
        <div className="mt-2">
          <input
            id="confirmPassword-signup"
            type="password"
            autoComplete="new-password"
            required
            {...register('confirmPassword')}
            className={`block w-full rounded-md border border-gray-300 py-1.5 px-3 text-gray-900 shadow-sm placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 sm:text-sm sm:leading-6 ${errors.confirmPassword ? 'border-red-500 focus:ring-red-500' : ''}`}
          />
          {errors.confirmPassword && <p className="mt-2 text-sm text-red-600">{errors.confirmPassword.message}</p>}
        </div>
      </div>

      <div>
        <button
          type="submit"
          disabled={isLoading}
          className="flex w-full justify-center rounded-md bg-gray-800 px-3 py-1.5 text-sm font-semibold leading-6 text-white shadow-sm hover:bg-blue-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-400 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Creating account...' : 'Sign up'}
        </button>
      </div>
    </form>
  );
};

export default SignupForm;
