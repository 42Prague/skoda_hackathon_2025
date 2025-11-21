import { exec } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';
import * as fs from 'fs';
import { fileURLToPath } from 'url';

const execAsync = promisify(exec);

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Get paths
const projectRoot = path.join(__dirname, '../../../');
const fitnessPredictionPath = path.join(projectRoot, 'fitness_prediction');
const predictScriptPath = path.join(fitnessPredictionPath, 'predict_sap_position.py');

interface FitnessPredictionResult {
  employee_id: string;
  fitness_score: number | null;
  success: boolean;
  error?: string;
}

/**
 * Predict fitness score for an employee using predict_sap_position.py
 * @param employeeId - Employee ID (e.g., "00004241" or "4241")
 * @returns Fitness score (0-100) or null if prediction failed
 */
export async function predictEmployeeFitness(employeeId: string): Promise<number | null> {
  try {
    // Normalize employee ID - remove leading zeros for Python script
    const normalizedId = employeeId.replace(/^0+/, '') || employeeId;
    
    // Check if Python script exists
    if (!fs.existsSync(predictScriptPath)) {
      console.error(`❌ Python script not found: ${predictScriptPath}`);
      return null;
    }

    // Check if .env file exists in fitness_prediction folder
    const envPath = path.join(fitnessPredictionPath, '.env');
    if (!fs.existsSync(envPath)) {
      console.warn(`⚠️  .env file not found in fitness_prediction folder`);
      // Try to use backend .env or environment variables
    }

    // Get Python path - try python3 first, then python
    let pythonCmd = 'python3';
    try {
      await execAsync('which python3');
    } catch {
      try {
        await execAsync('which python');
        pythonCmd = 'python';
      } catch {
        console.error('❌ Python not found. Please install Python 3.');
        return null;
      }
    }

    // Change to fitness_prediction directory and run script
    const command = `cd "${fitnessPredictionPath}" && ${pythonCmd} predict_sap_position.py ${normalizedId}`;
    
    console.log(`🔮 Running fitness prediction for employee ${employeeId}...`);
    const { stdout, stderr } = await execAsync(command, {
      cwd: fitnessPredictionPath,
      env: {
        ...process.env,
        PYTHONUNBUFFERED: '1', // Ensure output is not buffered
      },
      timeout: 60000, // 60 second timeout
    });

    // Parse JSON output from the script
    // The script outputs JSON at the end
    const lines = stdout.split('\n');
    let jsonOutput = '';
    let inJson = false;
    
    // Find the JSON output (should be the last line or near the end)
    for (let i = lines.length - 1; i >= 0; i--) {
      const line = lines[i].trim();
      if (line.startsWith('{') && line.endsWith('}')) {
        jsonOutput = line;
        break;
      }
      // Try to find JSON that might span multiple lines
      if (line.includes('"fitness_score"')) {
        // Look for complete JSON object
        const jsonStart = stdout.lastIndexOf('{');
        const jsonEnd = stdout.lastIndexOf('}') + 1;
        if (jsonStart >= 0 && jsonEnd > jsonStart) {
          jsonOutput = stdout.substring(jsonStart, jsonEnd);
          break;
        }
      }
    }

    if (!jsonOutput) {
      console.error('❌ Could not parse JSON output from prediction script');
      console.error('Script output:', stdout);
      return null;
    }

    try {
      const result: FitnessPredictionResult = JSON.parse(jsonOutput);
      
      if (result.success && result.fitness_score !== null && result.fitness_score !== undefined) {
        console.log(`✅ Fitness score for ${employeeId}: ${result.fitness_score}`);
        return result.fitness_score;
      } else {
        console.warn(`⚠️  Prediction completed but no fitness score returned for ${employeeId}`);
        return null;
      }
    } catch (parseError) {
      console.error('❌ Error parsing JSON output:', parseError);
      console.error('JSON string:', jsonOutput);
      return null;
    }
  } catch (error: any) {
    console.error(`❌ Error running fitness prediction for ${employeeId}:`, error.message);
    if (error.stderr) {
      console.error('Python script stderr:', error.stderr);
    }
    return null;
  }
}

/**
 * Predict fitness scores for multiple employees in parallel (with limit)
 * @param employeeIds - Array of employee IDs
 * @returns Map of employeeId -> fitness score
 */
export async function predictMultipleEmployeesFitness(
  employeeIds: string[],
  maxConcurrent: number = 3
): Promise<Map<string, number | null>> {
  const results = new Map<string, number | null>();
  
  // Process in batches to avoid overwhelming the API
  for (let i = 0; i < employeeIds.length; i += maxConcurrent) {
    const batch = employeeIds.slice(i, i + maxConcurrent);
    const batchPromises = batch.map(async (employeeId) => {
      const score = await predictEmployeeFitness(employeeId);
      return { employeeId, score };
    });
    
    const batchResults = await Promise.all(batchPromises);
    batchResults.forEach(({ employeeId, score }) => {
      results.set(employeeId, score);
    });
    
    // Small delay between batches to avoid rate limiting
    if (i + maxConcurrent < employeeIds.length) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  
  return results;
}

