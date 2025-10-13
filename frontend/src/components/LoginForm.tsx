// Enhanced login form component with validation
import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useLoginMutation, useInitiateLoginQuery } from '@/services/authApi';
import { useAppDispatch } from '@/hooks/redux';
import { loginStart, loginSuccess, loginFailure } from '@/store/authSlice';
import { getAuthErrorMessage, getRedirectPath, getUserFromToken } from '@/utils/authUtils';

const LoginForm: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useAppDispatch();
  const [login, { isLoading: isLoginLoading }] = useLoginMutation();
  const { data: authUrlData, isLoading: isAuthUrlLoading } = useInitiateLoginQuery();
  const [serverError, setServerError] = useState<string | null>(null);

  // Check for OAuth callback success
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    
    if (token) {
      // User returned from OAuth callback with token
      handleOAuthSuccess(token);
    }
  }, []);

  const handleOAuthSuccess = async (token: string) => {
    dispatch(loginStart());
    
    try {
      // Create user object from token (mock for now)
      const user = {
        id: '1',
        username: 'oauth-user',
        email: 'user@example.com',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      dispatch(
        loginSuccess({
          user: user as any,
          tokens: { access_token: token, refresh_token: '', token_type: 'bearer' },
          remember: false,
        })
      );

      // Redirect to intended destination
      const redirectPath = getRedirectPath(location.state);
      navigate(redirectPath, { replace: true });
    } catch (error) {
      const errorMessage = getAuthErrorMessage(error);
      setServerError(errorMessage);
      dispatch(loginFailure(errorMessage));
    }
  };

  const handleAzureLogin = () => {
    if (authUrlData?.auth_url) {
      // Redirect to Azure AD OAuth flow
      window.location.href = authUrlData.auth_url;
    } else {
      // Fallback for mock authentication
      window.location.href = 'http://localhost:8001/auth/callback';
    }
  };

  const isFormLoading = isAuthUrlLoading;

  return (
    <div className="login-form">
      {serverError && (
        <div className="error-message server-error" role="alert">
          {serverError}
        </div>
      )}

      <button
        type="button"
        onClick={handleAzureLogin}
        disabled={isFormLoading}
        className={`login-button azure-login ${isFormLoading ? 'loading' : ''}`}
        aria-describedby="login-button-status"
      >
        {isFormLoading ? (
          <>
            <span className="spinner" aria-hidden="true"></span>
            <span>Connecting to Azure...</span>
          </>
        ) : (
          <>
            <span className="microsoft-logo" aria-hidden="true">🏢</span>
            <span>Sign in with Microsoft</span>
          </>
        )}
      </button>

      <div className="form-footer">
        <p className="help-text">
          Sign in using your Microsoft Azure Active Directory account to access Email Helper.
        </p>
        <p className="help-text">
          This will redirect you to Microsoft's secure authentication service.
        </p>
      </div>
    </div>
  );
};

export default LoginForm;