import React from 'react';
import { AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react';

export default function TeamMatrixTable({ teamMembers, onEmployeeClick }) {
  const getStatusIcon = (compliance) => {
    if (compliance >= 86) return <CheckCircle size={16} className="text-[#4CAF50]" strokeWidth={2} />;
    if (compliance >= 61) return <AlertCircle size={16} className="text-[#FB8C00]" strokeWidth={2} />;
    return <AlertTriangle size={16} className="text-[#E53935]" strokeWidth={2} />;
  };

  const getStatusBadge = (status) => {
    const styles = {
      'Compliant': 'text-green-700 border-green-300',
      'On Track': 'text-blue-700 border-blue-300',
      'At Risk': 'text-orange-700 border-orange-300',
      'Critical': 'text-red-700 border-red-300'
    };
    return (
      <span className={`px-2 py-1 rounded text-xs font-normal border bg-white ${styles[status]}`}>
        {status}
      </span>
    );
  };

  const getComplianceColor = (compliance) => {
    if (compliance >= 86) return 'text-[#4CAF50]';
    if (compliance >= 61) return 'text-[#FB8C00]';
    return 'text-[#E53935]';
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-[#F8F9F8] border-b border-gray-200">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-normal text-[#616161] uppercase tracking-wider">Employee</th>
            <th className="px-4 py-3 text-left text-xs font-normal text-[#616161] uppercase tracking-wider">Role</th>
            <th className="px-4 py-3 text-left text-xs font-normal text-[#616161] uppercase tracking-wider">Department</th>
            <th className="px-4 py-3 text-center text-xs font-normal text-[#616161] uppercase tracking-wider">Compliance</th>
            <th className="px-4 py-3 text-center text-xs font-normal text-[#616161] uppercase tracking-wider">Missing</th>
            <th className="px-4 py-3 text-left text-xs font-normal text-[#616161] uppercase tracking-wider">Status</th>
            <th className="px-4 py-3 text-center text-xs font-normal text-[#616161] uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-100">
          {teamMembers.map((member) => (
            <tr
              key={member.employeeId}
              className="hover:bg-gray-50 transition-colors cursor-pointer"
              onClick={() => onEmployeeClick && onEmployeeClick(member)}
            >
              <td className="px-4 py-3">
                <div className="flex items-center gap-3">
                  <img
                    src={member.avatar}
                    alt={member.name}
                    className="w-8 h-8 rounded-full object-cover border border-gray-200"
                  />
                  <span className="font-normal text-sm text-[#212121]">{member.name}</span>
                </div>
              </td>
              <td className="px-4 py-3 text-sm text-[#616161]">{member.role}</td>
              <td className="px-4 py-3 text-sm text-[#616161]">{member.department}</td>
              <td className="px-4 py-3 text-center">
                <div className="flex items-center justify-center gap-2">
                  {getStatusIcon(member.compliance)}
                  <span className={`font-normal text-sm ${getComplianceColor(member.compliance)}`}>
                    {member.compliance}%
                  </span>
                </div>
              </td>
              <td className="px-4 py-3 text-center">
                <span className="inline-flex items-center justify-center px-2 py-1 rounded bg-white border border-red-300 text-red-700 font-normal text-xs">
                  {member.missingCount}
                </span>
              </td>
              <td className="px-4 py-3">{getStatusBadge(member.status)}</td>
              <td className="px-4 py-3 text-center">
                <button className="text-sm font-normal text-[#4CAF50] hover:text-[#388E3C]">
                  View
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
