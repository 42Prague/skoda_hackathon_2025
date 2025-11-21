/**
 * Get real employee ID from the dataset CSV file
 * This finds actual personal_number values from ERP_SK1.Start_month - SE.csv
 * 
 * Usage: npx tsx src/scripts/getRealEmployeeFromDataset.ts
 */

import XLSX from 'xlsx';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Dataset paths
const possibleDatasetPaths = [
  '/app/data',
  path.join(__dirname, '../../../data')
];

let DATASET_PATH = '';

for (const datasetPath of possibleDatasetPaths) {
  if (fs.existsSync(datasetPath)) {
    DATASET_PATH = datasetPath;
    break;
  }
}

if (!DATASET_PATH) {
  console.error('❌ No dataset folder found!');
  process.exit(1);
}

function readCSVFile(filename: string): any[] {
  const filePath = path.join(DATASET_PATH, filename);
  
  if (!fs.existsSync(filePath)) {
    console.error(`❌ File not found: ${filename}`);
    return [];
  }

  try {
    const workbook = XLSX.readFile(filePath);
    const sheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[sheetName];
    const data = XLSX.utils.sheet_to_json(worksheet);
    return data;
  } catch (error) {
    console.error(`❌ Error reading ${filename}:`, error);
    return [];
  }
}

async function main() {
  console.log('📊 Reading real employee IDs from dataset...\n');
  console.log(`📁 Dataset path: ${DATASET_PATH}\n`);

  const employeeData = readCSVFile('ERP_SK1.Start_month - SE.csv');
  
  if (employeeData.length === 0) {
    console.error('❌ No employee data found in CSV file');
    return;
  }

  console.log(`✅ Found ${employeeData.length} employees in dataset\n`);

  // Extract employee IDs (personal_number)
  const employeeIds: Array<{ id: string; profession?: string; position?: string }> = [];

  for (const row of employeeData) {
    const personalNumber = row['persstat_start_month.personal_number'] || 
                          row['Variabilní pole (os. číslo)'] || 
                          row['personal_number'];
    
    if (personalNumber) {
      const id = String(personalNumber).trim();
      if (id && !employeeIds.find(e => e.id === id)) {
        employeeIds.push({
          id: id,
          profession: row['persstat_start_month.profession'] || row['profession'],
          position: row['persstat_start_month.planned_position'] || row['position'],
        });
      }
    }
  }

  console.log('📋 Real Employee IDs from Dataset:\n');
  console.log('First 10 employees:\n');
  
  employeeIds.slice(0, 10).forEach((emp, idx) => {
    console.log(`${idx + 1}. Employee ID: ${emp.id}`);
    if (emp.profession) {
      const profession = String(emp.profession).replace(/^\d+\s+/, ''); // Remove code prefix
      console.log(`   Profession: ${profession}`);
    }
    if (emp.position) {
      const position = String(emp.position).replace(/^\d+\s+/, '').replace(/^\d+\s*-\s*/, '');
      console.log(`   Position: ${position}`);
    }
    console.log('');
  });

  // Recommended demo employee (first one from dataset)
  const demoEmployee = employeeIds[0];
  
  console.log('✅ Recommended Demo Employee:');
  console.log(`   Employee ID: ${demoEmployee.id}`);
  console.log(`   (This is a REAL ID from the CSV dataset)`);
  console.log(`   Password: password123`);
  console.log('');
  console.log('💡 All data linked to this employee ID comes from the dataset!');
  console.log('   - Skills from qualifications CSV');
  console.log('   - Courses from course participation CSV');
  console.log('   - Risk assessments linked by employeeId');
}

main().catch(console.error);

