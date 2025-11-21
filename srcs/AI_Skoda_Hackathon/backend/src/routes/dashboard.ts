import express from 'express';
import { prisma } from '../lib/prisma';
import { authenticate } from '../middleware/auth';
import XLSX from 'xlsx';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { analyzeEmployeeForJob } from '../services/employeeAnalysis';
import { translatePosition } from '../utils/positionTranslator';
import { translateCourseName } from '../utils/courseTranslator';

const router = express.Router();

// Get dataset path (same logic as seedRealData.ts)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const possibleDatasetPaths = [
  '/app/data', // Docker path
  path.join(__dirname, '../../../data') // Local path
];

function getDatasetPath(): string {
  for (const datasetPath of possibleDatasetPaths) {
    if (fs.existsSync(datasetPath)) {
      return datasetPath;
    }
  }
  return '';
}

// Employee data from CSV: personal_number -> { profession, planned_profession }
interface EmployeeCSVData {
  personalNumber: string;
  profession: string; // Current position
  plannedProfession: string; // Goal position
}

// Read employee data from CSV file (profession and planned_profession)
function getEmployeeCSVData(): Map<string, EmployeeCSVData> {
  const datasetPath = getDatasetPath();
  if (!datasetPath) {
    console.warn('Dataset path not found, employee data will be empty');
    return new Map();
  }

  const filePath = path.join(datasetPath, 'ERP_SK1.Start_month - SE.csv');
  if (!fs.existsSync(filePath)) {
    console.warn('ERP CSV file not found, employee data will be empty');
    return new Map();
  }

  try {
    const workbook = XLSX.readFile(filePath);
    const sheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[sheetName];
    const data = XLSX.utils.sheet_to_json(worksheet);
    
    const employeeMap = new Map<string, EmployeeCSVData>();
    
    data.forEach((row: any) => {
      // Personal number is in personal_number column (first column in CSV)
      // The CSV has: persstat_start_month.personal_number = employee ID (e.g., "00004241" or 4241 as number)
      //              persstat_start_month.ob1 = category code (e.g., "S")
      // Handle both string and number formats (XLSX may parse as number)
      let personalNumber: string;
      if (row['persstat_start_month.personal_number'] !== undefined && row['persstat_start_month.personal_number'] !== null) {
        // Convert to string (handles both string and number)
        personalNumber = String(row['persstat_start_month.personal_number']).trim();
      } else {
        // Fallback to ob1 if personal_number doesn't exist
        personalNumber = String(row['persstat_start_month.ob1'] || '').trim();
      }
      
      // Skip if personal number is invalid (like "S" or empty or too short)
      if (!personalNumber || personalNumber === 'S' || personalNumber === 'null' || personalNumber === 'NULL') {
        return;
      }
      
      // Validate it's numeric (after removing leading zeros)
      const normalizedId = personalNumber.replace(/^0+/, '') || personalNumber;
      if (!/^\d+$/.test(normalizedId) || normalizedId.length < 4) {
        return;
      }
      
      // Get profession (current position) - remove code prefix
      let profession = String(row['persstat_start_month.profession'] || '').trim();
      if (profession && profession !== 'NULL' && profession.toLowerCase() !== 'null') {
        // Remove code prefix: "502 Pedagogický/á pracovník/-vnice" -> "Pedagogický/á pracovník/-vnice"
        profession = profession.replace(/^\d+\s+/, '').trim();
      } else {
        profession = '';
      }
      
      // Get planned_profession (goal position) - remove code prefix
      let plannedProfession = String(row['persstat_start_month.planned_profession'] || '').trim();
      if (plannedProfession && plannedProfession !== 'NULL' && plannedProfession.toLowerCase() !== 'null') {
        // Remove code prefix: "502 Pedagogický/á pracovník/-vnice" -> "Pedagogický/á pracovník/-vnice"
        plannedProfession = plannedProfession.replace(/^\d+\s+/, '').trim();
      } else {
        plannedProfession = '';
      }
      
      // Only add if we have valid personal number and at least profession
      // Store with both full ID (with leading zeros) and normalized ID (without leading zeros)
      if (personalNumber && (profession || plannedProfession)) {
        const normalizedId = personalNumber.replace(/^0+/, '') || personalNumber;
        // Ensure full ID is 8 digits with leading zeros
        const fullId = normalizedId.padStart(8, '0');
        
        const employeeData = {
          personalNumber: fullId,
          profession: profession || 'N/A',
          plannedProfession: plannedProfession || profession || 'N/A', // Fallback to profession if planned_profession is empty
        };
        
        // Store with full ID (e.g., "00004241")
        employeeMap.set(fullId, employeeData);
        // Also store with normalized ID (e.g., "4241") for easier matching
        if (normalizedId !== fullId) {
          employeeMap.set(normalizedId, employeeData);
        }
        // Also store with original format if different
        if (personalNumber !== fullId && personalNumber !== normalizedId) {
          employeeMap.set(personalNumber, employeeData);
        }
      }
    });
    
    console.log(`Loaded ${employeeMap.size} employees from CSV`);
    return employeeMap;
  } catch (error) {
    console.error('Error reading employee data from CSV:', error);
    return new Map();
  }
}

