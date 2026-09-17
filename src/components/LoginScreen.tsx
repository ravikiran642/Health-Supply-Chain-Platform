import React, { useState } from 'react';
import {
  Lock,
  Mail,
  Eye,
  EyeOff,
  ArrowRight,
  ShieldCheck,
  Building2,
  Users,
  AlertCircle,
  Sparkles,
  Info,
  CheckCircle,
  KeyRound,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { SEED_ACCOUNTS, DEFAULT_PASSWORD, DEFAULT_BACKEND_URL } from '../data/seedAccounts';
import { ForgotPasswordModal } from './screens/common/ForgotPasswordModal';

export const LoginScreen: React.FC = () => {
  const {
    login,
    isLoading,
    error,
    backendUrl,
    tunnelStatus,
    tunnelError,
    useMockMode,
    setUseMockMode,
  } = useAuth();

  const [email, setEmail] = useState<string>('superadmin@hsc.gov.in');
  const [password, setPassword] = useState<string>(DEFAULT_PASSWORD);
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [selectedRoleIndex, setSelectedRoleIndex] = useState<number>(0);
  const [isForgotModalOpen, setIsForgotModalOpen] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    try {
      await login(email, password);
    } catch {
      // Error handled in AuthContext
    }
  };

  const handleSelectSeedAccount = (index: number) => {
    const acc = SEED_ACCOUNTS[index];
    setSelectedRoleIndex(index);
    setEmail(acc.email);
    setPassword(DEFAULT_PASSWORD);
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-slate-950 text-slate-100 flex flex-col justify-center py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        
        {/* Left Column: Context & Overview */}
        <div className="lg:col-span-6 space-y-6">
          <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-400 text-xs font-medium">
            <ShieldCheck className="w-4 h-4 text-teal-400" />
            <span>Health Supply Chain Authentication Gateway</span>
          </div>

          <div className="space-y-3">
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-white leading-tight">
              Secure RBAC & Geographic Multi-Tenancy
            </h1>
            <p className="text-slate-400 text-sm leading-relaxed">
              Authenticate via the FastAPI backend to receive cryptographic JWT access pairs, inspect fine-grained permissions, and test multi-tier geographic isolation across India's health network.
            </p>
          </div>

          {/* Backend Connection status banner */}
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400">Target Endpoint:</span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                {backendUrl === DEFAULT_BACKEND_URL ? 'Default URL' : 'Custom URL'}
              </span>
            </div>
            <div className="text-xs font-mono text-teal-300 break-all bg-slate-950 p-2 rounded-lg border border-slate-800">
              {backendUrl}
            </div>

            {tunnelStatus === 'offline' && !useMockMode && (
              <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 text-xs space-y-2">
                <div className="flex items-center space-x-1.5 text-rose-300 font-semibold">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>Cloudflare Tunnel Unreachable (Error 1033)</span>
                </div>
                <p className="text-rose-200/80 text-[11px] leading-relaxed">
                  The host tunnel is currently offline. You can enable <strong>Offline Simulation Mode</strong> below to test the full auth flow immediately, or run your local cloudflared tunnel.
                </p>
                <button
                  type="button"
                  onClick={() => setUseMockMode(true)}
                  className="w-full py-1.5 px-3 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 text-xs font-medium transition flex items-center justify-center space-x-1.5"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Enable Offline Mock Mode for Instant Preview</span>
                </button>
              </div>
            )}

            {useMockMode && (
              <div className="p-2.5 rounded-lg bg-amber-950/30 border border-amber-800/50 text-xs text-amber-300 flex items-center justify-between">
                <div className="flex items-center space-x-1.5">
                  <Sparkles className="w-4 h-4 text-amber-400 shrink-0" />
                  <span>Offline simulation active for UI preview</span>
                </div>
                <button
                  type="button"
                  onClick={() => setUseMockMode(false)}
                  className="text-[11px] underline hover:text-amber-200"
                >
                  Switch to Live
                </button>
              </div>
            )}
          </div>

          {/* Key Specs Pills */}
          <div className="grid grid-cols-2 gap-3 text-xs text-slate-300">
            <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800 flex items-start space-x-2.5">
              <Building2 className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold text-white">5 Scope Tiers</div>
                <div className="text-[11px] text-slate-400">Platform, National, State, District, PHC</div>
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800 flex items-start space-x-2.5">
              <Users className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold text-white">Dual-Token JWT</div>
                <div className="text-[11px] text-slate-400">15m Access + 7d Refresh rotation</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Sign In Card */}
        <div className="lg:col-span-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden p-6 sm:p-8">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-white">Sign In to Account</h2>
              <p className="text-xs text-slate-400 mt-1">
                Enter your credentials or choose a pre-configured role below
              </p>
            </div>

            {/* Quick-Fill Seed Accounts Selector */}
            <div className="mb-6">
              <label className="block text-xs font-medium text-slate-300 mb-2">
                Quick Demo Accounts (Seeded)
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {SEED_ACCOUNTS.map((acc, index) => {
                  const isSelected = selectedRoleIndex === index;
                  return (
                    <button
                      key={acc.email}
                      type="button"
                      onClick={() => handleSelectSeedAccount(index)}
                      className={`px-2.5 py-2 rounded-lg text-left border transition text-xs flex flex-col justify-between ${
                        isSelected
                          ? 'bg-teal-500/15 border-teal-500/60 text-teal-300 ring-1 ring-teal-500/50'
                          : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 text-slate-300'
                      }`}
                    >
                      <span className="font-medium truncate">{acc.role}</span>
                      <span className="text-[10px] text-slate-500 uppercase tracking-wider mt-0.5">
                        {acc.scope}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Login Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Email */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Email Address
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                    <Mail className="w-4 h-4" />
                  </div>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="user@hsc.gov.in"
                    className="w-full pl-10 pr-3.5 py-2.5 bg-slate-950 border border-slate-700/80 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-medium text-slate-300">
                    Password
                  </label>
                  <button
                    type="button"
                    onClick={() => setIsForgotModalOpen(true)}
                    className="text-[11px] text-teal-400 hover:text-teal-300 underline"
                  >
                    Forgot Password?
                  </button>
                </div>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-10 pr-10 py-2.5 bg-slate-950 border border-slate-700/80 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-500 hover:text-slate-300 transition"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Error banner */}
              {error && (
                <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300 flex items-start space-x-2">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
                  <div className="space-y-1">
                    <span className="font-medium">Authentication Error</span>
                    <p className="text-[11px] leading-relaxed text-rose-200/90">{error}</p>
                  </div>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-2.5 px-4 rounded-xl bg-teal-600 hover:bg-teal-500 disabled:bg-teal-800/50 text-white font-medium text-sm transition shadow-lg shadow-teal-900/30 flex items-center justify-center space-x-2"
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Authenticating...</span>
                  </>
                ) : (
                  <>
                    <span>Sign In to HSC Platform</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            <div className="mt-5 pt-4 border-t border-slate-800/80 text-center text-[11px] text-slate-500">
              Calls <code className="text-slate-400">POST /auth/login</code> on{' '}
              <span className="font-mono text-teal-400/90">
                {backendUrl.replace('https://', '')}
              </span>
            </div>
          </div>
        </div>

      </div>

      <ForgotPasswordModal
        isOpen={isForgotModalOpen}
        onClose={() => setIsForgotModalOpen(false)}
      />
    </div>
  );
};
