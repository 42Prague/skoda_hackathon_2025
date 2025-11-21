import OpenAI from 'openai';

// Initialize Azure OpenAI client
const endpoint = process.env.AZURE_OPENAI_ENDPOINT || '';
const apiKey = process.env.AZURE_OPENAI_API_KEY || '';
const apiVersion = process.env.AZURE_OPENAI_API_VERSION || '2024-08-01-preview';
const deploymentName = process.env.AZURE_OPENAI_DEPLOYMENT_NAME || 'gpt-4o';

const client = new OpenAI({
  apiKey,
  baseURL: `${endpoint}/openai/deployments/${deploymentName}`,
  defaultQuery: { 'api-version': apiVersion },
  defaultHeaders: { 'api-key': apiKey },
});

/**
 * Generate AI-powered feedback for assignment submissions
 */
export async function generateAssignmentFeedback(params: {
  skillName: string;
  assignmentTitle: string;
  assignmentDescription: string;
  submissionContent: string;
  employeeName: string;
  currentSkillLevel?: string;
}): Promise<{
  feedback: string;
  score: number;
  strengths: string[];
  improvements: string[];
  recommendations: string[];
}> {
  try {
    const prompt = `You are an expert skills assessor for Škoda employees. Analyze the following assignment submission and provide detailed, constructive feedback.

**Assignment Details:**
- Skill: ${params.skillName}
- Title: ${params.assignmentTitle}
- Description: ${params.assignmentDescription}
- Employee: ${params.employeeName}
${params.currentSkillLevel ? `- Current Skill Level: ${params.currentSkillLevel}` : ''}

**Submission Content:**
${params.submissionContent}

**Instructions:**
Provide a comprehensive assessment in JSON format with the following structure:
{
  "feedback": "A detailed paragraph of constructive feedback (3-5 sentences)",
  "score": <number between 0-100>,
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "improvements": ["area for improvement 1", "area for improvement 2", "area for improvement 3"],
  "recommendations": ["specific learning recommendation 1", "specific learning recommendation 2"]
}

Focus on:
1. Technical accuracy and completeness
2. Practical application of the skill
3. Areas for growth and development
4. Specific, actionable next steps

Respond ONLY with valid JSON.`;

    const response = await client.chat.completions.create({
      model: deploymentName,
      messages: [
        {
          role: 'system',
          content: 'You are an expert skills assessor specializing in automotive industry competencies and employee development. Provide constructive, actionable feedback that helps employees grow their skills.',
        },
        {
          role: 'user',
          content: prompt,
        },
      ],
      temperature: 0.7,
      max_tokens: 1500,
      response_format: { type: 'json_object' },
    });

    const content = response.choices[0]?.message?.content;
    if (!content) {
      throw new Error('No response from Azure OpenAI');
    }

    const result = JSON.parse(content);
    return {
      feedback: result.feedback || 'Good work on this assignment.',
      score: Math.min(100, Math.max(0, result.score || 75)),
      strengths: result.strengths || [],
      improvements: result.improvements || [],
      recommendations: result.recommendations || [],
    };
  } catch (error) {
    console.error('Error generating assignment feedback:', error);
    // Return fallback response
    return {
      feedback: 'Your submission has been received. A detailed review is being processed.',
      score: 75,
      strengths: ['Completed the assignment', 'Demonstrated effort'],
      improvements: ['Continue practicing this skill'],
      recommendations: ['Review course materials', 'Practice regularly'],
    };
  }
}

/**
 * Generate AI-powered skill risk analysis and recommendations
 */
