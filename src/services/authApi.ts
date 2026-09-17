import {
  LoginResponse,
  UserProfileResponse,
  RefreshResponse,
  LogoutResponse,
  HealthResponse,
  ApiLogEntry,
} from '../types';
import { DEFAULT_BACKEND_URL, SEED_ACCOUNTS, DEFAULT_PASSWORD } from '../data/seedAccounts';

export class AuthApiService {
  private baseUrl: string;
  private onLogCallback?: (log: ApiLogEntry) => void;

  constructor() {
    const saved = typeof window !== 'undefined' ? localStorage.getItem('hsc_backend_url') : null;
    this.baseUrl = saved || import.meta.env.VITE_BACKEND_URL || DEFAULT_BACKEND_URL;
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  public setBaseUrl(url: string): void {
    let cleanUrl = url.trim();
    if (cleanUrl.endsWith('/')) {
      cleanUrl = cleanUrl.slice(0, -1);
    }
    this.baseUrl = cleanUrl;
    if (typeof window !== 'undefined') {
      localStorage.setItem('hsc_backend_url', cleanUrl);
    }
  }

  public resetBaseUrl(): void {
    this.setBaseUrl(DEFAULT_BACKEND_URL);
  }

  public setLogger(callback: (log: ApiLogEntry) => void): void {
    this.onLogCallback = callback;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    payload?: unknown
  ): Promise<T> {
    const fullUrl = `${this.baseUrl}${endpoint}`;
    const startTime = performance.now();
    const method = (options.method || 'GET') as ApiLogEntry['method'];

    const headers: Record<string, string> = {
      Accept: 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    };

    if (payload && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    let response: Response;
    let durationMs = 0;

    try {
      response = await fetch(fullUrl, {
        ...options,
        headers,
        body: payload ? JSON.stringify(payload) : options.body,
      });
      durationMs = Math.round(performance.now() - startTime);
    } catch (err: unknown) {
      durationMs = Math.round(performance.now() - startTime);
      const networkErrorMsg = err instanceof Error ? err.message : 'Network request failed';
      const logEntry: ApiLogEntry = {
        id: Math.random().toString(36).substring(2, 9),
        timestamp: new Date().toLocaleTimeString(),
        method,
        url: fullUrl,
        status: 0,
        statusText: 'Network Error',
        durationMs,
        requestPayload: payload,
        error: networkErrorMsg,
      };
      this.onLogCallback?.(logEntry);
      throw new Error(`Connection failed to ${this.baseUrl}: ${networkErrorMsg}`);
    }

    const contentType = response.headers.get('content-type') || '';
    let parsedBody: unknown = null;
    let rawText = '';

    try {
      if (contentType.includes('application/json')) {
        parsedBody = await response.json();
      } else {
        rawText = await response.text();
        parsedBody = rawText;
      }
    } catch (parseError) {
      console.warn('Failed to parse response body', parseError);
    }

    const logEntry: ApiLogEntry = {
      id: Math.random().toString(36).substring(2, 9),
      timestamp: new Date().toLocaleTimeString(),
      method,
      url: fullUrl,
      status: response.status,
      statusText: response.statusText || (response.ok ? 'OK' : 'Error'),
      durationMs,
      requestPayload: payload,
      responseBody: parsedBody,
    };

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

      if (typeof parsedBody === 'object' && parsedBody !== null && 'detail' in parsedBody) {
        const detail = (parsedBody as { detail: unknown }).detail;
        if (typeof detail === 'string') {
          errorMessage = detail;
        } else if (Array.isArray(detail)) {
          errorMessage = detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join(', ');
        } else {
          errorMessage = JSON.stringify(detail);
        }
      } else if (typeof rawText === 'string' && rawText.includes('Cloudflare Tunnel error')) {
        errorMessage = 'Cloudflare Tunnel Error 1033: Tunnel is unreachable or cloudflared is disconnected on the backend server.';
      } else if (rawText && rawText.length < 200) {
        errorMessage = rawText;
      }

      logEntry.error = errorMessage;
      this.onLogCallback?.(logEntry);
      throw new Error(errorMessage);
    }

    this.onLogCallback?.(logEntry);
    return parsedBody as T;
  }

  // 1. Health check
  public async checkHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health', { method: 'GET' });
  }

