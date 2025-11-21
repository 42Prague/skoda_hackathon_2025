import express from 'express';
import bcrypt from 'bcryptjs';
import { prisma } from '../lib/prisma';
import { generateToken } from '../middleware/auth';
import { authenticate } from '../middleware/auth';

const router = express.Router();

// Register
router.post('/register', async (req, res) => {
  try {
    const { email, password, firstName, lastName, employeeId, role = 'EMPLOYEE', department, managerId } = req.body;

    if (!email || !password || !firstName || !lastName) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    // Check if user exists
    const existingUser = await prisma.user.findUnique({
      where: { email },
    });

    if (existingUser) {
      return res.status(400).json({ error: 'User already exists' });
    }

    // Hash password
    const hashedPassword = await bcrypt.hash(password, 10);

    // Create user
    const user = await prisma.user.create({
      data: {
        email,
        password: hashedPassword,
        firstName,
        lastName,
        employeeId,
        role,
        department,
        managerId,
      },
      select: {
        id: true,
        email: true,
        firstName: true,
        lastName: true,
        role: true,
        department: true,
        employeeId: true,
      },
    });

    const token = generateToken(user.id, user.role);

    res.status(201).json({
      user,
      token,
    });
  } catch (error) {
    console.error('Register error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Login
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }

    // Find user
    const user = await prisma.user.findUnique({
      where: { email },
    });

    if (!user) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    // Check password
    const isValidPassword = await bcrypt.compare(password, user.password);

    if (!isValidPassword) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const token = generateToken(user.id, user.role);

    res.json({
      user: {
        id: user.id,
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        role: user.role,
        department: user.department,
        employeeId: user.employeeId,
      },
      token,
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get demo employees (for login page)
router.get('/demo-employees', async (req, res) => {
  try {
    // Get first employee from dataset (not manager)
    const firstEmployee = await prisma.user.findFirst({
      where: {
        role: 'EMPLOYEE',
        employeeId: {
          not: null,
          not: {
            startsWith: 'MGR',
          },
        },
      },
      orderBy: {
        createdAt: 'asc',
      },
      select: {
        email: true,
        firstName: true,
        lastName: true,
        employeeId: true,
        role: true,
      },
    });

    // Get first manager
    const firstManager = await prisma.user.findFirst({
      where: {
        role: 'MANAGER',
      },
      orderBy: {
        createdAt: 'asc',
      },
      select: {
        email: true,
        firstName: true,
        lastName: true,
        employeeId: true,
        role: true,
      },
    });

    res.json({
      employee: firstEmployee || null,
      manager: firstManager || null,
      password: 'password123', // All demo accounts use same password
    });
  } catch (error) {
    console.error('Get demo employees error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get current user
router.get('/me', authenticate, async (req: any, res) => {
  try {
    const user = await prisma.user.findUnique({
      where: { id: req.userId },
      select: {
        id: true,
        email: true,
        firstName: true,
        lastName: true,
        role: true,
        department: true,
        employeeId: true,
        managerId: true,
      },
    });

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json({ user });
  } catch (error) {
    console.error('Get user error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;
