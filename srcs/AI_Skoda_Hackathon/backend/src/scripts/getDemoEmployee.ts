/**
 * Script to find a demo employee from the dataset
 * This finds the first employee created from the ERP CSV file
 * 
 * Usage: npx tsx src/scripts/getDemoEmployee.ts
 */

import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  try {
    console.log('🔍 Finding demo employee from dataset...\n');

    // Find the first employee (not manager) with an employeeId from the dataset
    // Employees from the dataset will have employeeId that's a personal_number (not starting with MGR)
    const employee = await prisma.user.findFirst({
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
        createdAt: 'asc', // Get the first one created (from CSV import)
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
      },
    });

    if (!employee) {
      console.log('❌ No employee found in database!');
      console.log('💡 Run the seed script first: npm run db:seed:real');
      return;
    }

    console.log('✅ Demo Employee Found:\n');
    console.log('   Name:', `${employee.firstName} ${employee.lastName}`);
    console.log('   Email:', employee.email);
    console.log('   Employee ID:', employee.employeeId);
    console.log('   Department:', employee.department || 'N/A');
    console.log('   Password: password123');
    console.log('   Skills:', employee.userSkills.length);
    
    if (employee.userSkills.length > 0) {
      console.log('\n   Skill Details:');
      employee.userSkills.forEach((us, idx) => {
        console.log(`   ${idx + 1}. ${us.skill.name}: ${Math.round(us.level)}%`);
      });
    }

    console.log('\n📋 Use these credentials for demo login:');
    console.log(`   Email: ${employee.email}`);
    console.log('   Password: password123');
    console.log('\n✨ All employee dashboard data will be specific to this user!');

  } catch (error) {
    console.error('❌ Error finding employee:', error);
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

