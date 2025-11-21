import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Sparkles, Clock, BookOpen } from 'lucide-react';

export default function AIPlanTab({ profile, gaps, onGeneratePlan }) {
  const [plan, setPlan] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);

  const handleGeneratePlan = async () => {
    setIsGenerating(true);
    setError(null);
    console.log('🎯 Starting AI plan generation...');
    const startTime = Date.now();
    
    try {
      const result = await onGeneratePlan();
      const duration = ((Date.now() - startTime) / 1000).toFixed(1);
      console.log(`✅ AI plan generated in ${duration}s`);
      setPlan(result);
    } catch (error) {
      const duration = ((Date.now() - startTime) / 1000).toFixed(1);
      console.error(`❌ AI plan failed after ${duration}s:`, error);
      setError(error.message || 'Failed to generate AI plan');
      alert(`Failed to generate AI plan: ${error.message}\n\nCheck browser console for details.`);
    } finally {
      setIsGenerating(false);
    }
  };

  const canGenerate = profile && gaps;

  return (
    <div className="space-y-6">
      {/* Generate Button */}
      {!plan && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              AI Learning Plan Generator
            </CardTitle>
            <CardDescription>
              Generate a personalized learning path based on your profile and career goals
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              onClick={handleGeneratePlan}
              disabled={!canGenerate || isGenerating}
              className="w-full md:w-auto"
              size="lg"
            >
              {isGenerating ? (
                <>
                  <div className="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                  Generating Plan...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Generate AI Learning Plan
                </>
              )}
            </Button>
            {!canGenerate && (
              <p className="text-sm text-muted-foreground mt-3">
                Please select an employee and target role first
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* AI Plan Display */}
      {plan && (
        <>
          {/* Explanation */}
          <Card className="border-primary/20 bg-primary/5">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                AI Recommendation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed">{plan.explanation}</p>
            </CardContent>
          </Card>

          {/* Time to Readiness */}
          {plan.estimated_time_to_readiness && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Clock className="h-5 w-5 text-primary" />
                  Estimated Time to Readiness
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold text-primary">
                  {plan.estimated_time_to_readiness}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Learning Path */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5 text-primary" />
                Your Personalized Learning Path
              </CardTitle>
              <CardDescription>
                Follow these steps to achieve your career goal
              </CardDescription>
            </CardHeader>
            <CardContent>
              {plan.learning_path && plan.learning_path.length > 0 ? (
                <div className="space-y-6">
                  {plan.learning_path.map((step, stepIndex) => (
                    <div key={stepIndex} className="relative">
                      {/* Connector line */}
                      {stepIndex < plan.learning_path.length - 1 && (
                        <div className="absolute left-4 top-12 bottom-0 w-0.5 bg-primary/20" />
                      )}

                      <div className="flex gap-4">
                        {/* Step number */}
                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-sm">
                          {step.step || stepIndex + 1}
                        </div>

                        {/* Step content */}
                        <div className="flex-1 pb-6">
                          <h4 className="font-semibold mb-3">{step.title}</h4>

                          {/* Courses */}
                          {step.courses && step.courses.length > 0 && (
                            <div className="space-y-2">
                              {step.courses.map((course, courseIndex) => (
                                <div
                                  key={courseIndex}
                                  className="bg-secondary/50 rounded-lg p-3 space-y-2"
                                >
                                  <div className="flex items-start justify-between gap-2">
                                    <p className="font-medium text-sm">
                                      {course.name}
                                    </p>
                                    {course.minutes && (
                                      <Badge variant="secondary" className="flex-shrink-0">
                                        {course.minutes} min
                                      </Badge>
                                    )}
                                  </div>
                                  {course.provider && (
                                    <p className="text-xs text-muted-foreground">
                                      Provider: {course.provider}
                                    </p>
                                  )}
                                  {course.skills && course.skills.length > 0 && (
                                    <div className="flex flex-wrap gap-1">
                                      {course.skills.map((skill, skillIndex) => (
                                        <Badge
                                          key={skillIndex}
                                          variant="outline"
                                          className="text-xs"
                                        >
                                          {skill}
                                        </Badge>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  No learning path steps available
                </p>
              )}
            </CardContent>
          </Card>

          {/* Regenerate Button */}
          <div className="flex justify-center">
            <Button
              onClick={handleGeneratePlan}
              variant="outline"
              disabled={isGenerating}
            >
              {isGenerating ? 'Regenerating...' : 'Regenerate Plan'}
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
