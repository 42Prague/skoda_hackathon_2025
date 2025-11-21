// Data Structures for the Skill Genome

export interface SkillNode {
  id: string;
  group: number; // Cluster ID
  label: string;
  value: number; // Importance/Frequency
  growth: number; // Evolution metric (-1 to 1)
}

export interface SkillLink {
  source: string;
  target: string;
  value: number; // Strength of connection
}

export interface GenomeData {
  nodes: SkillNode[];
  links: SkillLink[];
}

export interface TimeSeriesPoint {
  year: string;
  [key: string]: number | string;
}

export enum AppView {
  GENOME = 'GENOME',
  EVOLUTION = 'EVOLUTION',
  INSIGHTS = 'INSIGHTS',
  MANAGER_AI = 'MANAGER_AI',
  UPLOAD = 'UPLOAD'
}

export interface ClusterInfo {
  id: number;
  name: string;
  description: string;
  dominantSkills: string[];
  riskScore: number;
}