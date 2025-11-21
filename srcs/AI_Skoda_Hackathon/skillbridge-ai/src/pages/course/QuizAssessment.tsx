import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { CheckCircle2, XCircle, Lightbulb, ChevronRight, Trophy } from "lucide-react";
import { useEmployeeData } from "@/contexts/EmployeeDataContext";
import { toast } from "@/hooks/use-toast";
import { motion, AnimatePresence } from "framer-motion";

interface QuizQuestion {
  id: number;
  text: string;
  options: { id: string; text: string; isCorrect: boolean }[];
  explanation: string;
  skillImpact: string;
}

// Quiz questions database by course
const quizQuestions: Record<string, QuizQuestion[]> = {
  "AWS Cloud Architecture": [
    {
      id: 1,
      text: "What is the primary benefit of using AWS EC2 Auto Scaling?",
      options: [
        { id: "a", text: "Reduced costs only", isCorrect: false },
        { id: "b", text: "Automatic capacity adjustment based on demand", isCorrect: true },
        { id: "c", text: "Faster instance boot times", isCorrect: false },
        { id: "d", text: "Free data transfer", isCorrect: false },
      ],
      explanation: "Auto Scaling automatically adjusts the number of EC2 instances based on demand, ensuring optimal performance while minimizing costs. It's a key feature for building resilient, scalable applications.",
      skillImpact: "Cloud Architecture",
    },
    {
      id: 2,
      text: "Which AWS service provides a managed NoSQL database?",
      options: [
        { id: "a", text: "RDS", isCorrect: false },
        { id: "b", text: "DynamoDB", isCorrect: true },
        { id: "c", text: "Redshift", isCorrect: false },
        { id: "d", text: "Aurora", isCorrect: false },
      ],
      explanation: "DynamoDB is AWS's fully managed NoSQL database service, offering single-digit millisecond performance at any scale.",
      skillImpact: "Cloud Architecture",
    },
    {
      id: 3,
      text: "What does VPC stand for in AWS?",
      options: [
        { id: "a", text: "Virtual Private Cloud", isCorrect: true },
        { id: "b", text: "Very Private Connection", isCorrect: false },
        { id: "c", text: "Virtual Public Cloud", isCorrect: false },
        { id: "d", text: "Verified Private Container", isCorrect: false },
      ],
      explanation: "VPC (Virtual Private Cloud) allows you to provision a logically isolated section of the AWS cloud where you can launch resources in a virtual network that you define.",
      skillImpact: "Cloud Architecture",
    },
  ],
  "Agile Project Management": [
    {
      id: 1,
      text: "What is the recommended duration for a Sprint in Scrum?",
      options: [
        { id: "a", text: "1 week", isCorrect: false },
        { id: "b", text: "2-4 weeks", isCorrect: true },
        { id: "c", text: "6 weeks", isCorrect: false },
        { id: "d", text: "Variable length", isCorrect: false },
      ],
      explanation: "Scrum recommends Sprints of 2-4 weeks to maintain a consistent cadence while allowing enough time to deliver valuable increments.",
      skillImpact: "Leadership",
    },
    {
      id: 2,
      text: "Who is responsible for maximizing the value of the product in Scrum?",
      options: [
        { id: "a", text: "Scrum Master", isCorrect: false },
        { id: "b", text: "Product Owner", isCorrect: true },
        { id: "c", text: "Development Team", isCorrect: false },
        { id: "d", text: "Stakeholders", isCorrect: false },
      ],
      explanation: "The Product Owner is accountable for maximizing the value of the product resulting from the work of the Scrum Team.",
      skillImpact: "Leadership",
    },
    {
      id: 3,
      text: "What is the main purpose of a Sprint Retrospective?",
      options: [
        { id: "a", text: "Plan the next Sprint", isCorrect: false },
        { id: "b", text: "Inspect and adapt the process", isCorrect: true },
        { id: "c", text: "Demo completed work", isCorrect: false },
        { id: "d", text: "Estimate user stories", isCorrect: false },
      ],
      explanation: "The Sprint Retrospective is an opportunity for the Scrum Team to inspect itself and create a plan for improvements to be enacted during the next Sprint.",
      skillImpact: "Leadership",
    },
  ],
  "Advanced System Design": [
    {
      id: 1,
      text: "What is the CAP theorem in distributed systems?",
      options: [
        { id: "a", text: "Consistency, Availability, Partition tolerance", isCorrect: true },
        { id: "b", text: "Cache, API, Performance", isCorrect: false },
        { id: "c", text: "Compute, Access, Privacy", isCorrect: false },
        { id: "d", text: "Capacity, Allocation, Processing", isCorrect: false },
      ],
      explanation: "The CAP theorem states that a distributed system can only guarantee two out of three properties: Consistency, Availability, and Partition tolerance.",
      skillImpact: "System Design",
    },
    {
      id: 2,
      text: "Which caching strategy is best for read-heavy applications?",
      options: [
        { id: "a", text: "Write-through cache", isCorrect: false },
        { id: "b", text: "Cache-aside (Lazy loading)", isCorrect: true },
        { id: "c", text: "Write-behind cache", isCorrect: false },
        { id: "d", text: "Refresh-ahead cache", isCorrect: false },
      ],
      explanation: "Cache-aside (lazy loading) is ideal for read-heavy workloads as data is only loaded into the cache when requested, optimizing memory usage.",
      skillImpact: "System Design",
    },
    {
      id: 3,
      text: "What is database sharding?",
      options: [
        { id: "a", text: "Vertical partitioning of data", isCorrect: false },
        { id: "b", text: "Horizontal partitioning across multiple databases", isCorrect: true },
        { id: "c", text: "Replicating data across servers", isCorrect: false },
        { id: "d", text: "Compressing database files", isCorrect: false },
      ],
      explanation: "Sharding is a horizontal partitioning strategy that splits data across multiple database instances to improve scalability and performance.",
      skillImpact: "System Design",
    },
  ],
};

