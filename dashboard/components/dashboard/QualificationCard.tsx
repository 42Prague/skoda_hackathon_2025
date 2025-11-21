import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, AlertTriangle, Clock } from 'lucide-react';

export default function QualificationCard({ qualification, type = 'completed' }) {
  const getIcon = () => {
    if (type === 'completed') return <CheckCircle2 className="text-[#4BA82E]" size={20} />;
    if (qualification.dueInDays <= 15) return <AlertTriangle className="text-[#D32F2F]" size={20} />;
    return <Clock className="text-[#FFA000]" size={20} />;
  };

  const getStatusBadge = () => {
    if (type === 'completed') {
      return (
        <span className="px-3 py-1 rounded-full text-xs font-medium bg-[#C8E6C9] text-[#0F3D1D] border border-[#4BA82E]">
          Completed
        </span>
      );
    }

    if (qualification.dueInDays <= 15) {
      return (
        <span className="px-3 py-1 rounded-full text-xs font-medium bg-[#FFEBEE] text-[#B71C1C] border border-[#D32F2F]">
          Critical - {qualification.dueInDays} days
        </span>
      );
    }

    return (
      <span className="px-3 py-1 rounded-full text-xs font-medium bg-[#FFF3E0] text-[#E65100] border border-[#FFA000]">
        Due in {qualification.dueInDays} days
      </span>
    );
  };

  const getPriorityBadge = () => {
    const colors = {
      Critical: 'bg-[#FFEBEE] text-[#D32F2F] border-[#D32F2F]',
      Important: 'bg-[#FFF3E0] text-[#FFA000] border-[#FFA000]',
      Optional: 'bg-[#E3F2FD] text-[#1976D2] border-[#2196F3]'
    };

    return qualification.priority ? (
      <span className={`px-2 py-1 rounded text-xs font-medium border ${colors[qualification.priority]}`}>
        {qualification.priority}
      </span>
    ) : null;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2, boxShadow: '0 8px 16px rgba(0,0,0,0.1)' }}
      className="automotive-card p-5"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          {getIcon()}
          <div>
            <h3 className="font-semibold text-[rgb(var(--text-primary))]">
              {qualification.name}
            </h3>
            <p className="text-sm text-[rgb(var(--text-secondary))] mt-1">
              {qualification.category}
            </p>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 mt-4">
        {getStatusBadge()}
        {getPriorityBadge()}
      </div>

      {type === 'completed' && qualification.completedAt && (
        <p className="text-xs text-[rgb(var(--text-secondary))] mt-3">
          Completed on {new Date(qualification.completedAt).toLocaleDateString('en-GB')}
        </p>
      )}
    </motion.div>
  );
}
