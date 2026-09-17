export interface SeedAccount {
  email: string;
  name: string;
  role: string;
  scope: 'PLATFORM' | 'NATIONAL' | 'STATE' | 'DISTRICT' | 'PHC';
  tier: 'L0' | 'L1' | 'L2' | 'L3' | 'L5';
  description: string;
  permissions: string[];
}

export const SEED_ACCOUNTS: SeedAccount[] = [
  {
    email: 'superadmin@hsc.gov.in',
    name: 'National Super Admin',
    role: 'Super Admin',
    tier: 'L0',
    scope: 'PLATFORM',
    description: 'L0 — Full administrative access, FL orchestration, and user management',
    permissions: [
      'manage_users',
      'manage_fl',
      'view_all',
      'manage_permissions',
      'view_audit_logs',
      'view_system_health',
      'approve_phc_request',
      'view_district',
    ],
  },
  {
    email: 'national.viewer@hsc.gov.in',
    name: 'National Analytics Viewer',
    role: 'National Viewer',
    tier: 'L1',
    scope: 'NATIONAL',
    description: 'L1 — National overview, inter-state transfers, and nationwide alerts',
    permissions: [
      'view_national',
      'approve_inter_state_transfer',
      'view_national_forecast',
      'view_district',
    ],
  },
  {
    email: 'state.approver.jh@hsc.gov.in',
    name: 'Jharkhand State Approver',
    role: 'State Approver',
    tier: 'L2',
    scope: 'STATE',
    description: 'L2 — State-level dashboard, district-to-district redistribution, state alerts',
    permissions: [
      'view_state',
      'approve_inter_district_transfer',
      'view_state_forecast',
      'escalate_to_national',
      'view_fl_model_status',
    ],
  },
  {
    email: 'district.approver.ran@hsc.gov.in',
    name: 'Ranchi District Approver',
    role: 'District Approver',
    tier: 'L3',
    scope: 'DISTRICT',
    description: 'L3 — Ranchi district dashboard, PHC indent approvals, inter-PHC transfers',
    permissions: [
      'view_district',
      'approve_intra_district_transfer',
      'escalate_to_state',
      'view_district_forecast',
    ],
  },
  {
    email: 'phc.approver.ori_phc@hsc.gov.in',
    name: 'Ormanjhi PHC Medical Officer',
    role: 'PHC Approver',
    tier: 'L5',
    scope: 'PHC',
    description: 'L5 — PHC inventory, beds, staff, indent stock requests, and local transfers',
    permissions: [
      'create_inventory',
      'view_own_phc',
      'request_stock',
      'update_beds',
      'mark_attendance',
      'report_stock_out',
      'approve_phc_request',
      'approve_redistribution_to_phc',
    ],
  },
  {
    email: 'phc.operator.ori_phc@hsc.gov.in',
    name: 'Ormanjhi PHC Operator',
    role: 'PHC Operator',
    tier: 'L5',
    scope: 'PHC',
    description: 'L5 — Ground staff: stock entry, bed updates, and indent requisition',
    permissions: [
      'create_inventory',
      'view_own_phc',
      'request_stock',
      'update_beds',
      'mark_attendance',
      'report_stock_out',
    ],
  },
];

export const DEFAULT_PASSWORD = 'Test@123';
export const DEFAULT_BACKEND_URL = 'https://moderators-bears-efficient-instead.trycloudflare.com';

