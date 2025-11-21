import { GenomeData, ClusterInfo, TimeSeriesPoint } from './types';

// Simulation of Škoda Auto Skill Data (2013-2025)
export const MOCK_GENOME_DATA: GenomeData = {
  nodes: [
    // Cluster 1: Legacy Engineering (Dying)
    { id: "CATIA_V5", group: 1, label: "CATIA V5", value: 80, growth: -0.2 },
    { id: "Combustion_Engines", group: 1, label: "ICE Design", value: 90, growth: -0.4 },
    { id: "Mechanical_Drafting", group: 1, label: "Drafting", value: 60, growth: -0.1 },
    { id: "German_Lang", group: 1, label: "German (Tech)", value: 70, growth: -0.05 },

    // Cluster 2: Software & Cloud (Emerging)
    { id: "Python", group: 2, label: "Python", value: 85, growth: 0.8 },
    { id: "Azure_Cloud", group: 2, label: "Azure", value: 75, growth: 0.9 },
    { id: "Docker", group: 2, label: "Docker", value: 65, growth: 0.7 },
    { id: "Kubernetes", group: 2, label: "Kubernetes", value: 60, growth: 0.85 },
    { id: "React", group: 2, label: "React", value: 50, growth: 0.6 },

    // Cluster 3: EV & Battery (High Growth)
    { id: "Battery_Mgmt", group: 3, label: "BMS", value: 80, growth: 0.95 },
    { id: "High_Voltage", group: 3, label: "High Voltage", value: 85, growth: 0.9 },
    { id: "Power_Electronics", group: 3, label: "Power Elec.", value: 70, growth: 0.8 },

    // Cluster 4: AI & Data (Mutation/New)
    { id: "TensorFlow", group: 4, label: "TensorFlow", value: 40, growth: 0.9 },
    { id: "Computer_Vision", group: 4, label: "Comp. Vision", value: 45, growth: 0.8 },
    { id: "GenAI", group: 4, label: "GenAI", value: 30, growth: 1.0 },
  ],
  links: [
    { source: "CATIA_V5", target: "Mechanical_Drafting", value: 5 },
    { source: "Combustion_Engines", target: "Mechanical_Drafting", value: 4 },
    { source: "Python", target: "TensorFlow", value: 6 },
    { source: "Python", target: "Azure_Cloud", value: 4 },
    { source: "Docker", target: "Kubernetes", value: 8 },
    { source: "Battery_Mgmt", target: "High_Voltage", value: 7 },
    { source: "Battery_Mgmt", target: "Power_Electronics", value: 6 },
    // Cross-cluster links (evolution paths)
    { source: "Python", target: "GenAI", value: 5 },
    { source: "CATIA_V5", target: "High_Voltage", value: 1 }, // Retraining path
    { source: "Combustion_Engines", target: "Battery_Mgmt", value: 2 }, // Retraining path
  ]
};

export const CLUSTER_INFOS: ClusterInfo[] = [
  { id: 1, name: "Legacy Powertrain", description: "Traditional mechanical engineering skills showing gradual decline.", dominantSkills: ["ICE Design", "CATIA"], riskScore: 0.8 },
  { id: 2, name: "Digital Core", description: "Software infrastructure and cloud capabilities.", dominantSkills: ["Azure", "Python"], riskScore: 0.2 },
  { id: 3, name: "E-Mobility", description: "Critical skills for electric vehicle transition.", dominantSkills: ["BMS", "High Voltage"], riskScore: 0.1 },
  { id: 4, name: "AI Mutation", description: "Rapidly emerging algorithmic capabilities.", dominantSkills: ["GenAI", "Computer Vision"], riskScore: 0.4 },
];

export const EVOLUTION_DATA: TimeSeriesPoint[] = [
  { year: '2015', Legacy: 400, Software: 50, EV: 20, AI: 5 },
  { year: '2016', Legacy: 390, Software: 70, EV: 30, AI: 8 },
  { year: '2017', Legacy: 380, Software: 100, EV: 50, AI: 12 },
  { year: '2018', Legacy: 360, Software: 150, EV: 80, AI: 20 },
  { year: '2019', Legacy: 340, Software: 200, EV: 120, AI: 35 },
  { year: '2020', Legacy: 300, Software: 250, EV: 180, AI: 50 },
  { year: '2021', Legacy: 280, Software: 300, EV: 250, AI: 70 },
  { year: '2022', Legacy: 250, Software: 350, EV: 320, AI: 100 },
  { year: '2023', Legacy: 220, Software: 400, EV: 380, AI: 150 },
  { year: '2024', Legacy: 200, Software: 450, EV: 420, AI: 220 },
  { year: '2025', Legacy: 180, Software: 480, EV: 460, AI: 300 },
  { year: '2026 (Pred)', Legacy: 150, Software: 520, EV: 500, AI: 450 },
];
