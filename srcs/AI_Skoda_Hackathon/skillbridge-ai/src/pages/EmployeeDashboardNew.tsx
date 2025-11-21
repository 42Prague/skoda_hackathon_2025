import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Brain, ArrowLeft, TrendingUp, BookOpen, Award, Target, Loader2, LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from "recharts";
import { useAuth } from "@/contexts/AuthContext";
import { dashboardAPI } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import OpenJobs from "@/components/OpenJobs";
import JobMatches from "@/components/JobMatches";
import KnowledgeGraph from "@/components/KnowledgeGraph";

const EmployeeDashboard = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();
  const { toast } = useToast();
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      if (!user?.id) {
        setIsLoading(false);
        return;
      }

      try {
        const data = await dashboardAPI.getEmployeeDashboard(user.id);
        setDashboardData(data);
      } catch (error: any) {
        console.error('Failed to fetch dashboard:', error);
        toast({
          title: "Error",
          description: error.message || "Failed to load dashboard data",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboard();
  }, [user, toast]);

  // Transform user skills for radar chart
  const skillData = dashboardData?.userSkills?.slice(0, 6).map((us: any) => ({
    skill: us.skill,
    value: us.level,
  })) || [];

  const getRiskBadgeClass = (riskLevel: string) => {
    switch (riskLevel.toUpperCase()) {
      case 'LOW':
        return "bg-risk-low/10 text-risk-low border-risk-low";
      case 'MEDIUM':
        return "bg-risk-medium/10 text-risk-medium border-risk-medium";
      case 'HIGH':
        return "bg-risk-high/10 text-risk-high border-risk-high";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  const getGapBadgeClass = (gap: number) => {
    if (gap < 20) return "bg-risk-low/10 text-risk-low border-risk-low";
    if (gap < 40) return "bg-risk-medium/10 text-risk-medium border-risk-medium";
    return "bg-risk-high/10 text-risk-high border-risk-high";
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-subtle flex items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle>Authentication Required</CardTitle>
            <CardDescription>Please log in to view your dashboard</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => navigate("/")} className="w-full">
              Go to Login
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-subtle flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

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
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => {
                logout();
                navigate("/login");
              }}
              className="gap-2"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="space-y-8">
          {/* Welcome Section */}
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-3xl font-bold text-foreground">
                Welcome back, {dashboardData?.user?.firstName || 'User'}!
              </h2>
              {dashboardData?.user?.employeeId && (
                <Badge variant="outline" className="text-lg px-3 py-1">
                  ID: {dashboardData.user.employeeId}
                </Badge>
              )}
            </div>
            <p className="text-muted-foreground">
              Here's your personalized career development overview
              {dashboardData?.user?.employeeId && (
                <span className="ml-2 text-primary font-medium">
                  • Data from dataset for Employee ID: {dashboardData.user.employeeId}
                </span>
              )}
            </p>
          </div>

          {/* Skill Snapshot */}
          <Card className="shadow-card">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="w-5 h-5 text-primary" />
                    Skill Snapshot
                  </CardTitle>
                  <CardDescription>Your current skill profile and market relevance</CardDescription>
                </div>
                {dashboardData?.user?.employeeId && (
                  <Badge variant="secondary" className="text-base px-3 py-1">
                    Employee ID: {dashboardData.user.employeeId}
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-8">
                <div className="space-y-6">
                  <div>
                    <div className="flex items-baseline gap-3 mb-2">
                      <span className="text-5xl font-bold text-foreground">
                        {Math.round(dashboardData?.skillRelevanceScore || 0)}%
                      </span>
                      <span className="text-lg text-muted-foreground">Skill Relevance Score</span>
                    </div>
                    <Badge variant="outline" className={getRiskBadgeClass(dashboardData?.riskLevel || 'LOW')}>
                      {dashboardData?.riskLevel || 'Low'} Risk
                    </Badge>
                  </div>
                  
                  <div className="space-y-3">
                    <p className="text-sm text-muted-foreground">
                      Your skills are {dashboardData?.riskLevel === 'LOW' ? 'well-aligned' : 'evolving'} with current and future market demands. 
                      {dashboardData?.riskLevel === 'LOW' && ' Continue building on your technical strengths.'}
                    </p>
                    {dashboardData?.userSkills && dashboardData.userSkills.length > 0 && (
                      <div className="flex gap-2 flex-wrap">
                        {dashboardData.userSkills.slice(0, 3).map((us: any, idx: number) => (
                          <Badge key={idx} variant="secondary">{us.skill}</Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <div className="h-[300px]">
                  {skillData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={skillData}>
                        <PolarGrid stroke="hsl(var(--border))" />
                        <PolarAngleAxis dataKey="skill" tick={{ fill: 'hsl(var(--foreground))', fontSize: 12 }} />
                        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                        <Radar name="Skills" dataKey="value" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.3} />
                      </RadarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-full flex items-center justify-center text-muted-foreground">
                      No skill data available
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Knowledge Graph */}
          {(dashboardData?.courses && dashboardData.courses.length > 0) || dashboardData?.education ? (
            <KnowledgeGraph
              courses={dashboardData?.courses || []}
              education={dashboardData?.education || null}
              skills={dashboardData?.userSkills?.map((us: any) => ({
                skill: us.skill,
                level: us.level,
                category: us.category,
              })) || []}
              employeeName={`${dashboardData?.user?.firstName || ''} ${dashboardData?.user?.lastName || ''}`.trim() || 'Employee'}
            />
          ) : null}

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
                  <div className={`w-24 h-24 rounded-full ${
                    dashboardData?.riskLevel === 'LOW' ? 'bg-risk-low/20' : 
                    dashboardData?.riskLevel === 'MEDIUM' ? 'bg-risk-medium/20' : 
                    'bg-risk-high/20'
                  } flex items-center justify-center`}>
                    <div className={`w-16 h-16 rounded-full ${
                      dashboardData?.riskLevel === 'LOW' ? 'bg-risk-low' : 
                      dashboardData?.riskLevel === 'MEDIUM' ? 'bg-risk-medium' : 
                      'bg-risk-high'
                    } flex items-center justify-center`}>
                      <span className="text-2xl font-bold text-white">
                        {dashboardData?.riskLevel === 'LOW' ? '✓' : dashboardData?.riskLevel === 'MEDIUM' ? '!' : '⚠'}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="space-y-3 flex-1">
                  <h4 className="text-xl font-semibold text-foreground">
                    {dashboardData?.riskLevel === 'LOW' ? 'High Stability Predicted' : 
                     dashboardData?.riskLevel === 'MEDIUM' ? 'Moderate Stability' : 
                     'Action Recommended'}
                  </h4>
                  <p className="text-muted-foreground">
                    Based on industry trends and your skill profile, your current role shows{' '}
                    {dashboardData?.riskLevel === 'LOW' ? 'strong stability' : 
                     dashboardData?.riskLevel === 'MEDIUM' ? 'moderate stability with room for improvement' : 
                     'some risk - consider upskilling in key areas'}.
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
          {dashboardData?.careerPaths && dashboardData.careerPaths.length > 0 && (
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
                  {dashboardData.careerPaths.map((path: any, index: number) => (
                    <div key={index} className="p-4 rounded-lg border bg-muted/30 hover:bg-muted/50 transition-colors">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h4 className="font-semibold text-foreground mb-1">{path.title}</h4>
                          <p className="text-sm text-muted-foreground">{path.reason || path.description}</p>
                        </div>
                        <Badge 
                          variant="outline" 
                          className={getGapBadgeClass(path.overallGap || 0)}
                        >
                          Fit: {path.fitScore ? `${Math.round(path.fitScore)}%` : 'N/A'}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-3 mt-3">
                        <Progress value={path.fitScore || 0} className="flex-1" />
                        <span className="text-sm font-medium text-foreground">{Math.round(path.fitScore || 0)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

                {/* Job Matches with Three-Tier System */}
                {user?.id && (
                  <div>
                    <JobMatches userId={user.id} />
                  </div>
                )}

                {/* Open Job Positions */}
                <OpenJobs />

          {/* Learning Recommendations */}
          {dashboardData?.recommendedCourses && dashboardData.recommendedCourses.length > 0 && (
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
                  {dashboardData.recommendedCourses.map((course: any, index: number) => {
                    const enrollment = dashboardData.enrollments?.find((e: any) => e.courseId === course.id);
                    const progress = enrollment?.progress || 0;

                    return (
                      <div key={index} className="p-4 rounded-lg border bg-card">
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <h4 className="font-semibold text-foreground mb-1">{course.title}</h4>
                            <p className="text-sm text-muted-foreground">{course.description || `Duration: ${course.duration || 'N/A'}`}</p>
                          </div>
                          <Badge variant="outline">
                            {course.difficulty || 'Intermediate'}
                          </Badge>
                        </div>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">Progress</span>
                            <span className="font-medium text-foreground">{Math.round(progress)}%</span>
                          </div>
                          <Progress value={progress} />
                          {progress === 0 && (
                            <Button 
                              size="sm" 
                              className="mt-2 w-full bg-gradient-primary"
                              onClick={() => navigate(`/course/overview?course=${encodeURIComponent(course.title)}`)}
                            >
                              Start Course
                            </Button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Assessments */}
          {dashboardData?.assessments && dashboardData.assessments.length > 0 && (
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
                  {dashboardData.assessments.map((assessment: any) => (
                    <div key={assessment.id} className="flex items-center justify-between p-4 rounded-lg border">
                      <div className="flex-1">
                        <h4 className="font-semibold text-foreground mb-1">{assessment.name}</h4>
                        <Badge variant={assessment.status === "COMPLETED" ? "default" : "outline"}>
                          {assessment.status}
                        </Badge>
                      </div>
                      {assessment.score != null ? (
                        <div className="text-right">
                          <div className="text-2xl font-bold text-foreground">{Math.round(assessment.score)}</div>
                          <div className="text-xs text-muted-foreground">Score</div>
                        </div>
                      ) : (
                        <Button className="bg-gradient-primary">
                          Take Assessment
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
};

export default EmployeeDashboard;
