import React, { useState } from 'react';
import { X, Mail, Phone, KeyRound, CheckCircle2, ArrowRight } from 'lucide-react';

interface ForgotPasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultEmail?: string;
}

export const ForgotPasswordModal: React.FC<ForgotPasswordModalProps> = ({
  isOpen,
  onClose,
  defaultEmail = '',
}) => {
  const [step, setStep] = useState<'REQUEST' | 'OTP' | 'SUCCESS'>('REQUEST');
  const [method, setMethod] = useState<'EMAIL' | 'SMS'>('EMAIL');
  const [email, setEmail] = useState(defaultEmail);
  const [phone, setPhone] = useState('+91 94311 88421');
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  if (!isOpen) return null;

  const handleSendOtp = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      setStep('OTP');
      setOtp('739201'); // pre-fill demo OTP
    }, 600);
  };

  const handleResetPassword = (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      setStep('SUCCESS');
    }, 700);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm" id="forgot-password-modal">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 shadow-2xl relative">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {step === 'REQUEST' && (
          <form onSubmit={handleSendOtp} className="space-y-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-950/60 border border-emerald-700/50 flex items-center justify-center text-emerald-400 mb-2">
              <KeyRound className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-100">Reset Account Password</h3>
              <p className="text-xs text-slate-400 mt-1">
                Enter your registered official email or mobile number to receive a one-time reset code.
              </p>
            </div>

            <div className="flex gap-2 p-1 bg-slate-950 rounded-lg border border-slate-800 text-xs">
              <button
                type="button"
                onClick={() => setMethod('EMAIL')}
                className={`flex-1 py-1.5 rounded font-medium transition-colors flex items-center justify-center gap-1.5 ${
                  method === 'EMAIL' ? 'bg-slate-800 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Mail className="w-3.5 h-3.5" /> Email
              </button>
              <button
                type="button"
                onClick={() => setMethod('SMS')}
                className={`flex-1 py-1.5 rounded font-medium transition-colors flex items-center justify-center gap-1.5 ${
                  method === 'SMS' ? 'bg-slate-800 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Phone className="w-3.5 h-3.5" /> SMS / Mobile
              </button>
            </div>

            {method === 'EMAIL' ? (
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Official HSC Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@hsc.gov.in"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>
            ) : (
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Registered Mobile Number</label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+91 94311 00000"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2 shadow-sm"
            >
              {isLoading ? 'Dispatching OTP...' : 'Send Verification Code'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>
        )}

        {step === 'OTP' && (
          <form onSubmit={handleResetPassword} className="space-y-4">
            <div>
              <h3 className="text-lg font-bold text-slate-100">Verify & Set New Password</h3>
              <p className="text-xs text-slate-400 mt-1">
                Enter the 6-digit verification code sent to your {method.toLowerCase()}.
              </p>
            </div>

            {error && (
              <div className="p-3 bg-red-950/80 border border-red-800 rounded-lg text-red-300 text-xs">
                {error}
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">6-Digit OTP Code</label>
              <input
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                maxLength={6}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-center tracking-widest text-lg font-mono text-emerald-400 focus:outline-none focus:border-emerald-500"
                required
              />
              <p className="text-[11px] text-slate-500 mt-1 text-right">Demo OTP auto-generated: 739201</p>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">New Password</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Confirm New Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
                required
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium transition-colors shadow-sm"
            >
              {isLoading ? 'Updating Password...' : 'Save New Password & Finish'}
            </button>
          </form>
        )}

        {step === 'SUCCESS' && (
          <div className="text-center py-4 space-y-4">
            <div className="w-14 h-14 rounded-full bg-emerald-950/80 border border-emerald-700 flex items-center justify-center text-emerald-400 mx-auto">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-100">Password Reset Complete</h3>
              <p className="text-xs text-slate-400 mt-1">
                Your credentials have been securely updated. You may now log in with your new password.
              </p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium transition-colors shadow-sm"
            >
              Back to Login
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
