import express from 'express';
import { prisma } from '../lib/prisma';
import { authenticate } from '../middleware/auth';

const router = express.Router();

// Get user assignments
router.get('/user/:userId', authenticate, async (req: any, res) => {
  try {
    const { userId } = req.params;

    // Users can only view their own assignments unless they're managers
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN' && req.userId !== userId) {
      return res.status(403).json({ error: 'Forbidden' });
    }

    const assignments = await prisma.assignment.findMany({
      where: { userId },
      include: {
        module: {
          include: {
            course: {
              select: {
                id: true,
                title: true,
              },
            },
          },
        },
      },
      orderBy: {
        createdAt: 'desc',
      },
    });

    res.json({ assignments });
  } catch (error) {
    console.error('Get assignments error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get assignment by ID
router.get('/:id', authenticate, async (req: any, res) => {
  try {
    const { id } = req.params;

    const assignment = await prisma.assignment.findUnique({
      where: { id },
      include: {
        module: {
          include: {
            course: {
              select: {
                id: true,
                title: true,
              },
            },
          },
        },
        user: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            email: true,
          },
        },
      },
    });

    if (!assignment) {
      return res.status(404).json({ error: 'Assignment not found' });
    }

    // Users can only view their own assignments unless they're managers
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN' && assignment.userId !== req.userId) {
      return res.status(403).json({ error: 'Forbidden' });
    }

    res.json({ assignment });
  } catch (error) {
    console.error('Get assignment error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Create or update assignment
router.post('/', authenticate, async (req: any, res) => {
  try {
    const { moduleId, title, submission, files, aiFeedback } = req.body;
    const userId = req.userId;

    if (!moduleId || !title) {
      return res.status(400).json({ error: 'moduleId and title are required' });
    }

    // Find existing assignment
    const existingAssignment = await prisma.assignment.findFirst({
      where: {
        userId,
        moduleId,
      },
    });

    const assignment = existingAssignment
      ? await prisma.assignment.update({
          where: { id: existingAssignment.id },
          data: {
            title,
            submission,
            files,
            aiFeedback,
            submittedAt: submission ? new Date() : null,
          },
          include: {
            module: {
              include: {
                course: {
                  select: {
                    id: true,
                    title: true,
                  },
                },
              },
            },
          },
        })
      : await prisma.assignment.create({
          data: {
            userId,
            moduleId,
            title,
            submission,
            files,
            aiFeedback,
            submittedAt: submission ? new Date() : null,
          },
          include: {
            module: {
              include: {
                course: {
                  select: {
                    id: true,
                    title: true,
                  },
                },
              },
            },
          },
        });

    res.status(201).json({ assignment });
  } catch (error) {
    console.error('Create assignment error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Grade assignment (for managers/admins)
router.put('/:id/grade', authenticate, async (req: any, res) => {
  try {
    const { id } = req.params;
    const { grade } = req.body;

    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN') {
      return res.status(403).json({ error: 'Forbidden: Only managers can grade assignments' });
    }

    const assignment = await prisma.assignment.findUnique({
      where: { id },
    });

    if (!assignment) {
      return res.status(404).json({ error: 'Assignment not found' });
    }

    const updatedAssignment = await prisma.assignment.update({
      where: { id },
      data: {
        grade,
        gradedAt: new Date(),
      },
    });

    res.json({ assignment: updatedAssignment });
  } catch (error) {
    console.error('Grade assignment error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;

