import express from 'express';
import { prisma } from '../lib/prisma';
import { authenticate } from '../middleware/auth';

const router = express.Router();

// Get user assessments
router.get('/user/:userId', authenticate, async (req: any, res) => {
  try {
    const { userId } = req.params;

    // Users can only view their own assessments unless they're managers
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN' && req.userId !== userId) {
      return res.status(403).json({ error: 'Forbidden' });
    }

    const assessments = await prisma.assessment.findMany({
      where: { userId },
      orderBy: {
        createdAt: 'desc',
      },
    });

    res.json({ assessments });
  } catch (error) {
    console.error('Get assessments error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Create assessment
router.post('/', authenticate, async (req: any, res) => {
  try {
    const { moduleId, courseId, name, score, maxScore, aiFeedback } = req.body;
    const userId = req.userId;

    if (!name) {
      return res.status(400).json({ error: 'Assessment name is required' });
    }

    const assessment = await prisma.assessment.create({
      data: {
        userId,
        moduleId,
        courseId,
        name,
        score,
        maxScore,
        aiFeedback,
        status: score !== undefined ? 'COMPLETED' : 'PENDING',
        completedAt: score !== undefined ? new Date() : null,
      },
    });

    res.status(201).json({ assessment });
  } catch (error) {
    console.error('Create assessment error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Update assessment
router.put('/:id', authenticate, async (req: any, res) => {
  try {
    const { id } = req.params;
    const { score, maxScore, aiFeedback, status } = req.body;

    const assessment = await prisma.assessment.findUnique({
      where: { id },
    });

    if (!assessment) {
      return res.status(404).json({ error: 'Assessment not found' });
    }

    // Users can only update their own assessments
    if (assessment.userId !== req.userId && req.userRole !== 'ADMIN') {
      return res.status(403).json({ error: 'Forbidden' });
    }

    const updatedAssessment = await prisma.assessment.update({
      where: { id },
      data: {
        score,
        maxScore,
        aiFeedback,
        status: status || (score !== undefined ? 'COMPLETED' : 'PENDING'),
        completedAt: score !== undefined ? new Date() : null,
      },
    });

    res.json({ assessment: updatedAssessment });
  } catch (error) {
    console.error('Update assessment error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;

