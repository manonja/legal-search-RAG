'use client'; // Needs to be a client component to use hooks and render client forms

import React from 'react';
import Link from 'next/link';
import LoginForm from '@/components/auth/LoginForm';
// Optional: Add hooks like useAuth or useRouter if needed for conditional rendering based on auth state
// import { useAuth } from '@/contexts/AuthContext';
// import { useRouter } from 'next/navigation';

const LoginPage: React.FC = () => {
  // const { currentUser, loading } = useAuth();
  // const router = useRouter();

  // Middleware handles redirecting authenticated users away from /login
  // So, we primarily just need to render the form here.

  // Optional: Add a loading state check if desired, though middleware redirect is faster
  // if (loading) {
  //   return <div>Loading...</div>;
  // }

  return (
    <div className="flex min-h-full flex-1 flex-col justify-center px-6 py-12 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-sm">
        {/* Optional: Add logo/image here */}
        <h2 className="mt-10 text-center text-2xl font-bold leading-9 tracking-tight text-gray-900">
          Sign in to your account
        </h2>
      </div>

      <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-sm">
        <LoginForm />

        <p className="mt-10 text-center text-sm text-gray-500">
          Not a member?{' '}
          <Link href="/signup?bypassAuthRedirect=true" className="font-semibold leading-6 text-blue-600 hover:text-blue-500">
            Sign up now
          </Link>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
