import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  UserResponse,
  UserProfileResponse,
  ApiLogEntry,
  ScopeLevel,
} from '../types';
import { authApiService } from '../services/authApi';
import { DEFAULT_BACKEND_URL } from '../data/seedAccounts';

interface AuthContextType {
  user: UserResponse | UserProfileResponse | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  backendUrl: string;
  tunnelStatus: 'checking' | 'online' | 'offline';
  tunnelLatency: number | null;
  tunnelError: string | null;
  useMockMode: boolean;
  apiLogs: ApiLogEntry[];
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
  reloadProfile: () => Promise<void>;
  updateBackendUrl: (url: string) => void;
  resetBackendUrl: () => void;
  pingBackend: () => Promise<void>;
  clearLogs: () => void;
  setUseMockMode: (val: boolean) => void;
  runPhcApprovalTest: () => Promise<{ success: boolean; data?: unknown; error?: string }>;
  runDistrictAccessTest: (districtId?: string) => Promise<{ success: boolean; data?: unknown; error?: string }>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserResponse | UserProfileResponse | null>(() => {
    try {
      const savedUser = localStorage.getItem('hsc_user');
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });

  const [accessToken, setAccessToken] = useState<string | null>(() => {
    return localStorage.getItem('hsc_access_token');
  });

  const [refreshToken, setRefreshToken] = useState<string | null>(() => {
    return localStorage.getItem('hsc_refresh_token');
  });

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [backendUrl, setBackendUrl] = useState<string>(() => authApiService.getBaseUrl());
  const [tunnelStatus, setTunnelStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [tunnelLatency, setTunnelLatency] = useState<number | null>(null);
  const [tunnelError, setTunnelError] = useState<string | null>(null);
  const [useMockMode, setUseMockMode] = useState<boolean>(false);
  const [apiLogs, setApiLogs] = useState<ApiLogEntry[]>([]);

  // Wire up request logger
  useEffect(() => {
    authApiService.setLogger((log) => {
      setApiLogs((prev) => [log, ...prev.slice(0, 49)]); // keep latest 50 logs
    });
  }, []);

  // Ping backend to assess tunnel connectivity
  const pingBackend = useCallback(async () => {
    setTunnelStatus('checking');
    setTunnelError(null);
    const start = performance.now();
    try {
      const res = await authApiService.checkHealth();
      const latency = Math.round(performance.now() - start);
      setTunnelLatency(latency);
      setTunnelStatus(res.status === 'healthy' ? 'online' : 'offline');
    } catch (err: unknown) {
      setTunnelStatus('offline');
      setTunnelLatency(null);
      const errMsg = err instanceof Error ? err.message : 'Tunnel unreachable';
      setTunnelError(errMsg);
    }
  }, []);

  useEffect(() => {
    pingBackend();
  }, [backendUrl, pingBackend]);

  const updateBackendUrl = useCallback((newUrl: string) => {
    authApiService.setBaseUrl(newUrl);
    setBackendUrl(authApiService.getBaseUrl());
  }, []);

  const resetBackendUrl = useCallback(() => {
    authApiService.resetBaseUrl();
    setBackendUrl(DEFAULT_BACKEND_URL);
  }, []);

  const clearLogs = useCallback(() => {
    setApiLogs([]);
  }, []);

  // Login handler
  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);

    try {
      if (useMockMode) {
        const mockResponse = authApiService.mockLogin(email, password);
        setAccessToken(mockResponse.access_token);
        setRefreshToken(mockResponse.refresh_token);
        setUser(mockResponse.user);
        localStorage.setItem('hsc_access_token', mockResponse.access_token);
        localStorage.setItem('hsc_refresh_token', mockResponse.refresh_token);
        localStorage.setItem('hsc_user', JSON.stringify(mockResponse.user));
        return;
      }

      const res = await authApiService.login(email, password);
      setAccessToken(res.access_token);
      setRefreshToken(res.refresh_token);
      setUser(res.user);
      localStorage.setItem('hsc_access_token', res.access_token);
      localStorage.setItem('hsc_refresh_token', res.refresh_token);
      localStorage.setItem('hsc_user', JSON.stringify(res.user));
      // Mark tunnel as verified online upon successful response
      setTunnelStatus('online');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Authentication failed';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Reload live profile
  const reloadProfile = async () => {
    if (!accessToken) return;
    setIsLoading(true);
    setError(null);
    try {
      if (useMockMode) {
        // In mock mode, keep current user
        return;
      }
      const profile = await authApiService.getMe(accessToken);
      setUser(profile);
      localStorage.setItem('hsc_user', JSON.stringify(profile));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch user profile';
      setError(msg);
      // If token expired, attempt refresh
      if (msg.toLowerCase().includes('401') || msg.toLowerCase().includes('unauthorized')) {
        await refreshSession();
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Refresh token handler
  const refreshSession = async () => {
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    setIsLoading(true);
    setError(null);
    try {
      if (useMockMode) {
        const dummyToken = `eyJhbGciOiJIUzI1NiJ9.refreshed.${Date.now()}`;
        setAccessToken(dummyToken);
        localStorage.setItem('hsc_access_token', dummyToken);
        return;
      }
      const res = await authApiService.refreshToken(refreshToken);
      setAccessToken(res.access_token);
      localStorage.setItem('hsc_access_token', res.access_token);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to refresh token';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Logout handler
  const logout = async () => {
    setIsLoading(true);
    try {
      if (!useMockMode && refreshToken) {
        await authApiService.logout(refreshToken).catch((err) => {
          console.warn('Logout API warning:', err);
        });
      }
    } finally {
      setAccessToken(null);
      setRefreshToken(null);
      setUser(null);
      setError(null);
      localStorage.removeItem('hsc_access_token');
      localStorage.removeItem('hsc_refresh_token');
      localStorage.removeItem('hsc_user');
      setIsLoading(false);
    }
  };

  // RBAC test handler: Approve PHC
  const runPhcApprovalTest = async () => {
    if (!accessToken) return { success: false, error: 'Not authenticated' };
    try {
      if (useMockMode) {
        const hasPerm = user?.permissions?.includes('approve_phc_request');
        if (!hasPerm) {
          throw new Error('403 Forbidden: Missing required permission "approve_phc_request"');
        }
        return {
          success: true,
          data: {
            status: 'authorized',
            action: 'approve_phc_request',
            user_id: user?.id,
            scope_level: user?.scope_level,
          },
        };
      }
      const data = await authApiService.testApprovePhcRequest(accessToken);
      return { success: true, data };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Permission check failed';
      return { success: false, error: msg };
    }
  };

  // Multi-tenant Geographic Isolation test: District Data
  const runDistrictAccessTest = async (districtId?: string) => {
    if (!accessToken) return { success: false, error: 'Not authenticated' };
    const targetDistrict = districtId || 'd58e3e4a-921c-43f1-a185-123456789abc';
    try {
      if (useMockMode) {
        const isPlatformOrNat =
          user?.scope_level === ('PLATFORM' as ScopeLevel) ||
          user?.scope_level === ('NATIONAL' as ScopeLevel);
        const isMatchingDistrict = user?.scope_id === targetDistrict;

        if (isPlatformOrNat || isMatchingDistrict) {
          return {
            success: true,
            data: {
              status: 'authorized',
              district_id: targetDistrict,
              access: isPlatformOrNat ? 'full_platform_access' : 'tenant_authorized',
              bypassed: isPlatformOrNat,
            },
          };
        } else {
          throw new Error(
            '403 Forbidden: Cannot access data from a different district (Geographic Isolation Enforced)'
          );
        }
      }
      const data = await authApiService.testDistrictData(accessToken, targetDistrict);
      return { success: true, data };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'District data access check failed';
      return { success: false, error: msg };
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        refreshToken,
        isAuthenticated: !!accessToken,
        isLoading,
        error,
        backendUrl,
        tunnelStatus,
        tunnelLatency,
        tunnelError,
        useMockMode,
        apiLogs,
        login,
        logout,
        refreshSession,
        reloadProfile,
        updateBackendUrl,
        resetBackendUrl,
        pingBackend,
        clearLogs,
        setUseMockMode,
        runPhcApprovalTest,
        runDistrictAccessTest,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
