/**
 * Pre-calculate fitness scores for the first 5 employees from CSV data
 * This script reads real employee IDs from ERP_SK1.Start_month - SE.csv
 * (like 100870, 110153, etc.) and calculates fitness scores for them
 * 
 * Usage: npx tsx src/scripts/calculateFitnessScoresForFirst5.ts
 */

import { PrismaClient } from '@prisma/client';
import { predictMultipleEmployeesFitness } from '../services/fitnessPrediction';
import XLSX from 'xlsx';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const prisma = new PrismaClient();

// Get dataset path (same logic as dashboard.ts)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const possibleDatasetPaths = [
  '/app/data', // Docker path
  path.join(__dirname, '../../../data'), // Local path
];

function getDatasetPath(): string {
  for (const datasetPath of possibleDatasetPaths) {
    if (fs.existsSync(datasetPath)) {
      return datasetPath;
    }
  }
  return '';
}

/**
 * Get first 5 real employee IDs from CSV file (same logic as dashboard)
 * Prioritizes employee 00016687 if it exists
 */
function getFirst5EmployeeIdsFromCSV(): string[] {
  const datasetPath = getDatasetPath();
  if (!datasetPath) {
    console.warn('Dataset path not found');
    return [];
  }

  const filePath = path.join(datasetPath, 'ERP_SK1.Start_month - SE.csv');
  if (!fs.existsSync(filePath)) {
    console.warn('ERP CSV file not found');
    return [];
  }

  try {
    const workbook = XLSX.readFile(filePath);
    const sheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[sheetName];
    const data = XLSX.utils.sheet_to_json(worksheet);
    
    const employeeIds: string[] = [];
    let targetEmployeeFound = false;
    const targetEmployeeId = '00016687';
    const targetNormalized = '16687';
    
    // First, try to find employee 00016687
    for (const row of data) {
      const personalNumber = String(row['persstat_start_month.personal_number'] || '').trim();
      const normalizedId = personalNumber.replace(/^0+/, '') || personalNumber;
      
      if (normalizedId === targetNormalized || personalNumber === targetEmployeeId) {
        employeeIds.push(targetNormalized);
        targetEmployeeFound = true;
        break;
      }
    }
    
    // Then get other employees up to 5 total
    for (const row of data) {
      if (employeeIds.length >= 5) break;
      
      const personalNumber = String(row['persstat_start_month.personal_number'] || '').trim();
      
      // Skip invalid IDs
      if (!personalNumber || personalNumber === 'S' || personalNumber === 'null' || personalNumber === 'NULL') {
        continue;
      }
      
      // Validate it's numeric
      const normalizedId = personalNumber.replace(/^0+/, '') || personalNumber;
      if (!/^\d+$/.test(normalizedId) || normalizedId.length < 4) {
        continue;
      }
      
      // Skip if already added (target employee)
      if (targetEmployeeFound && normalizedId === targetNormalized) {
        continue;
      }
      
      // Use normalized ID (without leading zeros) for Python script
      // e.g., "00100870" -> "100870"
      employeeIds.push(normalizedId);
    }
    
    return employeeIds.slice(0, 5); // Ensure exactly 5
  } catch (error) {
    console.error('Error reading CSV file:', error);
    return [];
  }
}

