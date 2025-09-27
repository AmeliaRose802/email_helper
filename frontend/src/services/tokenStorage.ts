// Secure token storage service for JWT tokens
export interface TokenStorage {
  setTokens(accessToken: string, refreshToken: string, remember?: boolean): void;
  getTokens(): { accessToken: string; refreshToken: string } | null;
  clearTokens(): void;
  isTokenExpired(token: string): boolean;
}

class TokenStorageService implements TokenStorage {
  private readonly ACCESS_TOKEN_KEY = 'email_helper_access_token';
  private readonly REFRESH_TOKEN_KEY = 'email_helper_refresh_token';

  /**
   * Store tokens in localStorage (remember=true) or sessionStorage (remember=false)
   */
  setTokens(accessToken: string, refreshToken: string, remember: boolean = false): void {
    const storage = remember ? localStorage : sessionStorage;
    
    // Clear tokens from both storages first to avoid duplicates
    this.clearTokens();
    
    storage.setItem(this.ACCESS_TOKEN_KEY, accessToken);
    storage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
  }

  /**
   * Get tokens from localStorage or sessionStorage
   */
  getTokens(): { accessToken: string; refreshToken: string } | null {
    // Check localStorage first, then sessionStorage
    const accessToken = localStorage.getItem(this.ACCESS_TOKEN_KEY) || 
                       sessionStorage.getItem(this.ACCESS_TOKEN_KEY);
    const refreshToken = localStorage.getItem(this.REFRESH_TOKEN_KEY) || 
                        sessionStorage.getItem(this.REFRESH_TOKEN_KEY);
    
    if (accessToken && refreshToken) {
      return { accessToken, refreshToken };
    }
    return null;
  }

  /**
   * Clear all tokens from both localStorage and sessionStorage
   */
  clearTokens(): void {
    localStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    sessionStorage.removeItem(this.ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(this.REFRESH_TOKEN_KEY);
  }

  /**
   * Check if JWT token is expired
   */
  isTokenExpired(token: string): boolean {
    try {
      // Decode JWT payload without verification (client-side check only)
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      
      // Return true if token is expired (with 30 second buffer for network delays)
      return payload.exp && payload.exp < (currentTime + 30);
    } catch (error) {
      // If token can't be parsed, consider it expired
      return true;
    }
  }

  /**
   * Get the storage type where tokens are currently stored
   */
  getStorageType(): 'localStorage' | 'sessionStorage' | null {
    if (localStorage.getItem(this.ACCESS_TOKEN_KEY)) {
      return 'localStorage';
    }
    if (sessionStorage.getItem(this.ACCESS_TOKEN_KEY)) {
      return 'sessionStorage';
    }
    return null;
  }
}

export const tokenStorage = new TokenStorageService();