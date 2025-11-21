import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Brain, ArrowLeft, Users, AlertTriangle, Target, Loader2, LogOut } from "lucide-react";
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
import { useAuth } from "@/contexts/AuthContext";
import { dashboardAPI } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import KnowledgeGraph from "@/components/KnowledgeGraph";

const ManagerDashboardNew = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();
  const { toast } = useToast();
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [selectedEmployee, setSelectedEmployee] = useState<string | null>(null);
  const [employeeDetail, setEmployeeDetail] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  useEffect(() => {
    const fetchDashboard = async () => {
      if (!user?.id) {
        setIsLoading(false);
        return;
      }

      try {
        const data = await dashboardAPI.getManagerDashboard(user.id);
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

  useEffect(() => {
    const fetchEmployeeDetail = async () => {
      if (!selectedEmployee) {
        setEmployeeDetail(null);
        return;
      }

      setIsLoadingDetail(true);
      try {
        const data = await dashboardAPI.getEmployeeDetail(selectedEmployee);
        setEmployeeDetail(data);
      } catch (error: any) {
        console.error('Failed to fetch employee detail:', error);
        toast({
          title: "Error",
          description: error.message || "Failed to load employee details",
          variant: "destructive",
        });
      } finally {
        setIsLoadingDetail(false);
      }
    };

    fetchEmployeeDetail();
  }, [selectedEmployee, toast]);

  const getRiskBadge = (risk: string) => {
    const variants = {
      Low: "bg-risk-low/10 text-risk-low border-risk-low",
      Medium: "bg-risk-medium/10 text-risk-medium border-risk-medium",
      High: "bg-risk-high/10 text-risk-high border-risk-high",
    };
    return variants[risk as keyof typeof variants] || "bg-muted text-muted-foreground";
  };

  const riskDistribution = dashboardData?.riskDistribution?.map((item: any) => ({
    ...item,
    color: item.risk.includes('Low') ? 'hsl(var(--risk-low))' : 
           item.risk.includes('Medium') ? 'hsl(var(--risk-medium))' : 
           'hsl(var(--risk-high))'
  })) || [];

  const employeeSkillsData = employeeDetail?.skills?.slice(0, 6).map((s: any) => ({
    skill: s.skill,
    value: s.level,
  })) || [];

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-subtle flex items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle>Access Denied</CardTitle>
            <CardDescription>Please log in to access this dashboard</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button onClick={() => navigate("/login")} className="w-full">
              Go to Login
            </Button>
            <Button onClick={() => navigate("/")} variant="outline" className="w-full">
              Go to Home
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Allow MANAGER and ADMIN roles, or if no user role is set (for testing)
  if (user?.role && user.role !== 'MANAGER' && user.role !== 'ADMIN') {
    return (
      <div className="min-h-screen bg-gradient-subtle flex items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle>Access Denied</CardTitle>
            <CardDescription>This dashboard is only available to managers. Your role: {user.role}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button onClick={() => navigate("/login")} className="w-full">
              Login as Manager
            </Button>
            <Button onClick={() => navigate("/")} variant="outline" className="w-full">
              Go to Home
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
          <p className="text-muted-foreground">Loading your team dashboard...</p>
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
                <div className="w-10 h-10 rounded-lg bg-gradient-secondary flex items-center justify-center">
                  <Users className="w-6 h-6 text-secondary-foreground" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-foreground">Manager Dashboard</h1>
                  <p className="text-xs text-muted-foreground">Team Analytics & Planning</p>
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
            <h2 className="text-3xl font-bold text-foreground mb-2">Team Overview</h2>
            <p className="text-muted-foreground">Monitor your team's skills and plan for the future</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <Card className="shadow-card">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total Team Members</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-foreground">{dashboardData?.teamSize || 0}</div>
              </CardContent>
            </Card>

            <Card className="shadow-card">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Average Relevance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-foreground">
                  {dashboardData?.avgRelevance || 0}%
                </div>
              </CardContent>
            </Card>

            <Card className="shadow-card">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">High Risk Members</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-risk-high">
                  {dashboardData?.highRiskCount || 0}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Risk Heatmap */}
          {riskDistribution.length > 0 && (
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
                        {riskDistribution.map((entry: any, index: number) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Team Table */}
          {dashboardData?.teamMembers && dashboardData.teamMembers.length > 0 && (
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
                        <TableHead>Employee ID</TableHead>
                        <TableHead>Current Position</TableHead>
                        <TableHead>Relevance Score</TableHead>
                        <TableHead>Risk Level</TableHead>
                        <TableHead>Goal Position</TableHead>
                        <TableHead></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {dashboardData.teamMembers.map((member: any) => {
                        // Use real data from CSV: currentPosition and goalPosition
                        const currentPosition = member.currentPosition || member.position || 'N/A';
                        const goalPosition = member.goalPosition || 'N/A';
                        
                        return (
                          <TableRow key={member.id} className="cursor-pointer hover:bg-muted/50">
                            <TableCell className="font-medium">{member.employeeId || 'N/A'}</TableCell>
                            <TableCell>{currentPosition}</TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <Progress value={member.relevance || 0} className="w-20" />
                                <span className="text-sm font-medium">{member.relevance || 0}%</span>
                              </div>
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline" className={getRiskBadge(member.riskLabel)}>
                                {member.riskLabel}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              {member.goalPositionUrl ? (
                                <a
                                  href={member.goalPositionUrl}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-sm font-medium text-primary hover:underline"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  {goalPosition}
                                </a>
                              ) : (
                                <span className="text-sm font-medium text-foreground">
                                  {goalPosition}
                                </span>
                              )}
                            </TableCell>
                            <TableCell>
                              <Button 
                                size="sm" 
                                variant="outline"
                                onClick={() => setSelectedEmployee(member.id)}
                              >
                                View Details
                              </Button>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Available Positions (Open Jobs) */}
          {dashboardData?.availablePositions && dashboardData.availablePositions.length > 0 && (
            <Card className="shadow-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-primary" />
                  Available Positions (Open Jobs)
                </CardTitle>
                <CardDescription>Current open job positions that team members can apply for</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {dashboardData.availablePositions.map((job: any) => (
                    <div key={job.id} className="p-4 border rounded-lg bg-card hover:bg-muted/30 transition-colors">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-semibold text-lg text-foreground mb-1">{job.title}</h4>
                          <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                            {job.description || 'No description available'}
                          </p>
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            {job.department && (
                              <span className="flex items-center gap-1">
                                <Users className="w-3 h-3" /> {job.department}
                              </span>
                            )}
                            {job.location && (
                              <span className="flex items-center gap-1">
                                📍 {job.location}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Employee Detail View */}
          {selectedEmployee && employeeDetail && (
            <Card className="shadow-card border-primary/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="w-5 h-5 text-primary" />
                      Employee Details: {employeeDetail.user?.name}
                    </CardTitle>
                    <CardDescription>{employeeDetail.user?.role} - {employeeDetail.user?.department}</CardDescription>
                  </div>
                  <Button variant="outline" onClick={() => setSelectedEmployee(null)}>
                    Close
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {isLoadingDetail ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-primary" />
                  </div>
                ) : (
                  <div className="space-y-8">
                    {/* Knowledge Graph */}
                    <KnowledgeGraph
                      courses={employeeDetail.courses || []}
                      education={employeeDetail.education}
                      skills={employeeDetail.skills}
                      employeeName={employeeDetail.user?.name}
                    />
                    
                    <div className="grid md:grid-cols-2 gap-8">
                      {/* Skills Radar */}
                      <div>
                        <h4 className="font-semibold text-foreground mb-4">Skills Profile</h4>
                        {employeeSkillsData.length > 0 ? (
                          <div className="h-[300px]">
                            <ResponsiveContainer width="100%" height="100%">
                              <RadarChart data={employeeSkillsData}>
                                <PolarGrid stroke="hsl(var(--border))" />
                                <PolarAngleAxis dataKey="skill" tick={{ fill: 'hsl(var(--foreground))', fontSize: 12 }} />
                                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                                <Radar name="Skills" dataKey="value" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.3} />
                              </RadarChart>
                            </ResponsiveContainer>
                          </div>
                        ) : (
                          <p className="text-muted-foreground">No skill data available</p>
                        )}
                      </div>

                      {/* Details */}
                      <div className="space-y-6">
                        <div>
                          <h4 className="font-semibold text-foreground mb-2">Risk Analysis</h4>
                          <div className="space-y-2">
                            {employeeDetail.skillRisks && employeeDetail.skillRisks.length > 0 ? (
                              employeeDetail.skillRisks.slice(0, 3).map((risk: any, idx: number) => (
                                <div key={idx} className="flex items-center justify-between p-2 rounded border">
                                  <span className="text-sm">{risk.skillName}</span>
                                  <Badge variant="outline" className={getRiskBadge(risk.riskLabel)}>
                                    {risk.riskLabel}
                                  </Badge>
                                </div>
                              ))
                            ) : (
                              <p className="text-sm text-muted-foreground">No risk data available</p>
                            )}
                          </div>
                        </div>

                        <div>
                          <h4 className="font-semibold text-foreground mb-2">Learning Progress</h4>
                          <div className="space-y-2">
                            {employeeDetail.enrollments && employeeDetail.enrollments.length > 0 ? (
                              employeeDetail.enrollments.slice(0, 3).map((enrollment: any, idx: number) => (
                                <div key={idx} className="space-y-1">
                                  <div className="flex justify-between text-sm">
                                    <span>{enrollment.courseTitle}</span>
                                    <span className="font-medium">{Math.round(enrollment.progress)}%</span>
                                  </div>
                                  <Progress value={enrollment.progress} />
                                </div>
                              ))
                            ) : (
                              <p className="text-sm text-muted-foreground">No enrollments found</p>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
};

export default ManagerDashboardNew;
