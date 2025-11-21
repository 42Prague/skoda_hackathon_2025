import express from 'express';
import { prisma } from '../lib/prisma';
import { authenticate } from '../middleware/auth';

const router = express.Router();

// Get all open job positions
router.get('/', authenticate, async (req, res) => {
  try {
    const { status, department } = req.query;

    const where: any = {};
    
    // Filter by status (default to OPEN if not specified)
    if (status) {
      where.status = status;
    } else {
      where.status = 'OPEN'; // Default to open positions
    }

    if (department) {
      where.department = department;
    }

    const jobPositions = await prisma.jobPosition.findMany({
      where,
      include: {
        skills: {
          include: {
            skill: {
              select: {
                id: true,
                name: true,
                category: true,
              },
            },
          },
        },
        _count: {
          select: {
            applications: true,
          },
        },
      },
      orderBy: {
        postedAt: 'desc',
      },
    });

    res.json({ jobPositions });
  } catch (error) {
    console.error('Get job positions error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get job position by ID
router.get('/:id', authenticate, async (req, res) => {
  try {
    const { id } = req.params;

    const jobPosition = await prisma.jobPosition.findUnique({
      where: { id },
      include: {
        skills: {
          include: {
            skill: {
              select: {
                id: true,
                name: true,
                category: true,
                description: true,
              },
            },
          },
        },
        applications: {
          include: {
            user: {
              select: {
                id: true,
                firstName: true,
                lastName: true,
                employeeId: true,
              },
            },
          },
        },
      },
    });

    if (!jobPosition) {
      return res.status(404).json({ error: 'Job position not found' });
    }

    res.json({ jobPosition });
  } catch (error) {
    console.error('Get job position error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Create new job position (managers/admins only)
router.post('/', authenticate, async (req: any, res) => {
  try {
    // Only managers and admins can create job positions
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN') {
      return res.status(403).json({ error: 'Forbidden: Only managers can create job positions' });
    }

    const {
      title,
      description,
      department,
      location,
      employmentType,
      status = 'OPEN',
      requiredExperience,
      closingDate,
      skills, // Array of { skillId, requiredLevel, weight, isRequired }
    } = req.body;

    if (!title) {
      return res.status(400).json({ error: 'Title is required' });
    }

    // Create job position
    const jobPosition = await prisma.jobPosition.create({
      data: {
        title,
        description,
        department,
        location,
        employmentType,
        status: status as any,
        requiredExperience,
        closingDate: closingDate ? new Date(closingDate) : null,
        skills: skills && Array.isArray(skills) ? {
          create: skills.map((skill: any) => ({
            skillId: skill.skillId,
            requiredLevel: skill.requiredLevel || 70,
            weight: skill.weight || 1.0,
            isRequired: skill.isRequired !== undefined ? skill.isRequired : true,
          })),
        } : undefined,
      },
      include: {
        skills: {
          include: {
            skill: true,
          },
        },
      },
    });

    res.status(201).json({ jobPosition });
  } catch (error) {
    console.error('Create job position error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Update job position (managers/admins only)
router.put('/:id', authenticate, async (req: any, res) => {
  try {
    // Only managers and admins can update job positions
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN') {
      return res.status(403).json({ error: 'Forbidden: Only managers can update job positions' });
    }

    const { id } = req.params;
    const {
      title,
      description,
      department,
      location,
      employmentType,
      status,
      requiredExperience,
      closingDate,
    } = req.body;

    const jobPosition = await prisma.jobPosition.update({
      where: { id },
      data: {
        ...(title && { title }),
        ...(description !== undefined && { description }),
        ...(department !== undefined && { department }),
        ...(location !== undefined && { location }),
        ...(employmentType !== undefined && { employmentType }),
        ...(status && { status: status as any }),
        ...(requiredExperience !== undefined && { requiredExperience }),
        ...(closingDate !== undefined && { closingDate: closingDate ? new Date(closingDate) : null }),
      },
      include: {
        skills: {
          include: {
            skill: true,
          },
        },
      },
    });

    res.json({ jobPosition });
  } catch (error) {
    console.error('Update job position error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Delete job position (managers/admins only)
router.delete('/:id', authenticate, async (req: any, res) => {
  try {
    // Only managers and admins can delete job positions
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN') {
      return res.status(403).json({ error: 'Forbidden: Only managers can delete job positions' });
    }

    const { id } = req.params;

    await prisma.jobPosition.delete({
      where: { id },
    });

    res.json({ success: true, message: 'Job position deleted' });
  } catch (error) {
    console.error('Delete job position error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;

