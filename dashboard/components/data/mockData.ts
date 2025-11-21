export const MOCK_USERS = {
  worker: {
    id: 101,
    name: "Petr Novák",
    role: "Worker",
    position: "Mechanical Technician",
    department: "Assembly Line",
    location: "Mladá Boleslav Plant",
    email: "petr.novak@skoda.com",
    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop",
    compliance: 76,
    skills: ["Hydraulics", "Quality Control", "Safety Protocols", "Machine Operation", "Welding"],
    completedQualifications: [
      { id: "Q-001", name: "Basic Safety Training", completedAt: "2025-01-10", category: "Safety" },
      { id: "Q-002", name: "Quality Management Basics", completedAt: "2024-12-15", category: "Quality" },
      { id: "Q-003", name: "Hydraulic Systems Level 1", completedAt: "2024-11-20", category: "Technical" }
    ],
    missingQualifications: [
      { id: "Q-010", name: "Advanced Machine Safety", dueInDays: 22, priority: "Critical", category: "Safety" },
      { id: "Q-011", name: "Pneumatic Systems Certification", dueInDays: 45, priority: "Important", category: "Technical" },
      { id: "Q-012", name: "Leadership Fundamentals", dueInDays: 90, priority: "Optional", category: "Soft Skills" }
    ]
  },
  manager: {
    id: 12,
    name: "Anna Müller",
    role: "Manager",
    position: "Production Team Lead",
    department: "Production",
    location: "Mladá Boleslav Plant",
    email: "anna.mueller@skoda.com",
    avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&h=150&fit=crop",
    teamSize: 24,
    teamCompliance: 82
  }
};

export const TEAM_MEMBERS = [
  {
    employeeId: 101,
    name: "Petr Novák",
    role: "Mechanical Technician",
    department: "Assembly Line",
    compliance: 76,
    missingCount: 3,
    status: "At Risk",
    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop"
  },
  {
    employeeId: 102,
    name: "Lukas Schneider",
    role: "Production Operator",
    department: "Assembly Line",
    compliance: 89,
    missingCount: 1,
    status: "On Track",
    avatar: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&h=100&fit=crop"
  },
  {
    employeeId: 103,
    name: "Eva Horváth",
    role: "Quality Inspector",
    department: "Quality Control",
    compliance: 95,
    missingCount: 0,
    status: "Compliant",
    avatar: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop"
  },
  {
    employeeId: 104,
    name: "Martin Weber",
    role: "Maintenance Tech",
    department: "Maintenance",
    compliance: 68,
    missingCount: 4,
    status: "Critical",
    avatar: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop"
  },
  {
    employeeId: 105,
    name: "Sofia Kowalski",
    role: "Logistics Coordinator",
    department: "Logistics",
    compliance: 91,
    missingCount: 1,
    status: "On Track",
    avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&h=100&fit=crop"
  },
  {
    employeeId: 106,
    name: "Jan Dvořák",
    role: "Assembly Operator",
    department: "Assembly Line",
    compliance: 54,
    missingCount: 6,
    status: "Critical",
    avatar: "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=100&h=100&fit=crop"
  }
];

export const AI_RECOMMENDATIONS = [
  {
    id: "REC-001",
    qualificationId: "Q-010",
    qualificationName: "Advanced Machine Safety",
    requiredSkills: ["Machine Operation", "Safety Protocols"],
    recommendedCourse: {
      id: "C-301",
      title: "Advanced Safety for Automated Assembly Lines",
      provider: "Škoda Academy",
      durationHours: 5,
      format: "Blended Learning"
    },
    matchScore: 93,
    priority: "Critical",
    explanation: "Based on missing machine safety qualification and role as Mechanical Technician in Assembly Line. This course directly addresses operational safety requirements.",
    applicableEmployees: [101, 102, 106]
  },
  {
    id: "REC-002",
    qualificationId: "Q-011",
    qualificationName: "Pneumatic Systems Certification",
    requiredSkills: ["Hydraulics", "Machine Operation"],
    recommendedCourse: {
      id: "C-302",
      title: "Pneumatic Systems: Theory and Practice",
      provider: "Technical Training Center",
      durationHours: 8,
      format: "In-person Workshop"
    },
    matchScore: 87,
    priority: "Important",
    explanation: "Builds on existing hydraulics knowledge. Essential for working with modern automated production lines.",
    applicableEmployees: [101, 104]
  },
  {
    id: "REC-003",
    qualificationId: "Q-012",
    qualificationName: "Leadership Fundamentals",
    requiredSkills: ["Communication", "Team Coordination"],
    recommendedCourse: {
      id: "C-401",
      title: "Emerging Leaders: First Steps in Management",
      provider: "Škoda Leadership Institute",
      durationHours: 12,
      format: "Online + Workshop"
    },
    matchScore: 78,
    priority: "Optional",
    explanation: "Prepares for future leadership roles. Recommended for high-performing technical staff.",
    applicableEmployees: [101, 103, 105]
  },
  {
    id: "REC-004",
    qualificationId: "Q-015",
    qualificationName: "Quality Systems ISO 9001",
    requiredSkills: ["Quality Control", "Documentation"],
    recommendedCourse: {
      id: "C-205",
      title: "ISO 9001:2015 Quality Management Fundamentals",
      provider: "Quality Academy",
      durationHours: 6,
      format: "E-Learning"
    },
    matchScore: 91,
    priority: "Important",
    explanation: "Critical for quality assurance roles. Ensures compliance with international standards.",
    applicableEmployees: [103, 105]
  }
];

