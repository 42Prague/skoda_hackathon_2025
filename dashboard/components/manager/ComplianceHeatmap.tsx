import React from 'react';

export default function ComplianceHeatmap({ data }) {
  const getCellStyle = (value) => {
    if (value >= 86) {
      return 'bg-[#E8F5E9] text-green-700 border-green-200';
    }
    if (value >= 66) {
      return 'bg-[#FFF4E5] text-orange-700 border-orange-200';
    }
    return 'bg-[#FDECEA] text-red-700 border-red-200';
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse border border-gray-200">
        <thead>
          <tr className="bg-[#F8F9F8]">
            <th className="px-4 py-3 text-left text-xs font-normal text-[#616161] uppercase tracking-wider border border-gray-200">
              Department
            </th>
            <th className="px-4 py-3 text-center text-xs font-normal text-[#616161] uppercase tracking-wider border border-gray-200">
              Week 1
            </th>
            <th className="px-4 py-3 text-center text-xs font-normal text-[#616161] uppercase tracking-wider border border-gray-200">
              Week 2
            </th>
            <th className="px-4 py-3 text-center text-xs font-normal text-[#616161] uppercase tracking-wider border border-gray-200">
              Week 3
            </th>
            <th className="px-4 py-3 text-center text-xs font-normal text-[#616161] uppercase tracking-wider border border-gray-200">
              Week 4
            </th>
          </tr>
        </thead>
        <tbody className="bg-white">
          {data.map((row) => (
            <tr key={row.department} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 font-normal text-sm text-[#212121] border border-gray-200">
                {row.department}
              </td>
              {['week1', 'week2', 'week3', 'week4'].map((week) => (
                <td
                  key={week}
                  className={`text-center border border-gray-200 font-medium text-sm px-3 py-3 ${getCellStyle(row[week])}`}
                >
                  {row[week]}%
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      {/* Legend */}
      <div className="mt-4 flex items-center gap-4 text-xs">
        <span className="text-[#616161] font-normal">Performance Levels:</span>
        <span className="px-2 py-1 rounded-md border border-green-200 bg-[#E8F5E9] text-green-700 font-normal">
          ≥ 86% Excellent
        </span>
        <span className="px-2 py-1 rounded-md border border-orange-200 bg-[#FFF4E5] text-orange-700 font-normal">
          66-85% Acceptable
        </span>
        <span className="px-2 py-1 rounded-md border border-red-200 bg-[#FDECEA] text-red-700 font-normal">
          &lt; 66% Critical
        </span>
      </div>
    </div>
  );
}