// Helper function to read CSV files
function readCSVFile(filename: string): any[] {
  const datasetPath = getDatasetPath();
  if (!datasetPath) {
    return [];
  }
  
  const filePath = path.join(datasetPath, filename);
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

// Legacy function for backward compatibility - now uses profession from getEmployeeCSVData
// Read position data from CSV file
function getEmployeePositions(): Map<string, string> {
  const employeeMap = getEmployeeCSVData();
  const positionMap = new Map<string, string>();
  
  employeeMap.forEach((data, personalNumber) => {
    positionMap.set(personalNumber, data.profession);
  });
  
  return positionMap;
}

// Read IT fitness scores from JSON file
function getITFitnessScores(): Map<string, number> {
  const fitnessScores = new Map<string, number>();
  
  // Hardcoded scores as fallback (from it_fitness_scores.json)
  const hardcodedScores: Record<string, number> = {
    '100870': 70,
    '110153': 78,
    '110190': 68,
    '110464': 55,
    '110542': 85,
  };
  
  // Try to read from fitness_prediction folder
  const possiblePaths = [
    // From project root (assuming backend/src/routes -> ../../..)
    path.join(__dirname, '../../../fitness_prediction/it_fitness_scores.json'),
    // Alternative: from backend folder
    path.join(__dirname, '../../fitness_prediction/it_fitness_scores.json'),
    // From current working directory
    path.join(process.cwd(), 'fitness_prediction/it_fitness_scores.json'),
    path.join(process.cwd(), '../fitness_prediction/it_fitness_scores.json'),
    // Docker path
    '/app/fitness_prediction/it_fitness_scores.json',
  ];
  
  let loaded = false;
  for (const filePath of possiblePaths) {
    try {
      if (fs.existsSync(filePath)) {
        const fileContent = fs.readFileSync(filePath, 'utf-8');
        const scores = JSON.parse(fileContent);
        
        console.log(`📊 Found IT fitness scores file: ${filePath}`);
        console.log(`📊 Raw scores:`, scores);
        
        // Store with normalized IDs (without leading zeros) for easier matching
        for (const [empId, score] of Object.entries(scores)) {
          const normalizedId = String(empId).replace(/^0+/, '') || String(empId);
          const fullId = normalizedId.padStart(8, '0');
          
          // Store with multiple formats for flexible matching
          fitnessScores.set(normalizedId, score as number);
          fitnessScores.set(String(empId), score as number);
          if (fullId !== normalizedId && fullId !== String(empId)) {
            fitnessScores.set(fullId, score as number);
          }
          
          console.log(`  - Employee ID: ${empId} (normalized: ${normalizedId}, full: ${fullId}) -> Score: ${score}`);
        }
        
        console.log(`✅ Loaded ${fitnessScores.size} IT fitness score entries from ${filePath}`);
        loaded = true;
        break;
      }
    } catch (error) {
      console.warn(`⚠️  Could not read fitness scores from ${filePath}:`, error);
    }
  }
  
  // If file not loaded, use hardcoded scores
  if (!loaded) {
    console.warn('⚠️  IT fitness scores file not found. Using hardcoded scores.');
    console.warn('   Tried paths:', possiblePaths);
    
    for (const [empId, score] of Object.entries(hardcodedScores)) {
      const normalizedId = String(empId).replace(/^0+/, '') || String(empId);
      const fullId = normalizedId.padStart(8, '0');
      
      fitnessScores.set(normalizedId, score);
      fitnessScores.set(String(empId), score);
      if (fullId !== normalizedId && fullId !== String(empId)) {
        fitnessScores.set(fullId, score);
      }
    }
    
    console.log(`✅ Loaded ${fitnessScores.size} hardcoded IT fitness score entries`);
  }
  
  return fitnessScores;
}

// Get employee dashboard data (personalized for logged-in user)
router.get('/employee/:userId', authenticate, async (req: any, res) => {
  try {
    const { userId } = req.params;

    // Users can only view their own dashboard unless they're managers
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN' && req.userId !== userId) {
      return res.status(403).json({ error: 'Forbidden' });
    }

    // Get user details
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: {
        id: true,
        firstName: true,
        lastName: true,
        email: true,
        employeeId: true,
        department: true,
        role: true,
      },
    });

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    // Get user skills with skill details
    const userSkills = await prisma.userSkill.findMany({
      where: { userId },
      include: {
        skill: {
          select: {
            id: true,
            name: true,
            category: true,
            marketRelevance: true,
          },
        },
      },
      orderBy: {
        level: 'desc',
      },
    });

    // Get skill risk analysis for this employee
    const skillRisks = await prisma.employeeSkillRisk.findMany({
      where: {
        OR: [
          { userId },
          { employeeId: user.employeeId || '' },
        ],
      },
      include: {
        skill: {
          select: {
            id: true,
            name: true,
            category: true,
          },
        },
      },
      orderBy: {
        riskScore: 'desc',
      },
    });

    // Calculate overall risk score
    const avgRiskScore = skillRisks.length > 0
      ? skillRisks.reduce((sum, risk) => sum + risk.riskScore, 0) / skillRisks.length
      : 0;

    const riskLevel = avgRiskScore > 70 ? 'HIGH' : avgRiskScore > 40 ? 'MEDIUM' : 'LOW';

    // Get career paths
    const careerPaths = await prisma.careerPath.findMany({
      include: {
        skills: {
          include: {
            skill: true,
          },
        },
      },
      orderBy: {
        fitScore: 'desc',
      },
      take: 3,
    });

    // Calculate skill gaps for career paths
    const careerPathsWithGaps = careerPaths.map((path) => {
      const requiredSkills = path.skills;
      const gaps = requiredSkills.map((required) => {
        const userSkill = userSkills.find((us) => us.skillId === required.skillId);
        const currentLevel = userSkill?.level || 0;
        const requiredLevel = required.requiredLevel || 70;
        const gap = Math.max(0, requiredLevel - currentLevel);

        return {
          skillId: required.skillId,
          skillName: required.skill.name,
          currentLevel,
          requiredLevel,
          gap,
        };
      });

      return {
        ...path,
        skillGaps: gaps,
        overallGap: gaps.reduce((sum, g) => sum + g.gap, 0) / (gaps.length || 1),
      };
    });

    // Get enrollments and progress
    const enrollments = await prisma.enrollment.findMany({
      where: { userId },
      include: {
        course: {
          include: {
            courseSkills: {
              include: {
                skill: true,
              },
            },
          },
        },
      },
      orderBy: {
        enrolledAt: 'desc',
      },
    });

    // Get recommended courses based on skill gaps
    const skillGapIds = careerPathsWithGaps
      .flatMap((cp) => cp.skillGaps.filter((g) => g.gap > 20).map((g) => g.skillId))
      .slice(0, 10);

    const recommendedCourses = await prisma.course.findMany({
      where: {
        courseSkills: {
          some: {
            skillId: {
              in: skillGapIds,
            },
          },
        },
      },
      include: {
        courseSkills: {
          include: {
            skill: true,
          },
        },
      },
      take: 5,
    });

    // Get assessments
    const assessments = await prisma.assessment.findMany({
      where: { userId },
      orderBy: {
        createdAt: 'desc',
      },
      take: 5,
    });

    // Get employee courses from CSV data for knowledge graph
    let coursesData: any[] = [];
    let educationData: any = null;
    
    if (user.employeeId) {
      try {
        // Read course data from CSV
        const courseData = readCSVFile('ZHRPD_VZD_STA_007.csv');
        const normalizedId = user.employeeId.replace(/^0+/, '');
        
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
        
        // Format courses for knowledge graph (translate course names to English)
        coursesData = employeeCourses.map((course: any) => {
          const columnKeys = Object.keys(course);
          const courseName = String(
            course['Označení typu akce'] || 
            course[columnKeys.find((k: string) => k.toLowerCase().includes('oznaceni')) || ''] ||
            (columnKeys.length > 1 ? course[columnKeys[1]] : null) ||
            ''
          ).trim();
          
          const courseCode = String(
            course['Typ akce'] || 
            (columnKeys.length > 0 ? course[columnKeys[0]] : '') ||
            ''
          ).trim();
          
          const startDate = course['Datum zahájení'] || course[columnKeys[3]] || null;
          const endDate = course['Datum ukončení'] || course[columnKeys[4]] || null;
          
          // Translate course name from Czech to English
          const translatedCourseName = translateCourseName(courseName);
          
          return {
            code: courseCode,
            name: translatedCourseName, // Translated to English
            originalName: courseName, // Keep original for reference
            startDate: startDate ? new Date(startDate).toISOString() : null,
            endDate: endDate ? new Date(endDate).toISOString() : null,
          };
        });
        
        // Get education data from ERP CSV
        const erpData = readCSVFile('ERP_SK1.Start_month - SE.csv');
        const fullId = normalizedId.padStart(8, '0');
        let erpRecord = erpData.find((row: any) => {
          const personalNumber = String(row['persstat_start_month.personal_number'] || row['persstat_start_month.ob1'] || '').trim();
          const normalizedPersonal = personalNumber.replace(/^0+/, '') || personalNumber;
          return personalNumber === fullId || personalNumber === normalizedId || normalizedPersonal === normalizedId || normalizedPersonal === fullId;
        });
        
        if (erpRecord) {
          educationData = {
            educationCategory: erpRecord['persstat_start_month.education_category_name'] || null,
            fieldOfStudy: erpRecord['persstat_start_month.field_of_study_name'] || null,
            basicBranch: erpRecord['persstat_start_month.basic_branch_of_education_name'] || null,
          };
        }
      } catch (error) {
        console.error('Error fetching employee courses from CSV:', error);
        // Continue without course data if there's an error
      }
    }

    res.json({
      user,
      skillRelevanceScore: 100 - avgRiskScore,
      riskLevel,
      userSkills: userSkills.map((us) => ({
        skill: us.skill.name,
        category: us.skill.category,
        level: us.level,
        marketRelevance: us.skill.marketRelevance,
      })),
      skillRisks: skillRisks.map((sr) => ({
        skillName: sr.skillName,
        riskScore: sr.riskScore,
        riskLabel: sr.riskLabel,
        avgFutureDemand: sr.avgFutureDemand,
        automationExposure: sr.automationExposure,
      })),
      careerPaths: careerPathsWithGaps.map((cp) => ({
        id: cp.id,
        title: cp.title,
        description: cp.description,
        targetRole: cp.targetRole,
        fitScore: cp.fitScore,
        reason: cp.reason,
        skillGaps: cp.skillGaps,
        overallGap: cp.overallGap,
      })),
      enrollments: enrollments.map((e) => ({
        id: e.id,
        courseId: e.courseId,
        courseTitle: e.course.title,
        progress: e.progress,
        enrolledAt: e.enrolledAt,
        completedAt: e.completedAt,
        skills: e.course.courseSkills.map((cs) => cs.skill.name),
      })),
      recommendedCourses: recommendedCourses.map((c) => ({
        id: c.id,
        title: c.title,
        description: c.description,
        duration: c.duration,
        difficulty: c.difficulty,
        skills: c.courseSkills.map((cs) => cs.skill.name),
      })),
      assessments: assessments.map((a) => ({
        id: a.id,
        name: a.name,
        status: a.status,
        score: a.score,
        maxScore: a.maxScore,
        completedAt: a.completedAt,
      })),
      courses: coursesData, // Courses from CSV for knowledge graph (translated to English)
      education: educationData, // Education/degree information
    });
  } catch (error) {
    console.error('Get employee dashboard error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get job matches for employee with three-tier classification
router.get('/employee/:userId/job-matches', authenticate, async (req: any, res) => {
  try {
    const { userId } = req.params;

    // Only employee can view their own matches
    if (req.userRole !== 'EMPLOYEE' && req.userId !== userId && req.userRole !== 'ADMIN' && req.userRole !== 'MANAGER') {
      return res.status(403).json({ error: 'Forbidden' });
    }

    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: {
        id: true,
        employeeId: true,
      },
    });

    if (!user || !user.employeeId) {
      return res.status(404).json({ error: 'User not found or no employee ID' });
    }

    // Import job matching service
    const { getJobMatchesForEmployee } = await import('../services/jobMatching');
    
    // Get all job matches
    const matches = await getJobMatchesForEmployee(user.employeeId, userId);

    // Separate matches by tier for easier frontend handling
    const perfectMatches = matches.filter(m => m.matchTier === 'HIGH');
    const middleMatches = matches.filter(m => m.matchTier === 'MIDDLE');
    const lowMatches = matches.filter(m => m.matchTier === 'LOW');

    res.json({
      matches,
      perfectMatches, // ≥85% fitness
      middleMatches,  // 50-84% fitness
      lowMatches,     // <50% fitness
    });
  } catch (error) {
    console.error('Get job matches error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Apply for job (create job application)
router.post('/employee/:userId/job-applications', authenticate, async (req: any, res) => {
  try {
    const { userId } = req.params;
    const { jobPositionId } = req.body;

    // Only employee can apply for jobs
    if (req.userRole !== 'EMPLOYEE' && req.userId !== userId && req.userRole !== 'ADMIN') {
      return res.status(403).json({ error: 'Forbidden' });
    }

    if (!jobPositionId) {
      return res.status(400).json({ error: 'Job position ID is required' });
    }

    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: {
        id: true,
        employeeId: true,
      },
    });

    if (!user || !user.employeeId) {
      return res.status(404).json({ error: 'User not found or no employee ID' });
    }

    // Import job matching service
    const { createJobApplicationWithMatch } = await import('../services/jobMatching');
    
    // Create application with match details
    const { application, match } = await createJobApplicationWithMatch(
      user.employeeId,
      jobPositionId,
      userId
    );

    res.status(201).json({
      application,
      match,
      message: match.matchTier === 'HIGH' 
        ? 'Congratulations! You have been selected for an interview.' 
        : match.matchTier === 'MIDDLE'
        ? 'Courses have been recommended to improve your fit.'
        : 'A growth roadmap has been suggested.',
    });
  } catch (error: any) {
    console.error('Create job application error:', error);
    res.status(500).json({ error: error.message || 'Internal server error' });
  }
});

// Get manager dashboard data (team overview)
router.get('/manager/:managerId', authenticate, async (req: any, res) => {
  try {
    const { managerId } = req.params;

    // Only managers can view team dashboards
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN' && req.userId !== managerId) {
      return res.status(403).json({ error: 'Forbidden' });
    }

    // Get employee 00016687 specifically first
    const targetEmployee = await prisma.user.findFirst({
      where: {
        employeeId: '00016687',
        role: 'EMPLOYEE',
      },
      select: {
        id: true,
        firstName: true,
        lastName: true,
        employeeId: true,
        email: true,
        department: true,
        role: true,
      },
    });

    // Get exactly 5 employees from database (from ERP data) - ordered by employeeId
    // These should match the employees from the CSV file
    const allEmployees = await prisma.user.findMany({
      where: {
        employeeId: { not: null }, // Only employees with employeeId from ERP CSV
        role: 'EMPLOYEE',
      },
      select: {
        id: true,
        firstName: true,
        lastName: true,
        employeeId: true,
        email: true,
        department: true,
        role: true,
      },
      orderBy: {
        employeeId: 'asc', // Order by employeeId to get consistent first employees
      },
      take: 5, // Get exactly 5 employees
    });

    const finalEmployees = allEmployees.slice(0, 5); // Ensure exactly 5

    // Get employee data from CSV file (profession and planned_profession)
    const employeeCSVData = getEmployeeCSVData();
    
    // Get IT fitness scores for specific employees (load once, use for all employees)
    const itFitnessScores = getITFitnessScores();
    console.log(`📊 IT Fitness Scores Map size: ${itFitnessScores.size}`);
    if (itFitnessScores.size > 0) {
      console.log(`📊 IT Fitness Scores keys:`, Array.from(itFitnessScores.keys()));
    }
    
    // Log the employee IDs we're processing
    console.log(`📋 Processing ${finalEmployees.length} employees:`);
    finalEmployees.forEach(emp => {
      console.log(`  - Employee ID: "${emp.employeeId}" (type: ${typeof emp.employeeId})`);
    });

    // Get open job positions BEFORE employee mapping (to use for goal position matching)
    // Handle case where JobPosition table doesn't exist yet (migration not run)
    let openJobPositions: any[] = [];
    try {
      openJobPositions = await prisma.jobPosition.findMany({
        where: {
          status: 'OPEN',
        },
        select: {
          id: true,
          title: true,
          department: true,
          location: true,
          description: true,
        },
        orderBy: {
          postedAt: 'desc',
        },
        take: 10, // Limit to 10 most recent
      });
    } catch (error: any) {
      // If JobPosition table doesn't exist, return empty array (migration not run yet)
      console.warn('JobPosition table not found, returning empty array. Run migration first:', error?.message);
      openJobPositions = [];
    }

    // Find "IT Specialist (m/w)" job position for goal matching
    const itSpecialistJob = openJobPositions.find(job => 
      job.title && job.title.toLowerCase().includes('it specialist')
    );

    // Get skill risks for these employees
    const finalEmployeeIds = finalEmployees.map((e) => e.employeeId).filter((id) => id !== null) as string[];
    const userIds = finalEmployees.map((e) => e.id);

    // Build where clause - avoid empty arrays in Prisma queries
    const whereClause: any = {};
    if (finalEmployeeIds.length > 0 || userIds.length > 0) {
      const orConditions: any[] = [];
      if (finalEmployeeIds.length > 0) {
        orConditions.push({ employeeId: { in: finalEmployeeIds } });
      }
      if (userIds.length > 0) {
        orConditions.push({ userId: { in: userIds } });
      }
      whereClause.OR = orConditions;
    } else {
      // If no employees found, return empty result
      whereClause.id = 'no-match'; // This will return no results
    }

    const employeeSkillRisks = await prisma.employeeSkillRisk.findMany({
      where: whereClause,
      include: {
        user: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            employeeId: true,
          },
        },
        skill: true,
      },
    });

    // Group risks by employee and calculate metrics
    const employeeData = finalEmployees.map((employee) => {
      const risks = employeeSkillRisks.filter(
        (risk) => risk.userId === employee.id || risk.employeeId === employee.employeeId
      );

      const avgRiskScore = risks.length > 0
        ? risks.reduce((sum, r) => sum + r.riskScore, 0) / risks.length
        : 0;

      // Calculate relevance score - use IT fitness scores if available
      let relevance = 0;
      let riskLabel: 'Low' | 'Medium' | 'High' = 'High';
      
      if (employee.employeeId) {
        const normalizedEmployeeId = employee.employeeId.replace(/^0+/, '') || employee.employeeId;
        const fullId = normalizedEmployeeId.padStart(8, '0');
        
        // Try multiple ID formats to find fitness score
        // Check all possible formats
        const possibleIds = [
          normalizedEmployeeId,
          employee.employeeId,
          fullId,
          employee.employeeId.replace(/^0+/, ''),
          String(parseInt(normalizedEmployeeId, 10)), // In case of any string issues
        ].filter(id => id && id !== '');
        
        let itFitnessScore: number | undefined = undefined;
        for (const testId of possibleIds) {
          if (itFitnessScores.has(testId)) {
            itFitnessScore = itFitnessScores.get(testId);
            console.log(`🎯 Found fitness score for employee ${employee.employeeId} using ID format: "${testId}" -> ${itFitnessScore}`);
            break;
          }
        }
        
        if (itFitnessScore !== undefined && itFitnessScore !== null) {
          // Use IT fitness score as relevance score
          relevance = Math.round(itFitnessScore);
          // Convert fitness score to risk level (inverse relationship)
          // High fitness (80-100) = Low risk, Medium fitness (50-79) = Medium risk, Low fitness (0-49) = High risk
          riskLabel = itFitnessScore >= 80 ? 'Low' : itFitnessScore >= 50 ? 'Medium' : 'High';
          
          console.log(`✅ Employee ${employee.employeeId}: IT Fitness Score = ${itFitnessScore}, Relevance = ${relevance}, Risk = ${riskLabel}`);
        } else {
          // Fallback to risk-based calculation for employees without IT fitness scores
          relevance = risks.length > 0 ? Math.round(100 - avgRiskScore) : 0;
          riskLabel = avgRiskScore > 70 ? 'High' : avgRiskScore > 40 ? 'Medium' : 'Low';
          
          console.log(`⚠️  Employee ${employee.employeeId} (normalized: ${normalizedEmployeeId}, full: ${fullId}): No IT fitness score found. Tried: ${possibleIds.join(', ')}. Using fallback: ${relevance}`);
        }
      } else {
        // Fallback if no employee ID
        relevance = risks.length > 0 ? Math.round(100 - avgRiskScore) : 0;
        riskLabel = avgRiskScore > 70 ? 'High' : avgRiskScore > 40 ? 'Medium' : 'Low';
      }

      // Get employee data from CSV (profession and planned_profession)
      // Try multiple formats to match employee IDs (CSV uses 8-digit format with leading zeros)
      let csvData = null;
      if (employee.employeeId) {
        const normalizedEmployeeId = employee.employeeId.replace(/^0+/, '') || employee.employeeId;
        const fullId = normalizedEmployeeId.padStart(8, '0');
        
        // Try normalized ID first (e.g., "100870")
        csvData = employeeCSVData.get(normalizedEmployeeId);
        
        // Try full ID with leading zeros (e.g., "00100870")
        if (!csvData) {
          csvData = employeeCSVData.get(fullId);
        }
        
        // Try exact match as stored in database
        if (!csvData) {
          csvData = employeeCSVData.get(employee.employeeId);
        }
        
        // If still not found and ID is numeric, try with leading zeros (e.g., "4241" -> "00004241")
        if (!csvData && /^\d+$/.test(employee.employeeId) && employee.employeeId.length < 8) {
          const paddedId = employee.employeeId.padStart(8, '0');
          csvData = employeeCSVData.get(paddedId);
        }
        
        // If still not found and ID has leading zeros, try without them (e.g., "00004241" -> "4241")
        if (!csvData && /^\d+$/.test(employee.employeeId) && employee.employeeId.length >= 8 && employee.employeeId.startsWith('0')) {
          const unpaddedId = employee.employeeId.replace(/^0+/, '');
          csvData = employeeCSVData.get(unpaddedId);
        }
        
        // Try matching by last 4-8 digits (for IDs like "100870" try "00870" or "0870")
        if (!csvData && /^\d+$/.test(employee.employeeId) && employee.employeeId.length >= 4) {
          // Try last 8 digits padded
          const last8 = employee.employeeId.slice(-8).padStart(8, '0');
          csvData = employeeCSVData.get(last8);
          
          // Try last 4 digits padded to 8
          if (!csvData && employee.employeeId.length >= 4) {
            const last4 = employee.employeeId.slice(-4);
            const paddedLast4 = last4.padStart(8, '0');
            csvData = employeeCSVData.get(paddedLast4);
          }
          
          // Also search all CSV keys by last 4 digits
          if (!csvData) {
            const last4 = employee.employeeId.slice(-4);
            for (const [csvId, csvEmployeeData] of employeeCSVData.entries()) {
              if (csvId.endsWith(last4) || csvId.replace(/^0+/, '') === last4) {
                csvData = csvEmployeeData;
                break;
              }
            }
          }
        }
      }
      
      // Get current position from CSV data
      let currentPosition = 'N/A';
      if (csvData?.profession && csvData.profession !== 'N/A') {
        // Use CSV data first (most reliable source)
        currentPosition = csvData.profession;
      } else {
        // Last resort: use department
        currentPosition = employee.department || 'N/A';
      }
      
      // Translate Czech position to English
      currentPosition = translatePosition(currentPosition);
      
      // Set goal position to IT Specialist (m/w) for all employees with link
      const goalPosition = 'IT Specialist (m/w)';
      const goalPositionUrl = 'https://www.skoda-career.com/work-at-skoda/job-detail/50362';

      return {
        id: employee.id,
        employeeId: employee.employeeId,
        firstName: employee.firstName,
        lastName: employee.lastName,
        currentPosition: currentPosition, // From CSV data
        goalPosition: goalPosition, // IT Specialist (m/w) for all employees
        goalPositionUrl: goalPositionUrl, // URL to job posting
        position: currentPosition, // Legacy field for backward compatibility
        relevance: relevance, // IT fitness score or fallback calculation
        riskLabel: riskLabel, // Based on fitness score
        riskScore: avgRiskScore,
        skillCount: risks.length,
        matchedJobId: null,
      };
    });

    // Get enrollments for progress calculation
    const enrollments = userIds.length > 0 ? await prisma.enrollment.findMany({
      where: {
        userId: { in: userIds },
      },
      include: {
        user: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
          },
        },
        course: {
          select: {
            id: true,
            title: true,
          },
        },
      },
    }) : [];

    // Calculate risk distribution
    const riskDistribution = {
      low: employeeData.filter((e) => e.riskLabel === 'Low').length,
      medium: employeeData.filter((e) => e.riskLabel === 'Medium').length,
      high: employeeData.filter((e) => e.riskLabel === 'High').length,
    };

    // Calculate average metrics
    const avgRelevance = employeeData.length > 0
      ? employeeData.reduce((sum, e) => sum + e.relevance, 0) / employeeData.length
      : 0;
    
    // Log summary of relevance scores
    console.log(`\n📊 Relevance Scores Summary:`);
    employeeData.forEach(emp => {
      console.log(`  - ${emp.employeeId}: Relevance = ${emp.relevance}%, Risk = ${emp.riskLabel}`);
    });
    console.log(`  Average Relevance: ${Math.round(avgRelevance)}%\n`);

    const avgProgress = enrollments.length > 0
      ? enrollments.reduce((sum, e) => sum + e.progress, 0) / enrollments.length
      : 0;


    res.json({
      teamSize: employeeData.length,
      avgRelevance: Math.round(avgRelevance),
      highRiskCount: riskDistribution.high,
      avgProgress: Math.round(avgProgress),
      riskDistribution: [
        { risk: 'Low Risk', count: riskDistribution.low },
        { risk: 'Medium Risk', count: riskDistribution.medium },
        { risk: 'High Risk', count: riskDistribution.high },
      ],
      teamMembers: employeeData.map((ed) => {
        const enrollment = enrollments.find((e) => e.userId === ed.id);
        return {
          ...ed,
          learningProgress: enrollment ? Math.round(enrollment.progress) : 0,
          currentCourse: enrollment?.course.title,
        };
      }),
      availablePositions: openJobPositions, // Open job positions from database
    });
  } catch (error: any) {
    console.error('Get manager dashboard error:', error);
    console.error('Error stack:', error?.stack);
    res.status(500).json({ 
      error: 'Internal server error',
      message: error?.message || 'Unknown error',
      details: process.env.NODE_ENV === 'development' ? error?.stack : undefined
    });
  }
});