  // 2. Login
  public async login(email: string, password: string): Promise<LoginResponse> {
    return this.request<LoginResponse>(
      '/auth/login',
      { method: 'POST' },
      { email, password }
    );
  }

  // 3. User Profile (/auth/me)
  public async getMe(accessToken: string): Promise<UserProfileResponse> {
    return this.request<UserProfileResponse>('/auth/me', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
  }

  // 4. Token Refresh
  public async refreshToken(refreshToken: string): Promise<RefreshResponse> {
    return this.request<RefreshResponse>(
      '/auth/refresh',
      { method: 'POST' },
      { refresh_token: refreshToken }
    );
  }

  // 5. Logout
  public async logout(refreshToken: string): Promise<LogoutResponse> {
    return this.request<LogoutResponse>(
      '/auth/logout',
      { method: 'POST' },
      { refresh_token: refreshToken }
    );
  }

  // 6. Test PHC Approval (RBAC test)
  public async testApprovePhcRequest(accessToken: string): Promise<{ status: string; action: string; user_id: string; scope_level: string }> {
    return this.request('/auth/test/approve-phc-request', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
  }

  // 7. Test District Data (Multi-tenant geographic isolation test)
  public async testDistrictData(accessToken: string, districtId: string): Promise<{ status: string; district_id: string; access: string; bypassed?: boolean }> {
    return this.request(`/auth/test/district-data/${districtId}`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
  }

  // ===================== MOCK FALLBACK HANDLER =====================
  // Allows testing when the ephemeral tunnel is offline or in development
  public mockLogin(email: string, password: string): LoginResponse {
    const account = SEED_ACCOUNTS.find(
      (a) => a.email.toLowerCase() === email.toLowerCase().trim()
    );

    if (!account) {
      if (password !== DEFAULT_PASSWORD && password !== 'admin123' && password.length < 8) {
        throw new Error('Invalid email or password (min 8 characters)');
      }
    }

    const matchedAccount = account || {
      email,
      name: email.split('@')[0],
      role: 'Custom User',
      scope: 'NATIONAL' as const,
      description: 'Demo User Account',
      permissions: ['view_national', 'view_district'],
    };

    const dummyUuid = 'f47ac10b-58cc-4372-a567-0e02b2c3d479';
    const mockAccessToken = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mock.${btoa(
      JSON.stringify({
        sub: dummyUuid,
        email: matchedAccount.email,
        roles: [matchedAccount.role],
        scope_level: matchedAccount.scope,
        exp: Math.floor(Date.now() / 1000) + 15 * 60,
      })
    )}`;

    const mockRefreshToken = `rt_${Math.random().toString(36).substring(2)}${Math.random().toString(36).substring(2)}`;

    const logEntry: ApiLogEntry = {
      id: Math.random().toString(36).substring(2, 9),
      timestamp: new Date().toLocaleTimeString(),
      method: 'POST',
      url: `${this.baseUrl}/auth/login [Mock Mode]`,
      status: 200,
      statusText: 'OK (Mocked)',
      durationMs: 45,
      requestPayload: { email, password: '••••••••' },
      responseBody: {
        access_token: '[MOCK_JWT_ACCESS_TOKEN]',
        token_type: 'bearer',
        user: {
          email: matchedAccount.email,
          full_name: matchedAccount.name,
          roles: [matchedAccount.role],
          scope_level: matchedAccount.scope,
        },
      },
    };
    this.onLogCallback?.(logEntry);

    return {
      access_token: mockAccessToken,
      refresh_token: mockRefreshToken,
      token_type: 'bearer',
      user: {
        id: dummyUuid,
        email: matchedAccount.email,
        full_name: matchedAccount.name,
        is_active: true,
        scope_level: matchedAccount.scope,
        scope_id: matchedAccount.scope === 'PLATFORM' ? null : 'd58e3e4a-921c-43f1-a185-123456789abc',
        roles: [
          {
            id: 'role-1',
            name: matchedAccount.role,
            description: matchedAccount.description,
          },
        ],
        permissions: matchedAccount.permissions,
        created_at: new Date(Date.now() - 86400000 * 30).toISOString(),
        updated_at: new Date().toISOString(),
      },
    };
  }
}

export const authApiService = new AuthApiService();
