import React, { useState } from 'react';
import { Users, UserPlus, Search, Shield, KeyRound, Check, X, RefreshCw } from 'lucide-react';
import { SEED_ACCOUNTS } from '../../../data/seedAccounts';

export const UserManagement: React.FC = () => {
  const [search, setSearch] = useState('');
  const [scopeFilter, setScopeFilter] = useState('ALL');
  const [showAddModal, setShowAddModal] = useState(false);
  const [users, setUsers] = useState(
    SEED_ACCOUNTS.map((acc, idx) => ({
      id: `usr-${idx + 1}`,
      name: acc.name,
      email: acc.email,
      role: acc.role,
      tier: acc.tier,
      scope: acc.scope,
      isActive: true,
      lastLogin: 'Today, 08:30 AM',
    }))
  );

  const [newUserName, setNewUserName] = useState('');
  const [newUserEmail, setNewUserEmail] = useState('');
  const [newUserRole, setNewUserRole] = useState('PHC Operator');
  const [newUserScope, setNewUserScope] = useState('PHC');

  const safeUsers = users || [];
  const filteredUsers = safeUsers.filter((u) => {
    const matchesSearch =
      (u.name || '').toLowerCase().includes(search.toLowerCase()) ||
      (u.email || '').toLowerCase().includes(search.toLowerCase()) ||
      (u.role || '').toLowerCase().includes(search.toLowerCase());
    const matchesScope = scopeFilter === 'ALL' || u.scope === scopeFilter;
    return matchesSearch && matchesScope;
  });

  const handleToggleStatus = (id: string) => {
    setUsers(users.map((u) => (u.id === id ? { ...u, isActive: !u.isActive } : u)));
  };

  const handleCreateUser = (e: React.FormEvent) => {
    e.preventDefault();
    const tierMap: Record<string, 'L0' | 'L1' | 'L2' | 'L3' | 'L5'> = {
      PLATFORM: 'L0',
      NATIONAL: 'L1',
      STATE: 'L2',
      DISTRICT: 'L3',
      PHC: 'L5',
    };
    const created = {
      id: `usr-${Date.now()}`,
      name: newUserName,
      email: newUserEmail,
      role: newUserRole,
      tier: tierMap[newUserScope] || 'L5',
      scope: newUserScope as any,
      isActive: true,
      lastLogin: 'Never',
    };
    setUsers([created, ...users]);
    setShowAddModal(false);
    setNewUserName('');
    setNewUserEmail('');
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-10" id="user-management-screen">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Users className="w-5 h-5 text-purple-400" />
            User & Role Management
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Provision user accounts, assign hierarchical scopes (L0 to L5), configure RBAC permissions, and trigger password resets.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold rounded-lg flex items-center gap-2 transition-colors shadow-sm"
        >
          <UserPlus className="w-4 h-4" />
          Create New User
        </button>
      </div>

      {/* Filter and Search */}
      <div className="flex flex-col sm:flex-row items-center gap-3 justify-between">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by name, email, or role..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-purple-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto text-xs">
          {['ALL', 'PLATFORM', 'NATIONAL', 'STATE', 'DISTRICT', 'PHC'].map((scope) => (
            <button
              key={scope}
              type="button"
              onClick={() => setScopeFilter(scope)}
              className={`px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-colors ${
                scopeFilter === scope
                  ? 'bg-purple-600 text-white'
                  : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
              }`}
            >
              {scope === 'ALL' ? 'All Scopes' : scope}
            </button>
          ))}
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4">Assigned Role</th>
                <th className="py-3 px-4">Tier & Scope</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Last Login</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filteredUsers.map((user) => (
                <tr key={user.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3.5 px-4">
                    <div className="font-semibold text-slate-100">{user.name}</div>
                    <div className="text-slate-400 text-[11px] font-mono">{user.email}</div>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="font-medium text-slate-200">{user.role}</span>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800 border border-slate-700 text-slate-300">
                      {user.tier} • {user.scope}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium border ${
                        user.isActive
                          ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800'
                          : 'bg-red-950/60 text-red-400 border-red-800'
                      }`}
                    >
                      {user.isActive ? 'Active' : 'Disabled'}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-400 text-[11px]">{user.lastLogin}</td>
                  <td className="py-3.5 px-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => alert(`Password reset link dispatched for ${user.email}`)}
                        title="Send Password Reset"
                        className="p-1.5 text-slate-400 hover:text-purple-400 hover:bg-slate-800 rounded transition-colors"
                      >
                        <KeyRound className="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleToggleStatus(user.id)}
                        className={`text-xs px-2 py-1 rounded border transition-colors ${
                          user.isActive
                            ? 'bg-red-950/40 border-red-900/60 text-red-400 hover:bg-red-900/60'
                            : 'bg-emerald-950/40 border-emerald-900/60 text-emerald-400 hover:bg-emerald-900/60'
                        }`}
                      >
                        {user.isActive ? 'Disable' : 'Enable'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add User Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-purple-400" />
                Create New HSC User
              </h3>
              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateUser} className="space-y-4 text-xs">
              <div>
                <label className="block font-medium text-slate-300 mb-1">Full Name</label>
                <input
                  type="text"
                  value={newUserName}
                  onChange={(e) => setNewUserName(e.target.value)}
                  placeholder="e.g. Dr. Anita Sharma"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-purple-500 text-sm"
                  required
                />
              </div>

              <div>
                <label className="block font-medium text-slate-300 mb-1">Official HSC Email</label>
                <input
                  type="email"
                  value={newUserEmail}
                  onChange={(e) => setNewUserEmail(e.target.value)}
                  placeholder="e.g. anita.sharma@hsc.gov.in"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-purple-500 text-sm"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-slate-300 mb-1">Hierarchical Scope</label>
                  <select
                    value={newUserScope}
                    onChange={(e) => setNewUserScope(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-purple-500"
                  >
                    <option value="PLATFORM">PLATFORM (L0)</option>
                    <option value="NATIONAL">NATIONAL (L1)</option>
                    <option value="STATE">STATE (L2)</option>
                    <option value="DISTRICT">DISTRICT (L3)</option>
                    <option value="PHC">PHC (L5)</option>
                  </select>
                </div>

                <div>
                  <label className="block font-medium text-slate-300 mb-1">Assigned Role</label>
                  <select
                    value={newUserRole}
                    onChange={(e) => setNewUserRole(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-purple-500"
                  >
                    <option value="Super Admin">Super Admin</option>
                    <option value="National Viewer">National Viewer</option>
                    <option value="State Approver">State Approver</option>
                    <option value="District Approver">District Approver</option>
                    <option value="PHC Approver">PHC Approver (MO)</option>
                    <option value="PHC Operator">PHC Operator</option>
                  </select>
                </div>
              </div>

              <div className="p-3 bg-purple-950/40 border border-purple-800/40 rounded-lg text-purple-300 text-[11px]">
                Temporary password <code>Test@123</code> will be issued. User will be prompted to reset password upon first login.
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg hover:bg-slate-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-medium rounded-lg transition-colors"
                >
                  Save User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
