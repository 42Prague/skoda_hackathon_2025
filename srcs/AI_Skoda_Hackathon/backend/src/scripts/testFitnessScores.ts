/**
 * Test script to verify IT fitness scores are being loaded correctly
 */

import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function getITFitnessScores(): Map<string, number> {
  const fitnessScores = new Map<string, number>();
  
  const possiblePaths = [
    path.join(__dirname, '../../../fitness_prediction/it_fitness_scores.json'),
    path.join(__dirname, '../../fitness_prediction/it_fitness_scores.json'),
    path.join(process.cwd(), '../fitness_prediction/it_fitness_scores.json'),
    path.join(process.cwd(), 'fitness_prediction/it_fitness_scores.json'),
  ];
  
  let loaded = false;
  for (const filePath of possiblePaths) {
    try {
      if (fs.existsSync(filePath)) {
        const fileContent = fs.readFileSync(filePath, 'utf-8');
        const scores = JSON.parse(fileContent);
        
        console.log(`✅ Found file: ${filePath}`);
        console.log(`📊 Raw scores:`, scores);
        
        for (const [empId, score] of Object.entries(scores)) {
          const normalizedId = String(empId).replace(/^0+/, '') || String(empId);
          const fullId = normalizedId.padStart(8, '0');
          
          fitnessScores.set(normalizedId, score as number);
          fitnessScores.set(String(empId), score as number);
          if (fullId !== normalizedId && fullId !== String(empId)) {
            fitnessScores.set(fullId, score as number);
          }
          
          console.log(`  - ${empId} (normalized: ${normalizedId}, full: ${fullId}) -> ${score}`);
        }
        
        console.log(`✅ Loaded ${fitnessScores.size} entries`);
        loaded = true;
        break;
      } else {
        console.log(`❌ Not found: ${filePath}`);
      }
    } catch (error) {
      console.error(`❌ Error reading ${filePath}:`, error);
    }
  }
  
  if (!loaded) {
    console.error('❌ File not found in any path!');
  }
  
  return fitnessScores;
}

// Test matching
const scores = getITFitnessScores();
const testIds = ['100870', '110153', '110190', '110464', '110542', '00100870', '00110153'];

console.log('\n🧪 Testing ID matching:');
testIds.forEach(id => {
  const normalized = id.replace(/^0+/, '');
  const full = normalized.padStart(8, '0');
  const score1 = scores.get(normalized);
  const score2 = scores.get(id);
  const score3 = scores.get(full);
  console.log(`  ${id} -> normalized: ${normalized}, full: ${full}`);
  console.log(`    Score (normalized): ${score1 ?? 'NOT FOUND'}`);
  console.log(`    Score (original): ${score2 ?? 'NOT FOUND'}`);
  console.log(`    Score (full): ${score3 ?? 'NOT FOUND'}`);
});