export default function QuizAssessment() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { getCourse, updateCourseProgress, updateSkillLevel, employee } = useEmployeeData();
  
  const courseTitle = searchParams.get("course") || "AWS Cloud Architecture";
  const currentModule = parseInt(searchParams.get("module") || "3");
  
  const course = getCourse(courseTitle);
  const questions = quizQuestions[courseTitle] || quizQuestions["AWS Cloud Architecture"];
  
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<string>("");
  const [submitted, setSubmitted] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [score, setScore] = useState(0);
  const [answeredQuestions, setAnsweredQuestions] = useState<boolean[]>(new Array(questions.length).fill(false));
  const [quizCompleted, setQuizCompleted] = useState(false);

  const currentQuestion = questions[currentQuestionIndex];
  const progress = ((currentQuestionIndex + (submitted ? 1 : 0)) / questions.length) * 100;

  const handleSubmit = () => {
    const correct = currentQuestion.options.find(opt => opt.id === selectedAnswer)?.isCorrect || false;
    setIsCorrect(correct);
    setSubmitted(true);
    
    if (correct) {
      setScore(prev => prev + 1);
      toast({
        title: "Correct! ✓",
        description: "Great job! You're mastering this skill.",
      });
    } else {
      toast({
        title: "Not quite right",
        description: "Review the explanation to improve your understanding.",
        variant: "destructive",
      });
    }

    const newAnswered = [...answeredQuestions];
    newAnswered[currentQuestionIndex] = true;
    setAnsweredQuestions(newAnswered);
  };

  const handleNextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
      setSelectedAnswer("");
      setSubmitted(false);
    } else {
      // Quiz completed
      setQuizCompleted(true);
      
      // Update course progress
      if (course) {
        updateCourseProgress(course.id, currentModule, true);
      }
      
      // Update skill level based on score
      const scorePercentage = (score + (isCorrect ? 1 : 0)) / questions.length;
      const skillToUpdate = employee.skills.find(s => s.name === currentQuestion.skillImpact);
      
      if (skillToUpdate && scorePercentage >= 0.7) {
        const improvement = Math.floor(scorePercentage * 10);
        updateSkillLevel(skillToUpdate.id, Math.min(100, skillToUpdate.currentLevel + improvement));
        
        toast({
          title: "Skill Level Updated! 🎯",
          description: `Your ${currentQuestion.skillImpact} skill increased by ${improvement} points!`,
        });
      }
    }
  };

  const handleReturnToCourse = () => {
    navigate(`/course/lesson?course=${encodeURIComponent(courseTitle)}&module=${currentModule + 1}`);
  };

  const finalScore = score + (isCorrect ? 1 : 0);
  const scorePercentage = (finalScore / questions.length) * 100;

  if (quizCompleted) {
    return (
      <div className="min-h-screen bg-gradient-subtle">
        <div className="container mx-auto px-4 py-6">
          <div className="max-w-3xl mx-auto">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5 }}
            >
              <Card className="shadow-card">
                <CardContent className="pt-12 pb-8">
                  <div className="text-center space-y-6">
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
                      className="inline-block"
                    >
                      <div className={`rounded-full p-6 ${scorePercentage >= 70 ? 'bg-green-100 dark:bg-green-950' : 'bg-amber-100 dark:bg-amber-950'}`}>
                        <Trophy className={`h-16 w-16 ${scorePercentage >= 70 ? 'text-green-600 dark:text-green-400' : 'text-amber-600 dark:text-amber-400'}`} />
                      </div>
                    </motion.div>

                    <div>
                      <h2 className="text-3xl font-bold mb-2">Quiz Completed!</h2>
                      <p className="text-muted-foreground">
                        {scorePercentage >= 70 
                          ? "Outstanding performance! You've demonstrated strong mastery of this topic."
                          : "Good effort! Review the material to strengthen your understanding."}
                      </p>
                    </div>

                    <div className="grid grid-cols-3 gap-4 max-w-md mx-auto">
                      <div className="bg-muted rounded-lg p-4">
                        <div className="text-3xl font-bold text-primary">{finalScore}</div>
                        <div className="text-sm text-muted-foreground">Correct</div>
                      </div>
                      <div className="bg-muted rounded-lg p-4">
                        <div className="text-3xl font-bold text-primary">{questions.length}</div>
                        <div className="text-sm text-muted-foreground">Total</div>
                      </div>
                      <div className="bg-muted rounded-lg p-4">
                        <div className="text-3xl font-bold text-primary">{Math.round(scorePercentage)}%</div>
                        <div className="text-sm text-muted-foreground">Score</div>
                      </div>
                    </div>

                    {scorePercentage >= 70 && (
                      <motion.div
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.4 }}
                        className="bg-green-50 dark:bg-green-950 border-2 border-green-200 dark:border-green-800 rounded-lg p-4"
                      >
                        <div className="flex items-start gap-3">
                          <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5" />
                          <div className="text-left text-sm">
                            <p className="font-semibold mb-1">Skill Level Increased! 🎯</p>
                            <p className="text-muted-foreground">
                              Your performance has been recorded and your {currentQuestion.skillImpact} skill level has been updated.
                            </p>
                          </div>
                        </div>
                      </motion.div>
                    )}

                    <div className="pt-4 space-y-3">
                      <Button onClick={handleReturnToCourse} size="lg" className="w-full">
                        Continue to Next Module <ChevronRight className="ml-2 h-4 w-4" />
                      </Button>
                      <Button 
                        variant="outline" 
                        onClick={() => navigate("/employee")}
                        className="w-full"
                      >
                        Return to Dashboard
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-subtle">
      <div className="container mx-auto px-4 py-6">
        <Button 
          variant="ghost" 
          onClick={() => navigate("/employee")}
          className="mb-4"
        >
          ← Exit Course
        </Button>

        <div className="max-w-3xl mx-auto">
          {/* Progress & Score Header */}
          <Card className="mb-6 shadow-card">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm text-muted-foreground">Quiz Progress</span>
                    <Badge variant="secondary" className="text-xs">
                      {currentQuestionIndex + 1} of {questions.length}
                    </Badge>
                  </div>
                  <div className="text-2xl font-bold text-primary">{score} Correct</div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-muted-foreground mb-1">Current Score</div>
                  <div className="text-2xl font-bold">
                    {questions.length > 0 ? Math.round((score / questions.length) * 100) : 0}%
                  </div>
                </div>
              </div>
              <Progress value={progress} className="h-3" />
            </CardContent>
          </Card>

          {/* Question Card */}
          <AnimatePresence mode="wait">
            <motion.div
              key={currentQuestionIndex}
              initial={{ x: 20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -20, opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <Card className="shadow-card">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">
                        Question {currentQuestionIndex + 1} of {questions.length}
                      </p>
                      <CardTitle className="text-2xl">Knowledge Check</CardTitle>
                    </div>
                    <Badge variant="secondary" className="bg-entity-qualification/20 text-entity-qualification">
                      {currentQuestion.skillImpact}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Question */}
                  <div>
                    <h3 className="text-lg font-medium mb-4">{currentQuestion.text}</h3>
                    
                    <RadioGroup 
                      value={selectedAnswer} 
                      onValueChange={setSelectedAnswer}
                      disabled={submitted}
                    >
                      <div className="space-y-3">
                        {currentQuestion.options.map((option) => {
                          const showFeedback = submitted;
                          const isSelected = selectedAnswer === option.id;
                          const showCorrect = showFeedback && option.isCorrect;
                          const showIncorrect = showFeedback && isSelected && !option.isCorrect;

                          return (
                            <motion.div
                              key={option.id}
                              whileHover={!submitted ? { scale: 1.01 } : {}}
                              whileTap={!submitted ? { scale: 0.99 } : {}}
                              className={`
                                relative flex items-center space-x-2 rounded-lg border-2 p-4 transition-all
                                ${!showFeedback && 'hover:border-primary/50 cursor-pointer'}
                                ${isSelected && !showFeedback && 'border-primary bg-primary/5'}
                                ${showCorrect && 'border-green-500 bg-green-50 dark:bg-green-950'}
                                ${showIncorrect && 'border-red-500 bg-red-50 dark:bg-red-950'}
                                ${!isSelected && !showCorrect && 'border-border'}
                              `}
                            >
                              <RadioGroupItem value={option.id} id={option.id} />
                              <Label 
                                htmlFor={option.id} 
                                className="flex-1 cursor-pointer"
                              >
                                {option.text}
                              </Label>
                              {showCorrect && (
                                <motion.div
                                  initial={{ scale: 0 }}
                                  animate={{ scale: 1 }}
                                  transition={{ type: "spring", stiffness: 500 }}
                                >
                                  <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />
                                </motion.div>
                              )}
                              {showIncorrect && (
                                <motion.div
                                  initial={{ scale: 0 }}
                                  animate={{ scale: 1 }}
                                  transition={{ type: "spring", stiffness: 500 }}
                                >
                                  <XCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
                                </motion.div>
                              )}
                            </motion.div>
                          );
                        })}
                      </div>
                    </RadioGroup>
                  </div>

                  {/* Submit Button */}
                  {!submitted && (
                    <Button 
                      onClick={handleSubmit} 
                      disabled={!selectedAnswer}
                      className="w-full"
                      size="lg"
                    >
                      Submit Answer
                    </Button>
                  )}

                  {/* AI Feedback */}
                  {submitted && (
                    <motion.div
                      initial={{ y: 20, opacity: 0 }}
                      animate={{ y: 0, opacity: 1 }}
                      transition={{ duration: 0.3 }}
                      className={`
                        rounded-lg border-2 p-6 space-y-4
                        ${isCorrect ? 'bg-green-50 border-green-200 dark:bg-green-950 dark:border-green-800' : 'bg-amber-50 border-amber-200 dark:bg-amber-950 dark:border-amber-800'}
                      `}
                    >
                      <div className="flex items-start gap-3">
                        {isCorrect ? (
                          <CheckCircle2 className="h-6 w-6 text-green-600 dark:text-green-400 mt-0.5" />
                        ) : (
                          <Lightbulb className="h-6 w-6 text-amber-600 dark:text-amber-400 mt-0.5" />
                        )}
                        <div className="flex-1">
                          <h4 className="font-semibold text-lg mb-2">
                            {isCorrect ? "Excellent Work!" : "Let's Learn Together"}
                          </h4>
                          <p className="text-sm text-muted-foreground mb-3">
                            {currentQuestion.explanation}
                          </p>
                          <div className="flex items-center gap-2 text-sm">
                            <Badge variant="outline" className="font-normal">
                              AI Confidence: High
                            </Badge>
                            <Badge variant="outline" className="font-normal">
                              Skill: {currentQuestion.skillImpact}
                            </Badge>
                          </div>
                        </div>
                      </div>

                      <Button 
                        onClick={handleNextQuestion} 
                        className="w-full"
                        size="lg"
                      >
                        {currentQuestionIndex < questions.length - 1 ? (
                          <>Next Question <ChevronRight className="ml-2 h-4 w-4" /></>
                        ) : (
                          <>Complete Quiz <ChevronRight className="ml-2 h-4 w-4" /></>
                        )}
                      </Button>
                    </motion.div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
