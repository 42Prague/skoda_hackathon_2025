import React, { createContext, useContext, useState, ReactNode } from "react";

// Types
export interface Skill {
  id: string;
  name: string;
  category: string;
  currentLevel: number;
  targetLevel: number;
  lastUpdated: string;
  trend: "rising" | "stable" | "declining";
}

export interface Course {
  id: string;
  title: string;
  description: string;
  duration: string;
  progress: number;
  skillsImproved: string[];
  modules: CourseModule[];
  status: "not-started" | "in-progress" | "completed";
}

export interface CourseModule {
  id: number;
  type: "lesson" | "quiz" | "assignment" | "summary";
  title: string;
  completed: boolean;
  videoUrl?: string;
  duration?: string;
}

export interface Employee {
  id: string;
  name: string;
  email: string;
  role: string;
  department: string;
  skills: Skill[];
  courses: Course[];
  careerGoals: string[];
  education: string[];
  overallMatch: number;
  promotionReadiness: number;
}

// Mock Data
const mockSkills: Skill[] = [
  { id: "1", name: "Frontend Development", category: "Technical", currentLevel: 85, targetLevel: 90, lastUpdated: "2 days ago", trend: "rising" },
  { id: "2", name: "Backend Development", category: "Technical", currentLevel: 70, targetLevel: 85, lastUpdated: "5 days ago", trend: "stable" },
  { id: "3", name: "Cloud Architecture", category: "Technical", currentLevel: 45, targetLevel: 80, lastUpdated: "2 days ago", trend: "rising" },
  { id: "4", name: "System Design", category: "Technical", currentLevel: 52, targetLevel: 80, lastUpdated: "1 week ago", trend: "rising" },
  { id: "5", name: "DevOps", category: "Technical", currentLevel: 60, targetLevel: 75, lastUpdated: "3 days ago", trend: "stable" },
  { id: "6", name: "Leadership", category: "Soft Skills", currentLevel: 58, targetLevel: 80, lastUpdated: "3 days ago", trend: "rising" },
];

const mockCourses: Course[] = [
  {
    id: "1",
    title: "AWS Cloud Architecture",
    description: "Master cloud infrastructure and architecture patterns",
    duration: "8 weeks",
    progress: 45,
    skillsImproved: ["Cloud Architecture", "DevOps"],
    status: "in-progress",
    modules: [
      { id: 1, type: "lesson", title: "Introduction to AWS", completed: true, videoUrl: "https://www.youtube.com/embed/a9__D53WsUs", duration: "15 min" },
      { id: 2, type: "lesson", title: "EC2 & Compute Services", completed: true, videoUrl: "https://www.youtube.com/embed/iHX-jtKIVNA", duration: "20 min" },
      { id: 3, type: "quiz", title: "Knowledge Check: Basics", completed: false },
      { id: 4, type: "lesson", title: "VPC & Networking", completed: false, videoUrl: "https://www.youtube.com/embed/LX5lHYGFcnA", duration: "25 min" },
      { id: 5, type: "assignment", title: "Deploy a Multi-Tier App", completed: false },
      { id: 6, type: "lesson", title: "Security Best Practices", completed: false, videoUrl: "https://www.youtube.com/embed/Ul2FZdEZuMQ", duration: "18 min" },
      { id: 7, type: "quiz", title: "Final Assessment", completed: false },
      { id: 8, type: "summary", title: "Course Summary", completed: false },
    ]
  },
  {
    id: "2",
    title: "Agile Project Management",
    description: "Learn agile methodologies and team leadership",
    duration: "6 weeks",
    progress: 65,
    skillsImproved: ["Leadership", "Project Management"],
    status: "in-progress",
    modules: [
      { id: 1, type: "lesson", title: "Agile Fundamentals", completed: true, videoUrl: "https://www.youtube.com/embed/Z9QbYZh1YXY", duration: "12 min" },
      { id: 2, type: "lesson", title: "Scrum Framework", completed: true, videoUrl: "https://www.youtube.com/embed/9TycLR0TqFA", duration: "18 min" },
      { id: 3, type: "quiz", title: "Scrum Master Quiz", completed: true },
      { id: 4, type: "lesson", title: "Sprint Planning", completed: true, videoUrl: "https://www.youtube.com/embed/2A9rkiIcnVI", duration: "15 min" },
      { id: 5, type: "assignment", title: "Create Sprint Plan", completed: false },
      { id: 6, type: "lesson", title: "Team Retrospectives", completed: false, videoUrl: "https://www.youtube.com/embed/p0PFcFuZKI8", duration: "10 min" },
      { id: 7, type: "quiz", title: "Final Assessment", completed: false },
      { id: 8, type: "summary", title: "Course Summary", completed: false },
    ]
  },
  {
    id: "3",
    title: "Advanced System Design",
    description: "Design scalable distributed systems",
    duration: "10 weeks",
    progress: 20,
    skillsImproved: ["System Design", "Backend Development"],
    status: "in-progress",
    modules: [
      { id: 1, type: "lesson", title: "System Design Fundamentals", completed: true, videoUrl: "https://www.youtube.com/embed/SqcXvc3ZmRU", duration: "22 min" },
      { id: 2, type: "lesson", title: "Database Design", completed: false, videoUrl: "https://www.youtube.com/embed/ztHopE5Wnpc", duration: "25 min" },
      { id: 3, type: "quiz", title: "Design Principles Quiz", completed: false },
      { id: 4, type: "lesson", title: "Caching Strategies", completed: false, videoUrl: "https://www.youtube.com/embed/U3RkDLtS7uY", duration: "18 min" },
      { id: 5, type: "assignment", title: "Design Instagram", completed: false },
      { id: 6, type: "lesson", title: "Load Balancing", completed: false, videoUrl: "https://www.youtube.com/embed/K0Ta65OqQkY", duration: "16 min" },
      { id: 7, type: "quiz", title: "Final Assessment", completed: false },
      { id: 8, type: "summary", title: "Course Summary", completed: false },
    ]
  },
];

