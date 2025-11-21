/**
 * Employee Analysis Service
 * Analyzes employee skills from courses and compares with job requirements
 */

import XLSX from 'xlsx';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { translatePosition } from '../utils/positionTranslator';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Get dataset path
function getDatasetPath(): string {
  if (process.env.DATASET_PATH) {
    return process.env.DATASET_PATH;
  }
  
  const possiblePaths = [
    '/app/data', // Docker path
    path.join(process.cwd(), 'data'),
    path.join(process.cwd(), '../data'),
    path.join(__dirname, '../../../data'),
  ];
  
  for (const datasetPath of possiblePaths) {
    if (fs.existsSync(datasetPath) && fs.statSync(datasetPath).isDirectory()) {
      const testFile = path.join(datasetPath, 'ERP_SK1.Start_month - SE.csv');
      if (fs.existsSync(testFile)) {
        return datasetPath;
      }
    }
  }
  
  return process.cwd();
}

const DATASET_PATH = getDatasetPath();

// IT Specialist Job Requirements
const IT_SPECIALIST_REQUIREMENTS = {
  'Technical Skills': { requiredLevel: 70, weight: 1.0, isRequired: true },
  'Innovation': { requiredLevel: 65, weight: 0.9, isRequired: true },
  'Digital': { requiredLevel: 70, weight: 0.9, isRequired: true },
  'Adaptability': { requiredLevel: 75, weight: 0.8, isRequired: true },
  'Communication': { requiredLevel: 70, weight: 0.8, isRequired: false },
  'Teamwork': { requiredLevel: 70, weight: 0.8, isRequired: false },
  'Time Management': { requiredLevel: 65, weight: 0.7, isRequired: false },
};

// Course to skill mapping
const COURSE_TO_SKILL_MAPPING: Record<string, string[]> = {
  'ISMS': ['Technical Skills', 'Digital'],
  'IT': ['Technical Skills', 'Digital'],
  'Outlook': ['Technical Skills', 'Communication'],
  'Excel': ['Technical Skills'],
  'Word': ['Technical Skills'],
  'PowerPoint': ['Technical Skills', 'Communication'],
  'Office 365': ['Technical Skills', 'Digital'],
  'Cloud': ['Technical Skills', 'Digital', 'Innovation'],
  'AI': ['Technical Skills', 'Digital', 'Innovation'],
  'Robot': ['Technical Skills', 'Innovation'],
  'Digital': ['Digital'],
  'Internet': ['Digital', 'Technical Skills'],
  'Computer': ['Technical Skills'],
  'Network': ['Technical Skills'],
  'Big Data': ['Technical Skills', 'Digital', 'Innovation'],
  'Virtual Reality': ['Technical Skills', 'Innovation'],
  'Connected Car': ['Technical Skills', 'Innovation'],
  'Communication': ['Communication'],
  'Team': ['Teamwork'],
  'Leadership': ['Teamwork', 'Communication'],
  'Agile': ['Teamwork', 'Adaptability', 'Innovation'],
  'Time Management': ['Time Management'],
  'Stress': ['Time Management', 'Adaptability'],
  'Mentoring': ['Communication', 'Teamwork'],
  'Coaching': ['Communication', 'Teamwork'],
  'Innovation': ['Innovation'],
  'Transformation': ['Innovation', 'Adaptability'],
  'Change': ['Adaptability'],
  'Future': ['Innovation', 'Adaptability'],
  'English': ['Communication'],
  'German': ['Communication'],
  'Jazykový test': ['Communication'],
  'Language': ['Communication'],
  'Compliance': ['Communication', 'Time Management'],
  'GDPR': ['Digital', 'Technical Skills'],
  'Privacy': ['Digital'],
};

function readCSVFile(filename: string): any[] {
  const filePath = path.join(DATASET_PATH, filename);
  
  if (!fs.existsSync(filePath)) {
    return [];
  }

  try {
    const workbook = XLSX.readFile(filePath);
    const sheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[sheetName];
    const data = XLSX.utils.sheet_to_json(worksheet);
    return data;
  } catch (error) {
    console.error(`Error reading ${filename}:`, error);
    return [];
  }
}

