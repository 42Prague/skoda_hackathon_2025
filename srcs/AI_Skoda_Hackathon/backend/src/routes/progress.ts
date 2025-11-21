import express from 'express';
import { prisma } from '../lib/prisma';
import { authenticate } from '../middleware/auth';

const router = express.Router();

// Get user progress for a course
router.get('/user/:userId/course/:courseId', authenticate, async (req: any, res) => {
  try {
    const { userId, courseId } = req.params;

    // Users can only view their own progress unless they're managers
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN' && req.userId !== userId) {
      return res.status(403).json({ error: 'Forbidden' });
    }

    const enrollment = await prisma.enrollment.findUnique({
      where: {
        userId_courseId: {
          userId,
          courseId,
        },
      },
    });

    if (!enrollment) {
      return res.status(404).json({ error: 'Not enrolled in this course' });
    }

    const moduleProgress = await prisma.moduleProgress.findMany({
      where: {
        userId,
        module: {
          courseId,
        },
      },
      include: {
        module: {
          select: {
            id: true,
            title: true,
            type: true,
            order: true,
          },
        },
      },
      orderBy: {
        module: {
          order: 'asc',
        },
      },
    });

    res.json({
      enrollment,
      moduleProgress,
    });
  } catch (error) {
    console.error('Get progress error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Update module progress
router.put('/user/:userId/module/:moduleId', authenticate, async (req: any, res) => {
  try {
    const { userId, moduleId } = req.params;
    const { status, progress, timeSpent } = req.body;

    // Users can only update their own progress
    if (req.userId !== userId) {
      return res.status(403).json({ error: 'Forbidden' });
    }

    const moduleProgress = await prisma.moduleProgress.upsert({
      where: {
        userId_moduleId: {
          userId,
          moduleId,
        },
      },
      update: {
        status: status || undefined,
        progress: progress !== undefined ? progress : undefined,
        timeSpent: timeSpent !== undefined ? timeSpent : undefined,
        lastAccessed: new Date(),
        completedAt: status === 'COMPLETED' ? new Date() : undefined,
      },
      create: {
        userId,
        moduleId,
        status: status || 'UNLOCKED',
        progress: progress || 0,
        timeSpent: timeSpent || 0,
        lastAccessed: new Date(),
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

    // Update course enrollment progress if module is completed
    if (status === 'COMPLETED') {
      const courseId = moduleProgress.module.course.id;
      const totalModules = await prisma.courseModule.count({
        where: { courseId },
      });

      const completedModules = await prisma.moduleProgress.count({
        where: {
          userId,
          status: 'COMPLETED',
          module: {
            courseId,
          },
        },
      });

      const courseProgress = (completedModules / totalModules) * 100;

      await prisma.enrollment.update({
        where: {
          userId_courseId: {
            userId,
            courseId,
          },
        },
        data: {
          progress: courseProgress,
          completedAt: completedModules === totalModules ? new Date() : null,
        },
      });
    }

    res.json({ moduleProgress });
  } catch (error) {
    console.error('Update progress error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;