const mockEmployee: Employee = {
  id: "emp-001",
  name: "Jan Novák",
  email: "jan.novak@skoda-auto.cz",
  role: "Software Engineer",
  department: "Engineering",
  skills: mockSkills,
  courses: mockCourses,
  careerGoals: ["Senior Software Engineer", "Team Lead"],
  education: ["BSc Computer Science", "AWS Certified Solutions Architect"],
  overallMatch: 82,
  promotionReadiness: 76,
};

interface EmployeeDataContextType {
  employee: Employee;
  updateSkillLevel: (skillId: string, newLevel: number) => void;
  updateCourseProgress: (courseId: string, moduleId: number, completed: boolean) => void;
  getCourse: (courseTitle: string) => Course | undefined;
}

const EmployeeDataContext = createContext<EmployeeDataContextType | undefined>(undefined);

export const EmployeeDataProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [employee, setEmployee] = useState<Employee>(mockEmployee);

  const updateSkillLevel = (skillId: string, newLevel: number) => {
    setEmployee((prev) => ({
      ...prev,
      skills: prev.skills.map((skill) =>
        skill.id === skillId ? { ...skill, currentLevel: newLevel } : skill
      ),
    }));
  };

  const updateCourseProgress = (courseId: string, moduleId: number, completed: boolean) => {
    setEmployee((prev) => ({
      ...prev,
      courses: prev.courses.map((course) => {
        if (course.id === courseId) {
          const updatedModules = course.modules.map((module) =>
            module.id === moduleId ? { ...module, completed } : module
          );
          const completedCount = updatedModules.filter((m) => m.completed).length;
          const progress = Math.round((completedCount / updatedModules.length) * 100);
          return { ...course, modules: updatedModules, progress };
        }
        return course;
      }),
    }));
  };

  const getCourse = (courseTitle: string) => {
    return employee.courses.find(
      (c) => c.title.toLowerCase() === courseTitle.toLowerCase()
    );
  };

  return (
    <EmployeeDataContext.Provider
      value={{
        employee,
        updateSkillLevel,
        updateCourseProgress,
        getCourse,
      }}
    >
      {children}
    </EmployeeDataContext.Provider>
  );
};

export const useEmployeeData = () => {
  const context = useContext(EmployeeDataContext);
  if (context === undefined) {
    throw new Error("useEmployeeData must be used within EmployeeDataProvider");
  }
  return context;
};