function mapCourseToSkills(courseName: string): string[] {
  const courseUpper = courseName.toUpperCase();
  const skills = new Set<string>();
  
  for (const [keyword, skillList] of Object.entries(COURSE_TO_SKILL_MAPPING)) {
    if (courseUpper.includes(keyword.toUpperCase())) {
      skillList.forEach(skill => skills.add(skill));
    }
  }
  
  // Default skills for IT-related courses
  if (skills.size === 0 && (
    courseUpper.includes('IT') || 
    courseUpper.includes('TECHNIC') ||
    courseUpper.includes('DIGIT') ||
    courseUpper.includes('COMPUTER') ||
    courseUpper.includes('SYSTÉM') ||
    courseUpper.includes('SYSTEM')
  )) {
    skills.add('Technical Skills');
    skills.add('Digital');
  }
  
  return Array.from(skills);
}

function calculateRelevanceScore(employeeSkills: Map<string, number>): { score: number; riskLevel: 'Low' | 'Medium' | 'High' } {
  let totalWeightedScore = 0;
  let totalWeight = 0;
  let requiredSkillsMet = 0;
  let totalRequiredSkills = 0;
  
  for (const [skillName, requirement] of Object.entries(IT_SPECIALIST_REQUIREMENTS)) {
    const employeeLevel = employeeSkills.get(skillName) || 0;
    const matchRatio = Math.min(employeeLevel / requirement.requiredLevel, 1.0); // Cap at 1.0 (100%)
    
    totalWeightedScore += matchRatio * requirement.weight * 100;
    totalWeight += requirement.weight;
    
    if (requirement.isRequired) {
      totalRequiredSkills++;
      if (employeeLevel >= requirement.requiredLevel) {
        requiredSkillsMet++;
      }
    }
  }
  
  const baseScore = totalWeight > 0 ? totalWeightedScore / totalWeight : 0;
  
  // Bonus if required skills are met, penalty if not
  const requiredMultiplier = totalRequiredSkills > 0 
    ? 0.5 + (requiredSkillsMet / totalRequiredSkills) * 0.5  // 50-100% based on required skills met
    : 1.0;
  
  const relevanceScore = Math.round(Math.min(baseScore * requiredMultiplier, 100));
  
  // Determine risk level
  let riskLevel: 'Low' | 'Medium' | 'High';
  if (relevanceScore >= 70) {
    riskLevel = 'Low';
  } else if (relevanceScore >= 40) {
    riskLevel = 'Medium';
  } else {
    riskLevel = 'High';
  }
  
  return { score: relevanceScore, riskLevel };
}

/**
 * Analyze employee skills from courses and compare with job requirements
 */
