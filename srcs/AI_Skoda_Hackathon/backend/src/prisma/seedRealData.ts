import { PrismaClient } from '@prisma/client';
import XLSX from 'xlsx';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

// Get __dirname equivalent in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Dataset paths - use local data folder (not pushed to GitHub)
// Check if running in Docker (dataset mounted at /app/data)
const possibleDatasetPaths = [
  '/app/data', // Docker path
  path.join(__dirname, '../../../data') // Local path
];

let DATASET_PATH = '';

for (const datasetPath of possibleDatasetPaths) {
  if (fs.existsSync(datasetPath)) {
    DATASET_PATH = datasetPath;
    console.log(`✅ Found dataset at: ${DATASET_PATH}`);
    break;
  }
}

if (!DATASET_PATH) {
  console.error('❌ No dataset folder found!');
  process.exit(1);
}

console.log(`📁 Using dataset path: ${DATASET_PATH}\n`);

interface EmployeeData {
  personal_number: string;
  firstName?: string;
  lastName?: string;
  email?: string;
  profession?: string;
  planned_profession_id?: string;
  position?: string;
  planned_position_id?: string;
  education_group?: string;
  branch_of_education?: string;
  field_of_study?: string;
  sa_org_hierarchy_objid?: string;
  department?: string;
}

interface SkillMapping {
  courseCode: string;
  courseName: string;
  topic: string;
  skillId: string;
  skillName: string;
}

interface OrgHierarchy {
  objid: string;
  parent?: string;
  short?: string;
  stext?: string;
  stxtt?: string;
}

// Utility: Read Excel file
function readExcelFile(filename: string): any[] {
  const filePath = path.join(DATASET_PATH, filename);
  
  if (!fs.existsSync(filePath)) {
    console.log(`⚠️  File not found: ${filename}`);
    console.log(`   Tried path: ${filePath}`);
    console.log(`   Dataset path: ${DATASET_PATH}`);
    return [];
  }

  try {
    const workbook = XLSX.readFile(filePath);
    const sheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[sheetName];
    const data = XLSX.utils.sheet_to_json(worksheet);
    console.log(`✅ Loaded ${data.length} rows from ${filename}`);
    return data;
  } catch (error) {
    console.error(`❌ Error reading ${filename}:`, error);
    return [];
  }
}

// Generate realistic employee data from personal number
function generateEmployeeFromId(personalNumber: string): {
  firstName: string;
  lastName: string;
  email: string;
} {
  const firstNames = [
    'Jan', 'Petr', 'Pavel', 'Martin', 'Tomáš', 'Jakub', 'Lukáš', 'David', 'Michal', 'Ondřej',
    'Anna', 'Petra', 'Jana', 'Lucie', 'Kateřina', 'Lenka', 'Markéta', 'Tereza', 'Veronika', 'Hana'
  ];
  const lastNames = [
    'Novák', 'Svoboda', 'Novotný', 'Dvořák', 'Černý', 'Procházka', 'Kučera', 'Veselý', 'Horák', 'Němec',
    'Pokorný', 'Pospíšil', 'Král', 'Jelínek', 'Růžička', 'Beneš', 'Fiala', 'Sedláček', 'Doležal', 'Zeman'
  ];

  // Use personal number as seed for consistent name generation
  const seed = personalNumber.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const firstName = firstNames[seed % firstNames.length];
  const lastName = lastNames[(seed * 7) % lastNames.length];
  // Add personal number suffix to ensure unique emails
  const emailSuffix = personalNumber.slice(-4);
  const email = `${firstName.toLowerCase()}.${lastName.toLowerCase()}.${emailSuffix}@skoda.cz`;

  return { firstName, lastName, email };
}

