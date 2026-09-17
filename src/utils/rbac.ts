import { RoleTier, ScopeLevel, NavItem, ActiveScreen, User } from '../types';

export function getRoleTier(scopeLevel?: ScopeLevel | string, roles?: Array<{ name: string } | string>): RoleTier {
  const normScope = (scopeLevel || '').toUpperCase();
  if (normScope === 'PLATFORM') return 'L0';
  if (normScope === 'NATIONAL') return 'L1';
  if (normScope === 'STATE') return 'L2';
  if (normScope === 'DISTRICT') return 'L3';
  if (normScope === 'PHC') return 'L5';

  // Fallback by role name
  const roleNames = (roles || []).map((r) => (typeof r === 'string' ? r : r.name).toLowerCase());
  if (roleNames.some((r) => r.includes('super admin') || r.includes('platform'))) return 'L0';
  if (roleNames.some((r) => r.includes('national'))) return 'L1';
  if (roleNames.some((r) => r.includes('state'))) return 'L2';
  if (roleNames.some((r) => r.includes('district'))) return 'L3';
  if (roleNames.some((r) => r.includes('phc') || r.includes('operator') || r.includes('medical officer'))) return 'L5';

  return 'L5';
}

export function resolveUserTier(user?: User | null): RoleTier {
  if (!user) return 'L5';
  return getRoleTier(user.scope_level, user.roles);
}

export const ROLE_TIER_METADATA: Record<
  RoleTier,
  { tier: RoleTier; title: string; badgeColor: string; description: string }
> = {
  L0: {
    tier: 'L0',
    title: 'System / FL Admin',
    badgeColor: 'bg-purple-950 text-purple-300 border-purple-800',
    description: 'System health, user accounts, FL orchestration rounds, node approval, and audit logs',
  },
  L1: {
    tier: 'L1',
    title: 'National Health Officer',
    badgeColor: 'bg-blue-950 text-blue-300 border-blue-800',
    description: 'Pan-India supply monitoring, cross-state redistribution approvals, and global FL accuracy',
  },
  L2: {
    tier: 'L2',
    title: 'State Health Officer',
    badgeColor: 'bg-indigo-950 text-indigo-300 border-indigo-800',
    description: 'State district heatmap, intra-state transfer queue, and state forecast aggregation',
  },
  L3: {
    tier: 'L3',
    title: 'District Health Officer',
    badgeColor: 'bg-emerald-950 text-emerald-300 border-emerald-800',
    description: 'PHC inventory tracking, indent approval queue, and inter-PHC redistribution AI',
  },
  L5: {
    tier: 'L5',
    title: 'PHC User / Pharmacist',
    badgeColor: 'bg-amber-950 text-amber-300 border-amber-800',
    description: 'Local inventory dispensing, bed occupancy, staff roster, and stock indent requests',
  },
};

export function getTierBadge(tier?: RoleTier): { label: string; bg: string; text: string; border: string; desc: string } {
  switch (tier) {
    case 'L0':
      return {
        label: 'L0 — System / FL Admin',
        bg: 'bg-purple-950/60',
        text: 'text-purple-300',
        border: 'border-purple-700/60',
        desc: 'Full Platform Admin & Federated Learning Orchestrator',
      };
    case 'L1':
      return {
        label: 'L1 — National Health Officer',
        bg: 'bg-blue-950/60',
        text: 'text-blue-300',
        border: 'border-blue-700/60',
        desc: 'National Logistics & Inter-State Health Supply Chain',
      };
    case 'L2':
      return {
        label: 'L2 — State Health Officer',
        bg: 'bg-emerald-950/60',
        text: 'text-emerald-300',
        border: 'border-emerald-700/60',
        desc: 'State Operations & Intra-State District Coordination',
      };
    case 'L3':
      return {
        label: 'L3 — District Health Officer',
        bg: 'bg-amber-950/60',
        text: 'text-amber-300',
        border: 'border-amber-700/60',
        desc: 'District Hub & Primary Health Centre Indent Approvals',
      };
    case 'L5':
    default:
      return {
        label: 'L5 — PHC User',
        bg: 'bg-teal-950/60',
        text: 'text-teal-300',
        border: 'border-teal-700/60',
        desc: 'Primary Health Centre Inventory, Beds & Daily Care Operations',
      };
  }
}

