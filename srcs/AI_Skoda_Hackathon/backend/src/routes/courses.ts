import express from 'express';
import { prisma } from '../lib/prisma';
import { authenticate } from '../middleware/auth';

const router = express.Router();

// Get all courses
router.get('/', authenticate, async (req, res) => {
  try {
    const courses = await prisma.course.findMany({
      include: {
        courseSkills: {
          include: {
            skill: true,
          },
        },
        _count: {
          select: {
            modules: true,
            enrollments: true,
          },
        },
      },
      orderBy: {
        createdAt: 'desc',
      },
    });

    res.json({ courses });
  } catch (error) {
    console.error('Get courses error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get course by ID
router.get('/:id', authenticate, async (req, res) => {
  try {
    const { id } = req.params;

    const course = await prisma.course.findUnique({
      where: { id },
      include: {
        modules: {
          orderBy: {
            order: 'asc',
          },
          include: {
            quizQuestions: {
              orderBy: {
                order: 'asc',
              },
            },
          },
        },
        courseSkills: {
          include: {
            skill: true,
          },
        },
      },
    });

    if (!course) {
      return res.status(404).json({ error: 'Course not found' });
    }

    res.json({ course });
  } catch (error) {
    console.error('Get course error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get user enrollments
router.get('/user/:userId/enrollments', authenticate, async (req: any, res) => {
  try {
    const { userId } = req.params;

    // Users can only view their own enrollments unless they're managers
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN' && req.userId !== userId) {
      return res.status(403).json({ error: 'Forbidden' });
    }

    const enrollments = await prisma.enrollment.findMany({
      where: { userId },
      include: {
        course: {
          include: {
            courseSkills: {
              include: {
                skill: true,
              },
            },
          },
        },
      },
      orderBy: {
        enrolledAt: 'desc',
      },
    });

    res.json({ enrollments });
  } catch (error) {
    console.error('Get enrollments error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Enroll in course
router.post('/:courseId/enroll', authenticate, async (req: any, res) => {
  try {
    const { courseId } = req.params;
    const userId = req.userId;

    // Check if course exists
    const course = await prisma.course.findUnique({
      where: { id: courseId },
    });

    if (!course) {
      return res.status(404).json({ error: 'Course not found' });
    }

    // Check if already enrolled
    const existingEnrollment = await prisma.enrollment.findUnique({
      where: {
        userId_courseId: {
          userId,
          courseId,
        },
      },
    });

    if (existingEnrollment) {
      return res.status(400).json({ error: 'Already enrolled in this course' });
    }

    // Create enrollment
    const enrollment = await prisma.enrollment.create({
      data: {
        userId,
        courseId,
        progress: 0,
      },
      include: {
        course: true,
      },
    });

    // Unlock first module
    const firstModule = await prisma.courseModule.findFirst({
      where: {
        courseId,
        order: 0,
      },
    });

    if (firstModule) {
      await prisma.moduleProgress.create({
        data: {
          userId,
          moduleId: firstModule.id,
          status: 'UNLOCKED',
          progress: 0,
        },
      });
    }

    res.status(201).json({ enrollment });
  } catch (error) {
    console.error('Enroll error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;