async function main() {
  console.log('🚀 Calculating Fitness Scores for First 5 Employees from CSV...\n');

  try {
    // Get real employee IDs from CSV file (like 100870, 110153, etc.)
    const employeeIds = getFirst5EmployeeIdsFromCSV();
    
    console.log(`📊 Found ${employeeIds.length} employees from CSV:`);
    employeeIds.forEach((id, idx) => {
      console.log(`   ${idx + 1}. ${id}`);
    });
    console.log('');

    if (employeeIds.length === 0) {
      console.log('⚠️  No employees found in CSV file. Make sure data folder exists.');
      return;
    }

    // Check which employees already have fitness scores in database
    const employeesWithScores = await prisma.user.findMany({
      where: {
        employeeId: { in: employeeIds },
        fitnessScore: { not: null },
      },
      select: {
        employeeId: true,
        fitnessScore: true,
      },
    });

    const existingScores = new Map(
      employeesWithScores.map(e => [e.employeeId, e.fitnessScore])
    );

    // Filter out employees that already have scores
    const idsToCalculate = employeeIds.filter(id => {
      // Check if any user with this employeeId has a score
      // Need to handle different ID formats (with/without leading zeros)
      for (const [dbId, score] of existingScores) {
        const normalizedDbId = dbId?.replace(/^0+/, '') || dbId;
        if (normalizedDbId === id && score !== null) {
          return false; // Already calculated
        }
      }
      return true; // Needs calculation
    });

    if (idsToCalculate.length === 0) {
      console.log('✅ All employees already have fitness scores calculated!\n');
      employeeIds.forEach((id) => {
        const score = existingScores.get(id) || 'Not found in DB';
        console.log(`   ${id}: ${score}`);
      });
      return;
    }

    console.log(`🔮 Calculating fitness scores for ${idsToCalculate.length} employees...`);
    console.log('   This may take a few minutes...\n');

    // Calculate fitness scores in batches (2 at a time to avoid rate limits)
    const fitnessScores = await predictMultipleEmployeesFitness(idsToCalculate, 2);

    // Update database with fitness scores
    // Need to find users by employeeId (may have different formats)
    let successCount = 0;
    let failCount = 0;

    for (const employeeId of idsToCalculate) {
      const fitnessScore = fitnessScores.get(employeeId);

      if (fitnessScore !== null && fitnessScore !== undefined) {
        // Find user(s) with this employeeId (try different formats)
        const normalizedId = employeeId.replace(/^0+/, '') || employeeId;
        const fullId = normalizedId.padStart(8, '0');
        
        // Try to find user with exact match or normalized match
        const users = await prisma.user.findMany({
          where: {
            OR: [
              { employeeId: employeeId },
              { employeeId: normalizedId },
              { employeeId: fullId },
            ],
          },
        });

        if (users.length > 0) {
          // Update all matching users
          for (const user of users) {
            try {
              await prisma.user.update({
                where: { id: user.id },
                data: {
                  fitnessScore: fitnessScore,
                  fitnessScoreUpdatedAt: new Date(),
                },
              });
              console.log(`✅ ${employeeId} (User: ${user.firstName} ${user.lastName}): ${fitnessScore}`);
              successCount++;
            } catch (error) {
              console.error(`❌ Error updating user ${user.id} for employee ${employeeId}:`, error);
              failCount++;
            }
          }
        } else {
          console.log(`⚠️  ${employeeId}: No user found in database with this employee ID`);
          failCount++;
        }
      } else {
        console.log(`⚠️  ${employeeId}: No fitness score calculated`);
        failCount++;
      }
    }

    console.log('\n✨ Fitness Score Calculation Complete!\n');
    console.log(`📊 Summary:`);
    console.log(`   - Employees processed: ${idsToCalculate.length}`);
    console.log(`   - Successfully calculated: ${successCount}`);
    console.log(`   - Failed/Missing: ${failCount}`);
    
    // Show all 5 employees with their scores
    console.log('\n📋 All 5 Dashboard Employees:');
    for (const employeeId of employeeIds) {
      const normalizedId = employeeId.replace(/^0+/, '') || employeeId;
      const fullId = normalizedId.padStart(8, '0');
      
      const user = await prisma.user.findFirst({
        where: {
          OR: [
            { employeeId: employeeId },
            { employeeId: normalizedId },
            { employeeId: fullId },
          ],
        },
        select: {
          employeeId: true,
          fitnessScore: true,
        },
      });
      
      const score = user?.fitnessScore !== null && user?.fitnessScore !== undefined 
        ? user.fitnessScore 
        : 'Not calculated';
      console.log(`   ${employeeId}: ${score}`);
    }
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

