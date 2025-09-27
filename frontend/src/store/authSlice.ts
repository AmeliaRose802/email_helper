// Authentication slice for state management
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import type { AuthState, User, Token } from '@/types/auth';
import { tokenStorage } from '@/services/tokenStorage';
import { getUserFromToken } from '@/utils/authUtils';

// Initialize auth state from stored tokens
const initializeFromStorage = (): Partial<AuthState> => {
  const tokens = tokenStorage.getTokens();
  if (tokens && !tokenStorage.isTokenExpired(tokens.accessToken)) {
    const user = getUserFromToken(tokens.accessToken);
    return {
      user: user as User || null,
      token: tokens.accessToken,
      refreshToken: tokens.refreshToken,
      isAuthenticated: !!user,
      isLoading: false,
      error: null,
    };
  }
  
  // Clear invalid tokens
  tokenStorage.clearTokens();
  return {
    user: null,
    token: null,
    refreshToken: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
  };
};

const initialState: AuthState = {
  ...initializeFromStorage(),
} as AuthState;

// Async thunk for initializing authentication state
export const initializeAuth = createAsyncThunk(
  'auth/initialize',
  async (_, { rejectWithValue }) => {
    try {
      const tokens = tokenStorage.getTokens();
      if (!tokens || tokenStorage.isTokenExpired(tokens.accessToken)) {
        tokenStorage.clearTokens();
        return null;
      }

      // Validate token with backend by fetching user profile
      const response = await fetch('/auth/me', {
        headers: { 
          'Authorization': `Bearer ${tokens.accessToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const user = await response.json();
        return { user, tokens };
      } else {
        // Token is invalid, clear storage
        tokenStorage.clearTokens();
        return null;
      }
    } catch (error) {
      console.warn('Auth initialization failed:', error);
      tokenStorage.clearTokens();
      return rejectWithValue('Session initialization failed');
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    loginStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },
    loginSuccess: (state, action: PayloadAction<{ user: User; tokens: Token; remember?: boolean }>) => {
      const { user, tokens, remember = false } = action.payload;
      state.user = user;
      state.token = tokens.access_token;
      state.refreshToken = tokens.refresh_token;
      state.isAuthenticated = true;
      state.isLoading = false;
      state.error = null;

      // Persist tokens to storage
      tokenStorage.setTokens(tokens.access_token, tokens.refresh_token, remember);
    },
    loginFailure: (state, action: PayloadAction<string>) => {
      state.user = null;
      state.token = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      state.isLoading = false;
      state.error = action.payload;

      // Clear tokens from storage
      tokenStorage.clearTokens();
    },
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      state.isLoading = false;
      state.error = null;

      // Clear tokens from storage
      tokenStorage.clearTokens();
    },
    refreshTokenSuccess: (state, action: PayloadAction<string>) => {
      state.token = action.payload;
      state.isAuthenticated = true;

      // Update token in storage while preserving refresh token
      const tokens = tokenStorage.getTokens();
      if (tokens) {
        const storageType = tokenStorage.getStorageType();
        const remember = storageType === 'localStorage';
        tokenStorage.setTokens(action.payload, tokens.refreshToken, remember);
      }
    },
    setUser: (state, action: PayloadAction<User>) => {
      state.user = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(initializeAuth.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(initializeAuth.fulfilled, (state, action) => {
        if (action.payload) {
          state.user = action.payload.user;
          state.token = action.payload.tokens.accessToken;
          state.refreshToken = action.payload.tokens.refreshToken;
          state.isAuthenticated = true;
        }
        state.isLoading = false;
      })
      .addCase(initializeAuth.rejected, (state, action) => {
        state.user = null;
        state.token = null;
        state.refreshToken = null;
        state.isAuthenticated = false;
        state.isLoading = false;
        state.error = action.payload as string || 'Authentication initialization failed';
      });
  },
});

export const {
  loginStart,
  loginSuccess,
  loginFailure,
  logout,
  refreshTokenSuccess,
  setUser,
  clearError,
  setLoading,
} = authSlice.actions;

export default authSlice.reducer;
