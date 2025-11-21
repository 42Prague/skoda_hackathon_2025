import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { User, Briefcase, ArrowRight } from 'lucide-react';
import { MOCK_USERS } from '../components/data/mockData';
import { createPageUrl } from '../utils';

export default function Landing() {
  const [selectedRole, setSelectedRole] = useState(null);

  const handleRoleSelect = (role) => {
    const userData = role === 'Worker' ? MOCK_USERS.worker : MOCK_USERS.manager;
    localStorage.setItem('archerUser', JSON.stringify(userData));

    const targetPage = role === 'Worker' ? 'Dashboard' : 'ManagerDashboard';
    window.location.href = createPageUrl(targetPage);
  };

  return (
    <div className="min-h-screen bg-[#F8F9F8] flex items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="w-full max-w-4xl"
      >
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-[#4CAF50] rounded mb-4">
            <span className="text-white font-semibold text-2xl">SD</span>
          </div>
          <h1 className="text-3xl font-normal text-[#212121] mb-2">
            Welcome to Archer
          </h1>
          <p className="text-base text-[#616161] max-w-xl mx-auto">
            Skills & Qualification Management System. Select your role to continue.
          </p>
        </div>

        {/* Role Selection Cards */}
        <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
          {/* Worker Card */}
          <div
            onClick={() => handleRoleSelect('Worker')}
            className="bg-white border border-gray-200 rounded-lg p-6 cursor-pointer hover:border-[#4CAF50] hover:shadow-md transition-all"
          >
            <div className="flex flex-col">
              <div className="w-12 h-12 bg-[#E3F2FD] rounded flex items-center justify-center mb-4">
                <User size={24} className="text-[#1976D2]" strokeWidth={2} />
              </div>
              <h2 className="text-xl font-normal text-[#212121] mb-2">
                Worker
              </h2>
              <p className="text-sm text-[#616161] mb-4">
                Access your personal dashboard, track qualifications, and view learning paths.
              </p>
              <div className="border-t border-gray-100 pt-4 mb-4">
                <p className="text-xs text-[#9E9E9E] mb-1">Demo User</p>
                <p className="font-normal text-[#212121]">Petr Novák</p>
                <p className="text-sm text-[#616161]">Mechanical Technician</p>
              </div>
              <button className="flex items-center justify-center gap-2 px-4 py-2 bg-[#4CAF50] text-white rounded hover:bg-[#388E3C] transition-colors text-sm font-normal">
                <span>Continue as Worker</span>
                <ArrowRight size={16} strokeWidth={2} />
              </button>
            </div>
          </div>

          {/* Manager Card */}
          <div
            onClick={() => handleRoleSelect('Manager')}
            className="bg-white border border-gray-200 rounded-lg p-6 cursor-pointer hover:border-[#4CAF50] hover:shadow-md transition-all"
          >
            <div className="flex flex-col">
              <div className="w-12 h-12 bg-[#E8F5E9] rounded flex items-center justify-center mb-4">
                <Briefcase size={24} className="text-[#4CAF50]" strokeWidth={2} />
              </div>
              <h2 className="text-xl font-normal text-[#212121] mb-2">
                Manager
              </h2>
              <p className="text-sm text-[#616161] mb-4">
                View team compliance, identify skill gaps, and assign training to your team.
              </p>
              <div className="border-t border-gray-100 pt-4 mb-4">
                <p className="text-xs text-[#9E9E9E] mb-1">Demo User</p>
                <p className="font-normal text-[#212121]">Anna Müller</p>
                <p className="text-sm text-[#616161]">Production Team Lead</p>
              </div>
              <button className="flex items-center justify-center gap-2 px-4 py-2 bg-[#4CAF50] text-white rounded hover:bg-[#388E3C] transition-colors text-sm font-normal">
                <span>Continue as Manager</span>
                <ArrowRight size={16} strokeWidth={2} />
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-xs text-[#9E9E9E]">
          <p>Škoda System · Demo Environment</p>
        </div>
      </motion.div>
    </div>
  );
}
