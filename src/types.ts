export type ScopeLevel = 'PLATFORM' | 'NATIONAL' | 'STATE' | 'DISTRICT' | 'PHC' | 'platform' | 'national' | 'state' | 'district' | 'phc';

export type RoleTier = 'L0' | 'L1' | 'L2' | 'L3' | 'L5';

export interface RoleInfo {
  id: string;
  name: string;
  description?: string;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  scope_level: ScopeLevel;
  scope_id: string | null;
  roles: RoleInfo[];
  permissions: string[];
  created_at: string;
  updated_at: string;
  phone?: string;
  language?: string;
}

export interface UserProfileResponse {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  scope_level: ScopeLevel;
  scope_id: string | null;
  roles: string[];
  permissions: string[];
  phone?: string;
  language?: string;
}

export type User = UserResponse | UserProfileResponse | {
  id?: string;
  email?: string;
  full_name?: string;
  scope_level?: ScopeLevel | string;
  scope_id?: string | null;
  roles?: Array<{ name: string } | string>;
  permissions?: string[];
  [key: string]: any;
};

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: UserResponse;
}

export interface RefreshResponse {
  access_token: string;
  token_type: string;
}

export interface LogoutResponse {
  success: boolean;
  message: string;
}

export interface HealthResponse {
  status: string;
  service?: string;
  environment?: string;
}

export interface ApiLogEntry {
  id: string;
  timestamp: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  url: string;
  status: number;
  statusText: string;
  durationMs: number;
  requestPayload?: unknown;
  responseBody?: unknown;
  error?: string;
  headers?: Record<string, string>;
}

// ---------------- Screen Navigation Types ----------------
export type CommonScreenKey = 'profile' | 'notifications';

export type L0ScreenKey =
  | 'admin_dashboard'
  | 'user_management'
  | 'fl_orchestration'
  | 'node_management'
  | 'audit_logs'
  | 'system_settings';

export type L1ScreenKey =
  | 'national_dashboard'
  | 'cross_state_redistribution'
  | 'national_alerts'
  | 'reports_analytics'
  | 'fl_overview';

export type L2ScreenKey =
  | 'state_dashboard'
  | 'state_redistribution'
  | 'state_alerts'
  | 'state_forecast'
  | 'district_management'
  | 'fl_participation';

export type L3ScreenKey =
  | 'district_dashboard'
  | 'redistribution_recommendations'
  | 'indent_approvals'
  | 'district_forecast'
  | 'phc_management'
  | 'district_alerts'
  | 'fl_node_status';

export type L5ScreenKey =
  | 'phc_dashboard'
  | 'inventory_management'
  | 'bed_management'
  | 'staff_attendance'
  | 'stock_request'
  | 'redistribution_requests'
  | 'forecast_view'
  | 'patient_footfall'
  | 'reports'
  | 'alerts';

export type ActiveScreen = CommonScreenKey | L0ScreenKey | L1ScreenKey | L2ScreenKey | L3ScreenKey | L5ScreenKey;

export interface NavItem {
  id: ActiveScreen;
  key?: string;
  label: string;
  labelHi?: string;
  icon: string;
  badge?: number | string;
  badgeColor?: string;
  section?: string;
}

// ---------------- Domain Data Types ----------------
export type StockStatus = 'CRITICAL' | 'REORDER' | 'ADEQUATE';

export interface InventoryItem {
  id: string;
  drugCode?: string;
  code?: string;
  name: string;
  category: string;
  dosage?: string;
  currentStock: number;
  minThreshold?: number;
  minRequired?: number;
  maxThreshold?: number;
  unit: string;
  batchNumber: string;
  expiryDate: string;
  status: StockStatus;
  lastUpdated?: string;
  coldChain?: boolean;
  storageCondition?: string;
  daysOfSupply?: number;
}

export interface BedCategory {
  id: string;
  name: string;
  total: number;
  occupied: number;
  available: number;
  oxygenSupported?: boolean;
  ventilatorSupported?: boolean;
}

export interface StaffMember {
  id: string;
  name: string;
  role: 'Medical Officer' | 'Staff Nurse' | 'Pharmacist' | 'Lab Technician' | 'ANM / ASHA' | string;
  phone: string;
  status: 'PRESENT' | 'ON_DUTY' | 'ABSENT' | 'ON_LEAVE';
  shift: 'Morning' | 'Evening' | 'Night' | 'General' | string;
  checkInTime?: string;
  checkIn?: string;
}

export interface IndentRequest {
  id: string;
  indentNumber: string;
  phcId?: string;
  phcName: string;
  districtId?: string;
  districtName?: string;
  drugCode: string;
  drugName: string;
  requestedQty: number;
  recommendedQty: number;
  approvedQty?: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'DISPATCHED' | 'DELIVERED';
  createdAt: string;
  urgency: 'HIGH' | 'MEDIUM' | 'EMERGENCY' | 'URGENT' | 'ROUTINE' | string;
  notes?: string;
}

export interface RedistributionTransfer {
  id: string;
  transferNumber: string;
  tier: 'INTER_STATE' | 'INTRA_STATE' | 'INTER_PHC';
  sourceFacility: string;
  destinationFacility: string;
  item: string;
  quantity: number;
  unit: string;
  urgency: 'EMERGENCY' | 'HIGH' | 'NORMAL' | 'URGENT';
  status: 'RECOMMENDED' | 'PENDING_APPROVAL' | 'APPROVED' | 'IN_TRANSIT' | 'RECEIVED' | 'REJECTED' | 'DELIVERED';
  distanceKm: number;
  costSavingsEst: string;
  createdAt: string;
  approvedBy?: string;
}

export interface AlertNotification {
  id: string;
  title: string;
  description: string;
  type: 'STOCK_OUT' | 'EXPIRY' | 'COLD_CHAIN' | 'OUTBREAK_SIGNAL' | 'TRANSFER_REQUEST' | 'SYSTEM' | 'COLD_CHAIN_EXCURSION' | string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  timestamp: string;
  facility?: string;
  district?: string;
  state?: string;
  isRead: boolean;
  actionRequired?: boolean;
}

export interface FlRound {
  roundNumber: number;
  status: 'IN_PROGRESS' | 'COMPLETED' | 'AGGREGATING';
  globalAccuracy: number;
  loss: number;
  participatingNodes: number;
  totalNodes: number;
  startTime: string;
  completedTime?: string;
  convergenceProgress: number;
}
