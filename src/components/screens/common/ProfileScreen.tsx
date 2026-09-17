import React, { useState } from 'react';
import { UserResponse, RoleTier } from '../../../types';
import { getTierBadge } from '../../../utils/rbac';
import { User, Phone, Globe, Shield, CheckCircle2, Key, Bell, Save } from 'lucide-react';

interface ProfileScreenProps {
  user?: UserResponse | null;
  tier?: RoleTier;
  onUpdateUser?: (updated: Partial<UserResponse>) => void;
  language?: string;
  onLanguageChange?: (lang: string) => void;
  currentLanguage?: string;
  onUpdateLanguage?: (lang: string) => void;
}

export const ProfileScreen: React.FC<ProfileScreenProps> = ({
  user,
  tier = 'L5',
  onUpdateUser,
  language,
  onLanguageChange,
  currentLanguage,
  onUpdateLanguage,
}) => {
  const safeTier: RoleTier = (['L0', 'L1', 'L2', 'L3', 'L5'].includes(tier as string) ? tier : 'L5') as RoleTier;
  const badge = getTierBadge(safeTier) || {
    label: 'L5 — PHC User',
    bg: 'bg-teal-950/60',
    text: 'text-teal-300',
    border: 'border-teal-700/60',
    desc: 'Primary Health Centre Inventory, Beds & Daily Care Operations',
  };

  const activeUser: UserResponse = user || {
    id: 'usr-default',
    email: 'officer.phc@jharkhand.health.gov.in',
    full_name: 'Dr. Priya Sharma (Medical Officer)',
    roles: [{ id: 'r1', name: 'Medical Officer in-charge' }],
    scope_level: 'PHC',
    scope_id: 'JH-RAN-ORM-PHC01',
    permissions: ['INVENTORY_READ', 'INVENTORY_WRITE', 'BED_UPDATE', 'INDENT_CREATE'],
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const activeLang = language || currentLanguage || 'en';
  const handleLangSelect = onLanguageChange || onUpdateLanguage || (() => {});

  const [fullName, setFullName] = useState(activeUser.full_name || 'Health Officer');
  const [phone, setPhone] = useState(activeUser.phone || '+91 94311 88421');
  const [emailNotification, setEmailNotification] = useState(true);
  const [smsAlerts, setSmsAlerts] = useState(true);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (onUpdateUser) {
      onUpdateUser({ full_name: fullName, phone });
    }
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-10" id="profile-screen-container">
      {/* Header card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 relative overflow-hidden" id="profile-header-card">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-emerald-600/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 text-2xl font-bold">
              {(fullName || 'U').charAt(0)}
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-xl font-bold text-slate-100">{fullName}</h1>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${badge?.bg || 'bg-teal-950/60'} ${badge?.text || 'text-teal-300'} ${badge?.border || 'border-teal-700/60'}`}
                >
                  {badge?.label || 'PHC Operator'}
                </span>
              </div>
              <p className="text-sm text-slate-400 mt-0.5">{activeUser.email}</p>
              <p className="text-xs text-slate-500 mt-1">Scope: <span className="text-slate-300 font-mono uppercase">{activeUser.scope_level}</span> {activeUser.scope_id ? `(${activeUser.scope_id.slice(0, 8)}...)` : '(Global)'}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-950/60 border border-emerald-800 text-emerald-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Active Session
            </span>
          </div>
        </div>
      </div>

      {savedSuccess && (
        <div className="p-4 bg-emerald-950/80 border border-emerald-700/60 rounded-lg text-emerald-300 text-sm flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          Profile preferences updated successfully!
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left 2 cols: Profile Form */}
        <div className="md:col-span-2 space-y-6">
          <form onSubmit={handleSave} className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-5" id="profile-edit-form">
            <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
              <User className="w-4 h-4 text-emerald-400" />
              Personal Details & Contact
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Full Name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Phone Number (SMS Alerts)</label>
                <div className="relative">
                  <Phone className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
                    placeholder="+91 94311 00000"
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Official Email Address</label>
              <input
                type="email"
                value={activeUser.email}
                disabled
                className="w-full px-3 py-2 bg-slate-950/50 border border-slate-800 rounded-lg text-sm text-slate-400 cursor-not-allowed"
              />
              <p className="text-xs text-slate-500 mt-1">Managed centrally by National HSC Directory.</p>
            </div>

            <div className="pt-2 border-t border-slate-800">
              <h3 className="text-sm font-medium text-slate-300 mb-3 flex items-center gap-2">
                <Globe className="w-4 h-4 text-cyan-400" />
                Language & Localization
              </h3>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { code: 'en', label: 'English', sub: 'Default' },
                  { code: 'hi', label: 'हिंदी (Hindi)', sub: 'Rajbhasha' },
                  { code: 'bn', label: 'বাংলা (Bengali)', sub: 'Regional' },
                ].map((l) => (
                  <button
                    key={l.code}
                    type="button"
                    onClick={() => handleLangSelect(l.code)}
                    className={`p-3 rounded-lg border text-left transition-all ${
                      activeLang === l.code
                        ? 'bg-emerald-950/50 border-emerald-500 text-emerald-300'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <div className="font-medium text-sm text-slate-200">{l.label}</div>
                    <div className="text-xs text-slate-500">{l.sub}</div>
                  </button>
                ))}
              </div>
            </div>

            <div className="pt-2 border-t border-slate-800">
              <h3 className="text-sm font-medium text-slate-300 mb-3 flex items-center gap-2">
                <Bell className="w-4 h-4 text-amber-400" />
                Alert Notification Channels
              </h3>
              <div className="space-y-3">
                <label className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg cursor-pointer">
                  <div>
                    <div className="text-sm text-slate-200">Critical Stock-Out Email Notifications</div>
                    <div className="text-xs text-slate-500">Receive instant alerts when facility stock breaches emergency levels</div>
                  </div>
                  <input
                    type="checkbox"
                    checked={emailNotification}
                    onChange={(e) => setEmailNotification(e.target.checked)}
                    className="w-4 h-4 text-emerald-600 bg-slate-900 border-slate-700 rounded focus:ring-emerald-500"
                  />
                </label>
                <label className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg cursor-pointer">
                  <div>
                    <div className="text-sm text-slate-200">SMS & Cold Chain Excursion Alarms</div>
                    <div className="text-xs text-slate-500">Urgent SMS dispatch when ILR refrigerator rises above 8°C</div>
                  </div>
                  <input
                    type="checkbox"
                    checked={smsAlerts}
                    onChange={(e) => setSmsAlerts(e.target.checked)}
                    className="w-4 h-4 text-emerald-600 bg-slate-900 border-slate-700 rounded focus:ring-emerald-500"
                  />
                </label>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                id="save-profile-btn"
                className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium flex items-center gap-2 transition-colors shadow-sm"
              >
                <Save className="w-4 h-4" />
                Save Changes
              </button>
            </div>
          </form>
        </div>

        {/* Right col: RBAC Permissions & Security */}
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4" id="rbac-summary-card">
            <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
              <Shield className="w-4 h-4 text-purple-400" />
              Role & Permissions
            </h2>

            <div className="bg-slate-950 border border-slate-800 rounded-lg p-3">
              <div className="text-xs text-slate-500">Assigned Primary Role</div>
              <div className="text-sm font-semibold text-slate-200 mt-0.5">
                {activeUser.roles && activeUser.roles.length > 0 ? (typeof activeUser.roles[0] === 'string' ? activeUser.roles[0] : activeUser.roles[0].name) : 'Medical Officer'}
              </div>
              <div className="text-xs text-slate-400 mt-1">{badge?.desc || 'Health System Facility Operator'}</div>
            </div>

            <div>
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Granted RBAC Scopes</div>
              <div className="flex flex-wrap gap-1.5 max-h-56 overflow-y-auto pr-1">
                {activeUser.permissions && activeUser.permissions.length > 0 ? (
                  activeUser.permissions.map((perm) => (
                    <span
                      key={perm}
                      className="px-2 py-0.5 bg-slate-800 border border-slate-700 rounded text-[11px] text-slate-300 font-mono"
                    >
                      {perm}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-slate-500">No custom permissions granted.</span>
                )}
              </div>
            </div>

            <div className="pt-2 border-t border-slate-800">
              <div className="text-xs font-medium text-slate-400 mb-2 flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5 text-slate-400" />
                Security Credentials
              </div>
              <p className="text-xs text-slate-500 mb-3">Password last updated: 14 days ago. Two-Factor OTP authentication active.</p>
              <button
                type="button"
                onClick={() => setSavedSuccess(true)}
                className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium border border-slate-700 transition-colors"
              >
                Change Account Password
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
