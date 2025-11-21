import React from 'react';

export default function RiskAlerts({ alerts }) {
  const getSeverityStyle = (type) => {
    if (type === 'critical') {
      return {
        badge: 'bg-[#FDECEA] text-[#B00020] border-red-200',
        label: 'CRITICAL'
      };
    }
    return {
      badge: 'bg-[#FFF4E5] text-[#924700] border-orange-200',
      label: 'WARNING'
    };
  };

  return (
    <div className="space-y-3">
      {alerts.map((alert) => {
        const severity = getSeverityStyle(alert.type);

        return (
          <div
            key={alert.id}
            className="border border-gray-200 rounded-lg p-4 shadow-sm bg-white hover:shadow-md transition-shadow"
          >
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h4 className="text-base font-normal text-gray-800 mb-1">
                  {alert.employeeName}
                </h4>
                <p className="text-sm text-gray-600 mb-3">
                  {alert.message}
                </p>
                {alert.daysOverdue > 0 && (
                  <p className="text-xs text-gray-500 mb-3">
                    Overdue by {alert.daysOverdue} days
                  </p>
                )}
                <div className="flex gap-3 text-sm">
                  <button className="text-[#1565C0] hover:text-[#0D47A1] font-normal">
                    View Profile
                  </button>
                  <button className="text-[#1565C0] hover:text-[#0D47A1] font-normal">
                    Assign Training
                  </button>
                </div>
              </div>
              <span className={`px-3 py-1 rounded-md text-xs font-medium border ${severity.badge} whitespace-nowrap ml-4`}>
                {severity.label}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
