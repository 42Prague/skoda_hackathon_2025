/**
 * Job Matching Service
 * Calculates fitness scores between employees and job positions
 * Implements three-tier matching system:
 * - Perfect Match (≥85%): Selected for Interview
 * - Middle Match (50-84%): Courses Suggested
 * - Low Match (<50%): Roadmap Suggested
 */

import { prisma } from '../lib/prisma';
import { analyzeEmployeeForJob } from './employeeAnalysis';

export type MatchTier = 'HIGH' | 'MIDDLE' | 'LOW'; // HIGH = Perfect Match (≥85%)

export interface JobMatch {
  jobPositionId: string;
  jobTitle: string;
  jobDescription?: string;
  department?: string;
  location?: string;
  fitnessScore: number; // 0-100 percentage
  matchTier: MatchTier;
  recommendedAction: 'INTERVIEW' | 'COURSES' | 'ROADMAP';
  skillGaps: Array<{
    skillName: string;
    currentLevel: number;
    requiredLevel: number;
    gap: number;
  }>;
  skillMatches: Array<{
    skillName: string;
    currentLevel: number;
    requiredLevel: number;
    matchPercentage: number;
  }>;
  recommendedCourses?: string[]; // Course IDs for middle matches
  roadmapGenerated: boolean;
}

/**
 * Calculate fitness score between employee skills and job requirements
 */
async function calculateFitnessScore(
  employeeSkills: Map<string, number>,
  jobPositionId: string
): Promise<{
  fitnessScore: number;
  skillGaps: JobMatch['skillGaps'];
  skillMatches: JobMatch['skillMatches'];
}> {
  // Get job position requirements
  const jobPosition = await prisma.jobPosition.findUnique({
    where: { id: jobPositionId },
    include: {
      skills: {
        include: {
          skill: true,
        },
      },
    },
  });

  if (!jobPosition) {
    return {
      fitnessScore: 0,
      skillGaps: [],
      skillMatches: [],
    };
  }

  let totalWeightedScore = 0;
  let totalWeight = 0;
  const skillGaps: JobMatch['skillGaps'] = [];
  const skillMatches: JobMatch['skillMatches'] = [];
  let requiredSkillsMet = 0;
  let totalRequiredSkills = 0;

  // Calculate match for each required skill
  for (const jobSkill of jobPosition.skills) {
    const employeeLevel = employeeSkills.get(jobSkill.skill.name) || 0;
    const requiredLevel = jobSkill.requiredLevel || 70;
    const weight = jobSkill.weight || 1.0;

    // Calculate match percentage (cap at 100%)
    const matchPercentage = Math.min((employeeLevel / requiredLevel) * 100, 100);
    
    // Calculate gap
    const gap = Math.max(0, requiredLevel - employeeLevel);

    // Track skill matches/gaps
    if (gap > 0) {
      skillGaps.push({
        skillName: jobSkill.skill.name,
        currentLevel: employeeLevel,
        requiredLevel: requiredLevel,
        gap: gap,
      });
    }

    skillMatches.push({
      skillName: jobSkill.skill.name,
      currentLevel: employeeLevel,
      requiredLevel: requiredLevel,
      matchPercentage: matchPercentage,
    });

    // Weighted score calculation
    const skillScore = (matchPercentage / 100) * weight;
    totalWeightedScore += skillScore * 100; // Scale to 0-100
    totalWeight += weight;

    // Track required skills
    if (jobSkill.isRequired) {
      totalRequiredSkills++;
      if (employeeLevel >= requiredLevel) {
        requiredSkillsMet++;
      }
    }
  }

  // Calculate base fitness score
  const baseScore = totalWeight > 0 ? totalWeightedScore / totalWeight : 0;

  // Apply multiplier based on required skills met
  // If required skills are met, boost score; if not, penalize
  const requiredMultiplier = totalRequiredSkills > 0
    ? 0.5 + (requiredSkillsMet / totalRequiredSkills) * 0.5 // 50-100% based on required skills
    : 1.0;

  const fitnessScore = Math.round(Math.min(baseScore * requiredMultiplier, 100));

  return {
    fitnessScore,
    skillGaps: skillGaps.sort((a, b) => b.gap - a.gap), // Sort by largest gap first
    skillMatches,
  };
}

/**
 * Determine match tier and recommended action
 */
function determineMatchTier(fitnessScore: number): {
  matchTier: MatchTier;
  recommendedAction: 'INTERVIEW' | 'COURSES' | 'ROADMAP';
} {
  if (fitnessScore >= 85) {
    return {
      matchTier: 'HIGH' as MatchTier, // HIGH = Perfect Match (≥85%)
      recommendedAction: 'INTERVIEW',
    };
  } else if (fitnessScore >= 50) {
    return {
      matchTier: 'MIDDLE' as MatchTier, // MIDDLE = 50-84%
      recommendedAction: 'COURSES',
    };
  } else {
    return {
      matchTier: 'LOW' as MatchTier, // LOW = <50%
      recommendedAction: 'ROADMAP',
    };
  }
}

/**
 * Get recommended courses based on skill gaps
 */
