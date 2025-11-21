/**
 * Check if employee login credentials work
 * Verifies employee exists and login details
 * 
 * Usage: npx tsx src/scripts/checkEmployeeLogin.ts
 */

import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  try {
    console.log('🔍 Checking employee login credentials...\n');

    // Check for employee with Employee ID 00004241
    const employeeById = await prisma.user.findFirst({
      where: {
        employeeId: '00004241',
      },
      select: {
        id: true,
        email: true,
        firstName: true,
        lastName: true,
        employeeId: true,
        role: true,
        department: true,
      },
    });

    if (employeeById) {
      console.log('✅ Employee found by Employee ID: 00004241');
      console.log('   Name:', `${employeeById.firstName} ${employeeById.lastName}`);
      console.log('   Email:', employeeById.email);
      console.log('   Role:', employeeById.role);
      console.log('   Department:', employeeById.department || 'N/A');
      console.log('');
    } else {
      console.log('❌ Employee with ID 00004241 NOT found');
      console.log('');
    }

    // Check for employee by email
    const employeeByEmail = await prisma.user.findFirst({
      where: {
        email: {
          contains: '4241',
        },
      },
      select: {
        id: true,
        email: true,
        firstName: true,
        lastName: true,
        employeeId: true,
        role: true,
      },
    });

    if (employeeByEmail) {
      console.log('✅ Employee found by email containing "4241":');
      console.log('   Name:', `${employeeByEmail.firstName} ${employeeByEmail.lastName}`);
      console.log('   Email:', employeeByEmail.email);
      console.log('   Employee ID:', employeeByEmail.employeeId);
      console.log('   Role:', employeeByEmail.role);
      console.log('');
    }

    // List first 5 employees
    console.log('📋 First 5 employees in database:');
    const employees = await prisma.user.findMany({
      where: {
        role: 'EMPLOYEE',
        employeeId: {
          not: null,
        },
      },
      select: {
        email: true,
        firstName: true,
        lastName: true,
        employeeId: true,
      },
      take: 5,
      orderBy: {
        createdAt: 'asc',
      },
    });

    if (employees.length === 0) {
      console.log('❌ No employees found in database!');
      console.log('💡 Run: npm run db:seed:real');
    } else {
      employees.forEach((emp, idx) => {
        console.log(`${idx + 1}. ${emp.firstName} ${emp.lastName}`);
        console.log(`   Email: ${emp.email}`);
        console.log(`   Employee ID: ${emp.employeeId}`);
        console.log('');
      });
    }

    // Test password verification
    if (employeeById) {
      const defaultPassword = 'password123';
      const user = await prisma.user.findUnique({
        where: { email: employeeById.email },
        select: { password: true },
      });

      if (user) {
        const isValid = await bcrypt.compare(defaultPassword, user.password);
        console.log('🔐 Password verification:');
        console.log('   Email:', employeeById.email);
        console.log('   Password "password123" valid:', isValid ? '✅ YES' : '❌ NO');
      }
    }

    // Login test summary
    console.log('\n📝 Login Test Summary:');
    if (employeeById) {
      console.log('✅ Employee exists with ID: 00004241');
      console.log(`✅ Email: ${employeeById.email}`);
      console.log('✅ Password: password123');
      console.log('\n💡 Try logging in with:');
      console.log(`   Email: ${employeeById.email}`);
      console.log('   Password: password123');
    } else {
      console.log('❌ Employee with ID 00004241 not found');
      console.log('\n💡 Run: npm run db:seed:real');
      console.log('   This will import employees from the CSV dataset');
    }

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

