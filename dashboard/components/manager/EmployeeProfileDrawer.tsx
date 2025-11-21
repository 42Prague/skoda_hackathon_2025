import { X, Mail, MapPin, Briefcase, Building2, AlertCircle, TrendingUp, Clock } from 'lucide-react';

interface EmployeeProfileDrawerProps {
  employee: any;
  isOpen: boolean;
  onClose: () => void;
}

export default function EmployeeProfileDrawer({ employee, isOpen, onClose }: EmployeeProfileDrawerProps) {
  if (!isOpen || !employee) return null;

  const getStatusStyle = (status: string) => {
    const styles: Record<string, string> = {
      'Compliant': 'bg-white border-green-300 text-green-700',
      'On Track': 'bg-white border-blue-300 text-blue-700',
      'At Risk': 'bg-[#FFF4E5] border-orange-300 text-[#924700]',
      'Critical': 'bg-[#FDECEA] border-red-300 text-[#B00020]'
    };
    return styles[status] || 'bg-white border-gray-300 text-gray-700';
  };

  const getUrgencyStyle = (urgency: string) => {
    const styles: Record<string, string> = {
      'Critical': 'text-[#E53935] border-red-300 bg-white',
      'High': 'text-[#FB8C00] border-orange-300 bg-white',
      'Medium': 'text-[#1565C0] border-blue-300 bg-white'
    };
    return styles[urgency] || 'text-gray-700 border-gray-300 bg-white';
  };

  // Mock data for missing qualifications
  const missingQualifications = [
    { id: 1, title: 'Advanced Machine Safety', status: 'Expiring in 22 days', urgency: 'Critical' },
    { id: 2, title: 'Machine Operation License', status: 'Missing', urgency: 'High' },
    { id: 3, title: 'Quality Compliance Audit Training', status: 'Pending', urgency: 'Medium' }
  ];

  // Mock AI suggested training
  const suggestedTraining = [
    {
      id: 1,
      title: 'Advanced Safety for Automated Assembly Lines',
      provider: 'Škoda Academy',
      match: 93,
      duration: 5,
      format: 'Blended Learning'
    },
    {
      id: 2,
      title: 'Machine Operation Certification Renewal',
      provider: 'Technical Training Center',
      match: 89,
      duration: 4,
      format: 'In-person Workshop'
    }
  ];

  return (
    <>
      {/* Centered Modal Overlay */}
      <div
        className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-30 backdrop-blur-sm z-50 p-4"
        onClick={onClose}
      >
        {/* Modal Card */}
        <div
          className="max-w-[680px] w-full bg-white rounded-md border border-gray-200 shadow-md overflow-y-auto max-h-[90vh]"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header with Close Button */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Employee Profile</h2>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-md hover:bg-gray-100 flex items-center justify-center transition-colors"
            >
              <X size={20} className="text-gray-500" strokeWidth={2} />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-4">
            {/* Employee Header Section - Compact */}
            <div className="flex items-center gap-4 border-b pb-4 mb-4">
              <img
                src={employee.avatar}
                alt={employee.name}
                className="w-16 h-16 rounded-full object-cover border border-gray-200"
              />
              <div className="flex-1">
                <h2 className="text-lg font-semibold text-gray-900">{employee.name}</h2>
                <p className="text-sm text-gray-600 mt-1">{employee.role}</p>
              </div>
              <span className={`inline-block px-2 py-1 text-xs rounded-md border font-medium ${getStatusStyle(employee.status)}`}>
                {employee.status}
              </span>
            </div>

            {/* Contact & Location Info - Compact Grid */}
            <div className="grid grid-cols-2 gap-3 pb-4 border-b">
              <div className="flex items-start gap-2">
                <Mail size={16} className="text-gray-500 mt-0.5" strokeWidth={2} />
                <div>
                  <p className="text-xs text-gray-500">Email</p>
                  <a
                    href={`mailto:${employee.name.toLowerCase().replace(' ', '.')}@skoda.com`}
                    className="text-sm text-[#1565C0] hover:underline"
                  >
                    {employee.name.toLowerCase().replace(' ', '.')}@skoda.com
                  </a>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <MapPin size={16} className="text-gray-500 mt-0.5" strokeWidth={2} />
                <div>
                  <p className="text-xs text-gray-500">Location</p>
                  <p className="text-sm text-gray-900">Mladá Boleslav Plant</p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <Building2 size={16} className="text-gray-500 mt-0.5" strokeWidth={2} />
                <div>
                  <p className="text-xs text-gray-500">Department</p>
                  <p className="text-sm text-gray-900">{employee.department}</p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <Briefcase size={16} className="text-gray-500 mt-0.5" strokeWidth={2} />
                <div>
                  <p className="text-xs text-gray-500">Employee ID</p>
                  <p className="text-sm text-gray-900">EMP-{employee.employeeId}</p>
                </div>
              </div>
            </div>

            {/* Compliance Overview */}
            <div className="pt-4">
              <h4 className="text-base font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <TrendingUp size={18} className="text-gray-700" strokeWidth={2} />
                Compliance Overview
              </h4>

              <div className="grid grid-cols-2 gap-3">
                <div className="border border-gray-200 rounded-md p-3 bg-gray-50">
                  <p className="text-xs text-gray-600 mb-1">Compliance Score</p>
                  <p className={`text-xl font-semibold ${
                    employee.compliance >= 86 ? 'text-[#4CAF50]' :
                    employee.compliance >= 61 ? 'text-[#FB8C00]' :
                    'text-[#E53935]'
                  }`}>
                    {employee.compliance}%
                  </p>
                </div>

                <div className="border border-gray-200 rounded-md p-3 bg-gray-50">
                  <p className="text-xs text-gray-600 mb-1">Missing Qualifications</p>
                  <p className="text-xl font-semibold text-gray-900">{employee.missingCount}</p>
                </div>

                <div className="border border-gray-200 rounded-md p-3 bg-gray-50">
                  <p className="text-xs text-gray-600 mb-1">Expiring Soon</p>
                  <p className="text-xl font-semibold text-gray-900">2</p>
                </div>

                <div className="border border-gray-200 rounded-md p-3 bg-gray-50">
                  <p className="text-xs text-gray-600 mb-1 flex items-center gap-1">
                    <Clock size={12} strokeWidth={2} />
                    Last Updated
                  </p>
                  <p className="text-sm text-gray-900">12 days ago</p>
                </div>
              </div>
            </div>

            {/* Missing Qualifications Section */}
            <div className="pt-4">
              <h4 className="text-base font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <AlertCircle size={18} className="text-gray-700" strokeWidth={2} />
                Missing or Expiring Qualifications
              </h4>

              <div className="space-y-2">
                {missingQualifications.map((qual) => (
                  <div
                    key={qual.id}
                    className="border border-gray-200 rounded-md p-3 hover:border-gray-300 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-1">
                      <h5 className="text-sm font-medium text-gray-900 flex-1">{qual.title}</h5>
                      <span className={`px-2 py-1 text-xs rounded-md border ${getUrgencyStyle(qual.urgency)} whitespace-nowrap ml-3`}>
                        {qual.urgency}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600">{qual.status}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Suggested Training Actions */}
            <div className="pt-4">
              <h4 className="text-base font-semibold text-gray-900 mb-3">
                AI-Suggested Training
              </h4>

              <div className="space-y-2">
                {suggestedTraining.map((course) => (
                  <div
                    key={course.id}
                    className="border border-gray-200 rounded-md p-3 hover:border-gray-300 transition-colors"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h5 className="text-sm font-medium text-gray-900 flex-1 pr-3">
                        {course.title}
                      </h5>
                      <span className="px-2 py-1 text-xs rounded-md border bg-white text-green-700 border-green-300 whitespace-nowrap">
                        {course.match}% Match
                      </span>
                    </div>

                    <p className="text-xs text-gray-600 mb-2">
                      {course.provider} · {course.duration}h · {course.format}
                    </p>

                    <div className="flex gap-2 pt-2 border-t border-gray-100">
                      <button className="flex-1 px-3 py-1.5 text-xs bg-[#4CAF50] text-white rounded-md hover:bg-[#388E3C] transition-colors">
                        Assign to Employee
                      </button>
                      <button className="px-3 py-1.5 text-xs border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors">
                        View Course
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Action Buttons - Right Aligned */}
            <div className="flex justify-end gap-3 pt-4 border-t mt-4">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
              >
                Close
              </button>
              <button className="px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors">
                View Full Profile
              </button>
              <button className="px-4 py-2 text-sm bg-[#4CAF50] text-white rounded-md hover:bg-[#388E3C] transition-colors">
                Assign Training
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