export const LEARNING_PATHS = {
  worker: [
    {
      id: "PATH-001",
      name: "Technical Onboarding Path",
      description: "Essential qualifications for production floor workers",
      totalSteps: 5,
      completedSteps: 3,
      estimatedHours: 24,
      steps: [
        { id: 1, name: "Workplace Safety Basics", status: "completed", hours: 3 },
        { id: 2, name: "Machine Operation Fundamentals", status: "completed", hours: 6 },
        { id: 3, name: "Quality Standards Introduction", status: "completed", hours: 4 },
        { id: 4, name: "Advanced Safety Protocols", status: "in-progress", hours: 5 },
        { id: 5, name: "Specialized Equipment Training", status: "locked", hours: 6 }
      ]
    },
    {
      id: "PATH-002",
      name: "Quality Excellence Path",
      description: "Advanced quality management and inspection skills",
      totalSteps: 4,
      completedSteps: 1,
      estimatedHours: 18,
      steps: [
        { id: 1, name: "Quality Control Basics", status: "completed", hours: 4 },
        { id: 2, name: "Statistical Process Control", status: "available", hours: 6 },
        { id: 3, name: "Root Cause Analysis", status: "locked", hours: 5 },
        { id: 4, name: "ISO 9001 Certification", status: "locked", hours: 3 }
      ]
    }
  ],
  manager: [
    {
      id: "PATH-M01",
      name: "Production Team Lead Development",
      description: "Comprehensive path for new and existing team leaders",
      totalSteps: 6,
      estimatedHours: 36,
      targetRoles: ["Team Lead", "Supervisor"],
      enrolledCount: 8
    },
    {
      id: "PATH-M02",
      name: "Safety Leadership Certification",
      description: "Advanced safety management for production environments",
      totalSteps: 4,
      estimatedHours: 20,
      targetRoles: ["Manager", "Safety Officer"],
      enrolledCount: 12
    },
    {
      id: "PATH-M03",
      name: "Continuous Improvement Mastery",
      description: "Lean manufacturing and process optimization",
      totalSteps: 5,
      estimatedHours: 28,
      targetRoles: ["Manager", "Process Engineer"],
      enrolledCount: 6
    }
  ]
};

export const COMPLIANCE_HEATMAP_DATA = [
  { department: "Assembly Line", week1: 78, week2: 76, week3: 79, week4: 82 },
  { department: "Quality Control", week1: 94, week2: 95, week3: 93, week4: 95 },
  { department: "Maintenance", week1: 71, week2: 68, week3: 72, week4: 74 },
  { department: "Logistics", week1: 88, week2: 89, week3: 91, week4: 90 },
  { department: "Paint Shop", week1: 85, week2: 83, week3: 86, week4: 87 }
];

export const RISK_ALERTS = [
  {
    id: "ALERT-001",
    employeeId: 106,
    employeeName: "Jan Dvořák",
    type: "critical",
    message: "6 critical qualifications missing - immediate action required",
    daysOverdue: 5
  },
  {
    id: "ALERT-002",
    employeeId: 104,
    employeeName: "Martin Weber",
    type: "critical",
    message: "Safety certification expires in 8 days",
    daysOverdue: 0
  },
  {
    id: "ALERT-003",
    employeeId: 101,
    employeeName: "Petr Novák",
    type: "warning",
    message: "Advanced Machine Safety due in 22 days",
    daysOverdue: 0
  },
  {
    id: "ALERT-004",
    employeeId: 102,
    employeeName: "Lukas Schneider",
    type: "warning",
    message: "Quality certification renewal due in 30 days",
    daysOverdue: 0
  }
];
