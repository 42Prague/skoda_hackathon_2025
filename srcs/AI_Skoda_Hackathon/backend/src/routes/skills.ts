import express from 'express';
import { prisma } from '../lib/prisma';
import { authenticate } from '../middleware/auth';

const router = express.Router();

// Get all skills
router.get('/', authenticate, async (req, res) => {
  try {
    const { category } = req.query;

    const where = category ? { category: category as string } : {};

    const skills = await prisma.skill.findMany({
      where,
      orderBy: {
        name: 'asc',
      },
    });

    res.json({ skills });
  } catch (error) {
    console.error('Get skills error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get skill by ID
router.get('/:id', authenticate, async (req, res) => {
  try {
    const { id } = req.params;

    const skill = await prisma.skill.findUnique({
      where: { id },
    });

    if (!skill) {
      return res.status(404).json({ error: 'Skill not found' });
    }

    res.json({ skill });
  } catch (error) {
    console.error('Get skill error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get user skills
router.get('/user/:userId', authenticate, async (req: any, res) => {
  try {
    const { userId } = req.params;

    // Users can only view their own skills unless they're managers
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN' && req.userId !== userId) {
      return res.status(403).json({ error: 'Forbidden' });
    }

    const userSkills = await prisma.userSkill.findMany({
      where: { userId },
      include: {
        skill: true,
      },
      orderBy: {
        assessedAt: 'desc',
      },
    });

    res.json({ userSkills });
  } catch (error) {
    console.error('Get user skills error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Create or update user skill
router.post('/user/:userId', authenticate, async (req: any, res) => {
  try {
    const { userId } = req.params;
    const { skillId, level, notes } = req.body;

    if (!skillId || level === undefined) {
      return res.status(400).json({ error: 'skillId and level are required' });
    }

    // Users can only update their own skills unless they're managers
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN' && req.userId !== userId) {
      return res.status(403).json({ error: 'Forbidden' });
    }

    const userSkill = await prisma.userSkill.upsert({
      where: {
        userId_skillId: {
          userId,
          skillId,
        },
      },
      update: {
        level,
        notes,
        assessedAt: new Date(),
        assessedBy: req.userId,
      },
      create: {
        userId,
        skillId,
        level,
        notes,
        assessedBy: req.userId,
      },
      include: {
        skill: true,
      },
    });

    res.json({ userSkill });
  } catch (error) {
    console.error('Create/update user skill error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;

