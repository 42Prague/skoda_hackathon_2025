import { useState } from 'react';
import { Users, TrendingUp, AlertTriangle, Award } from 'lucide-react';
import ComplianceHeatmap from '../components/manager/ComplianceHeatmap';
import TeamMatrixTable from '../components/manager/TeamMatrixTable';
import RiskAlerts from '../components/manager/RiskAlerts';
import TrainingPlanCards from '../components/manager/TrainingPlanCards';
import EmployeeProfileDrawer from '../components/manager/EmployeeProfileDrawer';
import { TEAM_MEMBERS, RISK_ALERTS, COMPLIANCE_HEATMAP_DATA, AI_RECOMMENDATIONS } from '../components/data/mockData';

export default function ManagerDashboard() {
  const [selectedEmployee, setSelectedEmployee] = useState<any>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const handleEmployeeClick = (employee: any) => {
    setSelectedEmployee(employee);
    setIsDrawerOpen(true);
  };

  // Calculate KPIs
  const avgCompliance = Math.round(
    TEAM_MEMBERS.reduce((sum, member) => sum + member.compliance, 0) / TEAM_MEMBERS.length
  );

  // Since certifications field doesn't exist in mockData, we'll calculate based on compliance
  const totalCertifications = TEAM_MEMBERS.reduce((sum, member) => sum + (member.compliance > 85 ? 5 : 3), 0);

  const atRiskCount = TEAM_MEMBERS.filter(m => m.compliance < 80).length;

  const topPerformer = TEAM_MEMBERS.reduce((top, member) =>
    member.compliance > top.compliance ? member : top
  );

  return (
    <div className="max-w-[1200px] mx-auto p-6 space-y-6">
      {/* Page Header */}
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-2xl font-normal text-gray-900">Team Dashboard</h1>
        <p className="text-sm text-gray-600 mt-1">Compliance and skill development overview</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Average Compliance */}
        <div className="bg-white border border-gray-200 rounded-md p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-[#4CAF50]" strokeWidth={2} />
              <span className="text-sm text-gray-600">Avg Compliance</span>
            </div>
          </div>
          <p className="text-3xl font-normal text-gray-900 mt-2">{avgCompliance}%</p>
          <p className="text-xs text-gray-500 mt-1">
            Average across {TEAM_MEMBERS.length} employees
          </p>
        </div>

        {/* Total Certifications */}
        <div className="bg-white border border-gray-200 rounded-md p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Award className="w-5 h-5 text-[#1565C0]" strokeWidth={2} />
              <span className="text-sm text-gray-600">Certifications</span>
            </div>
          </div>
          <p className="text-3xl font-normal text-gray-900 mt-2">{totalCertifications}</p>
          <p className="text-xs text-gray-500 mt-1">
            Total team certifications
          </p>
        </div>

        {/* At Risk */}
        <div className="bg-white border border-gray-200 rounded-md p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-[#FB8C00]" strokeWidth={2} />
              <span className="text-sm text-gray-600">At Risk</span>
            </div>
          </div>
          <p className="text-3xl font-normal text-gray-900 mt-2">{atRiskCount}</p>
          <p className="text-xs text-gray-500 mt-1">
            Below 80% compliance
          </p>
        </div>

        {/* Top Performer */}
        <div className="bg-white border border-gray-200 rounded-md p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Users className="w-5 h-5 text-[#4CAF50]" strokeWidth={2} />
              <span className="text-sm text-gray-600">Top Performer</span>
            </div>
          </div>
          <p className="text-lg font-normal text-gray-900 mt-2">{topPerformer.name}</p>
          <p className="text-xs text-gray-500 mt-1">
            {topPerformer.compliance}% compliance
          </p>
        </div>
      </div>

      {/* Risk Alerts Section */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <div className="border-b border-gray-200 pb-3 mb-4">
          <h2 className="text-lg font-normal text-gray-900">Risk Alerts</h2>
          <p className="text-sm text-gray-600 mt-1">Employees requiring immediate attention</p>
        </div>
        <RiskAlerts alerts={RISK_ALERTS} />
      </div>

      {/* Compliance Heatmap Section */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <div className="border-b border-gray-200 pb-3 mb-4">
          <h2 className="text-lg font-normal text-gray-900">Weekly Compliance Overview</h2>
          <p className="text-sm text-gray-600 mt-1">Team performance by day</p>
        </div>
        <ComplianceHeatmap data={COMPLIANCE_HEATMAP_DATA} />
      </div>

      {/* Recommended Training Plans */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <div className="border-b border-gray-200 pb-3 mb-4">
          <h2 className="text-lg font-normal text-gray-900">Recommended Training Plans</h2>
          <p className="text-sm text-gray-600 mt-1">AI-matched courses for skill gaps</p>
        </div>
        <TrainingPlanCards recommendations={AI_RECOMMENDATIONS} />
      </div>

      {/* Team Matrix Section */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <div className="border-b border-gray-200 pb-3 mb-4">
          <h2 className="text-lg font-normal text-gray-900">Team Skills Matrix</h2>
          <p className="text-sm text-gray-600 mt-1">Detailed skill and certification status</p>
        </div>
        <TeamMatrixTable
          teamMembers={TEAM_MEMBERS}
          onEmployeeClick={handleEmployeeClick}
        />
      </div>

      {/* Employee Profile Drawer */}
      <EmployeeProfileDrawer
        employee={selectedEmployee}
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
      />
    </div>
  );
}
