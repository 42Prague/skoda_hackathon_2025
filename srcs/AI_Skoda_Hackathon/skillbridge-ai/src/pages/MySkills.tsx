import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Target, Info, TrendingUp, AlertCircle } from "lucide-react";
import AppLayout from "@/components/AppLayout";
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import {
  Tooltip as UITooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useEmployeeData } from "@/contexts/EmployeeDataContext";
import { SkillCard } from "@/components/ui/SkillCard";

const MySkills = () => {
  const { employee, updateSkillLevel } = useEmployeeData();
  
  const skillData = employee.skills.map(skill => ({
    skill: skill.name.split(' ').slice(0, 2).join(' '), // Shorter names for chart
    current: skill.currentLevel,
    target: skill.targetLevel,
    fullMark: 100,
  }));

  const skillDetails = employee.skills
    .map(skill => ({
      ...skill,
      gap: skill.targetLevel - skill.currentLevel,
      courses: Math.floor(Math.random() * 5) + 1, // Mock course count
      actions: [`Advanced ${skill.name}`, `${skill.name} Best Practices`],
    }))
    .sort((a, b) => b.gap - a.gap); // Sort by gap descending

  return (
    <AppLayout userType="employee">
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold text-foreground mb-2">My Skills Profile</h1>
          <p className="text-muted-foreground">
            Dynamic skill assessment for Senior Software Engineer role
          </p>
        </div>

        {/* Overall Match Score */}
        <Card className="shadow-card border-primary/50">
          <CardContent className="p-6">
            <div className="flex items-center gap-8">
              <div className="flex-shrink-0">
                <div className="relative w-32 h-32">
                  <svg className="w-full h-full transform -rotate-90">
                    <circle
                      cx="64"
                      cy="64"
                      r="56"
                      stroke="hsl(var(--muted))"
                      strokeWidth="8"
                      fill="none"
                    />
                    <circle
                      cx="64"
                      cy="64"
                      r="56"
                      stroke="hsl(var(--primary))"
                      strokeWidth="8"
                      fill="none"
                      strokeDasharray={`${2 * Math.PI * 56}`}
                      strokeDashoffset={`${2 * Math.PI * 56 * (1 - 0.82)}`}
                      className="transition-all duration-1000"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-3xl font-bold text-foreground">{employee.overallMatch}%</span>
                  </div>
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-2xl font-bold text-foreground mb-2">Overall Skill Match</h3>
                <p className="text-muted-foreground mb-4">
                  You match {employee.overallMatch}% of requirements for <strong>{employee.role}</strong>.
                  Focus on {skillDetails[0]?.name} to reach 90%+.
                </p>
                <div className="flex items-center gap-3">
                  <Badge className="bg-entity-growth/10 text-entity-growth border-entity-growth">
                    Low Risk
                  </Badge>
                  <Badge className="bg-entity-position/10 text-entity-position border-entity-position">
                    Target Role
                  </Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Skill Gap Radar */}
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="w-5 h-5 text-entity-skill" />
                Skill Gap Analysis
              </CardTitle>
              <CardDescription>Current vs Target for Senior Engineer role</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={skillData}>
                    <PolarGrid stroke="hsl(var(--border))" />
                    <PolarAngleAxis
                      dataKey="skill"
                      tick={{ fill: "hsl(var(--foreground))", fontSize: 12 }}
                    />
                    <PolarRadiusAxis
                      angle={90}
                      domain={[0, 100]}
                      tick={{ fill: "hsl(var(--muted-foreground))" }}
                    />
                    <Radar
                      name="Current"
                      dataKey="current"
                      stroke="hsl(var(--entity-employee))"
                      fill="hsl(var(--entity-employee))"
                      fillOpacity={0.3}
                    />
                    <Radar
                      name="Target"
                      dataKey="target"
                      stroke="hsl(var(--entity-position))"
                      fill="hsl(var(--entity-position))"
                      fillOpacity={0.2}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "0.5rem",
                      }}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
              <div className="flex items-center justify-center gap-6 mt-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-entity-employee"></div>
                  <span className="text-sm text-muted-foreground">Current Level</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-entity-position"></div>
                  <span className="text-sm text-muted-foreground">Target Level</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* AI Predictions */}
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-primary" />
                AI Skill Predictions
              </CardTitle>
              <CardDescription>Forecasted relevance for next 2 years</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="p-4 rounded-lg bg-entity-growth/10 border border-entity-growth">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-entity-growth flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-foreground mb-1">Strong Foundation</h4>
                    <p className="text-sm text-muted-foreground">
                      Your core development skills remain highly relevant. Focus upskilling efforts
                      on emerging cloud technologies.
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="font-semibold text-foreground">Skill Trend Indicators</h4>
                {[
                  { skill: "Cloud Architecture", trend: "rising", confidence: 95 },
                  { skill: "Frontend Dev", trend: "stable", confidence: 88 },
                  { skill: "System Design", trend: "rising", confidence: 92 },
                  { skill: "Leadership", trend: "rising", confidence: 85 },
                ].map((item) => (
                  <div key={item.skill} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-foreground">{item.skill}</span>
                      <TooltipProvider>
                        <UITooltip>
                          <TooltipTrigger>
                            <Badge
                              variant="outline"
                              className={
                                item.trend === "rising"
                                  ? "bg-entity-growth/10 text-entity-growth border-entity-growth"
                                  : "bg-muted text-muted-foreground"
                              }
                            >
                              {item.trend === "rising" ? "↗ Rising" : "→ Stable"}
                            </Badge>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>AI Confidence: {item.confidence}%</p>
                          </TooltipContent>
                        </UITooltip>
                      </TooltipProvider>
                    </div>
                  </div>
                ))}
              </div>

              <Button className="w-full" asChild>
                <a href="/career-path">View Career Projections</a>
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Detailed Skill Breakdown */}
        <Card className="shadow-card">
          <CardHeader>
            <CardTitle>Detailed Skill Breakdown</CardTitle>
            <CardDescription>
              Skills prioritized by gap size and role importance
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {skillDetails.slice(0, 4).map((skill) => (
                <SkillCard
                  key={skill.id}
                  skill={skill}
                  onUpdateLevel={(newLevel) => updateSkillLevel(skill.id, newLevel)}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
};

export default MySkills;
