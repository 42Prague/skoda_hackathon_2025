import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Starting seed...');

  // Create skills
  const skills = await Promise.all([
    prisma.skill.upsert({
      where: { name: 'Technical' },
      update: {},
      create: {
        name: 'Technical',
        category: 'Core',
        description: 'Technical and engineering skills',
        marketRelevance: 90,
      },
    }),
    prisma.skill.upsert({
      where: { name: 'Leadership' },
      update: {},
      create: {
        name: 'Leadership',
        category: 'Soft Skills',
        description: 'Leadership and management capabilities',
        marketRelevance: 85,
      },
    }),
    prisma.skill.upsert({
      where: { name: 'Communication' },
      update: {},
      create: {
        name: 'Communication',
        category: 'Soft Skills',
        description: 'Effective communication skills',
        marketRelevance: 80,
      },
    }),
    prisma.skill.upsert({
      where: { name: 'Problem Solving' },
      update: {},
      create: {
        name: 'Problem Solving',
        category: 'Core',
        description: 'Analytical and problem-solving abilities',
        marketRelevance: 88,
      },
    }),
    prisma.skill.upsert({
      where: { name: 'Innovation' },
      update: {},
      create: {
        name: 'Innovation',
        category: 'Core',
        description: 'Creative thinking and innovation',
        marketRelevance: 82,
      },
    }),
    prisma.skill.upsert({
      where: { name: 'Digital' },
      update: {},
      create: {
        name: 'Digital',
        category: 'Technical',
        description: 'Digital transformation and technology skills',
        marketRelevance: 92,
      },
    }),
    prisma.skill.upsert({
      where: { name: 'Data Analysis' },
      update: {},
      create: {
        name: 'Data Analysis',
        category: 'Technical',
        description: 'Data analysis and analytics capabilities',
        marketRelevance: 87,
      },
    }),
    prisma.skill.upsert({
      where: { name: 'Python' },
      update: {},
      create: {
        name: 'Python',
        category: 'Technical',
        description: 'Python programming language',
        marketRelevance: 90,
      },
    }),
    prisma.skill.upsert({
      where: { name: 'Statistical Modeling' },
      update: {},
      create: {
        name: 'Statistical Modeling',
        category: 'Technical',
        description: 'Statistical analysis and modeling',
        marketRelevance: 85,
      },
    }),
    prisma.skill.upsert({
      where: { name: 'Visualization' },
      update: {},
      create: {
        name: 'Visualization',
        category: 'Technical',
        description: 'Data visualization skills',
        marketRelevance: 80,
      },
    }),
  ]);

  console.log('✅ Skills created:', skills.length);

  // Hash password
  const hashedPassword = await bcrypt.hash('password123', 10);

  // Create manager user
  const manager = await prisma.user.upsert({
    where: { email: 'manager@skoda.com' },
    update: {},
    create: {
      email: 'manager@skoda.com',
      password: hashedPassword,
      firstName: 'Petr',
      lastName: 'Manager',
      employeeId: 'EMP001',
      role: 'MANAGER',
      department: 'IT',
    },
  });

  console.log('✅ Manager created:', manager.email);

  // Create employee users
  const employee1 = await prisma.user.upsert({
    where: { email: 'jan@skoda.com' },
    update: {},
    create: {
      email: 'jan@skoda.com',
      password: hashedPassword,
      firstName: 'Jan',
      lastName: 'Novák',
      employeeId: 'EMP002',
      role: 'EMPLOYEE',
      department: 'IT',
      managerId: manager.id,
    },
  });

  const employee2 = await prisma.user.upsert({
    where: { email: 'petra@skoda.com' },
    update: {},
    create: {
      email: 'petra@skoda.com',
      password: hashedPassword,
      firstName: 'Petra',
      lastName: 'Svobodová',
      employeeId: 'EMP003',
      role: 'EMPLOYEE',
      department: 'Design',
      managerId: manager.id,
    },
  });

  const employee3 = await prisma.user.upsert({
    where: { email: 'martin@skoda.com' },
    update: {},
    create: {
      email: 'martin@skoda.com',
      password: hashedPassword,
      firstName: 'Martin',
      lastName: 'Dvořák',
      employeeId: 'EMP004',
      role: 'EMPLOYEE',
      department: 'Analytics',
      managerId: manager.id,
    },
  });

  console.log('✅ Employees created:', 3);

  // Create user skills for employee1 (Jan)
  const technicalSkill = skills.find(s => s.name === 'Technical');
  const leadershipSkill = skills.find(s => s.name === 'Leadership');
  const communicationSkill = skills.find(s => s.name === 'Communication');
  const problemSolvingSkill = skills.find(s => s.name === 'Problem Solving');
  const innovationSkill = skills.find(s => s.name === 'Innovation');
  const digitalSkill = skills.find(s => s.name === 'Digital');

  if (technicalSkill && leadershipSkill && communicationSkill && problemSolvingSkill && innovationSkill && digitalSkill) {
    await Promise.all([
      prisma.userSkill.upsert({
        where: {
          userId_skillId: {
            userId: employee1.id,
            skillId: technicalSkill.id,
          },
        },
        update: { level: 85 },
        create: {
          userId: employee1.id,
          skillId: technicalSkill.id,
          level: 85,
        },
      }),
      prisma.userSkill.upsert({
        where: {
          userId_skillId: {
            userId: employee1.id,
            skillId: leadershipSkill.id,
          },
        },
        update: { level: 65 },
        create: {
          userId: employee1.id,
          skillId: leadershipSkill.id,
          level: 65,
        },
      }),
      prisma.userSkill.upsert({
        where: {
          userId_skillId: {
            userId: employee1.id,
            skillId: communicationSkill.id,
          },
        },
        update: { level: 78 },
        create: {
          userId: employee1.id,
          skillId: communicationSkill.id,
          level: 78,
        },
      }),
      prisma.userSkill.upsert({
        where: {
          userId_skillId: {
            userId: employee1.id,
            skillId: problemSolvingSkill.id,
          },
        },
        update: { level: 82 },
        create: {
          userId: employee1.id,
          skillId: problemSolvingSkill.id,
          level: 82,
        },
      }),
      prisma.userSkill.upsert({
        where: {
          userId_skillId: {
            userId: employee1.id,
            skillId: innovationSkill.id,
          },
        },
        update: { level: 70 },
        create: {
          userId: employee1.id,
          skillId: innovationSkill.id,
          level: 70,
        },
      }),
      prisma.userSkill.upsert({
        where: {
          userId_skillId: {
            userId: employee1.id,
            skillId: digitalSkill.id,
          },
        },
        update: { level: 88 },
        create: {
          userId: employee1.id,
          skillId: digitalSkill.id,
          level: 88,
        },
      }),
    ]);

    console.log('✅ User skills created for Jan');
  }

  // Create a sample course
  const dataAnalysisSkill = skills.find(s => s.name === 'Data Analysis');
  const pythonSkill = skills.find(s => s.name === 'Python');
  const statisticalSkill = skills.find(s => s.name === 'Statistical Modeling');
  const visualizationSkill = skills.find(s => s.name === 'Visualization');

  if (dataAnalysisSkill && pythonSkill && statisticalSkill && visualizationSkill) {
    const course = await prisma.course.create({
      data: {
        title: 'Advanced Data Analytics',
        description: 'Master the fundamentals and advanced techniques of data analytics to stay relevant in the evolving automotive industry.',
        duration: '4 weeks',
        difficulty: 'Intermediate',
        courseSkills: {
          create: [
            { skillId: dataAnalysisSkill.id },
            { skillId: pythonSkill.id },
            { skillId: statisticalSkill.id },
            { skillId: visualizationSkill.id },
          ],
        },
        modules: {
          create: [
            {
              type: 'LESSON',
              title: 'Introduction to Data Analytics',
              description: 'Learn the basics of data analytics',
              order: 0,
              isRequired: true,
            },
            {
              type: 'LESSON',
              title: 'Working with Python & Pandas',
              description: 'Master Python and Pandas for data manipulation',
              order: 1,
              isRequired: true,
            },
            {
              type: 'QUIZ',
              title: 'Knowledge Check: Basics',
              description: 'Test your understanding of the basics',
              order: 2,
              isRequired: true,
              unlockCondition: 'complete_previous',
              quizQuestions: {
                create: [
                  {
                    question: 'Which Python library is most commonly used for data manipulation and analysis?',
                    options: JSON.stringify([
                      { id: 'a', text: 'NumPy' },
                      { id: 'b', text: 'Pandas' },
                      { id: 'c', text: 'Matplotlib' },
                      { id: 'd', text: 'Scikit-learn' },
                    ]),
                    correctAnswer: 'b',
                    explanation: 'Pandas is the most widely used library for data manipulation and analysis in Python.',
                    skillLevel: 'Medium',
                    order: 0,
                  },
                ],
              },
            },
            {
              type: 'LESSON',
              title: 'Statistical Analysis Methods',
              description: 'Learn statistical methods for data analysis',
              order: 3,
              isRequired: true,
              unlockCondition: 'complete_previous',
            },
            {
              type: 'ASSIGNMENT',
              title: 'Practical Assignment: Data Project',
              description: 'Apply your skills to a real-world data project',
              order: 4,
              isRequired: true,
              unlockCondition: 'complete_previous',
            },
            {
              type: 'LESSON',
              title: 'Data Visualization & Reporting',
              description: 'Create compelling visualizations and reports',
              order: 5,
              isRequired: true,
              unlockCondition: 'complete_previous',
            },
            {
              type: 'QUIZ',
              title: 'Final Assessment',
              description: 'Final comprehensive assessment',
              order: 6,
              isRequired: true,
              unlockCondition: 'complete_previous',
            },
            {
              type: 'SUMMARY',
              title: 'Course Summary & Certificate',
              description: 'Review course content and receive certificate',
              order: 7,
              isRequired: true,
              unlockCondition: 'complete_previous',
            },
          ],
        },
      },
    });

    console.log('✅ Course created:', course.title);

    // Enroll employee1 in the course
    const enrollment = await prisma.enrollment.create({
      data: {
        userId: employee1.id,
        courseId: course.id,
        progress: 0,
      },
    });

    console.log('✅ Enrollment created for Jan');

    // Unlock first module
    const firstModule = await prisma.courseModule.findFirst({
      where: {
        courseId: course.id,
        order: 0,
      },
    });

    if (firstModule) {
      await prisma.moduleProgress.create({
        data: {
          userId: employee1.id,
          moduleId: firstModule.id,
          status: 'UNLOCKED',
          progress: 0,
        },
      });

      console.log('✅ First module unlocked for Jan');
    }
  }

  // Create career paths
  const careerPath1 = await prisma.careerPath.create({
    data: {
      title: 'Senior Software Engineer',
      description: 'Advanced technical role with focus on software development',
      currentRole: 'Software Engineer',
      targetRole: 'Senior Software Engineer',
      fitScore: 92,
      reason: 'Your technical skills and project experience align perfectly with this role',
      skills: {
        create: [
          { skillId: technicalSkill!.id, requiredLevel: 85 },
          { skillId: problemSolvingSkill!.id, requiredLevel: 80 },
          { skillId: digitalSkill!.id, requiredLevel: 85 },
        ],
      },
    },
  });

  const careerPath2 = await prisma.careerPath.create({
    data: {
      title: 'Technical Lead',
      description: 'Leadership role combining technical expertise with team management',
      currentRole: 'Software Engineer',
      targetRole: 'Technical Lead',
      fitScore: 88,
      reason: 'Strong technical foundation with growing leadership capabilities',
      skills: {
        create: [
          { skillId: technicalSkill!.id, requiredLevel: 85 },
          { skillId: leadershipSkill!.id, requiredLevel: 70 },
          { skillId: communicationSkill!.id, requiredLevel: 75 },
        ],
      },
    },
  });

  console.log('✅ Career paths created:', 2);

  console.log('🎉 Seed completed successfully!');
}

main()
  .catch((e) => {
    console.error('❌ Seed failed:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });

