import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Brain, ArrowLeft, Users, AlertTriangle, TrendingUp, Target } from "lucide-react";
import { useNavigate } from "react-router-dom";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from "recharts";

const ManagerDashboard = () => {
  const navigate = useNavigate();
  const [selectedEmployee, setSelectedEmployee] = useState<number | null>(null);

  const teamData = [
    { id: 1, name: "Jan Novák", role: "Software Engineer", relevance: 82, risk: "Low", learning: 65, futureRole: "Senior Engineer" },
    { id: 2, name: "Petra Svobodová", role: "UX Designer", relevance: 75, risk: "Medium", learning: 45, futureRole: "Lead Designer" },
    { id: 3, name: "Martin Dvořák", role: "Data Analyst", relevance: 68, risk: "Medium", learning: 30, futureRole: "Data Scientist" },
    { id: 4, name: "Lucie Veselá", role: "Product Owner", relevance: 55, risk: "High", learning: 20, futureRole: "Senior PO" },
    { id: 5, name: "Tomáš Černý", role: "DevOps Engineer", relevance: 88, risk: "Low", learning: 80, futureRole: "DevOps Lead" },
  ];

  const riskDistribution = [
    { risk: "Low Risk", count: 2, color: "hsl(var(--risk-low))" },
    { risk: "Medium Risk", count: 2, color: "hsl(var(--risk-medium))" },
    { risk: "High Risk", count: 1, color: "hsl(var(--risk-high))" },
  ];

  const employeeDetails = selectedEmployee ? teamData.find(e => e.id === selectedEmployee) : null;

  const employeeSkills = [
    { skill: 'Technical', value: 85 },
    { skill: 'Leadership', value: 65 },
    { skill: 'Communication', value: 78 },
    { skill: 'Problem Solving', value: 82 },
    { skill: 'Innovation', value: 70 },
    { skill: 'Digital', value: 88 }
  ];

  const getRiskBadge = (risk: string) => {
    const variants = {
      Low: "bg-risk-low/10 text-risk-low border-risk-low",
      Medium: "bg-risk-medium/10 text-risk-medium border-risk-medium",
      High: "bg-risk-high/10 text-risk-high border-risk-high",
    };
    return variants[risk as keyof typeof variants];
  };

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
                <div className="w-10 h-10 rounded-lg bg-gradient-secondary flex items-center justify-center">
                  <Users className="w-6 h-6 text-secondary-foreground" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-foreground">Manager Dashboard</h1>
                  <p className="text-xs text-muted-foreground">Team Analytics & Planning</p>
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
            <h2 className="text-3xl font-bold text-foreground mb-2">Team Overview</h2>
            <p className="text-muted-foreground">Monitor your team's skills and plan for the future</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <Card className="shadow-card">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total Team Members</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-foreground">{teamData.length}</div>
              </CardContent>
            </Card>

            <Card className="shadow-card">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Average Relevance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-foreground">
                  {Math.round(teamData.reduce((sum, emp) => sum + emp.relevance, 0) / teamData.length)}%
                </div>
              </CardContent>
            </Card>

            <Card className="shadow-card">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">High Risk Members</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-risk-high">
                  {teamData.filter(e => e.risk === "High").length}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Risk Heatmap */}
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-primary" />
                Team Risk Distribution
              </CardTitle>
              <CardDescription>Overview of skill relevance risk across your team</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={riskDistribution} layout="vertical">
                    <XAxis type="number" tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                    <YAxis dataKey="risk" type="category" tick={{ fill: 'hsl(var(--foreground))' }} width={120} />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '0.5rem'
                      }}
                    />
                    <Bar dataKey="count" radius={[0, 8, 8, 0]}>
                      {riskDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Team Table */}
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5 text-primary" />
                Team Skill Overview
              </CardTitle>
              <CardDescription>Click on any employee to view detailed analytics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Relevance Score</TableHead>
                      <TableHead>Risk Level</TableHead>
                      <TableHead>Learning Progress</TableHead>
                      <TableHead>Future Role</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {teamData.map((employee) => (
                      <TableRow key={employee.id} className="cursor-pointer hover:bg-muted/50">
                        <TableCell className="font-medium">{employee.name}</TableCell>
                        <TableCell>{employee.role}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Progress value={employee.relevance} className="w-20" />
                            <span className="text-sm font-medium">{employee.relevance}%</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className={getRiskBadge(employee.risk)}>
                            {employee.risk}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Progress value={employee.learning} className="w-20" />
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">{employee.futureRole}</TableCell>
                        <TableCell>
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => setSelectedEmployee(employee.id)}
                          >
                            View Details
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          {/* Employee Detail View */}
          {employeeDetails && (
            <Card className="shadow-card border-primary/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="w-5 h-5 text-primary" />
                      Employee Details: {employeeDetails.name}
                    </CardTitle>
                    <CardDescription>{employeeDetails.role}</CardDescription>
                  </div>
                  <Button variant="outline" onClick={() => setSelectedEmployee(null)}>
                    Close
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-8">
                  {/* Skills Radar */}
                  <div>
                    <h4 className="font-semibold text-foreground mb-4">Skills Profile</h4>
                    <div className="h-[300px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <RadarChart data={employeeSkills}>
                          <PolarGrid stroke="hsl(var(--border))" />
                          <PolarAngleAxis dataKey="skill" tick={{ fill: 'hsl(var(--foreground))', fontSize: 12 }} />
                          <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                          <Radar name="Skills" dataKey="value" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.3} />
                        </RadarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Details */}
                  <div className="space-y-6">
                    <div>
                      <h4 className="font-semibold text-foreground mb-2">Skill Relevance Score</h4>
                      <div className="flex items-baseline gap-2">
                        <span className="text-4xl font-bold text-foreground">{employeeDetails.relevance}%</span>
                        <Badge variant="outline" className={getRiskBadge(employeeDetails.risk)}>
                          {employeeDetails.risk} Risk
                        </Badge>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold text-foreground mb-2">Recommended Future Role</h4>
                      <p className="text-muted-foreground">{employeeDetails.futureRole}</p>
                    </div>

                    <div>
                      <h4 className="font-semibold text-foreground mb-2">Learning Progress</h4>
                      <Progress value={employeeDetails.learning} className="mb-2" />
                      <p className="text-sm text-muted-foreground">{employeeDetails.learning}% of recommended courses completed</p>
                    </div>

                    <div className="p-4 rounded-lg bg-accent border border-primary/20">
                      <div className="flex items-start gap-3">
                        <Brain className="w-5 h-5 text-primary flex-shrink-0 mt-1" />
                        <div>
                          <h4 className="font-semibold text-foreground mb-1">AI Prediction: 2-Year Skill Risk</h4>
                          <p className="text-sm text-muted-foreground">
                            {employeeDetails.risk === "Low" && "Strong alignment with future needs. Recommend leadership development track to maximize potential."}
                            {employeeDetails.risk === "Medium" && "Solid foundation but requires targeted upskilling. Prioritize emerging technology courses."}
                            {employeeDetails.risk === "High" && "Significant skill gap identified. Urgent reskilling needed in AI/ML and cloud technologies."}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
};

export default ManagerDashboard;
