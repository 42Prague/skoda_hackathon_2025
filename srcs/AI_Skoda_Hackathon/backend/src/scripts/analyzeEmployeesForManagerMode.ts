/**
 * Analyze specific employees (100870, 110153, 110190, 110464, 110542) for Manager Mode
 * 
 * This script:
 * 1. Extracts current positions from ERP_SK1.Start_month - SE.csv
 * 2. Analyzes finished courses from ZHRPD_VZD_STA_007.csv
 * 3. Maps courses to skills
 * 4. Compares with IT Specialist job requirements
 * 5. Calculates Relevance Score and Risk Level
 * 
 * Usage: npx tsx src/scripts/analyzeEmployeesForManagerMode.ts
 */

import XLSX from 'xlsx';
import * as path from 'path';
import * as fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Get dataset path - same logic as seedRealData.ts
function getDatasetPath(): string {
  // Try environment variable first
  if (process.env.DATASET_PATH) {
    return process.env.DATASET_PATH;
  }
  
  // Try multiple possible locations
  const possiblePaths = [
    path.join(process.cwd(), 'data'),
    path.join(process.cwd(), '../data'),
    path.join(__dirname, '../../../data'),
    path.join(__dirname, '../../../../data'),
    '/app/data', // Docker container path
    path.join(process.cwd(), '../../data'),
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

interface EmployeeAnalysis {
  employeeId: string;
  currentPosition: string;
  courses: Array<{ code: string; name: string; startDate: string; endDate: string }>;
  skills: Map<string, number>; // skill name -> level (0-100)
  relevanceScore: number; // 0-100 (how well skills match IT Specialist requirements)
  riskLevel: 'Low' | 'Medium' | 'High';
  goalPosition: string;
}

// IT Specialist Job Requirements (from addITSpecialistJob.ts)
const IT_SPECIALIST_REQUIREMENTS = {
  'Technical Skills': { requiredLevel: 70, weight: 1.0, isRequired: true },
  'Innovation': { requiredLevel: 65, weight: 0.9, isRequired: true },
  'Digital': { requiredLevel: 70, weight: 0.9, isRequired: true },
  'Adaptability': { requiredLevel: 75, weight: 0.8, isRequired: true },
  'Communication': { requiredLevel: 70, weight: 0.8, isRequired: false },
  'Teamwork': { requiredLevel: 70, weight: 0.8, isRequired: false },
  'Time Management': { requiredLevel: 65, weight: 0.7, isRequired: false },
};

// Course name to skill mapping (from analyzing course names)
const COURSE_TO_SKILL_MAPPING: Record<string, string[]> = {
  // Technical Skills
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
  
  // Soft Skills
  'Communication': ['Communication'],
  'Team': ['Teamwork'],
  'Leadership': ['Teamwork', 'Communication'],
  'Agile': ['Teamwork', 'Adaptability', 'Innovation'],
  'Time Management': ['Time Management'],
  'Stress': ['Time Management', 'Adaptability'],
  'Mentoring': ['Communication', 'Teamwork'],
  'Coaching': ['Communication', 'Teamwork'],
  
  // Innovation & Adaptability
  'Innovation': ['Innovation'],
  'Transformation': ['Innovation', 'Adaptability'],
  'Change': ['Adaptability'],
  'Future': ['Innovation', 'Adaptability'],
  'Adaptability': ['Adaptability'],
  
  // Language courses boost Communication
  'English': ['Communication'],
  'German': ['Communication'],
  'Jazykový test': ['Communication'],
  'Language': ['Communication'],
  
  // Compliance courses (basic skills)
  'Compliance': ['Communication', 'Time Management'],
  'Protikorupční': ['Communication'],
  'GDPR': ['Digital', 'Technical Skills'],
  'Privacy': ['Digital'],
};

function readCSVFile(filename: string): any[] {
  const filePath = path.join(DATASET_PATH, filename);
  
  if (!fs.existsSync(filePath)) {
    console.error(`❌ File not found: ${filePath}`);
    return [];
  }

  try {
    const workbook = XLSX.readFile(filePath);
    const sheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[sheetName];
    const data = XLSX.utils.sheet_to_json(worksheet);
    return data;
  } catch (error) {
    console.error(`❌ Error reading ${filename}:`, error);
    return [];
  }
}

function mapCourseToSkills(courseName: string): string[] {
  const courseUpper = courseName.toUpperCase();
  const skills = new Set<string>();
  
  // Check each mapping
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
    courseUpper.includes('SYSTÉM')
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
  
  // Penalty if required skills are not met
  const requiredPenalty = totalRequiredSkills > 0 
    ? (requiredSkillsMet / totalRequiredSkills) * 0.3  // 30% penalty factor
    : 1.0;
  
  const relevanceScore = Math.round(baseScore * requiredPenalty);
  
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

async function main() {
  console.log('📊 Analyzing Employees for Manager Mode\n');
  console.log(`📁 Dataset path: ${DATASET_PATH}\n`);
  
  const targetEmployeeIds = ['00100870', '00110153', '00110190', '00110464', '00110542'];
  const targetIdsShort = ['100870', '110153', '110190', '110464', '110542'];
  
  // 1. Read ERP data for current positions
  console.log('📋 Reading ERP data...');
  const erpData = readCSVFile('ERP_SK1.Start_month - SE.csv');
  
  // 2. Read course data
  console.log('📚 Reading course data...');
  const courseData = readCSVFile('ZHRPD_VZD_STA_007.csv');
  
  const employeeAnalyses: EmployeeAnalysis[] = [];
  
  for (let i = 0; i < targetEmployeeIds.length; i++) {
    const fullId = targetEmployeeIds[i];
    const shortId = targetIdsShort[i];
    
    console.log(`\n🔍 Analyzing Employee ${shortId}...`);
    
    // Get current position from ERP
    // Try multiple matching strategies
    let erpRecord = erpData.find((row: any) => {
      const ob1 = String(row['persstat_start_month.ob1'] || '').trim();
      const personalNum = String(row['persstat_start_month.personal_number'] || '').trim();
      return ob1 === fullId || personalNum === fullId || ob1 === shortId || personalNum === shortId;
    });
    
    // If not found, try matching by last 6 digits (e.g., 00100870 -> 100870)
    if (!erpRecord && fullId.length >= 8) {
      const last6 = fullId.slice(-6);
      erpRecord = erpData.find((row: any) => {
        const ob1 = String(row['persstat_start_month.ob1'] || '').trim();
        const personalNum = String(row['persstat_start_month.personal_number'] || '').trim();
        return ob1.endsWith(last6) || 
               ob1.replace(/^0+/, '').endsWith(last6) ||
               personalNum.endsWith(last6) ||
               personalNum.replace(/^0+/, '').endsWith(last6) ||
               ob1.replace(/^0+/, '') === last6 ||
               personalNum.replace(/^0+/, '') === last6;
      });
    }
    
    let currentPosition = 'N/A';
    if (erpRecord) {
      const profession = String(erpRecord['persstat_start_month.profession'] || '').trim();
      currentPosition = profession.replace(/^\d+\s+/, '').trim() || 'N/A';
      console.log(`   ✅ Found ERP record, position: ${currentPosition}`);
    } else {
      console.log(`   ⚠️  ERP record not found for ${fullId}`);
    }
    
    // Get courses for this employee (match by ID in last column)
    // CSV format: Typ akce, Označení typu akce, IDOBJ, Datum zahájení, Datum ukončení, ID účastníka
    const employeeCourses = courseData.filter((row: any) => {
      // Try different column names (handle encoding issues)
      const columnKeys = Object.keys(row);
      const lastColIndex = columnKeys.length - 1;
      
      // Try exact column name first
      let participantId = String(
        row['ID účastníka'] || 
        row['ID_ucastnika'] || 
        row['ID ucastnika'] ||
        // Handle encoding issues
        row[columnKeys.find((k: string) => k.toLowerCase().includes('ucastnika') || k.toLowerCase().includes('účastníka')) || ''] ||
        // Last column (should be participant ID)
        (lastColIndex >= 0 ? row[columnKeys[lastColIndex]] : null) ||
        // Try finding value that matches ID
        Object.values(row).find((val: any) => {
          const numVal = typeof val === 'number' ? val : parseInt(String(val || ''), 10);
          return !isNaN(numVal) && (
            numVal === parseInt(shortId, 10) || 
            numVal === parseInt(fullId, 10) ||
            String(numVal) === shortId ||
            String(numVal) === fullId
          );
        }) ||
        ''
      );
      
      // Convert to number for comparison if it's a number
      const idNum = typeof participantId === 'number' ? participantId : parseInt(String(participantId || ''), 10);
      const shortIdNum = parseInt(shortId, 10);
      const fullIdNum = parseInt(fullId, 10);
      
      // Match by number or string
      return !isNaN(idNum) && (
        idNum === shortIdNum || 
        idNum === fullIdNum ||
        String(idNum) === shortId ||
        String(idNum) === fullId ||
        String(participantId).trim() === shortId ||
        String(participantId).trim() === fullId
      );
    });
    
    console.log(`   Found ${employeeCourses.length} courses`);
    
    // Map courses to skills
    const skills = new Map<string, number>();
    
    employeeCourses.forEach((course: any) => {
      // CSV columns: Typ akce, Označení typu akce, IDOBJ, Datum zahájení, Datum ukončení, ID účastníka
      // Column names might be with/without diacritics or encoding issues
      const columnKeys = Object.keys(course);
      
      // Try to find course name column (usually 2nd column, index 1)
      let courseName = String(
        course['Označení typu akce'] || 
        course['Oznaceni typu akce'] ||
        // Handle encoding issues (check for partial matches)
        course[columnKeys.find((k: string) => k.toLowerCase().includes('oznaceni') || k.toLowerCase().includes('označení')) || ''] ||
        // Second column (index 1) should be course name
        (columnKeys.length > 1 ? course[columnKeys[1]] : null) ||
        // Try Typ akce as fallback
        course['Typ akce'] ||
        course[columnKeys.find((k: string) => k.toLowerCase().includes('typ akce')) || ''] ||
        ''
      ).trim();
      
      if (!courseName || courseName.length < 3) {
        // If still no course name, skip
        return;
      }
      
      const mappedSkills = mapCourseToSkills(courseName);
      
      // Each course increases skill level by 5-10 points (up to max 100)
      mappedSkills.forEach(skillName => {
        const currentLevel = skills.get(skillName) || 0;
        const increase = Math.min(8 + Math.floor(Math.random() * 5), 100 - currentLevel); // 8-12 points
        skills.set(skillName, Math.min(currentLevel + increase, 100));
      });
    });
    
    // Ensure all required skills have some level (even if 0)
    Object.keys(IT_SPECIALIST_REQUIREMENTS).forEach(skillName => {
      if (!skills.has(skillName)) {
        skills.set(skillName, 0);
      }
    });
    
    // Calculate relevance score
    const { score: relevanceScore, riskLevel } = calculateRelevanceScore(skills);
    
    // Goal position is IT Specialist (m/w)
    const goalPosition = 'IT Specialist (m/w)';
    
    employeeAnalyses.push({
      employeeId: shortId,
      currentPosition,
      courses: employeeCourses.slice(0, 10).map((c: any) => {
        const keys = Object.keys(c);
        return {
          code: String(c['Typ akce'] || (keys.length > 0 ? Object.values(c)[0] : '') || ''),
          name: String(c['Označení typu akce'] || (keys.length > 1 ? Object.values(c)[1] : '') || ''),
          startDate: String(c['Datum zahájení'] || c['Datum_zahajeni'] || (keys.length > 3 ? Object.values(c)[3] : '') || ''),
          endDate: String(c['Datum ukončení'] || c['Datum_ukonceni'] || (keys.length > 4 ? Object.values(c)[4] : '') || ''),
        };
      }),
      skills,
      relevanceScore,
      riskLevel,
      goalPosition,
    });
    
    console.log(`   Current Position: ${currentPosition}`);
    console.log(`   Relevance Score: ${relevanceScore}%`);
    console.log(`   Risk Level: ${riskLevel}`);
    console.log(`   Skills: ${Array.from(skills.entries()).map(([name, level]) => `${name}(${level})`).join(', ')}`);
  }
  
  // Print summary table
  console.log('\n' + '='.repeat(80));
  console.log('📊 MANAGER MODE TEAM SKILL OVERVIEW - ANALYSIS RESULTS');
  console.log('='.repeat(80));
  console.log('\n');
  console.log('Employee ID | Current Position | Relevance Score | Risk Level | Goal Position');
  console.log('-'.repeat(80));
  
  employeeAnalyses.forEach(emp => {
    const position = emp.currentPosition.length > 30 
      ? emp.currentPosition.substring(0, 27) + '...' 
      : emp.currentPosition.padEnd(30);
    console.log(
      `${emp.employeeId.padEnd(11)} | ${position.padEnd(30)} | ${String(emp.relevanceScore).padStart(3)}%${' '.repeat(9)} | ${emp.riskLevel.padEnd(9)} | ${emp.goalPosition}`
    );
  });
  
  console.log('\n' + '='.repeat(80));
  console.log('✅ Analysis complete! Use this data to populate Manager Dashboard.');
  console.log('='.repeat(80));
  
  // Export to JSON for use in backend (convert Map to object for JSON)
  const outputData = employeeAnalyses.map(emp => ({
    ...emp,
    skills: Object.fromEntries(emp.skills), // Convert Map to object for JSON
  }));
  
  const outputPath = path.join(process.cwd(), 'manager_mode_analysis.json');
  fs.writeFileSync(outputPath, JSON.stringify(outputData, null, 2));
  console.log(`\n💾 Results exported to: ${outputPath}`);
}

main().catch(console.error);

