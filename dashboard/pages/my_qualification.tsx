import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search, Filter, Download } from 'lucide-react';
import QualificationCard from '../components/dashboard/QualificationCard';

export default function MyQualifications() {
  const [currentUser, setCurrentUser] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('all');
  const [activeTab, setActiveTab] = useState('missing');

  useEffect(() => {
    const storedUser = localStorage.getItem('archerUser');
    if (storedUser) {
      setCurrentUser(JSON.parse(storedUser));
    }
  }, []);

  if (!currentUser) {
    return <div>Loading...</div>;
  }

  const categories = ['all', ...new Set([
    ...currentUser.completedQualifications.map(q => q.category),
    ...currentUser.missingQualifications.map(q => q.category)
  ])];

  const filterQualifications = (qualifications) => {
    return qualifications.filter(q => {
      const matchesSearch = q.name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory = filterCategory === 'all' || q.category === filterCategory;
      return matchesSearch && matchesCategory;
    });
  };

  const filteredCompleted = filterQualifications(currentUser.completedQualifications);
  const filteredMissing = filterQualifications(currentUser.missingQualifications);

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
            My Qualifications
          </h1>
          <p className="text-[rgb(var(--text-secondary))] mt-1">
            Track your completed and required qualifications
          </p>
        </div>
        <button className="flex items-center gap-2 px-6 py-3 bg-[rgb(var(--primary))] text-white rounded-lg hover:bg-[rgb(var(--primary-dark))] transition-colors font-medium">
          <Download size={18} />
          Export Report
        </button>
      </motion.div>

      {/* Stats Overview */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-6"
      >
        <div className="automotive-card p-6 bg-white">
          <h3 className="text-sm font-medium text-[rgb(var(--text-secondary))] mb-2">Completed</h3>
          <p className="text-4xl font-bold text-green-600">{currentUser.completedQualifications.length}</p>
        </div>
        <div className="automotive-card p-6 bg-white">
          <h3 className="text-sm font-medium text-[rgb(var(--text-secondary))] mb-2">Missing</h3>
          <p className="text-4xl font-bold text-red-600">{currentUser.missingQualifications.length}</p>
        </div>
        <div className="automotive-card p-6 bg-white">
          <h3 className="text-sm font-medium text-[rgb(var(--text-secondary))] mb-2">Compliance Rate</h3>
          <p className="text-4xl font-bold text-blue-600">{currentUser.compliance}%</p>
        </div>
      </motion.div>

      {/* Filters & Search */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="automotive-card p-6"
      >
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[rgb(var(--text-secondary))]" size={18} />
            <input
              type="text"
              placeholder="Search qualifications..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg border border-[rgb(var(--border))] focus:outline-none focus:ring-2 focus:ring-[rgb(var(--primary))]"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter size={18} className="text-[rgb(var(--text-secondary))]" />
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="px-4 py-2 rounded-lg border border-[rgb(var(--border))] font-medium focus:outline-none focus:ring-2 focus:ring-[rgb(var(--primary))]"
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>
                  {cat === 'all' ? 'All Categories' : cat}
                </option>
              ))}
            </select>
          </div>
        </div>
      </motion.div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-[rgb(var(--border))]">
        <button
          onClick={() => setActiveTab('missing')}
          className={`px-6 py-3 font-medium transition-all ${
            activeTab === 'missing'
              ? 'text-[rgb(var(--primary))] border-b-2 border-[rgb(var(--primary))]'
              : 'text-[rgb(var(--text-secondary))] hover:text-[rgb(var(--text-primary))]'
          }`}
        >
          Missing ({filteredMissing.length})
        </button>
        <button
          onClick={() => setActiveTab('completed')}
          className={`px-6 py-3 font-medium transition-all ${
            activeTab === 'completed'
              ? 'text-[rgb(var(--primary))] border-b-2 border-[rgb(var(--primary))]'
              : 'text-[rgb(var(--text-secondary))] hover:text-[rgb(var(--text-primary))]'
          }`}
        >
          Completed ({filteredCompleted.length})
        </button>
      </div>

      {/* Qualifications Grid */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="grid md:grid-cols-2 lg:grid-cols-3 gap-4"
      >
        {activeTab === 'missing' ? (
          filteredMissing.length > 0 ? (
            filteredMissing.map((qual, index) => (
              <motion.div
                key={qual.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <QualificationCard qualification={qual} type="missing" />
              </motion.div>
            ))
          ) : (
            <div className="col-span-full text-center py-12 text-[rgb(var(--text-secondary))]">
              No missing qualifications found
            </div>
          )
        ) : (
          filteredCompleted.length > 0 ? (
            filteredCompleted.map((qual, index) => (
              <motion.div
                key={qual.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <QualificationCard qualification={qual} type="completed" />
              </motion.div>
            ))
          ) : (
            <div className="col-span-full text-center py-12 text-[rgb(var(--text-secondary))]">
              No completed qualifications found
            </div>
          )
        )}
      </motion.div>
    </div>
  );
}
