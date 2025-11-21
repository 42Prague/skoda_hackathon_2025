/**
 * Find the first employee from the dataset that actually exists in the database
 * 
 * Usage: npx tsx src/scripts/findFirstEmployee.ts
 */

import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  try {
    console.log('🔍 Finding first employee from dataset in database...\n');

    // Find first employee (not manager) ordered by creation time
    const firstEmployee = await prisma.user.findFirst({
      where: {
        role: 'EMPLOYEE',
        employeeId: {
          not: null,
          not: {
            startsWith: 'MGR', // Exclude managers
          },
        },
      },
      orderBy: {
        createdAt: 'asc', // First created = first from dataset
      },
      select: {
        id: true,
        email: true,
        firstName: true,
        lastName: true,
        employeeId: true,
        department: true,
        role: true,
        userSkills: {
          select: {
            skill: {
              select: {
                name: true,
              },
            },
            level: true,
          },
        },
        employeeSkillRisks: {
          select: {
            id: true,
            riskScore: true,
            riskLabel: true,
          },
        },
      },
    });

    if (!firstEmployee) {
      console.log('❌ No employees found in database!');
      console.log('\n💡 Run the seed script to import employees:');
      console.log('   cd backend');
      console.log('   npm run db:seed:real');
      return;
    }

    console.log('✅ First Employee from Dataset:\n');
    console.log('   Employee ID:', firstEmployee.employeeId);
    console.log('   Name:', `${firstEmployee.firstName} ${firstEmployee.lastName}`);
    console.log('   Email:', firstEmployee.email);
    console.log('   Department:', firstEmployee.department || 'N/A');
    console.log('   Password: password123');
    console.log('   Skills:', firstEmployee.userSkills.length);
    console.log('   Risk Assessments:', firstEmployee.employeeSkillRisks.length);
    console.log('');

    if (firstEmployee.userSkills.length > 0) {
      console.log('   Skills:');
      firstEmployee.userSkills.slice(0, 5).forEach((us, idx) => {
        console.log(`   ${idx + 1}. ${us.skill.name}: ${Math.round(us.level)}%`);
      });
      if (firstEmployee.userSkills.length > 5) {
        console.log(`   ... and ${firstEmployee.userSkills.length - 5} more`);
      }
      console.log('');
    }

    console.log('📋 Login Credentials:');
    console.log('   Email:', firstEmployee.email);
    console.log('   Password: password123');
    console.log('   Employee ID:', firstEmployee.employeeId);
    console.log('');
    console.log('✅ Update Login.tsx with this email to use this employee!');

  } catch (error) {
    console.error('❌ Error:', error);
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

