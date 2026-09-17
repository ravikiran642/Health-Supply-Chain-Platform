import React, { useState, useEffect } from 'react';
import {
  Shield,
  User,
  LogOut,
  Bell,
  Globe2,
  ChevronRight,
  Menu,
  X,
  Sparkles,
  LayoutDashboard,
  Users,
  BrainCircuit,
  Server,
  FileText,
  Settings,
  ArrowLeftRight,
  AlertTriangle,
  FileBarChart,
  MapPin,
  Building2,
  TrendingUp,
  Layers,
  FileCheck,
  Stethoscope,
  Activity,
  Package,
  Bed,
  UserCheck,
  Send,
  LineChart,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { RoleTier, AlertNotification } from '../types';
import { resolveUserTier, getTierNavItems, getDefaultScreenForTier, ROLE_TIER_METADATA } from '../utils/rbac';
import { SEED_ACCOUNTS } from '../data/seedAccounts';
import { INITIAL_INVENTORY, INITIAL_BEDS, INITIAL_STAFF, INITIAL_ALERTS } from '../data/mockAppData';

// Common screens
import { ProfileScreen } from './screens/common/ProfileScreen';
import { NotificationsScreen } from './screens/common/NotificationsScreen';

// L0 Screens
import { AdminDashboard } from './screens/l0/AdminDashboard';
import { UserManagement } from './screens/l0/UserManagement';
import { FlOrchestration } from './screens/l0/FlOrchestration';
import { NodeManagement } from './screens/l0/NodeManagement';
import { AuditLogs } from './screens/l0/AuditLogs';
import { SystemSettings } from './screens/l0/SystemSettings';

// L1 Screens
import { NationalDashboard } from './screens/l1/NationalDashboard';
import { CrossStateRedistribution } from './screens/l1/CrossStateRedistribution';
import { NationalAlerts } from './screens/l1/NationalAlerts';
import { NationalReports } from './screens/l1/NationalReports';
import { FlGlobalOverview } from './screens/l1/FlGlobalOverview';

// L2 Screens
import { StateDashboard } from './screens/l2/StateDashboard';
import { StateRedistribution } from './screens/l2/StateRedistribution';
import { DistrictManagement } from './screens/l2/DistrictManagement';
import { StateAlerts } from './screens/l2/StateAlerts';
import { StateForecast } from './screens/l2/StateForecast';
import { FlStateParticipation } from './screens/l2/FlStateParticipation';

// L3 Screens
import { DistrictDashboard } from './screens/l3/DistrictDashboard';
import { IndentApprovals } from './screens/l3/IndentApprovals';
import { RedistributionRecommendations } from './screens/l3/RedistributionRecommendations';
import { DistrictForecast } from './screens/l3/DistrictForecast';
import { PhcManagement } from './screens/l3/PhcManagement';
import { DistrictAlerts } from './screens/l3/DistrictAlerts';
import { FlDistrictNode } from './screens/l3/FlDistrictNode';

// L5 Screens
import { PhcDashboard } from './screens/l5/PhcDashboard';
import { InventoryManagement } from './screens/l5/InventoryManagement';
import { BedManagement } from './screens/l5/BedManagement';
import { StaffAttendance } from './screens/l5/StaffAttendance';
import { StockRequestIndent } from './screens/l5/StockRequestIndent';
import { PhcRedistribution } from './screens/l5/PhcRedistribution';
import { PhcForecastView } from './screens/l5/PhcForecastView';
import { PatientFootfall } from './screens/l5/PatientFootfall';
import { PhcReports } from './screens/l5/PhcReports';
import { PhcAlerts } from './screens/l5/PhcAlerts';

export const DashboardScreen: React.FC = () => {
  const { user, logout, login } = useAuth();

  // Tier determination & Override for tester convenience
  const initialTier = resolveUserTier(user);
  const [activeTier, setActiveTier] = useState<RoleTier>(initialTier);
  const [currentScreen, setCurrentScreen] = useState<string>(getDefaultScreenForTier(initialTier));
  const [language, setLanguage] = useState<string>(user?.language_pref || 'English');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // App-level mutable state for PHC operations & alerts
  const [inventory, setInventory] = useState(INITIAL_INVENTORY || []);
  const [beds, setBeds] = useState(INITIAL_BEDS || []);
  const [staff, setStaff] = useState(INITIAL_STAFF || []);
  const [alerts, setAlerts] = useState<AlertNotification[]>(INITIAL_ALERTS || []);

  const handleMarkAsRead = (id: string) => {
    setAlerts((prev) => (prev || []).map((a) => (a.id === id ? { ...a, isRead: true } : a)));
  };

  const handleMarkAllAsRead = () => {
    setAlerts((prev) => (prev || []).map((a) => ({ ...a, isRead: true })));
  };

  // Sync tier when authenticated user changes
  useEffect(() => {
    const tier = resolveUserTier(user);
    setActiveTier(tier);
    setCurrentScreen(getDefaultScreenForTier(tier));
  }, [user]);

  // Handle manual role switcher (for testing other tiers seamlessly)
  const handleSwitchTier = (newTier: RoleTier) => {
    setActiveTier(newTier);
    setCurrentScreen(getDefaultScreenForTier(newTier));
  };

  const navItems = getTierNavItems(activeTier);
  const tierMeta = ROLE_TIER_METADATA[activeTier] || ROLE_TIER_METADATA['L5'];

  // Helper icon lookup for nav items
  const renderNavIcon = (iconName: string) => {
    switch (iconName) {
      case 'LayoutDashboard':
        return <LayoutDashboard className="w-4 h-4" />;
      case 'Users':
        return <Users className="w-4 h-4" />;
      case 'BrainCircuit':
        return <BrainCircuit className="w-4 h-4" />;
      case 'Server':
        return <Server className="w-4 h-4" />;
      case 'FileText':
        return <FileText className="w-4 h-4" />;
      case 'Settings':
        return <Settings className="w-4 h-4" />;
      case 'ArrowLeftRight':
        return <ArrowLeftRight className="w-4 h-4" />;
      case 'AlertTriangle':
        return <AlertTriangle className="w-4 h-4" />;
      case 'FileBarChart':
        return <FileBarChart className="w-4 h-4" />;
      case 'MapPin':
        return <MapPin className="w-4 h-4" />;
      case 'Building2':
        return <Building2 className="w-4 h-4" />;
      case 'TrendingUp':
        return <TrendingUp className="w-4 h-4" />;
      case 'Layers':
        return <Layers className="w-4 h-4" />;
      case 'FileCheck':
        return <FileCheck className="w-4 h-4" />;
      case 'Stethoscope':
        return <Stethoscope className="w-4 h-4" />;
      case 'Activity':
        return <Activity className="w-4 h-4" />;
      case 'Package':
        return <Package className="w-4 h-4" />;
      case 'Bed':
        return <Bed className="w-4 h-4" />;
      case 'UserCheck':
        return <UserCheck className="w-4 h-4" />;
      case 'Send':
        return <Send className="w-4 h-4" />;
      case 'LineChart':
        return <LineChart className="w-4 h-4" />;
      default:
        return <LayoutDashboard className="w-4 h-4" />;
    }
  };

  // Render the active view
  const renderMainContent = () => {
    // Common Screens
    if (currentScreen === 'profile') {
      return (
        <ProfileScreen
          user={user}
          tier={activeTier}
          onUpdateUser={(_updated) => {}}
          language={language}
          onLanguageChange={(l) => setLanguage(l)}
          currentLanguage={language}
          onUpdateLanguage={(l) => setLanguage(l)}
        />
      );
    }
    if (currentScreen === 'notifications') {
      return (
        <NotificationsScreen
          alerts={alerts}
          tier={activeTier}
          onMarkAsRead={handleMarkAsRead}
          onMarkAllAsRead={handleMarkAllAsRead}
          onNavigateToScreen={(screen) => setCurrentScreen(screen)}
          onNavigate={(screen) => setCurrentScreen(screen)}
        />
      );
    }

    // L0 Screens
    if (activeTier === 'L0') {
      switch (currentScreen) {
        case 'admin_dashboard':
          return <AdminDashboard onNavigate={(screen) => setCurrentScreen(screen)} />;
        case 'user_management':
          return <UserManagement />;
        case 'fl_orchestration':
          return <FlOrchestration />;
        case 'node_management':
          return <NodeManagement />;
        case 'audit_logs':
          return <AuditLogs />;
        case 'system_settings':
          return <SystemSettings />;
        default:
          return <AdminDashboard onNavigate={(screen) => setCurrentScreen(screen)} />;
      }
    }

    // L1 Screens
    if (activeTier === 'L1') {
      switch (currentScreen) {
        case 'national_dashboard':
          return <NationalDashboard onNavigate={(screen) => setCurrentScreen(screen)} />;
        case 'cross_state_redistribution':
          return <CrossStateRedistribution />;
        case 'national_alerts':
          return <NationalAlerts />;
        case 'national_reports':
          return <NationalReports />;
        case 'fl_global_overview':
          return <FlGlobalOverview />;
        default:
          return <NationalDashboard onNavigate={(screen) => setCurrentScreen(screen)} />;
      }
    }

    // L2 Screens
    if (activeTier === 'L2') {
      switch (currentScreen) {
        case 'state_dashboard':
          return <StateDashboard onNavigate={(screen) => setCurrentScreen(screen)} />;
        case 'state_redistribution':
          return <StateRedistribution />;
        case 'district_management':
          return <DistrictManagement />;
        case 'state_alerts':
          return <StateAlerts />;
        case 'state_forecast':
          return <StateForecast />;
        case 'fl_state_participation':
          return <FlStateParticipation />;
        default:
          return <StateDashboard onNavigate={(screen) => setCurrentScreen(screen)} />;
      }
    }

    // L3 Screens
    if (activeTier === 'L3') {
      switch (currentScreen) {
        case 'district_dashboard':
          return <DistrictDashboard onNavigate={(screen) => setCurrentScreen(screen)} />;
        case 'indent_approvals':
          return <IndentApprovals />;
        case 'redistribution_recommendations':
          return <RedistributionRecommendations />;
        case 'district_forecast':
          return <DistrictForecast />;
        case 'phc_management':
          return <PhcManagement />;
        case 'district_alerts':
          return <DistrictAlerts />;
        case 'fl_district_node':
          return <FlDistrictNode />;
        default:
          return <DistrictDashboard onNavigate={(screen) => setCurrentScreen(screen)} />;
      }
    }

    // L5 Screens
    if (activeTier === 'L5') {
      switch (currentScreen) {
        case 'phc_dashboard':
          return (
            <PhcDashboard
              inventory={inventory}
              beds={beds}
              staff={staff}
              onNavigate={(s) => setCurrentScreen(s)}
            />
          );
        case 'inventory_management':
          return (
            <InventoryManagement
              inventory={inventory}
              onUpdateInventory={(updated) => setInventory(updated)}
            />
          );
        case 'bed_management':
          return (
            <BedManagement
              beds={beds}
              onUpdateBeds={(updated) => setBeds(updated)}
            />
          );
        case 'staff_attendance':
          return (
            <StaffAttendance
              staff={staff}
              onUpdateStaff={(updated) => setStaff(updated)}
            />
          );
        case 'stock_request':
          return <StockRequestIndent inventory={inventory} />;
        case 'redistribution_requests':
          return <PhcRedistribution />;
        case 'forecast_view':
          return <PhcForecastView />;
        case 'patient_footfall':
          return <PatientFootfall />;
        case 'phc_reports':
          return <PhcReports />;
        case 'alerts':
          return <PhcAlerts />;
        default:
          return (
            <PhcDashboard
              inventory={inventory}
              beds={beds}
              staff={staff}
              onNavigate={(s) => setCurrentScreen(s)}
            />
          );
      }
    }

    return (
      <div className="p-8 text-center text-slate-400">
        Screen not found. Select a screen from the sidebar.
      </div>
    );
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-slate-950 text-slate-100 flex flex-col md:flex-row">
      {/* Role Switcher & Sub-Header Bar */}
      <div className="w-full bg-slate-900 border-b border-slate-800 px-4 py-2 flex flex-wrap items-center justify-between text-xs md:hidden">
        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 rounded font-bold border ${tierMeta.badgeColor}`}>
            {tierMeta.tier}
          </span>
          <span className="font-medium text-slate-200">{tierMeta.title}</span>
        </div>
        <button
          type="button"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-1.5 rounded bg-slate-800 text-slate-300"
        >
          {isMobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
        </button>
      </div>

      {/* Left Sidebar Shell */}
      <aside
        className={`${
          isMobileMenuOpen ? 'block' : 'hidden'
        } md:block w-full md:w-64 bg-slate-900/90 border-r border-slate-800 flex flex-col shrink-0 z-20`}
      >
        {/* User / Facility Info in Sidebar */}
        <div className="p-4 border-b border-slate-800 space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-500/15 border border-teal-500/30 flex items-center justify-center text-teal-400 font-bold shrink-0">
              {user?.full_name ? user.full_name.charAt(0) : 'U'}
            </div>
            <div className="overflow-hidden">
              <div className="font-semibold text-xs text-slate-100 truncate">
                {user?.full_name || 'HSC Operator'}
              </div>
              <div className="text-[11px] text-slate-400 truncate font-mono">
                {user?.email || 'operator@hsc.gov.in'}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className={`px-2 py-0.5 rounded text-[11px] font-bold border ${tierMeta.badgeColor}`}>
              {tierMeta.tier} &bull; {tierMeta.title}
            </span>
            <span className="text-[10px] text-slate-500 font-mono">
              {activeTier === 'L5' ? 'Ormanjhi' : activeTier === 'L3' ? 'Ranchi' : activeTier === 'L2' ? 'Jharkhand' : 'Grid'}
            </span>
          </div>

          {/* Quick Demo Switcher Dropdown (to test each role effortlessly) */}
          <div className="pt-2 border-t border-slate-800/80">
            <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
              Switch Role View (Demo RBAC)
            </label>
            <select
              value={activeTier}
              onChange={(e) => handleSwitchTier(e.target.value as RoleTier)}
              className="w-full px-2 py-1.5 bg-slate-950 border border-slate-700 rounded text-xs text-slate-200 focus:outline-none focus:border-teal-500"
            >
              <option value="L0">L0 — System / FL Admin</option>
              <option value="L1">L1 — National Health Officer</option>
              <option value="L2">L2 — State Health Officer (JH)</option>
              <option value="L3">L3 — District Health Officer (Ranchi)</option>
              <option value="L5">L5 — PHC Pharmacist (Ormanjhi)</option>
            </select>
          </div>
        </div>

        {/* Dynamic Navigation for this user role ONLY */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500 px-3 py-1">
            {tierMeta.title} Screens
          </div>

          {navItems.map((item) => {
            const isActive = currentScreen === item.key;
            return (
              <button
                key={item.key}
                type="button"
                onClick={() => {
                  setCurrentScreen(item.key);
                  setIsMobileMenuOpen(false);
                }}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                  isActive
                    ? 'bg-teal-500/15 text-teal-300 border border-teal-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <span className={isActive ? 'text-teal-400' : 'text-slate-400'}>
                    {renderNavIcon(item.icon)}
                  </span>
                  <span className="truncate">{item.label}</span>
                </div>
                {item.badge && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}

          {/* Common Screens Divider */}
          <div className="pt-4 mt-4 border-t border-slate-800 text-[10px] font-bold uppercase tracking-wider text-slate-500 px-3 py-1">
            Account & Utilities
          </div>

          {/* Notifications */}
          <button
            type="button"
            onClick={() => {
              setCurrentScreen('notifications');
              setIsMobileMenuOpen(false);
            }}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
              currentScreen === 'notifications'
                ? 'bg-teal-500/15 text-teal-300 border border-teal-500/40'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <div className="flex items-center gap-2.5">
              <Bell className="w-4 h-4 text-slate-400" />
              <span>Alerts & Notifications</span>
            </div>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-red-950 text-red-300 border border-red-800 font-mono font-bold">
              {(alerts || []).filter((a) => !a.isRead).length}
            </span>
          </button>

          {/* Profile Screen */}
          <button
            type="button"
            onClick={() => {
              setCurrentScreen('profile');
              setIsMobileMenuOpen(false);
            }}
            className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
              currentScreen === 'profile'
                ? 'bg-teal-500/15 text-teal-300 border border-teal-500/40'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <User className="w-4 h-4 text-slate-400" />
            <span>Profile & Settings</span>
          </button>
        </nav>

        {/* Bottom Language Switcher & Logout */}
        <div className="p-3 border-t border-slate-800 bg-slate-950/40 space-y-2">
          <div className="flex items-center justify-between px-2 text-xs text-slate-400">
            <span className="flex items-center gap-1 text-[11px]">
              <Globe2 className="w-3.5 h-3.5 text-teal-400" />
              Language:
            </span>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="px-2 py-1 bg-slate-900 border border-slate-800 rounded text-xs text-slate-300 focus:outline-none focus:border-teal-500"
            >
              <option value="English">English</option>
              <option value="हिंदी">हिंदी</option>
              <option value="বাংলা">বাংলা</option>
            </select>
          </div>

          <button
            type="button"
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-rose-950/30 hover:bg-rose-950/60 text-rose-300 border border-rose-800/40 text-xs font-medium transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Logout Session</span>
          </button>
        </div>
      </aside>

      {/* Main Content Viewport */}
      <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto max-h-[calc(100vh-4rem)]">
        {renderMainContent()}
      </main>
    </div>
  );
};
