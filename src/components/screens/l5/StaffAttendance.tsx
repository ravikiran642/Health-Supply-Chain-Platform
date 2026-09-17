import React, { useState } from 'react';
import { UserCheck, CheckCircle2, XCircle, Clock, AlertCircle, Calendar } from 'lucide-react';
import { StaffMember } from '../../../types';

interface StaffAttendanceProps {
  staff: StaffMember[];
  onUpdateStaff: (staff: StaffMember[]) => void;
}

export const StaffAttendance: React.FC<StaffAttendanceProps> = ({ staff = [], onUpdateStaff }) => {
  const [feedback, setFeedback] = useState<string | null>(null);

  const safeStaff = staff || [];

  const handleToggleStatus = (id: string, newStatus: 'PRESENT' | 'ABSENT' | 'ON_DUTY') => {
    const updated = safeStaff.map((s) => {
      if (s.id === id) {
        return {
          ...s,
          status: newStatus,
          checkIn: newStatus === 'ABSENT' ? '-' : s.checkIn === '-' ? '08:30 AM' : s.checkIn,
        };
      }
      return s;
    });
    onUpdateStaff(updated);
    setFeedback('Roster attendance logged and verified.');
    setTimeout(() => setFeedback(null), 2500);
  };

  const presentCount = safeStaff.filter((s) => s.status === 'PRESENT' || s.status === 'ON_DUTY').length;

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10" id="staff-attendance-screen">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <UserCheck className="w-5 h-5 text-emerald-400" />
            PHC Duty Roster & Biometric Attendance
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Monitor daily attendance of medical officers, staff nurses, and pharmacists for district compliance.
          </p>
        </div>

        <div className="flex items-center gap-3 bg-slate-950 px-4 py-2 rounded-lg border border-slate-800 text-xs">
          <span className="text-slate-400">Present Today:</span>
          <span className="text-base font-bold text-emerald-400">
            {presentCount} / {staff.length}
          </span>
          <span className="text-slate-500 font-mono">({Math.round((presentCount / staff.length) * 100)}%)</span>
        </div>
      </div>

      {feedback && (
        <div className="p-4 bg-emerald-950/80 border border-emerald-700/60 rounded-lg text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          {feedback}
        </div>
      )}

      {/* Staff list */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Staff Member</th>
                <th className="py-3 px-4">Designation</th>
                <th className="py-3 px-4">Assigned Shift</th>
                <th className="py-3 px-4">Check-In Time</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Roster Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {safeStaff.map((member) => (
                <tr key={member.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3.5 px-4 font-semibold text-slate-100">{member.name}</td>
                  <td className="py-3.5 px-4 text-slate-400">{member.role}</td>
                  <td className="py-3.5 px-4 text-slate-300">{member.shift}</td>
                  <td className="py-3.5 px-4 font-mono text-slate-400">{member.checkIn}</td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold border ${
                        member.status === 'ABSENT'
                          ? 'bg-red-950/70 border-red-800 text-red-400'
                          : 'bg-emerald-950/70 border-emerald-800 text-emerald-300'
                      }`}
                    >
                      {member.status === 'ABSENT' ? '❌ Absent' : '✅ Present'}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    {member.status === 'ABSENT' ? (
                      <button
                        type="button"
                        onClick={() => handleToggleStatus(member.id, 'PRESENT')}
                        className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-medium transition-colors"
                      >
                        Mark Present
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={() => handleToggleStatus(member.id, 'ABSENT')}
                        className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-red-400 rounded border border-slate-700 text-xs font-medium transition-colors"
                      >
                        Mark Absent
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
