/**
 * Calculate demo employee email from personal number
 * This generates the same email format as seedRealData.ts
 */

function generateEmployeeEmailFromId(personalNumber: string): {
  firstName: string;
  lastName: string;
  email: string;
} {
  const firstNames = [
    'Jan', 'Petr', 'Pavel', 'Martin', 'Tomáš', 'Jakub', 'Lukáš', 'David', 'Michal', 'Ondřej',
    'Anna', 'Petra', 'Jana', 'Lucie', 'Kateřina', 'Lenka', 'Markéta', 'Tereza', 'Veronika', 'Hana'
  ];
  const lastNames = [
    'Novák', 'Svoboda', 'Novotný', 'Dvořák', 'Černý', 'Procházka', 'Kučera', 'Veselý', 'Horák', 'Němec',
    'Pokorný', 'Pospíšil', 'Král', 'Jelínek', 'Růžička', 'Beneš', 'Fiala', 'Sedláček', 'Doležal', 'Zeman'
  ];

  // Use personal number as seed for consistent name generation
  const seed = personalNumber.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const firstName = firstNames[seed % firstNames.length];
  const lastName = lastNames[(seed * 7) % lastNames.length];
  
  // Add personal number suffix to ensure unique emails
  const emailSuffix = personalNumber.slice(-4);
  
  // Normalize Czech characters for email (remove diacritics)
  const normalize = (str: string) => str
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[č]/g, 'c')
    .replace(/[ď]/g, 'd')
    .replace(/[ě]/g, 'e')
    .replace(/[ň]/g, 'n')
    .replace(/[ř]/g, 'r')
    .replace(/[š]/g, 's')
    .replace(/[ť]/g, 't')
    .replace(/[ů]/g, 'u')
    .replace(/[ž]/g, 'z');
  
  const email = `${normalize(firstName)}.${normalize(lastName)}.${emailSuffix}@skoda.cz`;

  return { firstName, lastName, email };
}

// Common employee IDs from the dataset
const demoEmployeeIds = [
  '00016687', // Target employee mentioned in dashboard.ts
  '00000001', // First employee
  '00000002', // Second employee
];

console.log('📋 Demo Employee Emails (from dataset):\n');

for (const empId of demoEmployeeIds) {
  const { firstName, lastName, email } = generateEmployeeEmailFromId(empId);
  console.log(`Employee ID: ${empId}`);
  console.log(`  Name: ${firstName} ${lastName}`);
  console.log(`  Email: ${email}`);
  console.log(`  Password: password123`);
  console.log('');
}

// Use the target employee
const targetEmployee = generateEmployeeEmailFromId('00016687');
console.log('✅ Recommended demo employee:');
console.log(`   Email: ${targetEmployee.email}`);
console.log(`   Password: password123`);
console.log(`   Employee ID: 00016687`);

export { generateEmployeeEmailFromId, demoEmployeeIds };