// Get employee detail for manager view
router.get('/employee-detail/:employeeId', authenticate, async (req: any, res) => {
  try {
    const { employeeId } = req.params;

    // Only managers/admins can view employee details
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN') {
      return res.status(403).json({ error: 'Forbidden' });
    }

    const user = await prisma.user.findUnique({
      where: { id: employeeId },
      include: {
        userSkills: {
          include: {
            skill: true,
          },
        },
        enrollments: {
          include: {
            course: true,
          },
        },
      },
    });

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    const skillRisks = await prisma.employeeSkillRisk.findMany({
      where: {
        OR: [
          { userId: employeeId },
          { employeeId: user.employeeId || '' },
        ],
      },
      include: {
        skill: true,
      },
    });

    // Get employee courses from CSV data for knowledge graph
    let coursesData: any[] = [];
    let educationData: any = null;
    
    if (user.employeeId) {
      try {
        const { analyzeEmployeeForJob } = await import('../services/employeeAnalysis');
        const analysis = analyzeEmployeeForJob(user.employeeId);
        
        // Read course data from CSV
        const courseData = readCSVFile('ZHRPD_VZD_STA_007.csv');
        const normalizedId = user.employeeId.replace(/^0+/, '');
        
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
        
        // Format courses for knowledge graph
        coursesData = employeeCourses.map((course: any) => {
          const columnKeys = Object.keys(course);
          const courseName = String(
            course['Označení typu akce'] || 
            course[columnKeys.find((k: string) => k.toLowerCase().includes('oznaceni')) || ''] ||
            (columnKeys.length > 1 ? course[columnKeys[1]] : null) ||
            ''
          ).trim();
          
          const courseCode = String(
            course['Typ akce'] || 
            (columnKeys.length > 0 ? course[columnKeys[0]] : '') ||
            ''
          ).trim();
          
          const startDate = course['Datum zahájení'] || course[columnKeys[3]] || null;
          const endDate = course['Datum ukončení'] || course[columnKeys[4]] || null;
          
          return {
            code: courseCode,
            name: courseName,
            startDate: startDate ? new Date(startDate).toISOString() : null,
            endDate: endDate ? new Date(endDate).toISOString() : null,
          };
        });
        
        // Get education data from ERP CSV
        const erpData = readCSVFile('ERP_SK1.Start_month - SE.csv');
        const fullId = normalizedId.padStart(8, '0');
        let erpRecord = erpData.find((row: any) => {
          const ob1 = String(row['persstat_start_month.ob1'] || '').trim();
          return ob1 === fullId || ob1 === normalizedId || ob1.endsWith(normalizedId.slice(-6));
        });
        
        if (erpRecord) {
          educationData = {
            educationCategory: erpRecord['persstat_start_month.education_category_name'] || null,
            fieldOfStudy: erpRecord['persstat_start_month.field_of_study_name'] || null,
            basicBranch: erpRecord['persstat_start_month.basic_branch_of_education_name'] || null,
          };
        }
      } catch (error) {
        console.error('Error fetching employee courses from CSV:', error);
        // Continue without course data if there's an error
      }
    }

    res.json({
      user: {
        id: user.id,
        name: `${user.firstName} ${user.lastName}`,
        email: user.email,
        role: user.role,
        department: user.department,
        employeeId: user.employeeId,
      },
      skills: user.userSkills.map((us) => ({
        skill: us.skill.name,
        category: us.skill.category,
        level: us.level,
      })),
      skillRisks: skillRisks.map((sr) => ({
        skillName: sr.skillName,
        riskScore: sr.riskScore,
        riskLabel: sr.riskLabel,
        avgFutureDemand: sr.avgFutureDemand,
        automationExposure: sr.automationExposure,
      })),
      enrollments: user.enrollments.map((e) => ({
        courseTitle: e.course.title,
        progress: e.progress,
        enrolledAt: e.enrolledAt,
        completedAt: e.completedAt,
      })),
      courses: coursesData, // Courses from CSV for knowledge graph
      education: educationData, // Education/degree information
    });
  } catch (error) {
    console.error('Get employee detail error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;