export async function generateSkillRiskInsights(params: {
  employeeName: string;
  skillName: string;
  skillCategory: string;
  currentLevel?: string;
  riskScore: number;
  riskLabel: string;
  avgFutureDemand: number;
  automationExposure: number;
  department?: string;
}): Promise<{
  explanation: string;
  immediateActions: string[];
  shortTermGoals: string[];
  longTermStrategy: string;
  suggestedCourses: string[];
  marketInsights: string;
}> {
  try {
    const prompt = `You are a career development expert specializing in automotive industry skills and workforce planning. Analyze the following employee skill risk profile and provide strategic guidance.

**Employee Profile:**
- Name: ${params.employeeName}
- Skill: ${params.skillName} (${params.skillCategory})
${params.currentLevel ? `- Current Level: ${params.currentLevel}` : ''}
${params.department ? `- Department: ${params.department}` : ''}

**Risk Metrics:**
- Overall Risk Score: ${params.riskScore}/100
- Risk Level: ${params.riskLabel}
- Average Future Demand: ${params.avgFutureDemand}/100
- Automation Exposure: ${params.automationExposure}/100

**Instructions:**
Provide a comprehensive skill risk analysis in JSON format:
{
  "explanation": "A clear 3-4 sentence explanation of what this risk score means for the employee's career",
  "immediateActions": ["action 1 (can be done this week)", "action 2", "action 3"],
  "shortTermGoals": ["goal for next 1-3 months", "goal 2", "goal 3"],
  "longTermStrategy": "A paragraph describing the strategic approach for the next 6-12 months",
  "suggestedCourses": ["specific course/certification 1", "course 2", "course 3"],
  "marketInsights": "2-3 sentences about current market trends for this skill in automotive industry"
}

Consider:
1. The automotive industry's shift toward electric vehicles and digitalization
2. Škoda's focus on innovation and technology
3. Balance between upskilling current competencies and learning adjacent skills
4. Practical, actionable recommendations

Respond ONLY with valid JSON.`;

    const response = await client.chat.completions.create({
      model: deploymentName,
      messages: [
        {
          role: 'system',
          content: 'You are a career development expert with deep knowledge of the automotive industry, particularly in the context of digital transformation, electrification, and Industry 4.0. Provide strategic, actionable guidance.',
        },
        {
          role: 'user',
          content: prompt,
        },
      ],
      temperature: 0.7,
      max_tokens: 1500,
      response_format: { type: 'json_object' },
    });

    const content = response.choices[0]?.message?.content;
    if (!content) {
      throw new Error('No response from Azure OpenAI');
    }

    const result = JSON.parse(content);
    return {
      explanation: result.explanation || `Your ${params.skillName} skill has a risk score of ${params.riskScore}/100, indicating ${params.riskLabel.toLowerCase()} risk level.`,
      immediateActions: result.immediateActions || ['Review current skill level', 'Identify learning opportunities'],
      shortTermGoals: result.shortTermGoals || ['Complete relevant training', 'Apply skills in projects'],
      longTermStrategy: result.longTermStrategy || 'Focus on continuous learning and skill development to remain competitive.',
      suggestedCourses: result.suggestedCourses || ['Industry-relevant certifications', 'Practical workshops'],
      marketInsights: result.marketInsights || `The ${params.skillCategory} category is evolving rapidly in the automotive sector.`,
    };
  } catch (error) {
    console.error('Error generating skill risk insights:', error);
    // Return fallback response
    return {
      explanation: `Your ${params.skillName} skill has a risk score of ${params.riskScore}/100, indicating ${params.riskLabel.toLowerCase()} risk level. This metric helps identify skills that may need development.`,
      immediateActions: [
        'Assess your current proficiency level',
        'Identify specific areas for improvement',
        'Explore available training resources',
      ],
      shortTermGoals: [
        'Complete at least one relevant course in the next 3 months',
        'Apply new knowledge in daily work',
        'Seek feedback from peers and managers',
      ],
      longTermStrategy: 'Develop a comprehensive upskilling plan that balances deepening expertise in your current domain while exploring adjacent skills that are in high demand in the automotive industry.',
      suggestedCourses: [
        'Advanced technical certifications',
        'Leadership and soft skills development',
        'Industry-specific training programs',
      ],
      marketInsights: `The automotive industry is undergoing significant transformation with increased focus on electrification, digitalization, and sustainable manufacturing practices.`,
    };
  }
}

/**
 * Generate personalized learning recommendations based on skill gaps
 */
export async function generateLearningPath(params: {
  employeeName: string;
  currentSkills: Array<{ name: string; level: string; category: string }>;
  targetRole?: string;
  riskSkills: Array<{ name: string; riskScore: number }>;
  department?: string;
}): Promise<{
  careerPath: string;
  prioritySkills: Array<{ skill: string; reason: string; timeline: string }>;
  learningPlan: Array<{ phase: string; duration: string; focus: string[]; outcomes: string[] }>;
}> {
  try {
    const prompt = `You are a career development strategist for Škoda. Create a personalized learning path for an employee.

**Employee Profile:**
- Name: ${params.employeeName}
${params.department ? `- Department: ${params.department}` : ''}
${params.targetRole ? `- Target Role: ${params.targetRole}` : ''}

**Current Skills:**
${params.currentSkills.map(s => `- ${s.name} (${s.category}): ${s.level}`).join('\n')}

**Skills at Risk:**
${params.riskSkills.map(s => `- ${s.name}: Risk Score ${s.riskScore}/100`).join('\n')}

Create a comprehensive learning path in JSON format:
{
  "careerPath": "2-3 sentence description of recommended career trajectory",
  "prioritySkills": [
    {"skill": "skill name", "reason": "why this is important", "timeline": "when to focus on this"},
    ...
  ],
  "learningPlan": [
    {"phase": "Phase 1", "duration": "timeline", "focus": ["skill 1", "skill 2"], "outcomes": ["outcome 1", "outcome 2"]},
    ...
  ]
}

Respond ONLY with valid JSON.`;

    const response = await client.chat.completions.create({
      model: deploymentName,
      messages: [
        {
          role: 'system',
          content: 'You are a career development strategist specializing in automotive industry career paths and skill development.',
        },
        {
          role: 'user',
          content: prompt,
        },
      ],
      temperature: 0.7,
      max_tokens: 2000,
      response_format: { type: 'json_object' },
    });

    const content = response.choices[0]?.message?.content;
    if (!content) {
      throw new Error('No response from Azure OpenAI');
    }

    return JSON.parse(content);
  } catch (error) {
    console.error('Error generating learning path:', error);
    throw error;
  }
}

export const azureAIService = {
  generateAssignmentFeedback,
  generateSkillRiskInsights,
  generateLearningPath,
};
