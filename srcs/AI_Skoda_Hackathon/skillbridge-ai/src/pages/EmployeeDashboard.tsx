import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Brain, ArrowLeft, TrendingUp, AlertTriangle, BookOpen, Award, Target } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from "recharts";
import { useEmployeeData } from "@/contexts/EmployeeDataContext";

const EmployeeDashboard = () => {
  const navigate = useNavigate();
  const { employee } = useEmployeeData();

  // Transform employee skills for radar chart
  const skillData = employee.skills.slice(0, 6).map(skill => ({
    skill: skill.name.split(' ').slice(0, 2).join(' '),
    value: skill.currentLevel
  }));

  const careerPaths = [
    { title: "Senior Software Engineer", fit: "High", score: 92, reason: "Your technical skills and project experience align perfectly with this role" },
    { title: "Technical Lead", fit: "High", score: 88, reason: "Strong technical foundation with growing leadership capabilities" },
    { title: "Product Manager", fit: "Medium", score: 72, reason: "Good communication skills, but would benefit from product management training" }
  ];

  const learningRecommendations = employee.courses.slice(0, 3).map(course => ({
    title: course.title,
    gap: course.progress < 30 ? "Large" : course.progress < 70 ? "Medium" : "Small",
    progress: course.progress,
    duration: course.duration
  }));

  const assessments = [
    { name: "Technical Skills Assessment", score: 85, status: "Completed" },
    { name: "Leadership Potential", score: 72, status: "Completed" },
    { name: "Industry Knowledge Test", score: null, status: "Pending" }
  ];

  return (
    <div className="min-h-screen bg-gradient-subtle">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon" onClick={() => navigate("/")}>
                <ArrowLeft className="w-5 h-5" />
              </Button>
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-lg bg-gradient-primary flex items-center justify-center">
                  <Brain className="w-6 h-6 text-primary-foreground" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-foreground">Employee Dashboard</h1>
                  <p className="text-xs text-muted-foreground">Your Career Development Hub</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="space-y-8">
          {/* Welcome Section */}
          <div>
            <h2 className="text-3xl font-bold text-foreground mb-2">Welcome back, {employee.name.split(' ')[0]}!</h2>
            <p className="text-muted-foreground">Here's your personalized career development overview</p>
          </div>

          {/* Skill Snapshot */}
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="w-5 h-5 text-primary" />
                Skill Snapshot
              </CardTitle>
              <CardDescription>Your current skill profile and market relevance</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-8">
                <div className="space-y-6">
                  <div>
                    <div className="flex items-baseline gap-3 mb-2">
                      <span className="text-5xl font-bold text-foreground">{employee.overallMatch}%</span>
                      <span className="text-lg text-muted-foreground">Skill Relevance Score</span>
                    </div>
                    <Badge variant="outline" className="bg-risk-low/10 text-risk-low border-risk-low">
                      Low Risk
                    </Badge>
                  </div>
                  
                  <div className="space-y-3">
                    <p className="text-sm text-muted-foreground">Your skills are well-aligned with current and future market demands. Continue building on your technical strengths.</p>
                    <div className="flex gap-2">
                      <Badge variant="secondary">Technical Expert</Badge>
                      <Badge variant="secondary">Digital Native</Badge>
                    </div>
                  </div>
                </div>

                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart data={skillData}>
                      <PolarGrid stroke="hsl(var(--border))" />
                      <PolarAngleAxis dataKey="skill" tick={{ fill: 'hsl(var(--foreground))', fontSize: 12 }} />
                      <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                      <Radar name="Skills" dataKey="value" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.3} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Future Role Stability */}
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-primary" />
                Future Role Stability
              </CardTitle>
              <CardDescription>Will your current role stay relevant in the next 2-5 years?</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-start gap-6">
                <div className="flex-shrink-0">
                  <div className="w-24 h-24 rounded-full bg-risk-low/20 flex items-center justify-center">
                    <div className="w-16 h-16 rounded-full bg-risk-low flex items-center justify-center">
                      <span className="text-2xl font-bold text-white">✓</span>
                    </div>
                  </div>
                </div>
                <div className="space-y-3 flex-1">
                  <h4 className="text-xl font-semibold text-foreground">High Stability Predicted</h4>
                  <p className="text-muted-foreground">
                    Based on industry trends and your skill profile, your current role as a Software Engineer shows strong stability. 
                    The demand for software development expertise continues to grow, especially in automotive technology and digital transformation.
                  </p>
                  <div className="flex gap-2">
                    <Badge className="bg-primary/10 text-primary border-primary/20">AI Analysis</Badge>
                    <Badge className="bg-muted text-muted-foreground">Last Updated: Today</Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Career Paths */}
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="w-5 h-5 text-primary" />
                Recommended Career Paths
              </CardTitle>
              <CardDescription>Potential next steps in your career journey</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {careerPaths.map((path, index) => (
                  <div key={index} className="p-4 rounded-lg border bg-muted/30 hover:bg-muted/50 transition-colors">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h4 className="font-semibold text-foreground mb-1">{path.title}</h4>
                        <p className="text-sm text-muted-foreground">{path.reason}</p>
                      </div>
                      <Badge 
                        variant="outline" 
                        className={
                          path.fit === "High" 
                            ? "bg-risk-low/10 text-risk-low border-risk-low" 
                            : "bg-risk-medium/10 text-risk-medium border-risk-medium"
                        }
                      >
                        Fit: {path.fit}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-3 mt-3">
                      <Progress value={path.score} className="flex-1" />
                      <span className="text-sm font-medium text-foreground">{path.score}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Learning Recommendations */}
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-primary" />
                Skills & Learning Recommendations
              </CardTitle>
              <CardDescription>Personalized courses to advance your career</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {learningRecommendations.map((course, index) => (
                  <div key={index} className="p-4 rounded-lg border bg-card">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h4 className="font-semibold text-foreground mb-1">{course.title}</h4>
                        <p className="text-sm text-muted-foreground">Duration: {course.duration}</p>
                      </div>
                      <Badge 
                        variant="outline"
                        className={
                          course.gap === "Small" 
                            ? "bg-risk-low/10 text-risk-low border-risk-low" 
                            : "bg-risk-medium/10 text-risk-medium border-risk-medium"
                        }
                      >
                        Gap: {course.gap}
                      </Badge>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Progress</span>
                        <span className="font-medium text-foreground">{course.progress}%</span>
                      </div>
                      <Progress value={course.progress} />
                      <Button 
                        size="lg" 
                        className="mt-3 w-full bg-gradient-primary hover:scale-105 transition-transform"
                        onClick={() => navigate(`/course/overview?course=${encodeURIComponent(course.title)}`)}
                      >
                        {course.progress === 0 ? 'Start Course' : 'Continue Learning'} →
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Assessments */}
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Award className="w-5 h-5 text-primary" />
                Skills Assessments
              </CardTitle>
              <CardDescription>Test your knowledge and track your growth</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {assessments.map((assessment, index) => (
                  <div key={index} className="flex items-center justify-between p-4 rounded-lg border bg-muted/30">
                    <div className="flex-1">
                      <h4 className="font-semibold text-foreground mb-1">{assessment.name}</h4>
                      <Badge variant={assessment.status === "Completed" ? "default" : "outline"}>
                        {assessment.status}
                      </Badge>
                    </div>
                    {assessment.score ? (
                      <div className="text-right">
                        <div className="text-2xl font-bold text-foreground">{assessment.score}</div>
                        <div className="text-xs text-muted-foreground">Score</div>
                      </div>
                    ) : (
                      <Button className="bg-gradient-primary">
                        Take Assessment
                      </Button>
                    )}
                  </div>
                ))}
                
                <div className="mt-6 p-4 rounded-lg bg-accent border border-primary/20">
                  <div className="flex items-start gap-3">
                    <Brain className="w-5 h-5 text-primary flex-shrink-0 mt-1" />
                    <div>
                      <h4 className="font-semibold text-foreground mb-1">AI Skill Level Prediction</h4>
                      <p className="text-sm text-muted-foreground">
                        Based on your completed assessments and work history, our AI predicts you're performing at a <span className="font-semibold text-foreground">Senior Level (L4)</span> with readiness to advance to L5 within 12-18 months with targeted upskilling.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default EmployeeDashboard;
