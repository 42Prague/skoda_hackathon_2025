/**
 * Add IT Specialist (m/w) position
 * Job ID: 1486
 * 
 * Usage: npm run add-it-specialist-job
 * or: npx tsx src/scripts/addITSpecialistJob.ts
 */

import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  try {
    console.log('📋 Adding IT Specialist position...\n');

    // Find or create required skills
    const skills = [
      { name: 'Technical Skills', requiredLevel: 70, weight: 1.0, isRequired: true },
      { name: 'Innovation', requiredLevel: 65, weight: 0.9, isRequired: true },
      { name: 'Digital', requiredLevel: 70, weight: 0.9, isRequired: true },
      { name: 'Adaptability', requiredLevel: 75, weight: 0.8, isRequired: true },
      { name: 'Communication', requiredLevel: 70, weight: 0.8, isRequired: false },
      { name: 'Teamwork', requiredLevel: 70, weight: 0.8, isRequired: false },
      { name: 'Time Management', requiredLevel: 65, weight: 0.7, isRequired: false },
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
            category: skillReq.name === 'Technical Skills' || skillReq.name === 'Digital'
              ? 'Technical Skills'
              : skillReq.name === 'Innovation'
              ? 'Professional Skills'
              : skillReq.name === 'Communication' || skillReq.name === 'Teamwork' || skillReq.name === 'Time Management' || skillReq.name === 'Adaptability'
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
          equals: 'IT Specialist (m/w)',
          mode: 'insensitive',
        },
      },
    });

    if (existingJob) {
      console.log('⚠️  Job position already exists with title "IT Specialist (m/w)"');
      console.log('   ID:', existingJob.id);
      console.log('   Status:', existingJob.status);
      console.log('\n💡 If you want to update it, use the API or delete and recreate.');
      return;
    }

    // Create the job position
    const jobPosition = await prisma.jobPosition.create({
      data: {
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
        status: 'OPEN',
        requiredExperience: 'Entry level to experienced',
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

