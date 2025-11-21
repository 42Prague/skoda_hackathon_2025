/**
 * Add SAP DevOps Engineer (m/w) position
 * Job ID: 3881
 * 
 * Usage: npm run add-sap-job
 * or: npx tsx src/scripts/addSAPDevOpsJob.ts
 */

import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  try {
    console.log('📋 Adding SAP DevOps Engineer position...\n');

    // Find or create required skills
    const skills = [
      { name: 'SAP', requiredLevel: 85, weight: 1.0, isRequired: true },
      { name: 'DevOps', requiredLevel: 80, weight: 1.0, isRequired: true },
      { name: 'Process Improvement', requiredLevel: 75, weight: 0.9, isRequired: true },
      { name: 'Problem Solving', requiredLevel: 80, weight: 0.9, isRequired: true },
      { name: 'Teamwork', requiredLevel: 75, weight: 0.8, isRequired: false },
      { name: 'Communication', requiredLevel: 75, weight: 0.8, isRequired: false },
      { name: 'Quality', requiredLevel: 70, weight: 0.7, isRequired: false },
    ];

    const skillIds: Array<{ skillId: string; requiredLevel: number; weight: number; isRequired: boolean }> = [];

    for (const skillReq of skills) {
      // Try to find existing skill by name (case-insensitive search)
      let skill = await prisma.skill.findFirst({
        where: {
          name: {
            equals: skillReq.name,
            mode: 'insensitive',
          },
        },
      });

      // If skill doesn't exist, create it
      if (!skill) {
        console.log(`  ➕ Creating new skill: ${skillReq.name}`);
        skill = await prisma.skill.create({
          data: {
            name: skillReq.name,
            category: skillReq.name === 'SAP' || skillReq.name === 'DevOps' 
              ? 'Technical Skills' 
              : skillReq.name === 'Problem Solving' || skillReq.name === 'Teamwork' || skillReq.name === 'Communication'
              ? 'Soft Skills'
              : 'Professional Skills',
            marketRelevance: skillReq.requiredLevel,
          },
        });
      } else {
        console.log(`  ✓ Found existing skill: ${skill.name}`);
      }

      skillIds.push({
        skillId: skill.id,
        requiredLevel: skillReq.requiredLevel,
        weight: skillReq.weight,
        isRequired: skillReq.isRequired,
      });
    }

    // Check if job position already exists
    const existingJob = await prisma.jobPosition.findFirst({
      where: {
        title: {
          equals: 'SAP DevOps Engineer (m/w)',
          mode: 'insensitive',
        },
      },
    });

    if (existingJob) {
      console.log('⚠️  Job position already exists with title "SAP DevOps Engineer (m/w)"');
      console.log('   ID:', existingJob.id);
      console.log('   Status:', existingJob.status);
      console.log('\n💡 If you want to update it, use the API or delete and recreate.');
      return;
    }

    // Create the job position
    const jobPosition = await prisma.jobPosition.create({
      data: {
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
• Interest-free loan up to CZK 600,000 for housing or CZK 350,000 for renovation

Reference ID: 3881`,
        department: 'IT',
        location: 'Prague or Mladá Boleslav, Czech Republic',
        employmentType: 'Full-time',
        status: 'OPEN',
        requiredExperience: '3+ years',
        skills: {
          create: skillIds,
        },
      },
      include: {
        skills: {
          include: {
            skill: true,
          },
        },
      },
    });

    console.log('\n✅ Job position created successfully!');
    console.log('   ID:', jobPosition.id);
    console.log('   Title:', jobPosition.title);
    console.log('   Department:', jobPosition.department);
    console.log('   Location:', jobPosition.location);
    console.log('   Status:', jobPosition.status);
    console.log('   Skills linked:', jobPosition.skills.length);
    console.log('\n🎉 The job position will now appear in the web app!');
    console.log('   View it on: Employee Dashboard > Open Job Positions');

  } catch (error) {
    console.error('❌ Error adding job position:', error);
    throw error;
  } finally {
    await prisma.$disconnect();
  }
}

main()
  .catch((error) => {
    console.error('❌ Script failed:', error);
    process.exit(1);
  });

