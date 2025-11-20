import { useState, useEffect } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Card } from '@/components/ui/card';
import ProfileTab from './components/tabs/ProfileTab';
import GapsTab from './components/tabs/GapsTab';
import AIPlanTab from './components/tabs/AIPlanTab';
import apiService from './services/api';

function App() {
  // State for data
  const [employees, setEmployees] = useState([]);
  const [roles, setRoles] = useState([]);
  
  // State for selections
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [selectedRole, setSelectedRole] = useState('');
  const [useePlannedPosition, setUsePlannedPosition] = useState(true);
  
  // State for loaded data
  const [profile, setProfile] = useState(null);
  const [gaps, setGaps] = useState(null);
  
  // State for loading
  const [loadingEmployees, setLoadingEmployees] = useState(false);
  const [loadingRoles, setLoadingRoles] = useState(false);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [loadingGaps, setLoadingGaps] = useState(false);
  
  // State for tabs
  const [activeTab, setActiveTab] = useState('profile');

  // Load employees and roles on mount
  useEffect(() => {
    loadEmployees();
    loadRoles();
  }, []);

  // Load profile when employee changes
  useEffect(() => {
    if (selectedEmployee) {
      loadProfile(selectedEmployee);
    } else {
      setProfile(null);
    }
  }, [selectedEmployee]);

  // Load gaps when employee or role changes
  useEffect(() => {
    if (selectedEmployee && selectedRole) {
      loadGaps(selectedEmployee, selectedRole);
    } else {
      setGaps(null);
    }
  }, [selectedEmployee, selectedRole]);

  // Auto-select planned position when employee changes
  useEffect(() => {
    if (selectedEmployee && useePlannedPosition && profile?.employee?.planned_position_id) {
      setSelectedRole(profile.employee.planned_position_id);
    }
  }, [selectedEmployee, useePlannedPosition, profile]);

  const loadEmployees = async () => {
    setLoadingEmployees(true);
    try {
      const data = await apiService.getEmployees();
      setEmployees(data);
    } catch (error) {
      console.error('Error loading employees:', error);
      // Use mock data for development
      setEmployees([
        { personal_number: '00001', user_name: 'DEMO001', profession: 'Developer', planned_position_id: 'POS001', planned_position: 'Senior Developer' },
      ]);
    } finally {
      setLoadingEmployees(false);
    }
  };

  const loadRoles = async () => {
    setLoadingRoles(true);
    try {
      const data = await apiService.getRoles();
      setRoles(data);
    } catch (error) {
      console.error('Error loading roles:', error);
      // Use mock data for development
      setRoles([
        { role_id: 'POS001', name: 'Senior Developer' },
        { role_id: 'POS002', name: 'Team Lead' },
        { role_id: 'POS003', name: 'Technical Architect' },
        { role_id: 'POS004', name: 'Project Manager' },
      ]);
    } finally {
      setLoadingRoles(false);
    }
  };

  const loadProfile = async (personalNumber) => {
    setLoadingProfile(true);
    try {
      const data = await apiService.getProfile(personalNumber);
      setProfile(data);
    } catch (error) {
      console.error('Error loading profile:', error);
      // Use mock data for development
      setProfile({
        employee: { personal_number: personalNumber, user_name: 'DEMO', profession: 'Developer' },
        skills: [{ name: 'JavaScript', source: 'internal', count: 5 }],
        qualifications: [{ name: 'Fire Safety', active: true }],
      });
    } finally {
      setLoadingProfile(false);
    }
  };

  const loadGaps = async (personalNumber, roleId) => {
    setLoadingGaps(true);
    try {
      const data = await apiService.getGaps(personalNumber, roleId);
      setGaps(data);
    } catch (error) {
      console.error('Error loading gaps:', error);
      // Use mock data for development
      setGaps({
        role: { role_id: roleId, name: 'Target Role' },
        required_qualifications: [{ name: 'Advanced Certification' }],
        employee_qualifications: [{ name: 'Fire Safety' }],
        missing_qualifications: [{ name: 'Advanced Certification' }],
      });
    } finally {
      setLoadingGaps(false);
    }
  };

  const handleGenerateAIPlan = async () => {
    if (!profile || !gaps) {
      throw new Error('Profile and gaps data required');
    }

    console.log('🤖 Calling AI plan API...');
    console.log('Employee profile:', profile);
    console.log('Gaps:', gaps);

    try {
      const data = await apiService.generateAIPlan({
        employee_profile: profile,
        gaps: gaps,
      });
      console.log('✅ AI plan received:', data);
      return data;
    } catch (error) {
      console.error('❌ Error generating AI plan:', error);
      console.error('Error details:', error.response?.data || error.message);
      // Re-throw to show error in UI instead of silently using mock data
      throw error;
    }
  };

  const currentEmployee = employees.find(e => e.personal_number === selectedEmployee);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg overflow-hidden flex items-center justify-center">
                <img src="/logo-skoda.png" alt="Škoda Logo" className="w-full h-full object-contain" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">AI Skill Coach</h1>
                <p className="text-sm text-gray-500">Škoda Auto Employee Development</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Sidebar - Selectors */}
          <div className="lg:col-span-1 space-y-4">
            <Card className="p-4">
              <h3 className="font-semibold mb-4">Employee Selection</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Select Employee
                  </label>
                  <Select
                    value={selectedEmployee}
                    onValueChange={(value) => setSelectedEmployee(value)}
                    disabled={loadingEmployees}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Choose employee..." />
                    </SelectTrigger>
                    <SelectContent className="max-h-[300px] overflow-y-auto">
                      {employees.map((emp) => (
                        <SelectItem key={emp.personal_number} value={emp.personal_number}>
                          {emp.user_name} - {emp.profession}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Target Role
                  </label>
                  <Select
                    value={selectedRole}
                    onValueChange={(value) => {
                      setSelectedRole(value);
                      setUsePlannedPosition(value === currentEmployee?.planned_position_id);
                    }}
                    disabled={loadingRoles || !selectedEmployee}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Choose role..." />
                    </SelectTrigger>
                    <SelectContent className="max-h-[300px] overflow-y-auto">
                      {currentEmployee?.planned_position_id && (
                        <SelectItem value={currentEmployee.planned_position_id}>
                          📍 {currentEmployee.planned_position || 'My Planned Position'}
                        </SelectItem>
                      )}
                      {roles
                        .filter(role => role.role_id !== currentEmployee?.planned_position_id)
                        .map((role) => (
                          <SelectItem key={role.role_id} value={role.role_id}>
                            {role.name}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </Card>
          </div>

          {/* Right Content - Tabs */}
          <div className="lg:col-span-3">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="mb-6">
                <TabsTrigger value="profile">
                  Profile
                </TabsTrigger>
                <TabsTrigger value="gaps">
                  Gaps
                </TabsTrigger>
                <TabsTrigger value="ai-plan">
                  AI Plan
                </TabsTrigger>
              </TabsList>

              <TabsContent value="profile">
                <ProfileTab profile={profile} isLoading={loadingProfile} />
              </TabsContent>

              <TabsContent value="gaps">
                <GapsTab gaps={gaps} isLoading={loadingGaps} />
              </TabsContent>

              <TabsContent value="ai-plan">
                <AIPlanTab
                  profile={profile}
                  gaps={gaps}
                  onGeneratePlan={handleGenerateAIPlan}
                />
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
