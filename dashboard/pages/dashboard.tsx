import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, AlertCircle, BookOpen, Target, Filter } from 'lucide-react';
import ComplianceGauge from '../components/dashboard/ComplianceGauge';
import QualificationCard from '../components/dashboard/QualificationCard';
import { AI_RECOMMENDATIONS } from '../components/data/mockData';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

export default function Dashboard() {
  const [currentUser, setCurrentUser] = useState(null);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    const storedUser = localStorage.getItem('archerUser');
    if (storedUser) {
      setCurrentUser(JSON.parse(storedUser));
    }
  }, []);

  if (!currentUser) {
    return <div>Loading...</div>;
  }

  const priorityData = [
    { name: 'Critical', value: currentUser.missingQualifications.filter(q => q.priority === 'Critical').length },
    { name: 'Important', value: currentUser.missingQualifications.filter(q => q.priority === 'Important').length },
    { name: 'Optional', value: currentUser.missingQualifications.filter(q => q.priority === 'Optional').length }
  ];

  const skillRadarData = currentUser.skills.slice(0, 5).map(skill => ({
    skill,
    current: Math.floor(Math.random() * 30) + 70,
    target: 100
  }));

  const getStatusColor = () => {
    if (currentUser.compliance >= 86) return 'text-[#0F3D1D] bg-[#C8E6C9] border-[#4BA82E]';
    if (currentUser.compliance >= 61) return 'text-[#E65100] bg-[#FFF3E0] border-[#FFA000]';
    return 'text-[#B71C1C] bg-[#FFEBEE] border-[#D32F2F]';
  };

  const getStatusLabel = () => {
    if (currentUser.compliance >= 86) return 'On Track';
    if (currentUser.compliance >= 61) return 'At Risk';
    return 'Non-Compliant';
  };

  const filteredQualifications = filter === 'all'
    ? currentUser.missingQualifications
    : currentUser.missingQualifications.filter(q => q.priority === filter);

  const workerRecommendations = AI_RECOMMENDATIONS.filter(rec =>
    rec.applicableEmployees.includes(currentUser.id)
  ).slice(0, 3);

  return (
    <div className="space-y-8 pb-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-8"
      >
        <div>
          <h1 className="text-[28px] font-semibold text-[#212121] mb-2">
            Welcome back, {currentUser.name.split(' ')[0]}
          </h1>
          <p className="text-[14px] text-[#616161]">
            Here's your personalized skills and qualifications overview
          </p>
        </div>
        <div className={`px-4 py-2 rounded-lg border-2 font-medium text-[14px] ${getStatusColor()}`}>
          Status: {getStatusLabel()}
        </div>
      </motion.div>

      {/* Profile & Compliance Section */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Profile Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="automotive-card p-6 bg-white"
        >
          <div className="flex items-center gap-4 mb-6">
            <img
              src={currentUser.avatar}
              alt={currentUser.name}
              className="w-16 h-16 rounded-full object-cover ring-4 ring-white"
            />
            <div>
              <h2 className="font-bold text-lg text-[rgb(var(--text-primary))]">{currentUser.name}</h2>
              <p className="text-sm text-[rgb(var(--text-secondary))]">{currentUser.position}</p>
            </div>
          </div>
          <div className="space-y-3 border-t border-gray-200 pt-4">
            <div className="flex justify-between text-sm">
              <span className="text-[rgb(var(--text-secondary))]">Department</span>
              <span className="font-medium text-[rgb(var(--text-primary))]">{currentUser.department}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-[rgb(var(--text-secondary))]">Location</span>
              <span className="font-medium text-[rgb(var(--text-primary))]">{currentUser.location}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-[rgb(var(--text-secondary))]">Active Skills</span>
              <span className="font-medium text-[rgb(var(--text-primary))]">{currentUser.skills.length}</span>
            </div>
          </div>
        </motion.div>

        {/* Compliance Gauge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="automotive-card p-6 flex flex-col items-center justify-center"
        >
          <h3 className="text-lg font-semibold text-[rgb(var(--text-primary))] mb-4">Overall Compliance</h3>
          <ComplianceGauge value={currentUser.compliance} />
          <p className="text-sm text-[rgb(var(--text-secondary))] mt-4 text-center">
            {currentUser.completedQualifications.length} of {currentUser.completedQualifications.length + currentUser.missingQualifications.length} qualifications completed
          </p>
        </motion.div>

        {/* Stats Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="automotive-card p-6"
        >
          <h3 className="text-lg font-semibold text-[rgb(var(--text-primary))] mb-6">Quick Stats</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-[#C8E6C9] rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-[#4BA82E] rounded-lg flex items-center justify-center">
                  <TrendingUp size={20} className="text-white" />
                </div>
                <div>
                  <p className="text-sm text-[#616161]">Completed</p>
                  <p className="text-xl font-bold text-[#0F3D1D]">{currentUser.completedQualifications.length}</p>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between p-3 bg-[#FFEBEE] rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-[#D32F2F] rounded-lg flex items-center justify-center">
                  <AlertCircle size={20} className="text-white" />
                </div>
                <div>
                  <p className="text-sm text-[#616161]">Missing</p>
                  <p className="text-xl font-bold text-[#D32F2F]">{currentUser.missingQualifications.length}</p>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between p-3 bg-[#E3F2FD] rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-[#2196F3] rounded-lg flex items-center justify-center">
                  <BookOpen size={20} className="text-white" />
                </div>
                <div>
                  <p className="text-sm text-[#616161]">In Progress</p>
                  <p className="text-xl font-bold text-[#1976D2]">1</p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Missing Qualifications */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="automotive-card p-6"
      >
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <h2 className="text-[20px] font-semibold text-[#212121]">Missing Qualifications</h2>
          <div className="flex items-center gap-2">
            <Filter size={18} className="text-[rgb(var(--text-secondary))]" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-3 py-2 rounded-lg border border-[#E0E0E0] text-[14px] font-medium focus:outline-none focus:ring-2 focus:ring-[#4BA82E] bg-white transition-all duration-250"
            >
              <option value="all">All Priorities</option>
              <option value="Critical">Critical</option>
              <option value="Important">Important</option>
              <option value="Optional">Optional</option>
            </select>
          </div>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredQualifications.map((qual, index) => (
            <motion.div
              key={qual.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * index }}
            >
              <QualificationCard qualification={qual} type="missing" />
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* AI Recommendations & Skills - 2-Column Grid */}
      <div className="grid lg:grid-cols-[2fr_1fr] gap-8">
        {/* AI Recommendations */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
          className="automotive-card p-6"
        >
          <h2 className="text-[20px] font-semibold text-[#212121] mb-6 flex items-center gap-2">
            <Target className="text-[#4BA82E]" size={22} />
            AI Recommended Courses
          </h2>
          <div className="space-y-3">
            {workerRecommendations.map((rec) => (
              <div key={rec.id} className="p-4 bg-white rounded-lg border border-[#E0E0E0] hover:shadow-md transition-all duration-250 ease-in-out cursor-pointer">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-[14px] text-[#212121]">{rec.recommendedCourse.title}</h3>
                  <span className="px-2 py-1 bg-[#E8F5E9] text-[#4BA82E] text-[12px] font-bold rounded">
                    {rec.matchScore}%
                  </span>
                </div>
                <p className="text-[13px] text-[#616161] mb-3">{rec.recommendedCourse.provider}</p>
                <div className="flex items-center justify-between">
                  <span className="text-[12px] text-[#616161]">{rec.recommendedCourse.durationHours}h · {rec.recommendedCourse.format}</span>
                  <button className="text-[13px] font-medium text-[#4BA82E] hover:underline">View Details</button>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Skills & Priority Chart */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
          className="automotive-card p-6"
        >
          <h2 className="text-[20px] font-semibold text-[#212121] mb-6">Learning Priorities</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={priorityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E0E0E0" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#4BA82E" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>

          <div className="mt-6">
            <h3 className="font-semibold text-[16px] text-[#212121] mb-3">Your Skills</h3>
            <div className="flex flex-wrap gap-2">
              {currentUser.skills.map((skill) => (
                <span key={skill} className="px-3 py-1.5 bg-[#E8F5E9] text-[#4BA82E] rounded-full text-[13px] font-medium border border-[#4BA82E] hover:bg-[#4BA82E] hover:text-white transition-all duration-250 cursor-pointer">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
