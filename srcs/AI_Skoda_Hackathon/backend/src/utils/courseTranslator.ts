/**
 * Course Name Translator
 * Translates Czech course names to English
 */

const courseTranslations: Record<string, string> = {
  // Common course names (exact matches)
  'Etický kodex': 'Code of Ethics',
  'Etický kodex 2': 'Code of Ethics 2',
  'ISMS': 'Information Security Management System',
  'Outlook': 'Microsoft Outlook',
  'Excel': 'Microsoft Excel',
  'Word': 'Microsoft Word',
  'PowerPoint': 'Microsoft PowerPoint',
  'Office 365': 'Microsoft Office 365',
  'IT': 'Information Technology',
  'GDPR': 'General Data Protection Regulation',
  'Compliance': 'Compliance Training',
  'Leadership': 'Leadership Skills',
  'Communication': 'Communication Skills',
  'Time Management': 'Time Management',
  'Stress Management': 'Stress Management',
  'Agile': 'Agile Methodology',
  'Scrum': 'Scrum Framework',
  'Project Management': 'Project Management',
  'Teamwork': 'Teamwork Skills',
  'Mentoring': 'Mentoring',
  'Coaching': 'Coaching',
  'English': 'English Language',
  'German': 'German Language',
  'Jazykový test': 'Language Test',
  'Language': 'Language Skills',
  
  // Czech-specific terms
  'Digitální': 'Digital Skills',
  'Inovace': 'Innovation',
  'Transformace': 'Digital Transformation',
  'Budoucnost': 'Future Skills',
  'Změna': 'Change Management',
  'Robotika': 'Robotics',
  'Big Data': 'Big Data',
  'Cloud': 'Cloud Computing',
  'AI': 'Artificial Intelligence',
  'Umělá inteligence': 'Artificial Intelligence',
  'Virtual Reality': 'Virtual Reality',
  'Virtuální realita': 'Virtual Reality',
  'Connected Car': 'Connected Car',
  'Propojené vozidlo': 'Connected Car',
  'Internet': 'Internet Skills',
  'Počítač': 'Computer Skills',
  'Síť': 'Networking',
  'Bezpečnost': 'Security',
  'Kybernetická bezpečnost': 'Cybersecurity',
  'Kvalita': 'Quality Management',
  'Proces': 'Process Improvement',
  'Řešení problémů': 'Problem Solving',
  'Adaptabilita': 'Adaptability',
};

/**
 * Translate Czech course name to English
 */
export function translateCourseName(czechCourseName: string): string {
  if (!czechCourseName || czechCourseName.trim() === '') {
    return 'Unknown Course';
  }

  const trimmed = czechCourseName.trim();

  // Exact match first (case-insensitive)
  const lowerTrimmed = trimmed.toLowerCase();
  for (const [czech, english] of Object.entries(courseTranslations)) {
    if (czech.toLowerCase() === lowerTrimmed) {
      return english;
    }
  }

  // Try partial matches (case-insensitive)
  for (const [czech, english] of Object.entries(courseTranslations)) {
    const czechLower = czech.toLowerCase();
    if (lowerTrimmed.includes(czechLower) || czechLower.includes(lowerTrimmed)) {
      // If the Czech term is found in the course name, replace it
      const regex = new RegExp(czechLower, 'gi');
      if (regex.test(trimmed)) {
        let translated = trimmed.replace(regex, english);
        // Clean up the result
        translated = translated.replace(/\s+/g, ' ').trim();
        return translated || english;
      }
    }
  }

  // Try word-by-word translation for common Czech terms
  let translated = trimmed;
  
  const wordReplacements: Record<string, string> = {
    'etický': 'ethics',
    'kodex': 'code',
    'digitální': 'digital',
    'inovace': 'innovation',
    'transformace': 'transformation',
    'budoucnost': 'future',
    'změna': 'change',
    'robotika': 'robotics',
    'big data': 'big data',
    'cloud': 'cloud',
    'ai': 'ai',
    'umělá': 'artificial',
    'inteligence': 'intelligence',
    'virtual': 'virtual',
    'realita': 'reality',
    'virtuální': 'virtual',
    'propojené': 'connected',
    'vozidlo': 'car',
    'internet': 'internet',
    'počítač': 'computer',
    'síť': 'network',
    'bezpečnost': 'security',
    'kybernetická': 'cyber',
    'kvalita': 'quality',
    'proces': 'process',
    'řešení': 'solving',
    'problémů': 'problems',
    'adaptabilita': 'adaptability',
    'komunikace': 'communication',
    'týmová': 'team',
    'práce': 'work',
    'vedení': 'leadership',
    'management': 'management',
    'čas': 'time',
    'stres': 'stress',
    'agilní': 'agile',
    'projekt': 'project',
    'školení': 'training',
    'kurz': 'course',
    'vzdělávání': 'education',
    'dovednosti': 'skills',
    'znalosti': 'knowledge',
  };

  // Replace common Czech words (word boundary matching)
  for (const [czechWord, englishWord] of Object.entries(wordReplacements)) {
    const wordRegex = new RegExp(`\\b${czechWord}\\b`, 'gi');
    if (wordRegex.test(translated)) {
      translated = translated.replace(wordRegex, englishWord);
    }
  }

  // Clean up and format
  translated = translated.replace(/\s+/g, ' ').trim();
  
  // Capitalize first letter of each word
  translated = translated.split(/\s+/).map(word => {
    if (word.length === 0) return word;
    // Handle special cases (keep acronyms uppercase)
    if (word.match(/^[A-Z]{2,}$/)) return word;
    return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
  }).join(' ');

  // If translation resulted in mostly the same, return original but cleaned
  const originalCleaned = lowerTrimmed.replace(/[^a-zčšžýáíéúůó]/g, '');
  const translatedCleaned = translated.toLowerCase().replace(/[^a-z]/g, '');
  
  if (originalCleaned === translatedCleaned && originalCleaned.length > 0) {
    // Try simpler approach - just capitalize and clean
    return trimmed
      .split(/\s+/)
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  }

  return translated || trimmed;
}

/**
 * Translate multiple course names
 */
export function translateCourseNames(courseNames: string[]): string[] {
  return courseNames.map(translateCourseName);
}

