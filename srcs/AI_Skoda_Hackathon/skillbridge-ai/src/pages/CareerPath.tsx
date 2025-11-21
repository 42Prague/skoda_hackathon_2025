import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { TrendingUp, Target, Sparkles, ArrowRight, Info } from "lucide-react";
import AppLayout from "@/components/AppLayout";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const CareerPath = () => {
  const [selectedRole, setSelectedRole] = useState("senior-engineer");

  const careerRoles = [
    {
      id: "senior-engineer",
      title: "Senior Software Engineer",
      match: 82,
      timeToReady: "6-8 months",
      skills: [
        { name: "Cloud Architecture", current: 45, required: 80 },
        { name: "System Design", current: 52, required: 80 },
        { name: "Leadership", current: 58, required: 75 },
      ],
    },
    {
      id: "tech-lead",
      title: "Technical Lead",
      match: 68,
      timeToReady: "12-15 months",
      skills: [
        { name: "Team Leadership", current: 58, required: 85 },
        { name: "Architecture", current: 52, required: 90 },
        { name: "Project Management", current: 45, required: 80 },
      ],
    },
    {
      id: "staff-engineer",
      title: "Staff Engineer",
      match: 62,
      timeToReady: "18-24 months",
      skills: [
        { name: "Strategic Thinking", current: 48, required: 85 },
        { name: "Cross-team Influence", current: 40, required: 80 },
        { name: "Technical Vision", current: 55, required: 90 },
      ],
    },
  ];

  const currentRole = careerRoles.find((r) => r.id === selectedRole) || careerRoles[0];

  return (
    <AppLayout userType="employee">
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold text-foreground mb-2">Career Path Simulator</h1>
          <p className="text-muted-foreground">
            Explore different career trajectories and required skill investments
          </p>
        </div>

        {/* What-If Simulator */}
        <Card className="shadow-card border-primary/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-primary" />
              What-If Career Simulator
            </CardTitle>
            <CardDescription>
              Select a target role to see required skills and timeline
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div>
                <label className="text-sm font-medium text-foreground mb-2 block">
                  Select Target Role
                </label>
                <Select value={selectedRole} onValueChange={setSelectedRole}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a role" />
                  </SelectTrigger>
                  <SelectContent>
                    {careerRoles.map((role) => (
                      <SelectItem key={role.id} value={role.id}>
                        {role.title} - {role.match}% match
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="p-6 rounded-lg bg-gradient-subtle border border-border">
                <div className="flex items-start gap-6">
                  <div className="flex-1">
                    <h3 className="text-2xl font-bold text-foreground mb-2">
                      {currentRole.title}
                    </h3>
                    <div className="flex items-center gap-3 mb-4">
                      <Badge className="bg-entity-position/10 text-entity-position border-entity-position">
                        {currentRole.match}% Current Match
                      </Badge>
                      <Badge className="bg-entity-course/10 text-entity-course border-entity-course">
                        {currentRole.timeToReady} to ready
                      </Badge>
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    <div className="relative w-24 h-24">
                      <svg className="w-full h-full transform -rotate-90">
                        <circle
                          cx="48"
                          cy="48"
                          r="44"
                          stroke="hsl(var(--muted))"
                          strokeWidth="6"
                          fill="none"
                        />
                        <circle
                          cx="48"
                          cy="48"
                          r="44"
                          stroke="hsl(var(--entity-position))"
                          strokeWidth="6"
                          fill="none"
                          strokeDasharray={`${2 * Math.PI * 44}`}
                          strokeDashoffset={`${2 * Math.PI * 44 * (1 - currentRole.match / 100)}`}
                          className="transition-all duration-1000"
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-xl font-bold text-foreground">
                          {currentRole.match}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-6 space-y-4">
                  <h4 className="font-semibold text-foreground">Required Skill Improvements</h4>
                  {currentRole.skills.map((skill) => {
                    const gap = skill.required - skill.current;
                    return (
                      <div key={skill.name} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-foreground">{skill.name}</span>
                          <span className="text-sm text-muted-foreground">
                            {skill.current}% → {skill.required}% (+{gap}%)
                          </span>
                        </div>
                        <div className="relative">
                          <Progress value={(skill.current / skill.required) * 100} className="h-2" />
                        </div>
                      </div>
                    );
                  })}
                </div>

                <Button className="w-full mt-6" asChild>
                  <a href="/learning-plan">
                    Generate Learning Plan <ArrowRight className="w-4 h-4 ml-2" />
                  </a>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Career Trajectory */}
        <Card className="shadow-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-entity-growth" />
              Recommended Career Trajectory
            </CardTitle>
            <CardDescription>
              AI-optimized path based on your current skills and market trends
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {[
                {
                  role: "Current: Software Engineer",
                  time: "Now",
                  status: "current",
                  readiness: 100,
                },
                {
                  role: "Senior Software Engineer",
                  time: "6-8 months",
                  status: "ready-soon",
                  readiness: 82,
                },
                {
                  role: "Technical Lead",
                  time: "18-20 months",
                  status: "future",
                  readiness: 68,
                },
                {
                  role: "Staff Engineer",
                  time: "30-36 months",
                  status: "future",
                  readiness: 62,
                },
              ].map((stage, index) => (
                <div key={stage.role} className="relative">
                  {index !== 3 && (
                    <div className="absolute left-6 top-12 w-0.5 h-12 bg-border"></div>
                  )}
                  <div className="flex items-start gap-4">
                    <div
                      className={`w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0 ${
                        stage.status === "current"
                          ? "bg-entity-employee text-white"
                          : stage.status === "ready-soon"
                          ? "bg-entity-position text-white"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {index + 1}
                    </div>
                    <div className="flex-1 pt-2">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-foreground">{stage.role}</h4>
                        <Badge
                          variant="outline"
                          className={
                            stage.status === "current"
                              ? "bg-entity-employee/10 text-entity-employee border-entity-employee"
                              : stage.status === "ready-soon"
                              ? "bg-entity-growth/10 text-entity-growth border-entity-growth"
                              : "bg-muted text-muted-foreground"
                          }
                        >
                          {stage.time}
                        </Badge>
                      </div>
                      <Progress value={stage.readiness} className="h-2 mb-2" />
                      <p className="text-sm text-muted-foreground">{stage.readiness}% ready</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* AI Recommendations */}
        <Card className="shadow-card bg-accent border-primary/20">
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-6 h-6 text-primary" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-foreground mb-2">AI Career Insight</h3>
                <p className="text-muted-foreground mb-4">
                  Your current trajectory is strong. To accelerate to Senior Engineer, prioritize
                  cloud certifications and system design courses. The market demand for these skills
                  is projected to grow 45% in the next 2 years.
                </p>
                <div className="flex items-center gap-3">
                  <Button size="sm" asChild>
                    <a href="/recommendations">View Recommendations</a>
                  </Button>
                  <Button variant="outline" size="sm">
                    <Info className="w-4 h-4 mr-2" />
                    How is this calculated?
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
};

export default CareerPath;
