import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import Index from "./pages/Index";
import Login from "./pages/Login";
import About from "./pages/About";
import EmployeeDashboard from "./pages/EmployeeDashboard";
import EmployeeDashboardNew from "./pages/EmployeeDashboardNew";
import ManagerDashboard from "./pages/ManagerDashboard";
import ManagerDashboardNew from "./pages/ManagerDashboardNew";
import NotFound from "./pages/NotFound";
import Dashboard from "./pages/Dashboard";
import MySkills from "./pages/MySkills";
import CareerPath from "./pages/CareerPath";
import CourseOverview from "./pages/course/CourseOverview";
import LessonViewer from "./pages/course/LessonViewer";
import QuizAssessment from "./pages/course/QuizAssessment";
import PracticalAssignment from "./pages/course/PracticalAssignment";
import CourseCompletion from "./pages/course/CourseCompletion";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/login" element={<Login />} />
          <Route path="/about" element={<About />} />
          <Route path="/employee" element={<EmployeeDashboard />} />
          <Route path="/manager" element={<ManagerDashboard />} />
          
          {/* New Data-Driven Dashboards */}
          <Route path="/employee-new" element={<EmployeeDashboardNew />} />
          <Route path="/manager-new" element={<ManagerDashboardNew />} />
          
          {/* Other Interactive Pages */}
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/my-skills" element={<MySkills />} />
          <Route path="/career-path" element={<CareerPath />} />
          <Route path="/course/overview" element={<CourseOverview />} />
          <Route path="/course/lesson" element={<LessonViewer />} />
          <Route path="/course/quiz" element={<QuizAssessment />} />
          <Route path="/course/assignment" element={<PracticalAssignment />} />
          <Route path="/course/completion" element={<CourseCompletion />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
