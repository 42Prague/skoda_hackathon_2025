import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

export default function ComplianceGauge({ value, size = 200 }) {
  const [animatedValue, setAnimatedValue] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedValue(value);
    }, 300);
    return () => clearTimeout(timer);
  }, [value]);

  const getColor = () => {
    if (value >= 86) return '#4BA82E'; // Škoda Green
    if (value >= 61) return '#FFA000'; // Warning Amber
    return '#D32F2F'; // Critical Red
  };

  const getGradient = () => {
    if (value >= 86) return 'from-[#4BA82E] to-[#0F3D1D]'; // Škoda Green gradient
    if (value >= 61) return 'from-[#FFA000] to-[#FF8F00]'; // Amber gradient
    return 'from-[#D32F2F] to-[#C62828]'; // Red gradient
  };

  const circumference = 2 * Math.PI * 70;
  const offset = circumference - (animatedValue / 100) * circumference;

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      {/* Background Circle */}
      <svg className="transform -rotate-90" width={size} height={size}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r="70"
          stroke="#E0E0E0"
          strokeWidth="12"
          fill="none"
        />
        {/* Animated Progress Circle */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r="70"
          stroke={getColor()}
          strokeWidth="12"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.5, ease: 'easeOut' }}
        />
      </svg>

      {/* Center Content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.5, type: 'spring' }}
          className="text-center"
        >
          <div className={`text-4xl font-bold bg-gradient-to-r ${getGradient()} bg-clip-text text-transparent`}>
            {Math.round(animatedValue)}%
          </div>
          <div className="text-sm font-medium text-[rgb(var(--text-secondary))] mt-1">
            Compliance
          </div>
        </motion.div>
      </div>
    </div>
  );
}
