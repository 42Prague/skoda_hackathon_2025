import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Target,
  TrendingUp,
  BookOpen,
  Award,
  AlertCircle,
  Sparkles,
  ArrowRight,
} from "lucide-react";
import { Link } from "react-router-dom";
import AppLayout from "@/components/AppLayout";
import { useEmployeeData } from "@/contexts/EmployeeDataContext";

const Dashboard = () => {
  const { employee } = useEmployeeData();
  
  const activeCourses = employee.courses.filter(c => c.status === "in-progress");
  const avgProgress = activeCourses.length > 0 
    ? Math.round(activeCourses.reduce((sum, c) => sum + c.progress, 0) / activeCourses.length)
    : 0;
  const skillsGained = employee.skills.filter(s => s.trend === "rising").length;

  return (
    <AppLayout userType="employee">
      <div className="space-y-8">
        {/* Welcome Section */}
        <div>
          <h1 className="text-4xl font-bold text-foreground mb-2">Welcome Back, {employee.name.split(' ')[0]}</h1>
          <p className="text-muted-foreground">
            Your personalized career development insights powered by AI
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid md:grid-cols-4 gap-6">
          <Card className="shadow-card hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-entity-employee/10 flex items-center justify-center">
                  <Target className="w-4 h-4 text-entity-employee" />
                </div>
                Skill Match
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">{employee.overallMatch}%</div>
              <p className="text-xs text-entity-growth mt-1">+5% this month</p>
            </CardContent>
          </Card>

          <Card className="shadow-card hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-entity-course/10 flex items-center justify-center">
                  <BookOpen className="w-4 h-4 text-entity-course" />
                </div>
                Active Courses
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">{activeCourses.length}</div>
              <p className="text-xs text-muted-foreground mt-1">{avgProgress}% avg progress</p>
            </CardContent>
          </Card>

          <Card className="shadow-card hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-entity-position/10 flex items-center justify-center">
                  <TrendingUp className="w-4 h-4 text-entity-position" />
                </div>
                Promotion Readiness
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">{employee.promotionReadiness}%</div>
              <p className="text-xs text-entity-growth mt-1">High confidence</p>
            </CardContent>
          </Card>

          <Card className="shadow-card hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-entity-skill/10 flex items-center justify-center">
                  <Award className="w-4 h-4 text-entity-skill" />
                </div>
                Skills Gained
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">{skillsGained}</div>
              <p className="text-xs text-muted-foreground mt-1">This quarter</p>
            </CardContent>
          </Card>
        </div>

        {/* AI Insights Banner */}
        <Card className="shadow-card bg-gradient-primary border-0">
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-white mb-2">AI Career Insight</h3>
                <p className="text-white/90 mb-4">
                  Based on current trends, your skills align well with the{" "}
                  <span className="font-semibold">Senior Software Engineer</span> role. Complete 3
                  recommended courses to increase promotion readiness to 90%.
                </p>
                <Button variant="secondary" size="sm" asChild>
                  <Link to="/career-path">
                    Explore Career Path <ArrowRight className="w-4 h-4 ml-2" />
                  </Link>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Skill Gaps */}
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-entity-risk" />
                Critical Skill Gaps
              </CardTitle>
              <CardDescription>Prioritize these for your target role</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                { skill: "Cloud Architecture", gap: 35, entity: "skill" },
                { skill: "System Design", gap: 28, entity: "skill" },
                { skill: "Leadership", gap: 22, entity: "qualification" },
              ].map((item) => (
                <div key={item.skill} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-foreground">{item.skill}</span>
                    <Badge
                      variant="outline"
                      className={`bg-entity-${item.entity}/10 text-entity-${item.entity} border-entity-${item.entity}`}
                    >
                      {item.gap}% gap
                    </Badge>
                  </div>
                  <Progress value={100 - item.gap} className="h-2" />
                </div>
              ))}
              <Button variant="outline" className="w-full" asChild>
                <Link to="/my-skills">View Full Skill Analysis</Link>
              </Button>
            </CardContent>
          </Card>

          {/* Next Steps */}
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-primary" />
                Recommended Next Steps
              </CardTitle>
              <CardDescription>AI-suggested actions for optimal growth</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                {
                  action: "Complete AWS Solutions Architect course",
                  impact: "High",
                  time: "2 weeks",
                  type: "course",
                },
                {
                  action: "Take System Design Assessment",
                  impact: "Medium",
                  time: "1 hour",
                  type: "qualification",
                },
                {
                  action: "Review microservices learning path",
                  impact: "High",
                  time: "30 min",
                  type: "position",
                },
              ].map((step, index) => (
                <div
                  key={index}
                  className="p-4 rounded-lg border border-border hover:border-primary transition-colors cursor-pointer"
                >
                  <div className="flex items-start justify-between mb-2">
                    <span className="text-sm font-medium text-foreground flex-1">
                      {step.action}
                    </span>
                    <Badge
                      className={`bg-entity-${step.type}/10 text-entity-${step.type} border-entity-${step.type}`}
                      variant="outline"
                    >
                      {step.impact}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">{step.time} • Click to start</p>
                </div>
              ))}
              <Button className="w-full" asChild>
                <Link to="/recommendations">View All Recommendations</Link>
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Learning Progress */}
        <Card className="shadow-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-entity-course" />
              Active Learning Path
            </CardTitle>
            <CardDescription>Your current courses and progress</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { name: "AWS Cloud Practitioner", progress: 65, hours: 8, total: 12 },
                { name: "Advanced React Patterns", progress: 45, hours: 5, total: 10 },
                { name: "Leadership Fundamentals", progress: 30, hours: 3, total: 8 },
              ].map((course) => (
                <div
                  key={course.name}
                  className="p-4 rounded-lg border border-border hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium text-foreground">{course.name}</h4>
                    <span className="text-sm font-semibold text-entity-course">
                      {course.progress}%
                    </span>
                  </div>
                  <Progress value={course.progress} className="mb-2" />
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>
                      {course.hours} of {course.total} hours completed
                    </span>
                    <Button variant="link" size="sm" className="h-auto p-0">
                      Continue
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
};

export default Dashboard;
