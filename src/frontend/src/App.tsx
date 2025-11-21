import { ChakraProvider } from '@chakra-ui/react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { system } from './src/theme';
import './src/i18n'; // Initialize i18n
import './styles/globals.css'; // Global styles
import { MainLayout } from './src/components/layout/MainLayout';

// Create a QueryClient instance for TanStack Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
});

// Manager Pages
import { TeamCapabilityDashboard } from './src/pages/manager/TeamCapabilityDashboard';
import { SkillRiskRadarPage } from './src/pages/manager/SkillRiskRadarPage';
import { PromotionReadinessPage } from './src/pages/manager/PromotionReadinessPage';
import { SkillHeatmapPage } from './src/pages/SkillHeatmapPage';
import { EmployeeProfilePage } from './src/pages/EmployeeProfilePage';

// HRBP Pages
import { OrgWideDashboard } from './src/pages/hrbp/OrgWideDashboard';
import { FutureSkillForecast } from './src/pages/hrbp/FutureSkillForecast';

// Employee Pages
import { MyCareerDashboard } from './src/pages/employee/MyCareerDashboard';

// Shared Pages
import { AIAssistantPage } from './src/pages/AIAssistantPage';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ChakraProvider value={system}>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<MainLayout />}>
              {/* Manager Routes */}
              <Route index element={<TeamCapabilityDashboard />} />
              <Route path="risk-radar" element={<SkillRiskRadarPage />} />
              <Route path="promotion-readiness" element={<PromotionReadinessPage />} />
              <Route path="heatmap" element={<SkillHeatmapPage />} />
              <Route path="employees/:id" element={<EmployeeProfilePage />} />
              
              {/* HRBP Routes */}
              <Route path="hrbp/dashboard" element={<OrgWideDashboard />} />
              <Route path="hrbp/forecast" element={<FutureSkillForecast />} />
              
              {/* Employee Routes */}
              <Route path="employee/career" element={<MyCareerDashboard />} />
              
              {/* Shared Routes */}
              <Route path="assistant" element={<AIAssistantPage />} />
              
              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ChakraProvider>
    </QueryClientProvider>
  );
}

export default App;