import { useState, useEffect } from 'react';
import { CheckCircle2, Lock, Play, Users, TrendingUp } from 'lucide-react';
import { LEARNING_PATHS } from '../components/data/mockData';

export default function LearningPaths() {
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [filterRole, setFilterRole] = useState('all');
  const [sortBy, setSortBy] = useState('relevant');

  useEffect(() => {
    const storedUser = localStorage.getItem('archerUser');
    if (storedUser) {
      setCurrentUser(JSON.parse(storedUser));
    }
  }, []);

  if (!currentUser) {
    return <div>Loading...</div>;
  }

  const paths = currentUser.role === 'Worker' ? LEARNING_PATHS.worker : LEARNING_PATHS.manager;

  const getStepIcon = (status: string) => {
    if (status === 'completed') return <CheckCircle2 size={16} className="text-[#4CAF50]" strokeWidth={2} />;
    if (status === 'in-progress') return <Play size={16} className="text-[#1565C0]" strokeWidth={2} />;
    if (status === 'locked') return <Lock size={16} className="text-gray-400" strokeWidth={2} />;
    return <div className="w-4 h-4 rounded-full border-2 border-gray-300"></div>;
  };

  const getStepStyle = (status: string) => {
    if (status === 'completed') return 'bg-[#E8F5E9] border-green-200';
    if (status === 'in-progress') return 'bg-[#E3F2FD] border-blue-200';
    if (status === 'locked') return 'bg-gray-50 border-gray-200';
    return 'bg-white border-gray-200';
  };

  return (
    <div className="max-w-[1200px] mx-auto p-6 space-y-6">
      {/* Page Header */}
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-2xl font-semibold text-gray-900">Learning Paths</h1>
        <p className="text-sm text-gray-600 mt-1">
          {currentUser.role === 'Worker'
            ? 'Structured learning journeys to build your skills and qualifications'
            : 'Assign and manage learning paths for your team members'}
        </p>
      </div>

      {/* Worker View - Personal Paths */}
      {currentUser.role === 'Worker' && (
        <div className="space-y-6">
          {paths.map((path: any) => (
            <div key={path.id} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
              {/* Path Header */}
              <div className="flex items-start justify-between mb-4 pb-4 border-b border-gray-100">
                <div className="flex-1">
                  <h2 className="text-lg font-semibold text-gray-900 mb-1">
                    {path.name}
                  </h2>
                  <p className="text-sm text-gray-600 mb-3">
                    {path.description}
                  </p>
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span>
                      <span className="font-medium text-gray-900">{path.completedSteps}</span> of {path.totalSteps} steps completed
                    </span>
                    <span>·</span>
                    <span>{path.estimatedHours}h total</span>
                  </div>
                </div>
                <div className="text-right ml-4">
                  <div className="text-3xl font-semibold text-[#4CAF50]">
                    {Math.round((path.completedSteps / path.totalSteps) * 100)}%
                  </div>
                  <div className="text-xs text-gray-500">Complete</div>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-2 bg-gray-100 rounded-full mb-4 overflow-hidden">
                <div
                  className="h-full bg-[#4CAF50] transition-all duration-500"
                  style={{ width: `${(path.completedSteps / path.totalSteps) * 100}%` }}
                />
              </div>

              {/* Steps List */}
              <div className="space-y-2">
                {path.steps.map((step: any) => (
                  <div
                    key={step.id}
                    className={`p-3 rounded-md border ${getStepStyle(step.status)} transition-all ${
                      step.status !== 'locked' ? 'hover:shadow-sm cursor-pointer' : 'opacity-60'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-white border">
                        {getStepIcon(step.status)}
                      </div>
                      <div className="flex-1">
                        <h3 className="text-sm font-medium text-gray-900">
                          {step.name}
                        </h3>
                        <p className="text-xs text-gray-500">
                          {step.hours}h · {
                            step.status === 'completed' ? 'Completed' :
                            step.status === 'in-progress' ? 'In Progress' :
                            step.status === 'locked' ? 'Locked' :
                            'Available'
                          }
                        </p>
                      </div>
                      {step.status === 'in-progress' && (
                        <button className="px-4 py-2 text-sm bg-[#4CAF50] text-white rounded-md hover:bg-[#388E3C] transition-colors font-normal">
                          Continue
                        </button>
                      )}
                      {step.status === 'available' && (
                        <button className="px-4 py-2 text-sm border border-[#4CAF50] text-[#4CAF50] rounded-md hover:bg-[#4CAF50] hover:text-white transition-colors font-normal">
                          Start
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Manager View - Path Library */}
      {currentUser.role === 'Manager' && (
        <>
          {/* Filters and Stats Bar */}
          <div className="bg-white border border-gray-200 rounded-md p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-gray-500" strokeWidth={2} />
                <span className="text-sm font-medium text-gray-700">
                  {paths.length} Learning Paths Available
                </span>
              </div>
              <div className="flex items-center gap-3">
                <select
                  value={filterRole}
                  onChange={(e) => setFilterRole(e.target.value)}
                  className="px-3 py-2 text-sm border border-gray-300 rounded-md text-gray-700 focus:outline-none focus:ring-2 focus:ring-[#4CAF50]"
                >
                  <option value="all">All Roles</option>
                  <option value="team-lead">Team Lead</option>
                  <option value="supervisor">Supervisor</option>
                  <option value="manager">Manager</option>
                </select>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="px-3 py-2 text-sm border border-gray-300 rounded-md text-gray-700 focus:outline-none focus:ring-2 focus:ring-[#4CAF50]"
                >
                  <option value="relevant">Most Relevant</option>
                  <option value="duration">Duration</option>
                  <option value="enrollment">Enrollment</option>
                </select>
              </div>
            </div>
          </div>

          {/* Paths Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {paths.map((path: any) => (
              <div
                key={path.id}
                className="border border-gray-200 rounded-md shadow-sm p-5 hover:shadow-md transition bg-white"
              >
                {/* Header */}
                <div className="flex justify-between items-start mb-3">
                  <h3 className="text-base font-semibold text-gray-900 flex-1 pr-3">
                    {path.name}
                  </h3>
                  <span className="text-xs px-2 py-1 rounded-md border bg-white text-blue-700 border-blue-300 whitespace-nowrap flex items-center gap-1">
                    <Users size={12} strokeWidth={2} />
                    {path.enrolledCount}
                  </span>
                </div>

                {/* Description */}
                <p className="text-sm text-gray-600 mb-4">
                  {path.description}
                </p>

                {/* Metadata Grid */}
                <div className="text-xs text-gray-500 grid grid-cols-2 gap-y-2 mb-4 pb-4 border-b border-gray-100">
                  <div>
                    <span className="font-medium text-gray-700">Steps:</span> {path.totalSteps}
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Duration:</span> {path.estimatedHours}h
                  </div>
                  <div className="col-span-2">
                    <span className="font-medium text-gray-700">Target Roles:</span> {path.targetRoles.join(', ')}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-3">
                  <button className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors font-normal">
                    View Details
                  </button>
                  <button className="px-4 py-2 text-sm bg-[#4CAF50] text-white rounded-md hover:bg-[#388E3C] transition-colors font-normal">
                    Assign to Team
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