export function analyzeEmployeeForJob(employeeId: string, jobPositionTitle?: string): {
  employeeId: string;
  currentPosition: string;
  skills: { [key: string]: number }; // Changed from Map to object for JSON serialization
  relevanceScore: number;
  riskLevel: 'Low' | 'Medium' | 'High';
  goalPosition: string;
  courses?: any[];
  education?: {
    category: string;
    fieldOfStudy: string;
    branch: string;
  } | null;
} {
  // Normalize employee ID
  const normalizedId = employeeId.replace(/^0+/, '');
  const fullId = normalizedId.padStart(8, '0');
  
  // Read ERP data for current position
  const erpData = readCSVFile('ERP_SK1.Start_month - SE.csv');
  // The CSV uses persstat_start_month.personal_number for employee IDs (not ob1)
  let erpRecord = erpData.find((row: any) => {
    const personalNum = String(row['persstat_start_month.personal_number'] || '').trim();
    const ob1 = String(row['persstat_start_month.ob1'] || '').trim();
    // Match by personal_number first (correct column), then ob1 as fallback
    return personalNum === fullId || 
           personalNum === normalizedId || 
           personalNum.replace(/^0+/, '') === normalizedId ||
           ob1 === fullId || 
           ob1 === normalizedId;
  });
  
  // Try matching by last 6 digits
  if (!erpRecord && fullId.length >= 8) {
    const last6 = fullId.slice(-6);
    erpRecord = erpData.find((row: any) => {
      const personalNum = String(row['persstat_start_month.personal_number'] || '').trim();
      return personalNum.endsWith(last6) || 
             personalNum.replace(/^0+/, '') === last6 ||
             personalNum.replace(/^0+/, '').endsWith(last6);
    });
  }
  
  let currentPosition = 'N/A';
  if (erpRecord) {
    const profession = String(erpRecord['persstat_start_month.profession'] || '').trim();
    currentPosition = profession.replace(/^\d+\s+/, '').trim() || 'N/A';
    // Translate Czech position to English
    currentPosition = translatePosition(currentPosition);
  }
  
  // Read course data
  const courseData = readCSVFile('ZHRPD_VZD_STA_007.csv');
  
  // Get courses for this employee
  const employeeCourses = courseData.filter((row: any) => {
    const columnKeys = Object.keys(row);
    const lastColIndex = columnKeys.length - 1;
    
    let participantId = String(
      row['ID účastníka'] || 
      row['ID_ucastnika'] ||
      row[columnKeys.find((k: string) => k.toLowerCase().includes('ucastnika')) || ''] ||
      (lastColIndex >= 0 ? row[columnKeys[lastColIndex]] : null) ||
      ''
    );
    
    const idNum = typeof participantId === 'number' ? participantId : parseInt(String(participantId || ''), 10);
    const normalizedNum = parseInt(normalizedId, 10);
    
    return !isNaN(idNum) && (idNum === normalizedNum || String(idNum) === normalizedId);
  });
  
  // Map courses to skills
  const skills = new Map<string, number>();
  
  employeeCourses.forEach((course: any) => {
    const columnKeys = Object.keys(course);
    let courseName = String(
      course['Označení typu akce'] || 
      course[columnKeys.find((k: string) => k.toLowerCase().includes('oznaceni')) || ''] ||
      (columnKeys.length > 1 ? course[columnKeys[1]] : null) ||
      ''
    ).trim();
    
    if (!courseName || courseName.length < 3) return;
    
    const mappedSkills = mapCourseToSkills(courseName);
    
    // Each course increases skill level (with diminishing returns)
    mappedSkills.forEach(skillName => {
      const currentLevel = skills.get(skillName) || 0;
      // Diminishing returns: first courses give more, later courses give less
      const baseIncrease = currentLevel < 50 ? 15 : currentLevel < 80 ? 8 : 3;
      const increase = Math.min(baseIncrease + Math.floor(Math.random() * 5), 100 - currentLevel);
      skills.set(skillName, Math.min(currentLevel + increase, 100));
    });
  });
  
  // Ensure all required skills exist
  Object.keys(IT_SPECIALIST_REQUIREMENTS).forEach(skillName => {
    if (!skills.has(skillName)) {
      skills.set(skillName, 0);
    }
  });
  
  // Calculate relevance score
  const { score: relevanceScore, riskLevel } = calculateRelevanceScore(skills);
  
  // Goal position is IT Specialist (m/w) or provided job
  const goalPosition = jobPositionTitle || 'IT Specialist (m/w)';
  
  return {
    employeeId: normalizedId,
    currentPosition,
    skills,
    relevanceScore,
    riskLevel,
    goalPosition,
  };
}

/**
 * Get analysis for multiple employees
 */
export function analyzeEmployeesForManagerMode(employeeIds: string[], goalJobTitle?: string): Array<{
  employeeId: string;
  currentPosition: string;
  skills: Map<string, number>;
  relevanceScore: number;
  riskLevel: 'Low' | 'Medium' | 'High';
  goalPosition: string;
}> {
  return employeeIds.map(id => analyzeEmployeeForJob(id, goalJobTitle));
}

