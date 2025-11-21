/**
 * Helper script to manually add job positions to the database
 * 
 * Usage:
 *   npm run add-job-position
 *   or
 *   npx tsx src/scripts/addJobPosition.ts
 * 
 * This script allows you to quickly add job positions found on career pages
 */

import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

interface JobPositionInput {
  title: string;
  description?: string;
  department?: string;
  location?: string;
  employmentType?: string;
  requiredExperience?: string;
  closingDate?: string;
  skillRequirements?: Array<{
    skillName: string;
    requiredLevel?: number; // 0-100
    weight?: number; // 0-1, default 1.0
    isRequired?: boolean;
  }>;
}

async function addJobPosition(input: JobPositionInput) {
  try {
    console.log('📋 Adding job position:', input.title);

    // If skills are provided, find or create them
    const skillIds: Array<{ skillId: string; requiredLevel: number; weight: number; isRequired: boolean }> = [];

    if (input.skillRequirements && input.skillRequirements.length > 0) {
      for (const skillReq of input.skillRequirements) {
        // Try to find existing skill by name
        let skill = await prisma.skill.findUnique({
          where: { name: skillReq.skillName },
        });

        // If skill doesn't exist, create it
        if (!skill) {
          console.log(`  ➕ Creating new skill: ${skillReq.skillName}`);
          skill = await prisma.skill.create({
            data: {
              name: skillReq.skillName,
              category: 'Professional Development',
              marketRelevance: 75,
            },
          });
        }

        skillIds.push({
          skillId: skill.id,
          requiredLevel: skillReq.requiredLevel || 70,
          weight: skillReq.weight || 1.0,
          isRequired: skillReq.isRequired !== undefined ? skillReq.isRequired : true,
        });
      }
    }

    // Create the job position
    const jobPosition = await prisma.jobPosition.create({
      data: {
        title: input.title,
        description: input.description,
        department: input.department,
        location: input.location,
        employmentType: input.employmentType,
        status: 'OPEN',
        requiredExperience: input.requiredExperience,
        closingDate: input.closingDate ? new Date(input.closingDate) : null,
        skills: skillIds.length > 0 ? {
          create: skillIds,
        } : undefined,
      },
      include: {
        skills: {
          include: {
            skill: true,
          },
        },
      },
    });

    console.log('✅ Job position created successfully!');
    console.log('   ID:', jobPosition.id);
    console.log('   Title:', jobPosition.title);
    console.log('   Skills:', jobPosition.skills.length);
    console.log('\n');

    return jobPosition;
  } catch (error) {
    console.error('❌ Error adding job position:', error);
    throw error;
  }
}

