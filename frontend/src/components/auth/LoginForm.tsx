'use client';

import React, { useState } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod'; // To use Zod for validation
import * as z from 'zod';
import { useAuth } from '@/contexts/AuthContext';
import { LoginFormData } from '@/types/forms';
import { useRouter } from 'next/navigation'; // For redirecting after login

// Define validation schema using Zod
const loginSchema = z.object({
  email: z.string().email({ message: 'Invalid email address' }).min(1, { message: 'Email is required' }),
  password: z.string().min(6, { message: 'Password must be at least 6 characters' }),
});

const LoginForm: React.FC = () => {
  const { login } = useAuth();
  const router = useRouter();
  const [formError, setFormError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit: SubmitHandler<LoginFormData> = async (data) => {
    setIsLoading(true);
    setFormError(null);
    try {
      console.log("Attempting to login with Firebase...");
      const userCredential = await login(data);
      console.log("Firebase login successful, getting ID token...");

      // After Firebase login, get the ID token to establish a session
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
      // detect the server-side session cookie without a page reload
      window.location.href = '/';
      // Don't use router.push here as it won't cause a full page refresh
      // router.push('/');
    } catch (error: any) {
      console.error("Login process failed:", error);
      // Handle specific Firebase error codes
      let errorMessage = 'Login failed. Please check your credentials.';
      if (error.code === 'auth/user-not-found' || error.code === 'auth/wrong-password' || error.code === 'auth/invalid-credential') {
        errorMessage = 'Invalid email or password.';
      } else if (error.code === 'auth/too-many-requests') {
        errorMessage = 'Too many login attempts. Please try again later.';
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
        <label htmlFor="email" className="block text-sm font-medium leading-6 text-gray-700">
          Email address
        </label>
        <div className="mt-2">
          <input
            id="email"
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
        <label htmlFor="password" className="block text-sm font-medium leading-6 text-gray-700">
          Password
        </label>
        <div className="mt-2">
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            {...register('password')}
            className={`block w-full rounded-md border border-gray-300 py-1.5 px-3 text-gray-900 shadow-sm placeholder:text-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 sm:text-sm sm:leading-6 ${errors.password ? 'border-red-500 focus:ring-red-500' : ''}`}
          />
          {errors.password && <p className="mt-2 text-sm text-red-600">{errors.password.message}</p>}
        </div>
      </div>

      <div>
        <button
          type="submit"
          disabled={isLoading}
          className="flex w-full justify-center rounded-md bg-gray-800 px-3 py-1.5 text-sm font-semibold leading-6 text-white shadow-sm hover:bg-gray-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Signing in...' : 'Sign in'}
        </button>
      </div>
    </form>
  );
};

export default LoginForm;
