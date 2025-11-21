import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Users, TrendingUp, Award, AlertCircle, Filter, Download } from 'lucide-react';
import TeamMatrixTable from '../components/manager/TeamMatrixTable';
import EmployeeProfileDrawer from '../components/manager/EmployeeProfileDrawer';
import { TEAM_MEMBERS } from '../components/data/mockData';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

export default function TeamSkillsOverview() {
  const [currentUser, setCurrentUser] = useState(null);
  const [filterDepartment, setFilterDepartment] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedEmployee, setSelectedEmployee] = useState<any>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const handleEmployeeClick = (employee: any) => {
    setSelectedEmployee(employee);
    setIsDrawerOpen(true);
  };

  useEffect(() => {
    const storedUser = localStorage.getItem('archerUser');
    if (storedUser) {
      setCurrentUser(JSON.parse(storedUser));
    }
  }, []);

  if (!currentUser) {
    return <div>Loading...</div>;
  }

  const filteredMembers = TEAM_MEMBERS.filter(member => {
    const deptMatch = filterDepartment === 'all' || member.department === filterDepartment;
    const statusMatch = filterStatus === 'all' || member.status === filterStatus;
    return deptMatch && statusMatch;
  });

  const departments = ['all', ...new Set(TEAM_MEMBERS.map(m => m.department))];
  const statuses = ['all', 'Compliant', 'On Track', 'At Risk', 'Critical'];

  // Chart data
  const statusDistribution = [
    { name: 'Compliant', value: TEAM_MEMBERS.filter(m => m.status === 'Compliant').length, color: '#4BA82E' },
    { name: 'On Track', value: TEAM_MEMBERS.filter(m => m.status === 'On Track').length, color: '#3B82F6' },
    { name: 'At Risk', value: TEAM_MEMBERS.filter(m => m.status === 'At Risk').length, color: '#FFA000' },
    { name: 'Critical', value: TEAM_MEMBERS.filter(m => m.status === 'Critical').length, color: '#D32F2F' }
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold text-[rgb(var(--text-primary))]">
            Team Skills Overview
          </h1>
          <p className="text-[rgb(var(--text-secondary))] mt-1">
            Monitor skills compliance and qualification status across your team
          </p>
        </div>
        <button className="flex items-center gap-2 px-6 py-3 bg-[rgb(var(--primary))] text-white rounded-lg hover:bg-[rgb(var(--primary-dark))] transition-colors font-medium">
          <Download size={18} />
          Export Report
        </button>
      </motion.div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="automotive-card p-6"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <Users size={20} className="text-blue-600" />
            </div>
            <h3 className="text-sm font-medium text-[rgb(var(--text-secondary))]">Total Employees</h3>
          </div>
          <p className="text-3xl font-bold text-[rgb(var(--text-primary))]">{TEAM_MEMBERS.length}</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="automotive-card p-6"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <Award size={20} className="text-green-600" />
            </div>
            <h3 className="text-sm font-medium text-[rgb(var(--text-secondary))]">Avg Compliance</h3>
          </div>
          <p className="text-3xl font-bold text-green-600">
            {Math.round(TEAM_MEMBERS.reduce((sum, m) => sum + m.compliance, 0) / TEAM_MEMBERS.length)}%
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="automotive-card p-6"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
              <AlertCircle size={20} className="text-amber-600" />
            </div>
            <h3 className="text-sm font-medium text-[rgb(var(--text-secondary))]">At Risk</h3>
          </div>
          <p className="text-3xl font-bold text-amber-600">
            {TEAM_MEMBERS.filter(m => m.status === 'At Risk').length}
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="automotive-card p-6"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
              <TrendingUp size={20} className="text-red-600" />
            </div>
            <h3 className="text-sm font-medium text-[rgb(var(--text-secondary))]">Critical</h3>
          </div>
          <p className="text-3xl font-bold text-red-600">
            {TEAM_MEMBERS.filter(m => m.status === 'Critical').length}
          </p>
        </motion.div>
      </div>

      {/* Status Distribution Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="automotive-card p-6"
      >
        <h2 className="text-xl font-bold text-[rgb(var(--text-primary))] mb-6">
          Team Status Distribution
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={statusDistribution}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
            >
              {statusDistribution.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Filters & Team Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="automotive-card p-6"
      >
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <h2 className="text-xl font-bold text-[rgb(var(--text-primary))]">Team Members</h2>
          <div className="flex gap-3">
            <div className="flex items-center gap-2">
              <Filter size={18} className="text-[rgb(var(--text-secondary))]" />
              <select
                value={filterDepartment}
                onChange={(e) => setFilterDepartment(e.target.value)}
                className="px-3 py-2 rounded-lg border border-[rgb(var(--border))] text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[rgb(var(--primary))]"
              >
                {departments.map(dept => (
                  <option key={dept} value={dept}>
                    {dept === 'all' ? 'All Departments' : dept}
                  </option>
                ))}
              </select>
            </div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 rounded-lg border border-[rgb(var(--border))] text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[rgb(var(--primary))]"
            >
              {statuses.map(status => (
                <option key={status} value={status}>
                  {status === 'all' ? 'All Statuses' : status}
                </option>
              ))}
            </select>
          </div>
        </div>

        <TeamMatrixTable
          teamMembers={filteredMembers}
          onEmployeeClick={handleEmployeeClick}
        />
      </motion.div>

      <EmployeeProfileDrawer
        employee={selectedEmployee}
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
      />
    </div>
  );
}