// Example: Add a job position
async function main() {
  try {
    // Job positions - modify these or add your own
    const exampleJobs: JobPositionInput[] = [
      {
        title: 'IT Specialist (m/w)',
        description: `Looking for an opportunity or option to enter the IT world? Or have you already been into this area and are now waiting for a new impulse? Keen on working in an environment with a century-long tradition, one that is the backbone of Czech economy, while growing at the same time dynamically and setting digital trends? You wanna gain international experience and be a partner of our experts in various IT teams? In line with its growth, Škoda Auto is looking for experienced professionals, as well as inspiring IT enthusiasts. Let's jointly discuss a future IT projects we will be staffing troughout the year.

Location: Mladá Boleslav, Praha

What is your role about?

• You will be part of our IT department with focus on IT infrastructure, IT support or even IT development
• You will be chipping in new ideas as well as trends related to digitization and general technological direction (Connected Car, Big Data, Virtual Reality, Artificial Intelligence)
• Work together with experts in the Czech Republic and abroad - all over the world, online and via personal meetings (travel within Czech Republic, Europe or even between continents)
• Extend your knowledge, skills (ranging from professional to soft skills if you want), attend conferences, trainings and meetings to develop new ideas

What are our requirements?

• You have to have a high school or university degree in form a technical area or experience in the field
• You have either German or English at least on the intermediate level (B2)

What can you get from us?

• Competitive salary (include 13th month salary and yearly bonus)
• 5 weeks of vacation
• Flexible working hours, Home office or even choice of work location (Prague or Mladá Boleslav)
• Pensions contribution in amount of 1900 Kč per month
• Pluxee card for leisure activities
• Škoda Auto canteen with preisable lunches from 30 CZK
• Multisport card option
• Beneficial purchasing or renting Škoda Auto cars
• Interest-free housing loan up to 600 000 CZK

Reference ID: 1486`,
        department: 'IT',
        location: 'Mladá Boleslav, Praha, Czech Republic',
        employmentType: 'Full-time',
        requiredExperience: 'Entry level to experienced',
        skillRequirements: [
          { skillName: 'Technical Skills', requiredLevel: 70, weight: 1.0, isRequired: true },
          { skillName: 'Innovation', requiredLevel: 65, weight: 0.9, isRequired: true },
          { skillName: 'Digital', requiredLevel: 70, weight: 0.9, isRequired: true },
          { skillName: 'Adaptability', requiredLevel: 75, weight: 0.8, isRequired: true },
          { skillName: 'Communication', requiredLevel: 70, weight: 0.8, isRequired: false },
          { skillName: 'Teamwork', requiredLevel: 70, weight: 0.8, isRequired: false },
          { skillName: 'Time Management', requiredLevel: 65, weight: 0.7, isRequired: false },
        ],
      },
      {
        title: 'SAP DevOps Engineer (m/w)',
        description: `Škoda Auto is looking for experienced SAP IT professionals for its SAP Competence Center to deliver services for the VW Group (VW, Audi, Seat, Porsche, Bentley). We offer career growth in an international environment that also values work-life balance.

Location: Prague or Mladá Boleslav

What will you do with us?

• Deliver solution in SAP financial modules with focus on the entire lifecycle of SW product TranS/4m (analysis, solution design and development, testing and deployment).
• Review business function proposals and suggest optimizations of app, systems and processes within the scope.
• Create and maintain automated processes for deployment, testing, and monitoring of SAP systems.
• Collaborate with other VW IT departments, Škoda IT, relevant corporate stakeholders, and external suppliers.
• Deliver, implement and manage Continuous Integrations/Continuous Deployment (CI/CD).
• Coordinate function verifications, analyze and evaluate issues in the delivered solutions.

What do you need to know, have, and be able to do?

• University degree.
• Professional experience: 3 years plus.
• English at minimum B2 level – communicative.

What can you gain from us?

• 13th salary every year as a thank-you for your good work
• Annual bonuses based on the company's financial results
• Monthly contribution of CZK 1,900 to supplementary pension savings
• 5 extra vacation weeks as standard
• Pluxee card for leisure activities, vacation payments, or book purchases
• Multisport card allowing you to exercise daily for free
• Flexible working hours with the option of home office
• Favorable employee leasing of Škoda cars or discounts/interest-free loans
• Interest-free loan up to CZK 600,000 for housing or CZK 350,000 for renovation`,
        department: 'IT',
        location: 'Prague or Mladá Boleslav, Czech Republic',
        employmentType: 'Full-time',
        requiredExperience: '3+ years',
        skillRequirements: [
          { skillName: 'SAP', requiredLevel: 85, weight: 1.0, isRequired: true },
          { skillName: 'DevOps', requiredLevel: 80, weight: 1.0, isRequired: true },
          { skillName: 'Process Improvement', requiredLevel: 75, weight: 0.9, isRequired: true },
          { skillName: 'Problem Solving', requiredLevel: 80, weight: 0.9, isRequired: true },
          { skillName: 'Teamwork', requiredLevel: 75, weight: 0.8, isRequired: false },
          { skillName: 'Communication', requiredLevel: 75, weight: 0.8, isRequired: false },
          { skillName: 'Quality', requiredLevel: 70, weight: 0.7, isRequired: false },
        ],
      },
      {
        title: 'Senior Software Engineer',
        description: 'We are looking for an experienced Senior Software Engineer to join our team. You will work on cutting-edge projects and help shape the future of our technology stack.',
        department: 'IT',
        location: 'Prague, Czech Republic',
        employmentType: 'Full-time',
        requiredExperience: '5+ years',
        skillRequirements: [
          { skillName: 'Python', requiredLevel: 80, weight: 1.0, isRequired: true },
          { skillName: 'Problem Solving', requiredLevel: 85, weight: 1.0, isRequired: true },
          { skillName: 'Teamwork', requiredLevel: 75, weight: 0.8, isRequired: false },
          { skillName: 'Data Analysis', requiredLevel: 70, weight: 0.7, isRequired: false },
        ],
      },
      {
        title: 'Product Manager',
        description: 'Join our product team as a Product Manager. You will be responsible for defining product strategy and working closely with engineering and design teams.',
        department: 'Product',
        location: 'Mladá Boleslav, Czech Republic',
        employmentType: 'Full-time',
        requiredExperience: '3+ years',
        skillRequirements: [
          { skillName: 'Leadership', requiredLevel: 75, weight: 1.0, isRequired: true },
          { skillName: 'Communication', requiredLevel: 80, weight: 1.0, isRequired: true },
          { skillName: 'Project', requiredLevel: 70, weight: 0.9, isRequired: true },
          { skillName: 'Innovation', requiredLevel: 65, weight: 0.7, isRequired: false },
        ],
      },
    ];

    console.log('🚀 Starting job position import...\n');

    for (const job of exampleJobs) {
      await addJobPosition(job);
    }

    console.log('✨ All job positions added successfully!');
    console.log('\n💡 Tip: You can modify this script to add your own job positions.');
    console.log('   Or use the API endpoint: POST /api/job-positions');
    console.log('   (requires MANAGER or ADMIN role)');

  } catch (error) {
    console.error('❌ Script failed:', error);
    process.exit(1);
  } finally {
    await prisma.$disconnect();
  }
}

// Run the script
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { addJobPosition };

