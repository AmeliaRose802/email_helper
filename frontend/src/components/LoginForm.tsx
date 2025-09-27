// Enhanced login form component with validation
import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate, useLocation } from 'react-router-dom';
import { useLoginMutation } from '@/services/authApi';
import { useAppDispatch } from '@/hooks/redux';
import { loginStart, loginSuccess, loginFailure } from '@/store/authSlice';
import { getAuthErrorMessage, getRedirectPath, getUserFromToken } from '@/utils/authUtils';
import type { UserLogin } from '@/types/auth';

// Validation schema
const loginSchema = z.object({
  username: z
    .string()
    .min(1, 'Username is required')
    .min(3, 'Username must be at least 3 characters'),
  password: z
    .string()
    .min(1, 'Password is required')
    .min(6, 'Password must be at least 6 characters'),
  remember: z.boolean(),
});

type LoginFormData = z.infer<typeof loginSchema>;

const LoginForm: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useAppDispatch();
  const [login, { isLoading }] = useLoginMutation();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: '',
      password: '',
      remember: false,
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    setServerError(null);
    dispatch(loginStart());

    try {
      const credentials: UserLogin = {
        username: data.username,
        password: data.password,
      };

      const result = await login(credentials).unwrap();
      
      // Extract user from token or create mock user
      let user = getUserFromToken(result.access_token);
      if (!user || !user.id) {
        user = {
          id: 1,
          username: data.username,
          email: `${data.username}@example.com`,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
      }

      dispatch(
        loginSuccess({
          user: user as any,
          tokens: result,
          remember: data.remember,
        })
      );

      // Redirect to intended destination
      const redirectPath = getRedirectPath(location.state);
      navigate(redirectPath, { replace: true });
    } catch (error) {
      const errorMessage = getAuthErrorMessage(error);
      setServerError(errorMessage);
      dispatch(loginFailure(errorMessage));
      
      // Reset form password on error
      reset({ username: data.username, remember: data.remember, password: '' });
    }
  };

  const isFormLoading = isLoading || isSubmitting;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="login-form" noValidate>
      <div className="form-group">
        <label htmlFor="username" className="form-label">
          Username <span className="required" aria-label="required">*</span>
        </label>
        <input
          {...register('username')}
          type="text"
          id="username"
          className={`form-input ${errors.username ? 'error' : ''}`}
          disabled={isFormLoading}
          autoComplete="username"
          aria-describedby={errors.username ? 'username-error' : undefined}
          aria-invalid={!!errors.username}
        />
        {errors.username && (
          <p id="username-error" className="error-message" role="alert">
            {errors.username.message}
          </p>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="password" className="form-label">
          Password <span className="required" aria-label="required">*</span>
        </label>
        <input
          {...register('password')}
          type="password"
          id="password"
          className={`form-input ${errors.password ? 'error' : ''}`}
          disabled={isFormLoading}
          autoComplete="current-password"
          aria-describedby={errors.password ? 'password-error' : undefined}
          aria-invalid={!!errors.password}
        />
        {errors.password && (
          <p id="password-error" className="error-message" role="alert">
            {errors.password.message}
          </p>
        )}
      </div>

      <div className="form-group checkbox-group">
        <label htmlFor="remember" className="checkbox-label">
          <input
            {...register('remember')}
            type="checkbox"
            id="remember"
            className="checkbox-input"
            disabled={isFormLoading}
          />
          <span className="checkbox-text">Remember me</span>
        </label>
        <p className="help-text">
          Keep me signed in on this device
        </p>
      </div>

      {serverError && (
        <div className="error-message server-error" role="alert">
          {serverError}
        </div>
      )}

      <button
        type="submit"
        disabled={isFormLoading}
        className={`login-button ${isFormLoading ? 'loading' : ''}`}
        aria-describedby="login-button-status"
      >
        {isFormLoading ? (
          <>
            <span className="spinner" aria-hidden="true"></span>
            <span>Signing in...</span>
          </>
        ) : (
          'Sign In'
        )}
      </button>

      <div className="form-footer">
        <p className="help-text">
          Use your account credentials to access Email Helper.
        </p>
      </div>
    </form>
  );
};

export default LoginForm;