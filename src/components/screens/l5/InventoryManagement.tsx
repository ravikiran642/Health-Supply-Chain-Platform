import React, { useState } from 'react';
import {
  Package,
  Search,
  Plus,
  QrCode,
  AlertTriangle,
  Calendar,
  CheckCircle2,
  Filter,
  Edit2,
  Trash2,
} from 'lucide-react';
import { InventoryItem } from '../../../types';

interface InventoryManagementProps {
  inventory: InventoryItem[];
  onUpdateInventory: (items: InventoryItem[]) => void;
}

export const InventoryManagement: React.FC<InventoryManagementProps> = ({
  inventory = [],
  onUpdateInventory,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [scanning, setScanning] = useState(false);
  const [scanMessage, setScanMessage] = useState<string | null>(null);

  // Quick edit modal or state
  const [editingItem, setEditingItem] = useState<InventoryItem | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newItem, setNewItem] = useState<Partial<InventoryItem>>({
    name: '',
    code: '',
    category: 'Essential Drug',
    currentStock: 100,
    unit: 'strips',
    minRequired: 50,
    batchNumber: 'BT-2026-X',
    expiryDate: '2027-12-31',
    storageCondition: 'Room Temp (15-25°C)',
  });

  const safeInventory = inventory || [];

  const filteredInventory = safeInventory.filter((item) => {
    const itemCode = (item.code || item.drugCode || '').toLowerCase();
    const itemName = (item.name || '').toLowerCase();
    const itemBatch = (item.batchNumber || '').toLowerCase();
    const term = searchTerm.toLowerCase();

    const matchesSearch =
      itemName.includes(term) ||
      itemCode.includes(term) ||
      itemBatch.includes(term);
    const matchesCategory = categoryFilter === 'ALL' || item.category === categoryFilter;
    const matchesStatus = statusFilter === 'ALL' || item.status === statusFilter;
    return matchesSearch && matchesCategory && matchesStatus;
  });

  const handleSimulateScan = () => {
    setScanning(true);
    setTimeout(() => {
      setScanning(false);
      // Pick Paracetamol or another item and add 100
      const target = safeInventory[0];
      if (target) {
        const updated = safeInventory.map((it) =>
          it.id === target.id
            ? {
                ...it,
                currentStock: it.currentStock + 100,
                status:
                  it.currentStock + 100 < it.minRequired
                    ? ('CRITICAL' as const)
                    : it.currentStock + 100 < it.minRequired * 1.5
                    ? ('REORDER' as const)
                    : ('ADEQUATE' as const),
              }
            : it
        );
        onUpdateInventory(updated);
        const codeLabel = target.code || target.drugCode || 'MED-ITEM';
        setScanMessage(`Scanned Barcode: [${codeLabel}] ${target.name}. Stock incremented by +100 strips.`);
        setTimeout(() => setScanMessage(null), 4000);
      }
    }, 1200);
  };

  const handleSaveEdit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingItem) return;

    const newStock = Number(editingItem.currentStock);
    const newStatus =
      newStock < editingItem.minRequired
        ? ('CRITICAL' as const)
        : newStock < editingItem.minRequired * 1.5
        ? ('REORDER' as const)
        : ('ADEQUATE' as const);

    const updated = safeInventory.map((i) =>
      i.id === editingItem.id ? { ...editingItem, currentStock: newStock, status: newStatus } : i
    );
    onUpdateInventory(updated);
    setEditingItem(null);
  };

  const handleAddItem = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newItem.name || !newItem.code) return;

    const stock = Number(newItem.currentStock || 0);
    const min = Number(newItem.minRequired || 50);
    const status =
      stock < min ? ('CRITICAL' as const) : stock < min * 1.5 ? ('REORDER' as const) : ('ADEQUATE' as const);

    const created: InventoryItem = {
      id: `inv-${Date.now()}`,
      name: newItem.name,
      code: newItem.code,
      category: newItem.category || 'Essential Drug',
      currentStock: stock,
      unit: newItem.unit || 'units',
      minRequired: min,
      batchNumber: newItem.batchNumber || 'BT-AUTO',
      expiryDate: newItem.expiryDate || '2027-12-31',
      storageCondition: newItem.storageCondition || 'Room Temp',
      status,
      daysOfSupply: Math.round(stock / 5),
    };

    onUpdateInventory([created, ...safeInventory]);
    setShowAddModal(false);
    setNewItem({
      name: '',
      code: '',
      category: 'Essential Drug',
      currentStock: 100,
      unit: 'strips',
      minRequired: 50,
      batchNumber: 'BT-2026-X',
      expiryDate: '2027-12-31',
      storageCondition: 'Room Temp (15-25°C)',
    });
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-10" id="inventory-management-screen">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Package className="w-5 h-5 text-teal-400" />
            PHC Drug & Vaccine Dispensary Inventory
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Maintain real-time physical stock counts, scan barcodes, monitor batch expiries, and prevent drug shortages.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleSimulateScan}
            disabled={scanning}
            className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-teal-300 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <QrCode className="w-4 h-4 text-teal-400" />
            {scanning ? 'Reading Barcode...' : 'Scan QR / Barcode'}
          </button>
          <button
            type="button"
            onClick={() => setShowAddModal(true)}
            className="px-3.5 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            Add New Batch
          </button>
        </div>
      </div>

      {/* Barcode feedback banner */}
      {scanMessage && (
        <div className="p-4 bg-teal-950/80 border border-teal-700/60 rounded-lg text-teal-200 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
          {scanMessage}
        </div>
      )}

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row items-center gap-3 bg-slate-900 border border-slate-800 p-4 rounded-xl">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search medicine name, drug code, or batch #..."
            className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-teal-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-teal-500"
          >
            <option value="ALL">All Stock Statuses</option>
            <option value="CRITICAL">🔴 Critical Stock</option>
            <option value="REORDER">🟡 Reorder Level</option>
            <option value="ADEQUATE">🟢 Adequate Stock</option>
          </select>

          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-teal-500"
          >
            <option value="ALL">All Categories</option>
            <option value="Essential Drug">Essential Drug</option>
            <option value="Cold Chain Vaccine">Cold Chain Vaccine</option>
            <option value="Injectable">Injectable</option>
            <option value="Consumable">Consumable</option>
          </select>
        </div>
      </div>

      {/* Inventory Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Medicine & Code</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Current Stock</th>
                <th className="py-3 px-4">Min Buffer</th>
                <th className="py-3 px-4">Batch & Expiry</th>
                <th className="py-3 px-4">Storage</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filteredInventory.map((item) => (
                <tr key={item.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3.5 px-4">
                    <div className="font-semibold text-slate-100">{item.name}</div>
                    <div className="text-slate-500 font-mono text-[11px]">{item.code}</div>
                  </td>
                  <td className="py-3.5 px-4 text-slate-400">{item.category}</td>
                  <td className="py-3.5 px-4 font-mono">
                    <span className="font-bold text-sm text-slate-100">{item.currentStock}</span>{' '}
                    <span className="text-slate-400 text-[11px]">{item.unit}</span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-400 font-mono">
                    {item.minRequired} {item.unit}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-slate-300">
                    <div>{item.batchNumber}</div>
                    <div className="text-slate-500 text-[11px] flex items-center gap-1 mt-0.5">
                      <Calendar className="w-3 h-3 text-slate-500" />
                      {item.expiryDate}
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-slate-400 text-[11px]">{item.storageCondition}</td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold border ${
                        item.status === 'CRITICAL'
                          ? 'bg-red-950/70 border-red-800 text-red-300'
                          : item.status === 'REORDER'
                          ? 'bg-amber-950/70 border-amber-800 text-amber-300'
                          : 'bg-emerald-950/70 border-emerald-800 text-emerald-300'
                      }`}
                    >
                      {item.status === 'CRITICAL' ? '🔴 Critical' : item.status === 'REORDER' ? '🟡 Reorder' : '🟢 Adequate'}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <button
                      type="button"
                      onClick={() => setEditingItem(item)}
                      className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 text-xs font-medium transition-colors"
                    >
                      Adjust Stock
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit Modal */}
      {editingItem && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-md w-full space-y-4 shadow-xl">
            <h2 className="text-base font-bold text-slate-100">Adjust Physical Stock Count</h2>
            <p className="text-xs text-slate-400">
              Update physical inventory count for <strong>{editingItem.name}</strong> ({editingItem.code}).
            </p>

            <form onSubmit={handleSaveEdit} className="space-y-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Physical Stock Count ({editingItem.unit})</label>
                <input
                  type="number"
                  value={editingItem.currentStock}
                  onChange={(e) => setEditingItem({ ...editingItem, currentStock: Number(e.target.value) })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100 font-mono focus:outline-none focus:border-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Batch Number</label>
                <input
                  type="text"
                  value={editingItem.batchNumber}
                  onChange={(e) => setEditingItem({ ...editingItem, batchNumber: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Expiry Date</label>
                <input
                  type="date"
                  value={editingItem.expiryDate}
                  onChange={(e) => setEditingItem({ ...editingItem, expiryDate: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-teal-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setEditingItem(null)}
                  className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold rounded-lg shadow-sm"
                >
                  Save Stock Count
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add New Batch Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-md w-full space-y-4 shadow-xl">
            <h2 className="text-base font-bold text-slate-100">Register New Drug / Consumable Batch</h2>

            <form onSubmit={handleAddItem} className="space-y-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Drug Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Ciprofloxacin 500mg"
                  value={newItem.name}
                  onChange={(e) => setNewItem({ ...newItem, name: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-teal-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Drug Code</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. MED-CIP-01"
                    value={newItem.code}
                    onChange={(e) => setNewItem({ ...newItem, code: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-100 font-mono focus:outline-none focus:border-teal-500"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Category</label>
                  <select
                    value={newItem.category}
                    onChange={(e) => setNewItem({ ...newItem, category: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-teal-500"
                  >
                    <option value="Essential Drug">Essential Drug</option>
                    <option value="Cold Chain Vaccine">Cold Chain Vaccine</option>
                    <option value="Injectable">Injectable</option>
                    <option value="Consumable">Consumable</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Initial Stock Count</label>
                  <input
                    type="number"
                    value={newItem.currentStock}
                    onChange={(e) => setNewItem({ ...newItem, currentStock: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-100 font-mono focus:outline-none focus:border-teal-500"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Minimum Buffer</label>
                  <input
                    type="number"
                    value={newItem.minRequired}
                    onChange={(e) => setNewItem({ ...newItem, minRequired: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-100 font-mono focus:outline-none focus:border-teal-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Batch Number</label>
                  <input
                    type="text"
                    value={newItem.batchNumber}
                    onChange={(e) => setNewItem({ ...newItem, batchNumber: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-100 font-mono focus:outline-none focus:border-teal-500"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Expiry Date</label>
                  <input
                    type="date"
                    value={newItem.expiryDate}
                    onChange={(e) => setNewItem({ ...newItem, expiryDate: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-teal-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold rounded-lg shadow-sm"
                >
                  Create Batch Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
