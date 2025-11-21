import { useState, useEffect } from 'react';
import { Mail, MapPin, Briefcase, Building2, Shield, Bell } from 'lucide-react';
import { createPageUrl } from '../utils';
import { MOCK_USERS } from '../components/data/mockData';

export default function Profile() {
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [notifications, setNotifications] = useState(true);
  const [emailDigest, setEmailDigest] = useState(false);

  useEffect(() => {
    const storedUser = localStorage.getItem('archerUser');
    if (storedUser) {
      setCurrentUser(JSON.parse(storedUser));
    }
  }, []);

  const handleRoleSwitch = () => {
    const newRole = currentUser.role === 'Worker' ? 'Manager' : 'Worker';
    const newUserData = newRole === 'Worker'
      ? { ...MOCK_USERS.worker }
      : { ...MOCK_USERS.manager };

    localStorage.setItem('archerUser', JSON.stringify(newUserData));
    const targetPage = newRole === 'Worker' ? 'Dashboard' : 'ManagerDashboard';
    window.location.href = createPageUrl(targetPage);
  };

  if (!currentUser) {
    return <div>Loading...</div>;
  }

  return (
    <div className="max-w-[1200px] mx-auto p-6 space-y-6">
      {/* Page Header */}
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-2xl font-semibold text-gray-900">Profile Settings</h1>
        <p className="text-sm text-gray-600 mt-1">
          Manage your account information and preferences
        </p>
      </div>

      {/* Profile Header Card */}
      <div className="bg-white border border-gray-200 rounded-md shadow-sm">
        {/* Avatar and Name Section */}
        <div className="flex items-center gap-6 p-6 border-b border-gray-100">
          <img
            src={currentUser.avatar}
            alt={currentUser.name}
            className="w-20 h-20 rounded-full object-cover border-2 border-gray-200"
          />
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-gray-900">{currentUser.name}</h2>
            <p className="text-sm text-gray-600 mt-1">{currentUser.position}</p>
            <span className="inline-block px-2 py-1 text-xs rounded-md border bg-white text-green-700 border-green-300 mt-2 font-medium">
              {currentUser.role}
            </span>
          </div>
        </div>

        {/* Profile Details Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-6">
          {/* Email */}
          <div className="flex items-start gap-3">
            <Mail className="w-5 h-5 text-gray-500 mt-0.5" strokeWidth={2} />
            <div className="flex-1">
              <p className="text-xs text-gray-500 mb-1">Email</p>
              <p className="text-sm font-medium text-gray-900">{currentUser.email}</p>
            </div>
          </div>

          {/* Location */}
          <div className="flex items-start gap-3">
            <MapPin className="w-5 h-5 text-gray-500 mt-0.5" strokeWidth={2} />
            <div className="flex-1">
              <p className="text-xs text-gray-500 mb-1">Location</p>
              <p className="text-sm font-medium text-gray-900">{currentUser.location}</p>
            </div>
          </div>

          {/* Department */}
          <div className="flex items-start gap-3">
            <Building2 className="w-5 h-5 text-gray-500 mt-0.5" strokeWidth={2} />
            <div className="flex-1">
              <p className="text-xs text-gray-500 mb-1">Department</p>
              <p className="text-sm font-medium text-gray-900">{currentUser.department}</p>
            </div>
          </div>

          {/* Role */}
          <div className="flex items-start gap-3">
            <Briefcase className="w-5 h-5 text-gray-500 mt-0.5" strokeWidth={2} />
            <div className="flex-1">
              <p className="text-xs text-gray-500 mb-1">Role</p>
              <p className="text-sm font-medium text-gray-900">{currentUser.position}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Notification Preferences Section */}
      <div className="bg-white border border-gray-200 rounded-md shadow-sm">
        <div className="border-b border-gray-100 p-4">
          <h2 className="text-lg font-medium text-gray-900 flex items-center gap-2">
            <Bell className="w-5 h-5 text-gray-700" strokeWidth={2} />
            Notification Preferences
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Configure how you receive updates and alerts
          </p>
        </div>

        <div className="p-6 space-y-4">
          {/* Push Notifications Toggle */}
          <div className="flex items-start justify-between pb-4 border-b border-gray-100">
            <div className="flex-1 pr-4">
              <p className="text-sm font-medium text-gray-900 mb-1">Push Notifications</p>
              <p className="text-xs text-gray-600">
                Receive alerts about qualification updates and deadlines
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notifications}
                onChange={(e) => setNotifications(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[#4CAF50] peer-focus:ring-offset-1 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#4CAF50]"></div>
            </label>
          </div>

          {/* Email Digest Toggle */}
          <div className="flex items-start justify-between">
            <div className="flex-1 pr-4">
              <p className="text-sm font-medium text-gray-900 mb-1">Email Digest</p>
              <p className="text-xs text-gray-600">
                Weekly summary of your learning progress and team updates
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={emailDigest}
                onChange={(e) => setEmailDigest(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[#4CAF50] peer-focus:ring-offset-1 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#4CAF50]"></div>
            </label>
          </div>
        </div>
      </div>

      {/* Demo Mode Section */}
      <div className="bg-white border border-gray-200 rounded-md shadow-sm">
        <div className="border-b border-gray-100 p-4">
          <h2 className="text-lg font-medium text-gray-900 flex items-center gap-2">
            <Shield className="w-5 h-5 text-gray-700" strokeWidth={2} />
            Account Mode
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Switch between Worker and Manager preview modes
          </p>
        </div>

        <div className="p-6">
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-4">
            <p className="text-sm text-blue-900 mb-2">
              <span className="font-medium">Demo Mode Active</span>
            </p>
            <p className="text-xs text-blue-700">
              Currently viewing as <span className="font-medium">{currentUser.role}</span>.
              Switch to explore different features and permissions.
            </p>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleRoleSwitch}
              className="px-4 py-2 text-sm bg-[#4CAF50] text-white rounded-md hover:bg-[#388E3C] transition-colors font-normal"
            >
              Switch to {currentUser.role === 'Worker' ? 'Manager' : 'Worker'} View
            </button>
            <button
              className="px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors font-normal"
            >
              View Current Permissions
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