async function main() {
  console.log('🚀 Starting Real Dataset Import...\n');

  try {
    // Clean existing data
    console.log('🧹 Cleaning existing data...');
    await prisma.employeeSkillRisk.deleteMany();
    await prisma.assignmentAI.deleteMany();
    await prisma.certificate.deleteMany();
    await prisma.careerPathSkill.deleteMany();
    await prisma.careerPath.deleteMany();
    await prisma.assignment.deleteMany();
    await prisma.assessment.deleteMany();
    await prisma.moduleProgress.deleteMany();
    await prisma.enrollment.deleteMany();
    await prisma.courseSkill.deleteMany();
    await prisma.quizQuestion.deleteMany();
    await prisma.courseModule.deleteMany();
    await prisma.course.deleteMany();
    await prisma.userSkill.deleteMany();
    await prisma.skill.deleteMany();
    await prisma.user.deleteMany();

    console.log('✅ Database cleaned\n');

    // 1. Import Skills from Skill_mapping.csv
    console.log('📊 Importing Skills...');
    const skillMappingData = readExcelFile('Skill_mapping.csv');
    const uniqueSkills = new Map<string, { name: string; category: string }>();

    // Use course topics as skills (since Skill_mapping doesn't have explicit skills)
    skillMappingData.forEach((row: any) => {
      const topic = row['Téma'] || row['Topic'] || row['Tema'];
      const courseName = row['Název D'] || row['Course Name'];
      
      if (topic && !uniqueSkills.has(topic)) {
        uniqueSkills.set(topic, {
          name: topic,
          category: 'Professional Development'
        });
      }
      
      // Also extract skills from course names (e.g., "Excel", "SAP", "Leadership")
      if (courseName) {
        const keywords = ['Excel', 'SAP', 'Leadership', 'Management', 'Communication', 'Project', 
                         'Quality', 'English', 'German', 'Innovation', 'Digital', 'Data', 'Agile', 
                         'Python', 'SQL', 'Analytics', 'Reporting', 'Process', 'Safety'];
        
        keywords.forEach(keyword => {
          if (courseName.toLowerCase().includes(keyword.toLowerCase()) && !uniqueSkills.has(keyword)) {
            uniqueSkills.set(keyword, {
              name: keyword,
              category: 'Technical Skills'
            });
          }
        });
      }
    });

    // Add common industry skills
    const commonSkills = [
      { name: 'Problem Solving', category: 'Soft Skills' },
      { name: 'Teamwork', category: 'Soft Skills' },
      { name: 'Critical Thinking', category: 'Soft Skills' },
      { name: 'Time Management', category: 'Soft Skills' },
      { name: 'Adaptability', category: 'Soft Skills' },
      { name: 'Technical Documentation', category: 'Technical Skills' },
      { name: 'Process Improvement', category: 'Professional Skills' },
      { name: 'Risk Management', category: 'Professional Skills' },
    ];

    commonSkills.forEach(skill => {
      if (!uniqueSkills.has(skill.name)) {
        uniqueSkills.set(skill.name, skill);
      }
    });

    const skillMap = new Map<string, string>(); // skillName -> skillId

    for (const [name, data] of uniqueSkills) {
      const skill = await prisma.skill.create({
        data: {
          name: data.name,
          category: data.category,
          marketRelevance: Math.random() * 30 + 70, // 70-100
        },
      });
      skillMap.set(name, skill.id);
    }

    console.log(`✅ Created ${uniqueSkills.size} skills\n`);

    // 2. Import Organizational Hierarchy
    console.log('🏢 Importing Organizational Hierarchy...');
    const orgData = readExcelFile('RLS.sa_org_hierarchy - SE.csv');
    const departments = new Map<string, string>();

    orgData.forEach((row: any, index: number) => {
      const deptName = row['stext'] || row['short'] || `Department ${index + 1}`;
      departments.set(deptName, deptName);
    });

    console.log(`✅ Loaded ${departments.size} departments\n`);

    // 3. Import Employees from ERP_SK1.Start_month - SE.csv
    console.log('👥 Importing Employees...');
    const employeeData = readExcelFile('ERP_SK1.Start_month - SE.csv');
    
    const userMap = new Map<string, string>(); // personalNumber -> userId
    const defaultPassword = await bcrypt.hash('password123', 10);

    // Create managers first
    const managersData = [
      { firstName: 'Karel', lastName: 'Vágner', email: 'karel.vagner@skoda.cz', role: 'MANAGER' },
      { firstName: 'Eva', lastName: 'Horská', email: 'eva.horska@skoda.cz', role: 'MANAGER' },
      { firstName: 'Petr', lastName: 'Dvořák', email: 'petr.dvorak@skoda.cz', role: 'MANAGER' },
    ];

    const managerIds: string[] = [];

    for (const managerData of managersData) {
      const manager = await prisma.user.create({
        data: {
          ...managerData,
          role: managerData.role as any,
          password: defaultPassword,
          employeeId: `MGR${Math.floor(Math.random() * 10000)}`,
          department: Array.from(departments.keys())[Math.floor(Math.random() * departments.size)],
        },
      });
      managerIds.push(manager.id);
    }

    console.log(`✅ Created ${managerIds.length} managers`);

    // Import ALL employees from the CSV file
    const employeesToImport = employeeData; // Import all employees, not just first 150

    for (const row of employeesToImport) {
      // Try multiple column names for personal number
      // Note: persstat_start_month.personal_number contains the 8-digit ID, persstat_start_month.ob1 contains the "S" prefix
      const rawPersonalNumber = row['persstat_start_month.personal_number'] || 
                                row['personal_number'] || 
                                row['Variabilní pole (os. číslo)'] || 
                                row['persstat_start_month.ob1'] || 
                                `EMP${Math.floor(Math.random() * 100000)}`;
      const personalNumber = String(rawPersonalNumber).trim();
      
      if (!personalNumber || userMap.has(personalNumber)) continue;

      const { firstName, lastName, email } = generateEmployeeFromId(personalNumber);
      const department = row['sa_org_hierarchy.objid'] 
        ? Array.from(departments.keys())[Math.floor(Math.random() * departments.size)]
        : Array.from(departments.keys())[0];

      try {
        const user = await prisma.user.create({
          data: {
            email,
            password: defaultPassword,
            firstName,
            lastName,
            employeeId: personalNumber,
            role: 'EMPLOYEE',
            department,
            managerId: managerIds[Math.floor(Math.random() * managerIds.length)],
          },
        });

        userMap.set(personalNumber, user.id);
      } catch (error) {
        // Skip duplicate emails
        continue;
      }
    }

    console.log(`✅ Created ${userMap.size} employees\n`);

    // 4. Import Courses from ZHRPD_VZD_STA_007.csv (Course participation)
    console.log('📚 Importing Courses...');
    const courseData = readExcelFile('ZHRPD_VZD_STA_007.csv');
    const courseMap = new Map<string, string>(); // courseName -> courseId

    const uniqueCourses = new Map<string, any>();
    
    // First check what columns we have
    if (courseData.length > 0) {
      console.log('Course data columns:', Object.keys(courseData[0]));
    }
    
    courseData.forEach((row: any) => {
      const courseName = row['Označení typu akce'] || row['Název'] || row['Course Name'] || row['Typ akce'];
      if (courseName && !uniqueCourses.has(String(courseName))) {
        uniqueCourses.set(String(courseName), {
          name: String(courseName),
          startDate: row['Datum zahájení'] || row['Start Date'],
          endDate: row['Datum ukončení'] || row['End Date'],
        });
      }
    });

    // Create courses from ALL unique names in the dataset
    for (const [name, data] of Array.from(uniqueCourses)) {
      const course = await prisma.course.create({
        data: {
          title: String(name),
          description: `Professional development course: ${name}`,
          duration: '4-6 weeks',
          difficulty: ['Beginner', 'Intermediate', 'Advanced'][Math.floor(Math.random() * 3)],
        },
      });

      courseMap.set(name, course.id);

      // Add 2-4 modules per course
      const moduleCount = Math.floor(Math.random() * 3) + 2;
      for (let i = 0; i < moduleCount; i++) {
        await prisma.courseModule.create({
          data: {
            courseId: course.id,
            type: ['LESSON', 'QUIZ', 'ASSIGNMENT'][i % 3] as any,
            title: `Module ${i + 1}: ${['Introduction', 'Core Concepts', 'Practical Application', 'Assessment'][i % 4]}`,
            order: i,
            content: `Content for module ${i + 1}`,
          },
        });
      }
    }

    console.log(`✅ Created ${courseMap.size} courses\n`);

    // 5. Link Courses to Skills from Skill_mapping.csv (process all data)
    console.log('🔗 Linking Courses to Skills...');
    let courseSkillLinks = 0;

    for (const row of skillMappingData) {
      const courseName = row['Název D'] || row['Course Name'] || row['Zkratka D'];
      const topic = row['Téma'] || row['Topic'];

      const courseId = courseMap.get(courseName);
      const skillId = skillMap.get(topic); // Use topic as skill

      if (courseId && skillId) {
        try {
          await prisma.courseSkill.create({
            data: { courseId, skillId },
          });
          courseSkillLinks++;
        } catch (error) {
          // Skip duplicates
        }
      }
    }

    console.log(`✅ Created ${courseSkillLinks} course-skill links\n`);

    // 6. Assign Skills to Users (from qualification data - process all data)
    console.log('🎯 Assigning Skills to Employees...');
    const qualificationData = readExcelFile('ZHRPD_VZD_STA_016_RE_RHRHAZ00.csv');
    let userSkillCount = 0;

    for (const row of qualificationData) {
      const personalNumber = row['Variabilní pole (os. číslo)'] || row['personal_number'];
      const qualName = row['Název Q'] || row['Qualification'];

      const userId = userMap.get(personalNumber);
      
      if (userId && qualName) {
        // Find related skill
        const relatedSkill = Array.from(skillMap.entries()).find(([name]) => 
          name.toLowerCase().includes(qualName.toLowerCase().split(' ')[0]) ||
          qualName.toLowerCase().includes(name.toLowerCase().split(' ')[0])
        );

        if (relatedSkill) {
          const [, skillId] = relatedSkill;
          
          try {
            await prisma.userSkill.create({
              data: {
                userId,
                skillId,
                level: Math.random() * 40 + 60, // 60-100
                assessedBy: 'System Import',
              },
            });
            userSkillCount++;
          } catch (error) {
            // Skip duplicates
          }
        }
      }
    }

    // Assign random skills to users without skills (process all users)
    for (const [, userId] of Array.from(userMap)) {
      const userSkills = await prisma.userSkill.findMany({ where: { userId } });
      
      if (userSkills.length === 0) {
        // Assign 3-6 random skills
        const skillCount = Math.floor(Math.random() * 4) + 3;
        const allSkillIds = Array.from(skillMap.values());
        
        for (let i = 0; i < Math.min(skillCount, allSkillIds.length); i++) {
          const randomSkillId = allSkillIds[Math.floor(Math.random() * allSkillIds.length)];
          
          try {
            await prisma.userSkill.create({
              data: {
                userId,
                skillId: randomSkillId,
                level: Math.random() * 40 + 50, // 50-90
                assessedBy: 'System Import',
              },
            });
            userSkillCount++;
          } catch (error) {
            // Skip duplicates
          }
        }
      }
    }

    console.log(`✅ Created ${userSkillCount} user-skill assignments\n`);

    // 7. Create Enrollments (from course participation data - increased limit)
    console.log('📝 Creating Course Enrollments...');
    let enrollmentCount = 0;
    let matchedUsers = 0;
    let matchedCourses = 0;
    
    // Sample debugging
    console.log('   Sample userMap keys:', Array.from(userMap.keys()).slice(0, 5));
    if (courseData.length > 0) {
      console.log('   Course data columns:', Object.keys(courseData[0]));
      console.log('   Sample row:', courseData[0]);
    }

    for (const row of courseData) {
      // Use the exact column name as read by xlsx library (with encoding issues)
      const rawPersonalNumber = row['ID ÃºÄ\x8DastnÃ­ka'] || row['ID účastníka'] || row['personal_number'];
      const courseName = String(row['OznaÄ\x8DenÃ­ typu akce'] || row['Označení typu akce'] || row['Název'] || row['Course Name'] || row['Typ akce']);
      
      // Normalize personal number - try both with and without leading zeros
      const personalNumber = String(rawPersonalNumber).trim();
      const personalNumberPadded = personalNumber.padStart(8, '0');
      
      const userId = userMap.get(personalNumber) || userMap.get(personalNumberPadded);
      const courseId = courseMap.get(courseName);
      
      if (userId) matchedUsers++;
      if (courseId) matchedCourses++;

      if (userId && courseId) {
        try {
          await prisma.enrollment.create({
            data: {
              userId,
              courseId,
              progress: Math.random() * 100,
              enrolledAt: new Date(row['Datum zahájení'] || Date.now()),
              completedAt: row['Datum ukončení'] ? new Date(row['Datum ukončení']) : null,
            },
          });
          enrollmentCount++;
        } catch (error) {
          // Skip duplicates
        }
      }
    }

    console.log(`   Matched users: ${matchedUsers}, Matched courses: ${matchedCourses}`);
    console.log(`✅ Created ${enrollmentCount} enrollments\n`);

    // 8. Generate Employee Skill Risks (AI predictions based on real employee data - process all employees)
    console.log('⚠️  Generating Skill Risk Analysis...');
    let riskCount = 0;

    for (const [personalNumber, userId] of Array.from(userMap)) {
      const user = await prisma.user.findUnique({
        where: { id: userId },
        include: { userSkills: { include: { skill: true } } },
      });

      if (!user) continue;

      for (const userSkill of user.userSkills.slice(0, 5)) {
        const automationExposure = Math.random() * 100;
        const avgFutureDemand = Math.random() * 100;
        const riskScore = (automationExposure + (100 - avgFutureDemand)) / 2;

        const riskLabel = riskScore > 70 ? 'HIGH' : riskScore > 40 ? 'MEDIUM' : 'LOW';

        await prisma.employeeSkillRisk.create({
          data: {
            employeeId: personalNumber,
            userId: user.id,
            department: user.department,
            skillName: userSkill.skill.name,
            skillId: userSkill.skillId,
            avgFutureDemand,
            automationExposure,
            riskScore,
            riskLabel,
          },
        });
        riskCount++;
      }
    }

    console.log(`✅ Created ${riskCount} risk assessments\n`);

    // 9. Create Career Paths
    console.log('🎯 Creating Career Paths...');
    const careerPaths = [
      { title: 'Senior Software Engineer', targetRole: 'Senior Engineer', fitScore: 85 },
      { title: 'Technical Lead', targetRole: 'Team Lead', fitScore: 78 },
      { title: 'Solutions Architect', targetRole: 'Architect', fitScore: 72 },
      { title: 'Product Manager', targetRole: 'Product Manager', fitScore: 68 },
      { title: 'Data Scientist', targetRole: 'Data Scientist', fitScore: 75 },
    ];

    for (const pathData of careerPaths) {
      const path = await prisma.careerPath.create({
        data: {
          ...pathData,
          description: `Career progression to ${pathData.targetRole}`,
          reason: 'Based on your current skills and market demand',
        },
      });

      // Link 3-5 required skills
      const requiredSkillCount = Math.floor(Math.random() * 3) + 3;
      const allSkillIds = Array.from(skillMap.values());

      for (let i = 0; i < requiredSkillCount; i++) {
        const skillId = allSkillIds[Math.floor(Math.random() * allSkillIds.length)];
        
        try {
          await prisma.careerPathSkill.create({
            data: {
              careerPathId: path.id,
              skillId,
              requiredLevel: Math.random() * 20 + 70, // 70-90
            },
          });
        } catch (error) {
          // Skip duplicates
        }
      }
    }

    console.log(`✅ Created ${careerPaths.length} career paths\n`);

    console.log('✨ Real Dataset Import Complete!\n');
    console.log('📊 Summary:');
    console.log(`   - Skills: ${uniqueSkills.size}`);
    console.log(`   - Departments: ${departments.size}`);
    console.log(`   - Managers: ${managerIds.length}`);
    console.log(`   - Employees: ${userMap.size}`);
    console.log(`   - Courses: ${courseMap.size}`);
    console.log(`   - Enrollments: ${enrollmentCount}`);
    console.log(`   - User Skills: ${userSkillCount}`);
    console.log(`   - Risk Assessments: ${riskCount}`);
    console.log(`   - Career Paths: ${careerPaths.length}`);
    console.log('\n🔐 Login credentials:');
    console.log('   Email: karel.vagner@skoda.cz (Manager)');
    console.log('   Email: Any employee email from import');
    console.log('   Password: password123');

  } catch (error) {
    console.error('❌ Error during import:', error);
    throw error;
  } finally {
    await prisma.$disconnect();
  }
}

main()
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
