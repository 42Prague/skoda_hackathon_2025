import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  Award,
  Sparkles,
  Route,
  User,
  LogOut,
  Menu,
  X,
  Plus,
  BookOpen
} from 'lucide-react';
import { createPageUrl } from './utils';

export default function Layout({ children, currentPageName }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const storedUser = localStorage.getItem('archerUser');
    if (storedUser) {
      setCurrentUser(JSON.parse(storedUser));
    }
  }, [location.pathname]);

  if (!currentUser || currentPageName === 'Login') {
    return <div className="min-h-screen">{children}</div>;
  }

  const workerNavItems = [
    { name: 'Dashboard', icon: LayoutDashboard, path: 'Dashboard' },
    { name: 'My Qualifications', icon: Award, path: 'MyQualifications' },
    { name: 'AI Recommendations', icon: Sparkles, path: 'AIRecommendations' },
    { name: 'Learning Paths', icon: Route, path: 'LearningPaths' },
    { name: 'Profile', icon: User, path: 'Profile' }
  ];

  const managerNavItems = [
    { name: 'Dashboard', icon: LayoutDashboard, path: 'ManagerDashboard' },
    { name: 'Team Skills Overview', icon: Award, path: 'TeamSkillsOverview' },
    { name: 'AI Recommendations', icon: Sparkles, path: 'AIRecommendations' },
    { name: 'Learning Paths', icon: Route, path: 'LearningPaths' },
    { name: 'Profile', icon: User, path: 'Profile' }
  ];

  const navItems = currentUser.role === 'Worker' ? workerNavItems : managerNavItems;

  const handleLogout = () => {
    localStorage.removeItem('archerUser');
    window.location.href = createPageUrl('Login');
  };

  const getStatusColor = () => {
    if (currentUser.role === 'Worker') {
      if (currentUser.compliance >= 86) return 'bg-white text-green-700 border-green-300';
      if (currentUser.compliance >= 61) return 'bg-white text-orange-700 border-orange-300';
      return 'bg-white text-red-700 border-red-300';
    }
    return 'bg-white text-gray-700 border-gray-300';
  };

  const getStatusLabel = () => {
    if (currentUser.role === 'Manager') return 'Manager';
    if (currentUser.compliance >= 86) return 'On Track';
    if (currentUser.compliance >= 61) return 'At Risk';
    return 'Non-Compliant';
  };

  return (
    <div className="min-h-screen bg-[#F8F9F8]">
      {/* Top Bar */}
      <header className="fixed top-0 left-0 right-0 h-16 bg-white border-b border-[#E0E0E0] z-50">
        <div className="h-full px-8 flex items-center justify-between">
          {/* Logo & Title */}
          <div className="flex items-center gap-4">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="lg:hidden p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              {isMobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
            <Link to={createPageUrl(currentUser.role === 'Worker' ? 'Dashboard' : 'ManagerDashboard')} className="flex items-center gap-3">
              <div className="w-8 h-8 bg-[#4CAF50] rounded flex items-center justify-center">
                <span className="text-white font-semibold text-sm">SD</span>
              </div>
              <span className="text-lg font-normal text-[#212121] hidden sm:block">
                Archer
              </span>
            </Link>
          </div>

          {/* User Info & Actions */}
          <div className="flex items-center gap-4">
            {/* Quick Action Button */}
            {currentUser.role === 'Manager' ? (
              <button className="hidden md:flex items-center gap-2 px-4 py-2 bg-[#4CAF50] text-white rounded border border-[#4CAF50] hover:bg-[#388E3C] transition-colors">
                <Plus size={16} strokeWidth={2} />
                <span className="text-sm font-normal">Assign Training</span>
              </button>
            ) : (
              <button className="hidden md:flex items-center gap-2 px-4 py-2 bg-[#4CAF50] text-white rounded border border-[#4CAF50] hover:bg-[#388E3C] transition-colors">
                <BookOpen size={16} strokeWidth={2} />
                <span className="text-sm font-normal">Continue Learning</span>
              </button>
            )}

            {/* User Avatar & Info */}
            <div className="flex items-center gap-3 pl-4 border-l border-[rgb(var(--border))]">
              <div className="hidden sm:block text-right">
                <p className="text-sm font-medium text-[rgb(var(--text-primary))]">{currentUser.name}</p>
                <p className="text-xs text-[rgb(var(--text-secondary))]">{currentUser.position}</p>
              </div>
              <div className="relative">
                <img
                  src={currentUser.avatar}
                  alt={currentUser.name}
                  className="w-10 h-10 rounded-full object-cover border-2 border-gray-200"
                />
                <span className={`absolute -bottom-1 -right-1 px-2 py-0.5 text-xs font-normal rounded border ${getStatusColor()}`}>
                  {getStatusLabel()}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Sidebar */}
      <AnimatePresence>
        {(isMobileMenuOpen || window.innerWidth >= 1024) && (
          <motion.aside
            initial={{ x: -280 }}
            animate={{ x: 0 }}
            exit={{ x: -280 }}
            transition={{ type: 'spring', damping: 25 }}
            className="fixed top-16 left-0 bottom-0 w-64 bg-white border-r border-[#E0E0E0] z-40 lg:translate-x-0"
          >
            <nav className="px-3 py-4 space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentPageName === item.path;
                return (
                  <Link
                    key={item.path}
                    to={createPageUrl(item.path)}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-3 py-2 rounded transition-colors ${
                      isActive
                        ? 'bg-[#E8F5E9] text-[#4CAF50] font-normal'
                        : 'text-[#616161] hover:bg-[#F5F5F5] hover:text-[#212121]'
                    }`}
                  >
                    <Icon size={18} className="flex-shrink-0" strokeWidth={2} />
                    <span className="text-sm">{item.name}</span>
                  </Link>
                );
              })}

              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-3 py-2 rounded text-[#616161] hover:bg-red-50 hover:text-[#E53935] transition-colors mt-6"
              >
                <LogOut size={18} className="flex-shrink-0" strokeWidth={2} />
                <span className="text-sm">Logout</span>
              </button>
            </nav>

            {/* User Info Card in Sidebar - Fixed Bottom */}
            <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-[#E0E0E0] bg-white">
              <div className="flex items-center gap-3">
                <img
                  src={currentUser.avatar}
                  alt={currentUser.name}
                  className="w-10 h-10 rounded-full object-cover ring-2 ring-[#E0E0E0]"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] font-medium text-[#212121] truncate">{currentUser.name}</p>
                  <p className="text-[12px] text-[#616161] truncate">{currentUser.location}</p>
                </div>
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div
          onClick={() => setIsMobileMenuOpen(false)}
          className="fixed inset-0 bg-black bg-opacity-30 z-30 lg:hidden"
        />
      )}

      {/* Main Content */}
      <main className="pt-16 lg:pl-64 min-h-screen bg-[#F8F9F8]">
        <motion.div
          key={currentPageName}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2 }}
          className="p-6 max-w-[1200px] mx-auto"
        >
          {children}
        </motion.div>
      </main>
    </div>
  );
}
