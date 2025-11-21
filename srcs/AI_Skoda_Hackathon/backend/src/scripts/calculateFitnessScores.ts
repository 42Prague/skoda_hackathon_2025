/**
 * Pre-calculate fitness scores for all employees
 * This script should be run during database seeding or as a separate migration step
 * 
 * Usage: npx tsx src/scripts/calculateFitnessScores.ts
 */

import { PrismaClient } from '@prisma/client';
import { predictMultipleEmployeesFitness } from '../services/fitnessPrediction';

const prisma = new PrismaClient();

async function main() {
  console.log('🚀 Starting Fitness Score Calculation...\n');

  try {
    // Get all employees with employeeId
    const employees = await prisma.user.findMany({
      where: {
        employeeId: { not: null },
        role: 'EMPLOYEE',
      },
      select: {
        id: true,
        employeeId: true,
        firstName: true,
        lastName: true,
      },
      orderBy: {
        employeeId: 'asc',
      },
    });

    console.log(`📊 Found ${employees.length} employees to process\n`);

    if (employees.length === 0) {
      console.log('⚠️  No employees found. Make sure database is seeded.');
      return;
    }

    // Get employee IDs
    const employeeIds = employees
      .map((e) => e.employeeId)
      .filter((id) => id !== null) as string[];

    // Calculate fitness scores in batches (2 at a time to avoid rate limits)
    console.log(`🔮 Calculating fitness scores for ${employeeIds.length} employees...`);
    console.log('   This may take several minutes...\n');
    
    const fitnessScores = await predictMultipleEmployeesFitness(employeeIds, 2);

    // Update database with fitness scores
    let successCount = 0;
    let failCount = 0;

    for (const employee of employees) {
      if (!employee.employeeId) continue;

      const fitnessScore = fitnessScores.get(employee.employeeId);

      if (fitnessScore !== null && fitnessScore !== undefined) {
        try {
          await prisma.user.update({
            where: { id: employee.id },
            data: {
              fitnessScore: fitnessScore,
              fitnessScoreUpdatedAt: new Date(),
            },
          });
          console.log(`✅ ${employee.employeeId} (${employee.firstName} ${employee.lastName}): ${fitnessScore}`);
          successCount++;
        } catch (error) {
          console.error(`❌ Error updating ${employee.employeeId}:`, error);
          failCount++;
        }
      } else {
        console.log(`⚠️  ${employee.employeeId}: No fitness score calculated`);
        failCount++;
      }
    }

    console.log('\n✨ Fitness Score Calculation Complete!\n');
    console.log(`📊 Summary:`);
    console.log(`   - Total employees: ${employees.length}`);
    console.log(`   - Successfully calculated: ${successCount}`);
    console.log(`   - Failed/Missing: ${failCount}`);
  } catch (error) {
    console.error('❌ Error during fitness score calculation:', error);
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

