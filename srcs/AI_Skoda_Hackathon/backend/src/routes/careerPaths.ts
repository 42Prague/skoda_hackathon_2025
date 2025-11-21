import express from 'express';
import { prisma } from '../lib/prisma';
import { authenticate } from '../middleware/auth';

const router = express.Router();

// Get all career paths
router.get('/', authenticate, async (req, res) => {
  try {
    const careerPaths = await prisma.careerPath.findMany({
      include: {
        skills: {
          include: {
            skill: true,
          },
        },
      },
      orderBy: {
        createdAt: 'desc',
      },
    });

    res.json({ careerPaths });
  } catch (error) {
    console.error('Get career paths error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get career path by ID
router.get('/:id', authenticate, async (req, res) => {
  try {
    const { id } = req.params;

    const careerPath = await prisma.careerPath.findUnique({
      where: { id },
      include: {
        skills: {
          include: {
            skill: true,
          },
        },
      },
    });

    if (!careerPath) {
      return res.status(404).json({ error: 'Career path not found' });
    }

    res.json({ careerPath });
  } catch (error) {
    console.error('Get career path error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;

