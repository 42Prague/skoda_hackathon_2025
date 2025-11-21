import { azureAIService } from './services/azureAI';

/**
 * Test script for Azure OpenAI integration
 * Run with: npx ts-node src/testAI.ts
 */

async function testAssignmentFeedback() {
  console.log('\n🧪 Testing Assignment Feedback Generation...\n');
  
  try {
    const feedback = await azureAIService.generateAssignmentFeedback({
      skillName: 'JavaScript Programming',
      assignmentTitle: 'Build a REST API',
      assignmentDescription: 'Create a RESTful API with CRUD operations for a todo app',
      submissionContent: `
        I created a REST API using Express.js and PostgreSQL. 
        
        Features implemented:
        - GET /api/todos - List all todos
        - POST /api/todos - Create a new todo
        - PUT /api/todos/:id - Update a todo
        - DELETE /api/todos/:id - Delete a todo
        
        The API uses proper HTTP methods and status codes. I also added basic 
        error handling and validation for required fields.
      `,
      employeeName: 'Jan Novák',
      currentSkillLevel: 'INTERMEDIATE',
    });
    
    console.log('✅ Assignment Feedback Generated:\n');
    console.log('📝 Feedback:', feedback.feedback);
    console.log('📊 Score:', feedback.score);
    console.log('💪 Strengths:', feedback.strengths);
    console.log('📈 Improvements:', feedback.improvements);
    console.log('🎯 Recommendations:', feedback.recommendations);
    
    return true;
  } catch (error) {
    console.error('❌ Error generating feedback:', error);
    return false;
  }
}

async function testSkillRiskInsights() {
  console.log('\n🧪 Testing Skill Risk Insights Generation...\n');
  
  try {
    const insights = await azureAIService.generateSkillRiskInsights({
      employeeName: 'Jan Novák',
      skillName: 'Manual Assembly',
      skillCategory: 'Manufacturing',
      currentLevel: 'ADVANCED',
      riskScore: 72,
      riskLabel: 'HIGH',
      avgFutureDemand: 35,
      automationExposure: 85,
      department: 'Production',
    });
    
    console.log('✅ Skill Risk Insights Generated:\n');
    console.log('📖 Explanation:', insights.explanation);
    console.log('⚡ Immediate Actions:', insights.immediateActions);
    console.log('🎯 Short-term Goals:', insights.shortTermGoals);
    console.log('🗺️  Long-term Strategy:', insights.longTermStrategy);
    console.log('📚 Suggested Courses:', insights.suggestedCourses);
    console.log('📊 Market Insights:', insights.marketInsights);
    
    return true;
  } catch (error) {
    console.error('❌ Error generating insights:', error);
    return false;
  }
}

async function testLearningPath() {
  console.log('\n🧪 Testing Learning Path Generation...\n');
  
  try {
    const learningPath = await azureAIService.generateLearningPath({
      employeeName: 'Jan Novák',
      currentSkills: [
        { name: 'Manual Assembly', level: 'ADVANCED', category: 'Manufacturing' },
        { name: 'Quality Control', level: 'INTERMEDIATE', category: 'Manufacturing' },
      ],
      targetRole: 'Automation Technician',
      riskSkills: [
        { name: 'Manual Assembly', riskScore: 75 },
      ],
      department: 'Production',
    });
    
    console.log('✅ Learning Path Generated:\n');
    console.log('🛤️  Career Path:', learningPath.careerPath);
    console.log('🎯 Priority Skills:', learningPath.prioritySkills);
    console.log('📅 Learning Plan:', learningPath.learningPlan);
    
    return true;
  } catch (error) {
    console.error('❌ Error generating learning path:', error);
    return false;
  }
}

async function runTests() {
  console.log('🚀 Starting Azure OpenAI Integration Tests...\n');
  console.log('=' .repeat(60));
  
  const results = {
    feedback: await testAssignmentFeedback(),
    insights: await testSkillRiskInsights(),
    learningPath: await testLearningPath(),
  };
  
  console.log('\n' + '='.repeat(60));
  console.log('\n📊 Test Results Summary:\n');
  console.log(`   Assignment Feedback: ${results.feedback ? '✅ PASSED' : '❌ FAILED'}`);
  console.log(`   Skill Risk Insights: ${results.insights ? '✅ PASSED' : '❌ FAILED'}`);
  console.log(`   Learning Path:       ${results.learningPath ? '✅ PASSED' : '❌ FAILED'}`);
  
  const allPassed = Object.values(results).every(r => r);
  console.log(`\n${allPassed ? '🎉 All tests passed!' : '⚠️  Some tests failed.'}\n`);
  
  process.exit(allPassed ? 0 : 1);
}

// Run tests if this file is executed directly
if (require.main === module) {
  runTests().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export { testAssignmentFeedback, testSkillRiskInsights, testLearningPath };
