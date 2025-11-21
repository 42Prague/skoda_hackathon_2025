import express from 'express';
import { prisma } from '../lib/prisma';
import { authenticate } from '../middleware/auth';
import { azureAIService } from '../services/azureAI';

const router = express.Router();

// Get all assignment AI records
router.get('/', authenticate, async (req: any, res) => {
  try {
    const { department, riskLabel, employeeId, skillId } = req.query;

    const where: any = {};
    if (department) where.department = department;
    if (riskLabel) where.riskLabel = riskLabel;
    if (employeeId) where.employeeId = employeeId;
    if (skillId) where.skillId = skillId;

    // Only managers and admins can see all records
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN') {
      // Employees can only see their own records
      const user = await prisma.user.findUnique({
        where: { id: req.userId },
        select: { employeeId: true },
      });
      if (user?.employeeId) {
        where.employeeId = user.employeeId;
      }
    }

    const assignments = await prisma.assignmentAI.findMany({
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
        employeeSkillRisk: {
          select: {
            id: true,
            avgFutureDemand: true,
            automationExposure: true,
            riskScore: true,
            riskLabel: true,
            predictedAt: true,
          },
        },
      },
      orderBy: [
        { riskScore: 'desc' },
        { createdAt: 'desc' },
      ],
    });

    res.json({ assignments, count: assignments.length });
  } catch (error) {
    console.error('Get assignment AI records error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get assignment AI records by employee ID
router.get('/employee/:employeeId', authenticate, async (req: any, res) => {
  try {
    const { employeeId } = req.params;

    // Users can only view their own records unless they're managers
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN') {
      const user = await prisma.user.findUnique({
        where: { id: req.userId },
        select: { employeeId: true },
      });
      if (user?.employeeId !== employeeId) {
        return res.status(403).json({ error: 'Forbidden' });
      }
    }

    const assignments = await prisma.assignmentAI.findMany({
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
        skill: true,
        employeeSkillRisk: {
          select: {
            id: true,
            avgFutureDemand: true,
            automationExposure: true,
            riskScore: true,
            riskLabel: true,
            predictedAt: true,
          },
        },
      },
      orderBy: {
        riskScore: 'desc',
      },
    });

    res.json({ assignments });
  } catch (error) {
    console.error('Get assignment AI records error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Create or update assignment AI record
router.post('/', authenticate, async (req: any, res) => {
  try {
    const {
      employeeId,
      userId,
      department,
      skillName,
      skillId,
      employeeSkillRiskId,
      avgFutureDemand,
      automationExposure,
      riskScore,
      riskLabel,
      assignmentType,
    } = req.body;

    if (!employeeId) {
      return res.status(400).json({ error: 'employeeId is required' });
    }

    // Only managers and admins can create/update records
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN') {
      return res.status(403).json({ error: 'Forbidden: Only managers can create assignment records' });
    }

    // Calculate risk score if not provided
    let calculatedRiskScore = riskScore;
    let calculatedRiskLabel = riskLabel || 'LOW';

    if (avgFutureDemand !== undefined && automationExposure !== undefined) {
      calculatedRiskScore = (100 - (avgFutureDemand || 0)) * 0.4 + (automationExposure || 0) * 0.6;

      if (calculatedRiskScore >= 70) calculatedRiskLabel = 'HIGH';
      else if (calculatedRiskScore >= 40) calculatedRiskLabel = 'MEDIUM';
      else calculatedRiskLabel = 'LOW';
    }

    const assignment = await prisma.assignmentAI.create({
      data: {
        employeeId,
        userId,
        department,
        skillName,
        skillId,
        employeeSkillRiskId,
        avgFutureDemand,
        automationExposure,
        riskScore: calculatedRiskScore,
        riskLabel: calculatedRiskLabel as any,
        assignmentType,
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
        employeeSkillRisk: {
          select: {
            id: true,
            avgFutureDemand: true,
            automationExposure: true,
            riskScore: true,
            riskLabel: true,
          },
        },
      },
    });

    res.status(201).json({ assignment });
  } catch (error) {
    console.error('Create assignment AI record error:', error);
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
      prisma.assignmentAI.count(),
      prisma.assignmentAI.groupBy({
        by: ['riskLabel'],
        _count: true,
      }),
      prisma.assignmentAI.groupBy({
        by: ['department'],
        _count: true,
        _avg: {
          avgFutureDemand: true,
          automationExposure: true,
          riskScore: true,
        },
      }),
      prisma.assignmentAI.aggregate({
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

// Generate AI-powered feedback for an assignment submission
router.post('/generate-feedback', authenticate, async (req: any, res) => {
  try {
    const {
      assignmentId,
      submissionContent,
      skillName,
      assignmentTitle,
      assignmentDescription,
    } = req.body;

    if (!submissionContent || !skillName) {
      return res.status(400).json({ error: 'submissionContent and skillName are required' });
    }

    // Get user information
    const user = await prisma.user.findUnique({
      where: { id: req.userId },
      select: {
        firstName: true,
        lastName: true,
        employeeId: true,
      },
    });

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    const employeeName = `${user.firstName} ${user.lastName}`;

    // Get skill information if assignmentId is provided
    let currentSkillLevel: string | undefined;
    // Simplified: skill level tracking would require proper course-skill-assignment linking
    currentSkillLevel = undefined;

    // Generate AI feedback
    const feedback = await azureAIService.generateAssignmentFeedback({
      skillName,
      assignmentTitle: assignmentTitle || 'Assignment Submission',
      assignmentDescription: assignmentDescription || 'Please complete the assignment',
      submissionContent,
      employeeName,
      currentSkillLevel,
    });

    // If assignmentId is provided, save the feedback to the database
    if (assignmentId) {
      await prisma.assignment.update({
        where: { id: assignmentId },
        data: {
          aiFeedback: feedback.feedback,
          grade: feedback.score,
          gradedAt: new Date(),
        },
      });
    }

    res.json({
      success: true,
      feedback,
    });
  } catch (error) {
    console.error('Generate feedback error:', error);
    res.status(500).json({ error: 'Failed to generate feedback' });
  }
});

// Bulk generate feedback for pending assignments
router.post('/bulk-generate-feedback', authenticate, async (req: any, res) => {
  try {
    // Only managers and admins can bulk generate feedback
    if (req.userRole !== 'MANAGER' && req.userRole !== 'ADMIN') {
      return res.status(403).json({ error: 'Forbidden' });
    }

    const { assignmentIds } = req.body;

    if (!assignmentIds || !Array.isArray(assignmentIds)) {
      return res.status(400).json({ error: 'assignmentIds array is required' });
    }

    const results = [];
    const errors = [];

    for (const assignmentId of assignmentIds) {
      try {
        const assignment = await prisma.assignment.findUnique({
          where: { id: assignmentId },
          include: {
            user: true,
          },
        });

        if (!assignment || !assignment.submittedAt || assignment.grade !== null) {
          continue; // Skip if not submitted or already graded
        }

        const feedback = await azureAIService.generateAssignmentFeedback({
          skillName: 'General',
          assignmentTitle: assignment.title || 'Assignment',
          assignmentDescription: assignment.title || '',
          submissionContent: assignment.submission || '',
          employeeName: assignment.user ? `${assignment.user.firstName} ${assignment.user.lastName}` : 'Unknown',
        });

        await prisma.assignment.update({
          where: { id: assignmentId },
          data: {
            aiFeedback: feedback.feedback,
            grade: feedback.score,
            gradedAt: new Date(),
          },
        });

        results.push({
          assignmentId,
          success: true,
          feedback,
        });
      } catch (error) {
        console.error(`Error processing assignment ${assignmentId}:`, error);
        errors.push({
          assignmentId,
          error: 'Failed to generate feedback',
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
    console.error('Bulk generate feedback error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;

