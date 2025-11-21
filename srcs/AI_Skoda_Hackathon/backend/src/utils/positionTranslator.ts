/**
 * Position Translator
 * Translates Czech job positions to English
 */

const positionTranslations: Record<string, string> = {
  // Common positions from ERP data (exact matches)
  'Pedagogický/á pracovník/-vnice': 'Educational Worker',
  'Pedagogický pracovník': 'Educational Worker',
  'Pedagogický/á': 'Educational Worker',
  'Koordinátor/ka': 'Coordinator',
  'Koordinátor': 'Coordinator',
  'DPP/DPČ': 'Part-time/Contract Worker',
  'DPP': 'Part-time Worker',
  'DPČ': 'Contract Worker',
  'Administrátor/ka': 'Administrator',
  'Administrátor': 'Administrator',
  'Specialista/-tka admin.a služ.': 'Administrative Services Specialist',
  'Specialista/-tka financí': 'Finance Specialist',
  'Specialista/-tka': 'Specialist',
  'Specialista': 'Specialist',
  
  // More specific positions
  'Učitel/ lektor-CNC Centrum': 'Teacher/Lecturer - CNC Center',
  'Učitel': 'Teacher',
  'Lektor': 'Lecturer',
  'Lektor elektromobilita - pohony': 'Lecturer - Electromobility - Drives',
  'Lektor robotiky a aplik. techniky': 'Lecturer - Robotics and Applied Technology',
  'Koordinátor kariérního managementu': 'Career Management Coordinator',
  'Koord. rozvoj kompetencí a man. programy': 'Coordinator - Competence Development and Management Programs',
  '595 - DPP/DPČ': 'Part-time/Contract Worker',
  'Projektant/ka': 'Project Designer',
  'Projektový/á koordinátor/ka': 'Project Coordinator',
  'Odborný/á koordinátor/ka': 'Professional Coordinator',
  'Vedoucí': 'Manager',
  'Stážista': 'Intern',
  'IT Specialista/-tka': 'IT Specialist',
  'Specialista/-tka logistiky': 'Logistics Specialist',
  'Specialista/-tka výroby': 'Production Specialist',
  'Specialista/-tka údržby': 'Maintenance Specialist',
  'Specialista/-tka GRC': 'GRC Specialist',
  'Specialista/-tka HR': 'HR Specialist',
  
  // Generic fallbacks
  'N/A': 'N/A',
  '': 'N/A',
};

/**
 * Translate Czech position to English
 */
export function translatePosition(czechPosition: string): string {
  if (!czechPosition || czechPosition.trim() === '' || czechPosition === 'N/A') {
    return 'N/A';
  }
  
  const trimmed = czechPosition.trim();
  
  // Exact match first (case-sensitive)
  if (positionTranslations[trimmed]) {
    return positionTranslations[trimmed];
  }
  
  // Try case-insensitive exact match
  const lowerTrimmed = trimmed.toLowerCase();
  for (const [czech, english] of Object.entries(positionTranslations)) {
    if (czech.toLowerCase() === lowerTrimmed) {
      return english;
    }
  }
  
  // Try partial matches (if Czech position contains known keyword)
  for (const [czech, english] of Object.entries(positionTranslations)) {
    if (czech !== 'N/A' && czech !== '' && lowerTrimmed.includes(czech.toLowerCase())) {
      return english;
    }
  }
  
  // Try to translate common words
  let translated = trimmed;
  
  // Common word replacements (comprehensive dictionary)
  const wordReplacements: Record<string, string> = {
    'pedagogický': 'educational',
    'pedagogická': 'educational',
    'pracovník': 'worker',
    'pracovnice': 'worker',
    'koordinátor': 'coordinator',
    'koordinátorka': 'coordinator',
    'administrátor': 'administrator',
    'administrátorka': 'administrator',
    'specialista': 'specialist',
    'specialistka': 'specialist',
    'učitel': 'teacher',
    'lektorka': 'lecturer',
    'lektor': 'lecturer',
    'elektromobilita': 'electromobility',
    'robotika': 'robotics',
    'robotiky': 'robotics',
    'kariérního': 'career',
    'managementu': 'management',
    'pohony': 'drives',
    'aplik': 'applied',
    'aplikované': 'applied',
    'techniky': 'technology',
    'technologie': 'technology',
    'financí': 'finance',
    'logistiky': 'logistics',
    'výroby': 'production',
    'údržby': 'maintenance',
    'projektant': 'project designer',
    'projektový': 'project',
    'projektová': 'project',
    'odborný': 'professional',
    'odborná': 'professional',
    'vedoucí': 'manager',
    'stážista': 'intern',
    'projektov': 'project',
    'koordinátor/ka': 'coordinator',
  };
  
  // Replace common Czech words (word boundary matching)
  for (const [czechWord, englishWord] of Object.entries(wordReplacements)) {
    // Try whole word match first
    const wholeWordRegex = new RegExp(`\\b${czechWord}\\b`, 'gi');
    if (wholeWordRegex.test(translated)) {
      translated = translated.replace(wholeWordRegex, englishWord);
    } else {
      // Fallback to partial match
      const partialRegex = new RegExp(czechWord, 'gi');
      translated = translated.replace(partialRegex, englishWord);
    }
  }
  
  // Clean up multiple spaces and format
  translated = translated.replace(/\s+/g, ' ').trim();
  
  // Capitalize first letter of each word
  translated = translated.split(/[\s\/-]+/).map(word => {
    if (word.length === 0) return word;
    return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
  }).join(' ');
  
  // Handle special characters properly
  translated = translated.replace(/\s*\/\s*/g, '/');
  translated = translated.replace(/\s*-\s*/g, ' - ');
  
  // If translation resulted in mostly the same (no meaningful change), try simpler approach
  const originalCleaned = trimmed.toLowerCase().replace(/[^a-zčšžýáíéúůó]/g, '');
  const translatedCleaned = translated.toLowerCase().replace(/[^a-z]/g, '');
  
  if (originalCleaned === translatedCleaned && originalCleaned.length > 0) {
    // Try to extract key words and create a simpler translation
    if (trimmed.toLowerCase().includes('pedagog')) {
      return 'Educational Worker';
    }
    if (trimmed.toLowerCase().includes('koordin')) {
      return 'Coordinator';
    }
    if (trimmed.toLowerCase().includes('specialist')) {
      return 'Specialist';
    }
    if (trimmed.toLowerCase().includes('administr')) {
      return 'Administrator';
    }
    if (trimmed.toLowerCase().includes('dpp') || trimmed.toLowerCase().includes('dpč')) {
      return 'Part-time/Contract Worker';
    }
    if (trimmed.toLowerCase().includes('projekt')) {
      return 'Project Coordinator';
    }
    if (trimmed.toLowerCase().includes('vedoucí') || trimmed.toLowerCase().includes('vedouci')) {
      return 'Manager';
    }
    if (trimmed.toLowerCase().includes('stáž') || trimmed.toLowerCase().includes('staz')) {
      return 'Intern';
    }
  }
  
  // Return translated version (even if similar, it's better than Czech)
  return translated || trimmed;
}

/**
 * Translate multiple positions
 */
export function translatePositions(positions: string[]): string[] {
  return positions.map(translatePosition);
}

