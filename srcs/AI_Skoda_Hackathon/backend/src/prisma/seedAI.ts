import { PrismaClient, RiskLevel } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

// Helper function to generate random number in range
const random = (min: number, max: number) => Math.floor(Math.random() * (max - min + 1)) + min;
const randomFloat = (min: number, max: number) => Math.random() * (max - min) + min;

// Generate risk label based on risk score
const getRiskLabel = (riskScore: number): RiskLevel => {
  if (riskScore >= 70) return 'HIGH';
  if (riskScore >= 40) return 'MEDIUM';
  return 'LOW';
};

async function main() {
  console.log('🌱 Starting AI seed data generation...');

  // Get existing skills
  const skills = await prisma.skill.findMany();
  if (skills.length === 0) {
    console.log('⚠️  No skills found. Please run the main seed script first.');
    return;
  }

  // Departments
  const departments = ['IT', 'Engineering', 'Design', 'Analytics', 'Sales', 'Marketing', 'HR', 'Operations', 'Finance', 'R&D'];
  
  // Assignment types
  const assignmentTypes = ['Code Review', 'Data Analysis', 'UI Design', 'System Architecture', 'Testing', 'Documentation', 'Planning', 'Research'];

  // Real Czech first names
  const firstNames = [
    'Jan', 'Petr', 'Josef', 'Pavel', 'Martin', 'Tomáš', 'Jaroslav', 'Lukáš', 'Michal', 'David',
    'Petra', 'Jana', 'Marie', 'Hana', 'Anna', 'Lucie', 'Eva', 'Kateřina', 'Alena', 'Lenka',
    'Zdeněk', 'Václav', 'Jiří', 'Jakub', 'Marek', 'Ondřej', 'Jan', 'Filip', 'Matěj', 'Adam',
    'Karolína', 'Markéta', 'Tereza', 'Veronika', 'Barbora', 'Nikola', 'Simona', 'Kristýna', 'Adéla', 'Eliška',
    'Daniel', 'Michal', 'Lukáš', 'Matěj', 'Vojtěch', 'Sebastian', 'Dominik', 'Matyáš', 'Štěpán', 'Kryštof',
    'Natálie', 'Sofie', 'Ema', 'Nela', 'Amálie', 'Tereza', 'Elisabeth', 'Julie', 'Klára', 'Sára'
  ];

  // Real Czech last names
  const lastNames = [
    'Novák', 'Svoboda', 'Novotný', 'Dvořák', 'Černý', 'Procházka', 'Veselý', 'Horák', 'Němec', 'Pokorný',
    'Pospíšil', 'Havel', 'Mareš', 'Jelínek', 'Růžička', 'Beneš', 'Fiala', 'Sedláček', 'Krejčí', 'Doležal',
    'Kučera', 'Navrátil', 'Bartoš', 'Vlček', 'Urban', 'Šimek', 'Hrubý', 'Konečný', 'Zeman', 'Hrubý',
    'Tichý', 'Veselý', 'Holub', 'Vávra', 'Kříž', 'Kadlec', 'Blažek', 'Bureš', 'Kratochvíl', 'Polák',
    'Zahradník', 'Říha', 'Moravec', 'Mach', 'Kolář', 'Lukáš', 'Bělohlávek', 'Kubát', 'Štěpánek', 'Kratochvíl'
  ];

  // Create 100 employees with AI risk data
  const hashedPassword = await bcrypt.hash('password123', 10);
  const managerId = (await prisma.user.findFirst({ where: { role: 'MANAGER' } }))?.id;

  const employees: any[] = [];
  const usedNames = new Set<string>(); // Track used name combinations
  
  for (let i = 1; i <= 100; i++) {
    const employeeId = `EMP${String(i).padStart(3, '0')}`;
    const department = departments[random(0, departments.length - 1)];
    
    // Generate unique name combination
    let firstName: string, lastName: string, nameKey: string;
    do {
      firstName = firstNames[random(0, firstNames.length - 1)];
      lastName = lastNames[random(0, lastNames.length - 1)];
      nameKey = `${firstName}_${lastName}`;
    } while (usedNames.has(nameKey) && usedNames.size < firstNames.length * lastNames.length);
    
    usedNames.add(nameKey);
    
    // Create or get user (upsert to handle existing users)
    const user = await prisma.user.upsert({
      where: { employeeId },
      update: {
        department, // Update department if exists
        firstName,
        lastName,
      },
      create: {
        email: `employee${i}@skoda.com`,
        password: hashedPassword,
        firstName,
        lastName,
        employeeId,
        role: 'EMPLOYEE',
        department,
        managerId: managerId || undefined,
      },
    });

    employees.push({ user, employeeId, department });

    // Create 3-5 skill risk records per employee
    const numSkills = random(3, 5);
    const selectedSkills = skills.sort(() => 0.5 - Math.random()).slice(0, numSkills);

    for (const skill of selectedSkills) {
      // Generate realistic AI predictions
      // Low risk: high future demand, low automation exposure
      // Medium risk: moderate future demand, moderate automation exposure
      // High risk: low future demand, high automation exposure
      
      const riskCategory = random(1, 3); // 1=LOW, 2=MEDIUM, 3=HIGH
      
      let avgFutureDemand: number;
      let automationExposure: number;
      
      switch (riskCategory) {
        case 1: // LOW RISK
          avgFutureDemand = randomFloat(70, 95);
          automationExposure = randomFloat(5, 30);
          break;
        case 2: // MEDIUM RISK
          avgFutureDemand = randomFloat(40, 70);
          automationExposure = randomFloat(30, 60);
          break;
        case 3: // HIGH RISK
          avgFutureDemand = randomFloat(10, 40);
          automationExposure = randomFloat(60, 90);
          break;
        default:
          avgFutureDemand = randomFloat(30, 70);
          automationExposure = randomFloat(20, 70);
      }

      const riskScore = (100 - avgFutureDemand) * 0.4 + automationExposure * 0.6;
      const riskLabel = getRiskLabel(riskScore);

      await prisma.employeeSkillRisk.create({
        data: {
          employeeId,
          userId: user.id,
          department,
          skillName: skill.name,
          skillId: skill.id,
          avgFutureDemand: Math.round(avgFutureDemand * 10) / 10,
          automationExposure: Math.round(automationExposure * 10) / 10,
          riskScore: Math.round(riskScore * 10) / 10,
          riskLabel,
        },
      });
    }

    // Create 2-4 assignment AI records per employee
    const numAssignments = random(2, 4);
    const selectedAssignmentSkills = skills.sort(() => 0.5 - Math.random()).slice(0, numAssignments);

    for (const skill of selectedAssignmentSkills) {
      const assignmentType = assignmentTypes[random(0, assignmentTypes.length - 1)];
      
      const riskCategory = random(1, 3);
      
      let avgFutureDemand: number;
      let automationExposure: number;
      
      switch (riskCategory) {
        case 1: // LOW RISK
          avgFutureDemand = randomFloat(65, 90);
          automationExposure = randomFloat(10, 35);
          break;
        case 2: // MEDIUM RISK
          avgFutureDemand = randomFloat(35, 65);
          automationExposure = randomFloat(35, 65);
          break;
        case 3: // HIGH RISK
          avgFutureDemand = randomFloat(15, 35);
          automationExposure = randomFloat(65, 85);
          break;
        default:
          avgFutureDemand = randomFloat(30, 70);
          automationExposure = randomFloat(25, 75);
      }

      const riskScore = (100 - (avgFutureDemand || 0)) * 0.4 + (automationExposure || 0) * 0.6;
      const riskLabel = getRiskLabel(riskScore);

      await prisma.assignmentAI.create({
        data: {
          employeeId,
          userId: user.id,
          department,
          skillName: skill.name,
          skillId: skill.id,
          avgFutureDemand: Math.round(avgFutureDemand * 10) / 10,
          automationExposure: Math.round(automationExposure * 10) / 10,
          riskScore: Math.round(riskScore * 10) / 10,
          riskLabel,
          assignmentType,
        },
      });
    }

    if (i % 10 === 0) {
      console.log(`✅ Created ${i}/100 employees...`);
    }
  }

  // Summary statistics
  const [riskStats, assignmentStats] = await Promise.all([
    prisma.employeeSkillRisk.groupBy({
      by: ['riskLabel'],
      _count: true,
    }),
    prisma.assignmentAI.groupBy({
      by: ['riskLabel'],
      _count: true,
    }),
  ]);

  console.log('\n📊 Summary Statistics:');
  console.log('\nEmployee Skill Risks by Risk Label:');
  riskStats.forEach(stat => {
    console.log(`  ${stat.riskLabel}: ${stat._count} records`);
  });

  console.log('\nAssignment AI by Risk Label:');
  assignmentStats.forEach(stat => {
    console.log(`  ${stat.riskLabel}: ${stat._count} records`);
  });

  console.log(`\n🎉 AI seed data completed successfully!`);
  console.log(`   - ${employees.length} employees created`);
  console.log(`   - Employee skill risk records: ${await prisma.employeeSkillRisk.count()}`);
  console.log(`   - Assignment AI records: ${await prisma.assignmentAI.count()}`);
}

main()
  .catch((e) => {
    console.error('❌ AI seed failed:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });

