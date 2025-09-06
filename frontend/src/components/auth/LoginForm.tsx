'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import { isAxiosError } from 'axios';

export default function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();
  const [formData, setFormData] = useState({
    username_or_email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login(formData);
      const redirectTo = localStorage.getItem('redirectAfterLogin') || '/meals';
      localStorage.removeItem('redirectAfterLogin');
      router.push(redirectTo);
    } catch (err: unknown) {
      let message = 'Login failed. Please try again.';
      if (isAxiosError(err)) {
        const data = err.response?.data as unknown;
        if (data && typeof data === 'object' && 'error' in data) {
          const maybeError = (data as { error?: unknown }).error;
          if (typeof maybeError === 'string') message = maybeError;
        }
      }
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">
            Sign in to your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Access your meal creation and nutrition tools
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-md">
              {error}
            </div>
          )}
          
          <div>
            <label htmlFor="email" className="sr-only">
              Email address
            </label>
            <input
              id="email"
              name="username_or_email"
              type="email"
              autoComplete="email"
              required
              value={formData.username_or_email}
              onChange={handleChange}
              className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
              placeholder="Email address"
            />
          </div>
          
          <div className="relative">
            <label htmlFor="password" className="sr-only">
              Password
            </label>
            <input
              id="password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              required
              value={formData.password}
              onChange={handleChange}
              className="appearance-none rounded-md relative block w-full px-3 py-2 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
              placeholder="Password"
            />
            <button
              type="button"
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? (
                <EyeSlashIcon className="h-5 w-5 text-gray-400" />
              ) : (
                <EyeIcon className="h-5 w-5 text-gray-400" />
              )}
            </button>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-gradient-primary hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </div>

          <div className="text-center">
            <Link
              href="/auth/register"
              className="text-primary-600 hover:text-primary-500 text-sm"
            >
              Don&apos;t have an account? Sign up
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}