import express from 'express';
import { prisma } from '../lib/prisma';
import { authenticate } from '../middleware/auth';
import { azureAIService } from '../services/azureAI';

const router = express.Router();

// Get all employee skill risks (for managers/admins or for feeding AI models)
router.get('/', authenticate, async (req: any, res) => {
  try {
    const { department, riskLabel, employeeId } = req.query;

    const where: any = {};
    if (department) where.department = department;
    if (riskLabel) where.riskLabel = riskLabel;
    if (employeeId) where.employeeId = employeeId;

    // Only managers and admins can see all records
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN') {
      // Employees can only see their own records - get their employeeId
      const user = await prisma.user.findUnique({
        where: { id: req.userId },
        select: { employeeId: true },
      });
      if (user?.employeeId) {
        where.employeeId = user.employeeId;
      } else {
        where.employeeId = 'NONEXISTENT'; // Return no results if no employeeId
      }
    }

    const risks = await prisma.employeeSkillRisk.findMany({
      where,
      include: {
        user: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            employeeId: true,
            email: true,
            department: true,
          },
        },
        skill: {
          select: {
            id: true,
            name: true,
            category: true,
          },
        },
        assignmentAIs: {
          select: {
            id: true,
            assignmentType: true,
            riskScore: true,
            riskLabel: true,
            createdAt: true,
          },
        },
      },
      orderBy: [
        { riskScore: 'desc' },
        { predictedAt: 'desc' },
      ],
    });

    res.json({ risks, count: risks.length });
  } catch (error) {
    console.error('Get employee skill risks error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get employee skill risks by employee ID
router.get('/employee/:employeeId', authenticate, async (req: any, res) => {
  try {
    const { employeeId } = req.params;

    // Users can only view their own risks unless they're managers
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN') {
      // Check if the requested employeeId matches the logged-in user's employeeId
      const user = await prisma.user.findUnique({
        where: { id: req.userId },
        select: { employeeId: true },
      });
      if (user?.employeeId !== employeeId) {
        return res.status(403).json({ error: 'Forbidden' });
      }
    }

    const risks = await prisma.employeeSkillRisk.findMany({
      where: { employeeId },
      include: {
        user: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            employeeId: true,
            department: true,
          },
        },
        skill: {
          select: {
            id: true,
            name: true,
            category: true,
            marketRelevance: true,
          },
        },
        assignmentAIs: {
          select: {
            id: true,
            assignmentType: true,
            riskScore: true,
            riskLabel: true,
            avgFutureDemand: true,
            automationExposure: true,
            createdAt: true,
          },
        },
      },
      orderBy: {
        riskScore: 'desc',
      },
    });

    res.json({ risks });
  } catch (error) {
    console.error('Get employee skill risks error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Create or update employee skill risk
router.post('/', authenticate, async (req: any, res) => {
  try {
    const {
      employeeId,
      userId,
      department,
      skillName,
      skillId,
      avgFutureDemand,
      automationExposure,
      riskScore,
      riskLabel,
    } = req.body;

    if (!employeeId || avgFutureDemand === undefined || automationExposure === undefined) {
      return res.status(400).json({ error: 'employeeId, avgFutureDemand, and automationExposure are required' });
    }

    // Only managers and admins can create/update risk records
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN') {
      return res.status(403).json({ error: 'Forbidden: Only managers can create risk records' });
    }

    // Calculate risk score if not provided
    const calculatedRiskScore = riskScore !== undefined
      ? riskScore
      : (100 - avgFutureDemand) * 0.4 + automationExposure * 0.6;

    // Determine risk label if not provided
    let calculatedRiskLabel = riskLabel || 'LOW';
    if (calculatedRiskScore >= 70) calculatedRiskLabel = 'HIGH';
    else if (calculatedRiskScore >= 40) calculatedRiskLabel = 'MEDIUM';
    else calculatedRiskLabel = 'LOW';

    const risk = await prisma.employeeSkillRisk.create({
      data: {
        employeeId,
        userId,
        department,
        skillName,
        skillId,
        avgFutureDemand,
        automationExposure,
        riskScore: calculatedRiskScore,
        riskLabel: calculatedRiskLabel as any,
      },
      include: {
        user: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            employeeId: true,
            department: true,
          },
        },
        skill: true,
      },
    });

    res.status(201).json({ risk });
  } catch (error) {
    console.error('Create employee skill risk error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get statistics for AI model feeding
router.get('/stats/ai-feeding', authenticate, async (req: any, res) => {
  try {
    // Only managers and admins can see statistics
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN') {
      return res.status(403).json({ error: 'Forbidden' });
    }

    const [
      totalRecords,
      byRiskLabel,
      byDepartment,
      avgMetrics,
    ] = await Promise.all([
      prisma.employeeSkillRisk.count(),
      prisma.employeeSkillRisk.groupBy({
        by: ['riskLabel'],
        _count: true,
      }),
      prisma.employeeSkillRisk.groupBy({
        by: ['department'],
        _count: true,
        _avg: {
          avgFutureDemand: true,
          automationExposure: true,
          riskScore: true,
        },
      }),
      prisma.employeeSkillRisk.aggregate({
        _avg: {
          avgFutureDemand: true,
          automationExposure: true,
          riskScore: true,
        },
      }),
    ]);

    res.json({
      totalRecords,
      byRiskLabel,
      byDepartment,
      avgMetrics,
    });
  } catch (error) {
    console.error('Get statistics error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Generate AI-powered insights for a specific skill risk
router.post('/generate-insights/:riskId', authenticate, async (req: any, res) => {
  try {
    const { riskId } = req.params;

    // Get the risk record with all related data
    const risk = await prisma.employeeSkillRisk.findUnique({
      where: { id: riskId },
      include: {
        user: {
          select: {
            firstName: true,
            lastName: true,
            employeeId: true,
            department: true,
          },
        },
        skill: {
          select: {
            name: true,
            category: true,
          },
        },
      },
    });

    if (!risk) {
      return res.status(404).json({ error: 'Risk record not found' });
    }

    // Check access permissions
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN') {
      const user = await prisma.user.findUnique({
        where: { id: req.userId },
        select: { employeeId: true },
      });
      if (user?.employeeId !== risk.employeeId) {
        return res.status(403).json({ error: 'Forbidden' });
      }
    }

    // Get user's current skill level if available
    const userSkill = await prisma.userSkill.findFirst({
      where: {
        userId: risk.userId || undefined,
        skillId: risk.skillId || undefined,
      },
    });

    // Generate AI insights
    const insights = await azureAIService.generateSkillRiskInsights({
      employeeName: risk.user ? `${risk.user.firstName} ${risk.user.lastName}` : 'Unknown',
      skillName: risk.skill?.name || 'Unknown',
      skillCategory: risk.skill?.category || 'Unknown',
      currentLevel: userSkill?.level?.toString(),
      riskScore: risk.riskScore || 0,
      riskLabel: risk.riskLabel || 'UNKNOWN',
      avgFutureDemand: risk.avgFutureDemand || 0,
      automationExposure: risk.automationExposure || 0,
      department: risk.user?.department || risk.department || 'Unknown',
    });

    // Optionally save insights to the risk record
    await prisma.employeeSkillRisk.update({
      where: { id: riskId },
      data: {
        aiInsights: JSON.stringify(insights),
        insightsGeneratedAt: new Date(),
      },
    });

    res.json({
      success: true,
      riskId,
      insights,
    });
  } catch (error) {
    console.error('Generate insights error:', error);
    res.status(500).json({ error: 'Failed to generate insights' });
  }
});

// Bulk generate AI insights for high-risk skills
router.post('/bulk-generate-insights', authenticate, async (req: any, res) => {
  try {
    // Only managers and admins can bulk generate insights
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN') {
      return res.status(403).json({ error: 'Forbidden' });
    }

    const { minRiskScore = 40, department } = req.body;

    const where: any = {
      riskScore: { gte: minRiskScore },
    };
    if (department) {
      where.department = department;
    }

    const risks = await prisma.employeeSkillRisk.findMany({
      where,
      include: {
        user: {
          select: {
            firstName: true,
            lastName: true,
            employeeId: true,
            department: true,
            id: true,
          },
        },
        skill: {
          select: {
            name: true,
            category: true,
            id: true,
          },
        },
      },
      take: 50, // Limit to 50 records to avoid timeout
    });

    const results = [];
    const errors = [];

    for (const risk of risks) {
      try {
        // Get user's current skill level if available
        const userSkill = await prisma.userSkill.findFirst({
          where: {
            userId: risk.user?.id,
            skillId: risk.skill?.id,
          },
        });

        const insights = await azureAIService.generateSkillRiskInsights({
          employeeName: risk.user ? `${risk.user.firstName} ${risk.user.lastName}` : 'Unknown',
          skillName: risk.skill?.name || 'Unknown',
          skillCategory: risk.skill?.category || 'Unknown',
          currentLevel: userSkill?.level?.toString(),
          riskScore: risk.riskScore || 0,
          riskLabel: risk.riskLabel || 'UNKNOWN',
          avgFutureDemand: risk.avgFutureDemand || 0,
          automationExposure: risk.automationExposure || 0,
          department: risk.user?.department || risk.department || 'Unknown',
        });

        await prisma.employeeSkillRisk.update({
          where: { id: risk.id },
          data: {
            aiInsights: JSON.stringify(insights),
            insightsGeneratedAt: new Date(),
          },
        });

        results.push({
          riskId: risk.id,
          employeeId: risk.employeeId,
          skillName: risk.skill?.name || 'Unknown',
          success: true,
        });
      } catch (error) {
        console.error(`Error processing risk ${risk.id}:`, error);
        errors.push({
          riskId: risk.id,
          employeeId: risk.employeeId,
          error: 'Failed to generate insights',
        });
      }
    }

    res.json({
      success: true,
      processed: results.length,
      errorCount: errors.length,
      results,
      errors,
    });
  } catch (error) {
    console.error('Bulk generate insights error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get AI insights for a specific employee's risks
router.get('/insights/employee/:employeeId', authenticate, async (req: any, res) => {
  try {
    const { employeeId } = req.params;

    // Check access permissions
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN') {
      const user = await prisma.user.findUnique({
        where: { id: req.userId },
        select: { employeeId: true },
      });
      if (user?.employeeId !== employeeId) {
        return res.status(403).json({ error: 'Forbidden' });
      }
    }

    const risks = await prisma.employeeSkillRisk.findMany({
      where: {
        employeeId,
        aiInsights: { not: null },
      },
      include: {
        skill: {
          select: {
            name: true,
            category: true,
          },
        },
      },
      orderBy: {
        riskScore: 'desc',
      },
    });

    const insightsData = risks.map((risk: any) => ({
      riskId: risk.id,
      skillName: risk.skill.name,
      skillCategory: risk.skill.category,
      riskScore: risk.riskScore,
      riskLabel: risk.riskLabel,
      insights: risk.aiInsights ? JSON.parse(risk.aiInsights) : null,
      insightsGeneratedAt: risk.insightsGeneratedAt,
    }));

    res.json({
      employeeId,
      insights: insightsData,
      count: insightsData.length,
    });
  } catch (error) {
    console.error('Get insights error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;