async function getRecommendedCourses(
  skillGaps: JobMatch['skillGaps'],
  limit: number = 5
): Promise<string[]> {
  if (skillGaps.length === 0) {
    return [];
  }

  // Get top skill gaps (largest gaps first)
  const topSkillGaps = skillGaps.slice(0, Math.min(5, skillGaps.length));

  // Find courses that teach these skills
  const skillNames = topSkillGaps.map(gap => gap.skillName);

  // Find skills in database
  const skills = await prisma.skill.findMany({
    where: {
      name: {
        in: skillNames,
      },
    },
  });

  const skillIds = skills.map(s => s.id);

  // Find courses that have these skills
  const courses = await prisma.course.findMany({
    where: {
      courseSkills: {
        some: {
          skillId: {
            in: skillIds,
          },
        },
      },
    },
    take: limit,
    select: {
      id: true,
    },
  });

  return courses.map(c => c.id);
}

/**
 * Get all job matches for an employee
 */
export async function getJobMatchesForEmployee(
  employeeId: string,
  userId?: string
): Promise<JobMatch[]> {
  // Get employee skills using the analysis service
  const analysis = analyzeEmployeeForJob(employeeId);

  // Convert skills Map to the format needed
  // analyzeEmployeeForJob returns skills as an object, not a Map
  const employeeSkills = new Map<string, number>();
  
  // The analysis.skills is returned as { [key: string]: number } from analyzeEmployeeForJob
  const skillsObj = analysis.skills as any;
  if (skillsObj instanceof Map) {
    // If it's already a Map, use it directly
    for (const [skillName, level] of skillsObj.entries()) {
      employeeSkills.set(skillName, level);
    }
  } else if (typeof skillsObj === 'object' && skillsObj !== null) {
    // If it's an object, convert to Map
    for (const [skillName, level] of Object.entries(skillsObj)) {
      employeeSkills.set(skillName, level as number);
    }
  }

  // Also get skills from database (as fallback/supplement)
  if (userId) {
    const dbSkills = await prisma.userSkill.findMany({
      where: { userId },
      include: { skill: true },
    });

    for (const userSkill of dbSkills) {
      const existingLevel = employeeSkills.get(userSkill.skill.name) || 0;
      // Use the higher level from either source
      employeeSkills.set(userSkill.skill.name, Math.max(existingLevel, userSkill.level));
    }
  }

  // Get all open job positions
  const openJobs = await prisma.jobPosition.findMany({
    where: {
      status: 'OPEN',
    },
    include: {
      skills: {
        include: {
          skill: true,
        },
      },
    },
    orderBy: {
      postedAt: 'desc',
    },
  });

  // Calculate matches for each job
  const matches: JobMatch[] = [];

  for (const job of openJobs) {
    const { fitnessScore, skillGaps, skillMatches } = await calculateFitnessScore(
      employeeSkills,
      job.id
    );

    const { matchTier, recommendedAction } = determineMatchTier(fitnessScore);

    // Get recommended courses for middle matches
    let recommendedCourses: string[] | undefined;
    if (matchTier === 'MIDDLE') {
      recommendedCourses = await getRecommendedCourses(skillGaps, 5);
    }

    matches.push({
      jobPositionId: job.id,
      jobTitle: job.title,
      jobDescription: job.description || undefined,
      department: job.department || undefined,
      location: job.location || undefined,
      fitnessScore,
      matchTier,
      recommendedAction,
      skillGaps,
      skillMatches,
      recommendedCourses,
      roadmapGenerated: false, // Roadmap generation would be implemented separately
    });
  }

  // Sort by fitness score (highest first)
  return matches.sort((a, b) => b.fitnessScore - a.fitnessScore);
}

/**
 * Get single job match for an employee
 */
export async function getJobMatchForEmployee(
  employeeId: string,
  jobPositionId: string,
  userId?: string
): Promise<JobMatch | null> {
  const allMatches = await getJobMatchesForEmployee(employeeId, userId);
  return allMatches.find(m => m.jobPositionId === jobPositionId) || null;
}

/**
 * Create or update job application with match tier
 */
export async function createJobApplicationWithMatch(
  employeeId: string,
  jobPositionId: string,
  userId?: string
): Promise<{
  application: any;
  match: JobMatch;
}> {
  // Get the match details
  const match = await getJobMatchForEmployee(employeeId, jobPositionId, userId);

  if (!match) {
    throw new Error('Job position not found or not open');
  }

  // Check if application already exists
  const existingApplication = await prisma.jobApplication.findUnique({
    where: {
      jobPositionId_employeeId: {
        jobPositionId,
        employeeId,
      },
    },
  });

  if (existingApplication) {
    // Update existing application
    const updated = await prisma.jobApplication.update({
      where: { id: existingApplication.id },
      data: {
        fitnessScore: match.fitnessScore,
        matchTier: match.matchTier as any, // Cast to enum
        recommendedAction: match.recommendedAction,
        skillGaps: JSON.stringify(match.skillGaps),
        recommendedCourses: match.recommendedCourses ? JSON.stringify(match.recommendedCourses) : null,
        updatedAt: new Date(),
      },
    });

    return { application: updated, match };
  }

  // Create new application
  const application = await prisma.jobApplication.create({
    data: {
      userId: userId || null,
      employeeId,
      jobPositionId,
      fitnessScore: match.fitnessScore,
      matchTier: match.matchTier as any,
      recommendedAction: match.recommendedAction,
      skillGaps: JSON.stringify(match.skillGaps),
      recommendedCourses: match.recommendedCourses ? JSON.stringify(match.recommendedCourses) : null,
      status: match.matchTier === 'HIGH' ? 'SHORTLISTED' as any : 'PENDING' as any,
    },
  });

  return { application, match };
}