export function getTierNavItems(tier?: RoleTier): NavItem[] {
  switch (tier) {
    case 'L0':
      return [
        { id: 'admin_dashboard', key: 'admin_dashboard', label: 'Admin Dashboard', labelHi: 'सिस्टम डैशबोर्ड', icon: 'LayoutDashboard', section: 'Overview' },
        { id: 'user_management', key: 'user_management', label: 'User Management', labelHi: 'उपयोगकर्ता प्रबंधन', icon: 'Users', section: 'Administration' },
        { id: 'fl_orchestration', key: 'fl_orchestration', label: 'FL Orchestration', labelHi: 'एफएल ऑर्केस्ट्रेशन', icon: 'Cpu', badge: 'Round #14', badgeColor: 'bg-purple-600', section: 'Federated Learning' },
        { id: 'node_management', key: 'node_management', label: 'Node Management', labelHi: 'नोड प्रबंधन', icon: 'Server', section: 'Federated Learning' },
        { id: 'audit_logs', key: 'audit_logs', label: 'Audit Logs', labelHi: 'ऑडिट लॉग्स', icon: 'ShieldCheck', section: 'Security' },
        { id: 'system_settings', key: 'system_settings', label: 'System Settings', labelHi: 'सिस्टम सेटिंग्स', icon: 'Settings', section: 'Configuration' },
      ];

    case 'L1':
      return [
        { id: 'national_dashboard', key: 'national_dashboard', label: 'National Dashboard', labelHi: 'राष्ट्रीय डैशबोर्ड', icon: 'Globe', section: 'National Overview' },
        { id: 'cross_state_redistribution', key: 'cross_state_redistribution', label: 'Inter-State Transfers', labelHi: 'अंतर-राज्यीय स्थानांतरण', icon: 'ArrowLeftRight', badge: '1 Pending', badgeColor: 'bg-amber-600', section: 'Redistribution' },
        { id: 'national_alerts', key: 'national_alerts', label: 'National Alerts', labelHi: 'राष्ट्रीय अलर्ट', icon: 'AlertTriangle', badge: '2 Critical', badgeColor: 'bg-red-600', section: 'Surveillance' },
        { id: 'fl_overview', key: 'fl_overview', label: 'FL Global Model', labelHi: 'वैश्विक मॉडल स्थिति', icon: 'BrainCircuit', section: 'AI Intelligence' },
        { id: 'reports_analytics', key: 'reports_analytics', label: 'Reports & Analytics', labelHi: 'रिपोर्ट एवं विश्लेषण', icon: 'FileBarChart', section: 'Analytics' },
      ];

    case 'L2':
      return [
        { id: 'state_dashboard', key: 'state_dashboard', label: 'State Dashboard', labelHi: 'राज्य डैशबोर्ड', icon: 'MapPin', section: 'State Overview' },
        { id: 'district_management', key: 'district_management', label: 'District Nodes', labelHi: 'जिला नोड्स', icon: 'Building2', section: 'Monitoring' },
        { id: 'state_redistribution', key: 'state_redistribution', label: 'State Redistribution', labelHi: 'राज्य पुनर्वितरण कतार', icon: 'ArrowLeftRight', badge: '1 Action', badgeColor: 'bg-amber-600', section: 'Supply Chain' },
        { id: 'state_alerts', key: 'state_alerts', label: 'State Alerts', labelHi: 'राज्य अलर्ट', icon: 'AlertOctagon', badge: '1 Alert', badgeColor: 'bg-red-600', section: 'Surveillance' },
        { id: 'state_forecast', key: 'state_forecast', label: 'State Forecast', labelHi: 'मांग पूर्वानुमान', icon: 'TrendingUp', section: 'Planning' },
        { id: 'fl_participation', key: 'fl_participation', label: 'FL State Contribution', labelHi: 'एफएल राज्य योगदान', icon: 'Layers', section: 'AI Intelligence' },
      ];

    case 'L3':
      return [
        { id: 'district_dashboard', key: 'district_dashboard', label: 'District Dashboard', labelHi: 'जिला डैशबोर्ड', icon: 'Building', section: 'District Hub' },
        { id: 'redistribution_recommendations', key: 'redistribution_recommendations', label: 'Redistribution AI', labelHi: 'पुनर्वितरण अनुशंसाएं', icon: 'ArrowRightLeft', badge: '1 Rec', badgeColor: 'bg-emerald-600', section: 'Logistics' },
        { id: 'indent_approvals', key: 'indent_approvals', label: 'Indent Approvals', labelHi: 'इंडेंट अनुमोदन', icon: 'FileCheck', badge: '2 Requests', badgeColor: 'bg-amber-600', section: 'Logistics' },
        { id: 'district_forecast', key: 'district_forecast', label: 'District 30D Forecast', labelHi: '30-दिवसीय पूर्वानुमान', icon: 'LineChart', section: 'Forecasting' },
        { id: 'phc_management', key: 'phc_management', label: 'PHC Facilities', labelHi: 'पीएचसी सुविधाएं', icon: 'Stethoscope', section: 'Facilities' },
        { id: 'district_alerts', key: 'district_alerts', label: 'District Alerts', labelHi: 'जिला अलर्ट', icon: 'Bell', badge: '1 Crit', badgeColor: 'bg-red-600', section: 'Surveillance' },
        { id: 'fl_node_status', key: 'fl_node_status', label: 'District Edge Node', labelHi: 'जिला एज नोड', icon: 'Activity', section: 'FL Node' },
      ];

    case 'L5':
    default:
      return [
        { id: 'phc_dashboard', key: 'phc_dashboard', label: 'PHC Dashboard', labelHi: 'पीएचसी डैशबोर्ड', icon: 'Hospital', section: 'Facility Status' },
        { id: 'inventory_management', key: 'inventory_management', label: 'Drug Inventory', labelHi: 'दवा स्टॉक प्रबंधन', icon: 'Package', badge: '3 Low', badgeColor: 'bg-red-600', section: 'Clinical Stock' },
        { id: 'bed_management', key: 'bed_management', label: 'Bed Occupancy', labelHi: 'बेड प्रबंधन', icon: 'Bed', section: 'Facility Status' },
        { id: 'staff_attendance', key: 'staff_attendance', label: 'Staff Attendance', labelHi: 'कर्मचारी उपस्थिति', icon: 'UserCheck', section: 'Staff' },
        { id: 'alerts', key: 'alerts', label: 'Alerts & Cold Chain', labelHi: 'अलर्ट व कोल्ड चेन', icon: 'AlertCircle', badge: '2 New', badgeColor: 'bg-amber-600', section: 'Safety' },
        { id: 'stock_request', key: 'stock_request', label: 'Stock Indent (Requisition)', labelHi: 'दवा मांग (इंडेंट)', icon: 'Send', section: 'Supplies' },
        { id: 'redistribution_requests', key: 'redistribution_requests', label: 'Redistribution Transfers', labelHi: 'स्थानांतरण अनुरोध', icon: 'Truck', section: 'Supplies' },
        { id: 'forecast_view', key: 'forecast_view', label: 'Expected Demand & Beds', labelHi: 'मांग व बेड पूर्वानुमान', icon: 'Sparkles', section: 'Intelligence' },
        { id: 'patient_footfall', key: 'patient_footfall', label: 'Patient Footfall', labelHi: 'मरीज़ आवक (OPD/IPD)', icon: 'UsersRound', section: 'Records' },
        { id: 'reports', key: 'reports', label: 'PHC Reports', labelHi: 'पीएचसी रिपोर्ट', icon: 'FileText', section: 'Records' },
      ];
  }
}

export function getDefaultScreenForTier(tier?: RoleTier): ActiveScreen {
  switch (tier) {
    case 'L0':
      return 'admin_dashboard';
    case 'L1':
      return 'national_dashboard';
    case 'L2':
      return 'state_dashboard';
    case 'L3':
      return 'district_dashboard';
    case 'L5':
    default:
      return 'phc_dashboard';
  }
}
