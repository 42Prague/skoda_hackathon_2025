import express from 'express';
import { prisma } from '../lib/prisma';
import { authenticate, authorize } from '../middleware/auth';

const router = express.Router();

// Get all users (managers only)
router.get('/', authenticate, authorize('MANAGER', 'ADMIN'), async (req, res) => {
  try {
    const users = await prisma.user.findMany({
      select: {
        id: true,
        email: true,
        firstName: true,
        lastName: true,
        employeeId: true,
        role: true,
        department: true,
        managerId: true,
        createdAt: true,
      },
      orderBy: {
        createdAt: 'desc',
      },
    });

    res.json({ users });
  } catch (error) {
    console.error('Get users error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get user by ID
router.get('/:id', authenticate, async (req: any, res) => {
  try {
    const { id } = req.params;

    // Users can only view their own profile unless they're managers
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN' && req.userId !== id) {
      return res.status(403).json({ error: 'Forbidden' });
    }

    const user = await prisma.user.findUnique({
      where: { id },
      select: {
        id: true,
        email: true,
        firstName: true,
        lastName: true,
        employeeId: true,
        role: true,
        department: true,
        managerId: true,
        createdAt: true,
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

// Get team members (for managers)
router.get('/team/:managerId', authenticate, async (req: any, res) => {
  try {
    const { managerId } = req.params;

    // Only managers can view their team or view own team
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN' && req.userId !== managerId) {
      return res.status(403).json({ error: 'Forbidden' });
    }

    const team = await prisma.user.findMany({
      where: { managerId },
      select: {
        id: true,
        email: true,
        firstName: true,
        lastName: true,
        employeeId: true,
        role: true,
        department: true,
        createdAt: true,
      },
      orderBy: {
        createdAt: 'desc',
      },
    });

    res.json({ team });
  } catch (error) {
    console.error('Get team error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;

