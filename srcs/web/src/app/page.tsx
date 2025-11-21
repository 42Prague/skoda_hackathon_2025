"use client";

import { useMemo, useState, Suspense } from "react";
import Link from "next/link";
import { Search, User, ChevronRight, Filter, X, AlertTriangle } from "lucide-react";
import usersData from "@/data/users.json";

import { useSearchParams } from "next/navigation";

type FilterType = "all" | "has-gaps" | "no-gaps";

function HRSearchPageContent() {
  const searchParams = useSearchParams();
  const initialSearch = searchParams.get("q") || "";
  const [searchTerm, setSearchTerm] = useState(initialSearch);
  const [displayCount, setDisplayCount] = useState(50);
  const [filter, setFilter] = useState<FilterType>("all");
  const [selectedDepartment, setSelectedDepartment] = useState<string>("all");

  // Get unique departments
  const departments = useMemo(() => {
    const depts = new Set(usersData.map(u => u.department));
    return Array.from(depts).sort();
  }, []);

  const filteredUsers = useMemo(() => {
    let filtered = usersData;

    // Text search
    if (searchTerm) {
      filtered = filtered.filter(user =>
        user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.id.includes(searchTerm) ||
        user.department.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by gaps
    if (filter === "has-gaps") {
      filtered = filtered.filter(user => {
        const skills = user.skills || {};
        return Object.values(skills).some((level: any) => 
          level?.toLowerCase() !== "advanced"
        );
      });
    } else if (filter === "no-gaps") {
      filtered = filtered.filter(user => {
        const skills = user.skills || {};
        const skillLevels = Object.values(skills);
        return skillLevels.length > 0 && skillLevels.every((level: any) => 
          level?.toLowerCase() === "advanced"
        );
      });
    }

    // Filter by department
    if (selectedDepartment !== "all") {
      filtered = filtered.filter(user => user.department === selectedDepartment);
    }

    return filtered;
  }, [searchTerm, filter, selectedDepartment]);

  const visibleUsers = filteredUsers.slice(0, displayCount);

  const handleLoadMore = () => {
    setDisplayCount(prev => prev + 50);
  };

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-slate-950 p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100 mb-2">Employee Skill Search</h1>
          <p className="text-slate-500 dark:text-slate-400">Find employees to view their skill gaps and assign micro-learning.</p>
        </div>

        {/* Search Bar */}
        <div className="max-w-xl mx-auto relative mb-6">
          <Search className="absolute left-4 top-3.5 text-slate-400" size={20} />
          <input
            type="text"
            placeholder="Search by Name or Employee ID..."
            className="w-full pl-12 pr-4 py-3 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all"
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setDisplayCount(50); // Reset pagination on search
            }}
          />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4 justify-center">
          <div className="flex items-center gap-2">
            <Filter size={18} className="text-slate-500 dark:text-slate-400" />
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Filters:</span>
          </div>

          {/* Skill Gap Filter */}
          <div className="flex gap-2">
            <button
              onClick={() => setFilter("all")}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                filter === "all"
                  ? "bg-emerald-600 text-white shadow-md"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
              }`}
            >
              All Employees
            </button>
            <button
              onClick={() => setFilter("has-gaps")}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                filter === "has-gaps"
                  ? "bg-amber-600 text-white shadow-md"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
              }`}
            >
              <AlertTriangle size={16} />
              Has Gaps
            </button>
            <button
              onClick={() => setFilter("no-gaps")}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                filter === "no-gaps"
                  ? "bg-emerald-600 text-white shadow-md"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
              }`}
            >
              No Gaps
            </button>
          </div>

          {/* Department Filter */}
          <select
            value={selectedDepartment}
            onChange={(e) => {
              setSelectedDepartment(e.target.value);
              setDisplayCount(50);
            }}
            className="px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 text-sm font-medium focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all"
          >
            <option value="all">All Departments</option>
            {departments.map(dept => (
              <option key={dept} value={dept}>{dept}</option>
            ))}
          </select>

          {/* Clear Filters */}
          {(filter !== "all" || selectedDepartment !== "all") && (
            <button
              onClick={() => {
                setFilter("all");
                setSelectedDepartment("all");
              }}
              className="px-4 py-2 rounded-lg text-sm font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-all flex items-center gap-2"
            >
              <X size={16} />
              Clear Filters
            </button>
          )}
        </div>

        {/* Results Count */}
        <div className="mt-4 text-center">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Showing <span className="font-semibold text-slate-900 dark:text-slate-100">{filteredUsers.length}</span> employee{filteredUsers.length !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {visibleUsers.map((user) => {
          const skills = user.skills || {};
          const hasGaps = Object.values(skills).some((level: any) => level?.toLowerCase() !== "advanced");
          const gapCount = Object.values(skills).filter((level: any) => level?.toLowerCase() !== "advanced").length;
          
          return (
            <Link key={user.id} href={`/employee/${user.id}`}>
              <div className={`bg-white dark:bg-slate-950 p-4 rounded-xl border transition-all hover:shadow-md group cursor-pointer flex items-center justify-between ${
                hasGaps 
                  ? 'border-amber-200 dark:border-amber-800/50 hover:border-amber-400 dark:hover:border-amber-700' 
                  : 'border-slate-200 dark:border-slate-800 hover:border-emerald-500'
              }`}>
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors flex-shrink-0 ${
                    hasGaps
                      ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 group-hover:bg-amber-200'
                      : 'bg-slate-100 dark:bg-slate-900 text-slate-500 group-hover:bg-emerald-100 group-hover:text-emerald-600'
                  }`}>
                    <User size={20} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium text-slate-900 dark:text-slate-100 truncate">{user.name}</h3>
                      {hasGaps && (
                        <span className="px-2 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 text-xs font-medium rounded-full flex items-center gap-1 flex-shrink-0">
                          <AlertTriangle size={12} />
                          {gapCount}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 truncate">{user.department} • {user.role}</p>
                    <p className="text-xs text-slate-500">Experience: {user.experience_years?.toFixed?.(1) || user.experience_years} yrs</p>
                  </div>
                </div>
                <ChevronRight size={16} className={`flex-shrink-0 transition-colors ${
                  hasGaps 
                    ? 'text-amber-300 group-hover:text-amber-500' 
                    : 'text-slate-300 group-hover:text-emerald-500'
                }`} />
              </div>
            </Link>
          );
        })}
      </div>

      {visibleUsers.length < filteredUsers.length && (
        <div className="flex justify-center pt-8">
          <button
            onClick={handleLoadMore}
            className="px-6 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 font-medium rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors shadow-sm"
          >
            Load More Employees ({filteredUsers.length - visibleUsers.length} remaining)
          </button>
        </div>
      )}

      {filteredUsers.length === 0 && (
        <div className="text-center py-12 text-slate-500">
          No employees found matching &ldquo;{searchTerm}&rdquo;
        </div>
      )}
    </div>
  );
}

export default function HRSearchPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-slate-500 dark:text-slate-400">Loading...</div>
      </div>
    }>
      <HRSearchPageContent />
    </Suspense>
  );
}
