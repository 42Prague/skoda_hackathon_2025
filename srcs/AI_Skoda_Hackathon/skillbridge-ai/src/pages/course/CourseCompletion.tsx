import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CheckCircle2, Download, ArrowRight, Lightbulb, TrendingUp, Award } from "lucide-react";

export default function CourseCompletion() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const courseName = searchParams.get("course") || "Advanced Data Analytics";

  const completionData = {
    skillImprovements: [
      { name: "Data Analysis", before: 45, after: 78 },
      { name: "Python", before: 40, after: 72 },
      { name: "Statistical Modeling", before: 35, after: 68 },
      { name: "Visualization", before: 50, after: 82 },
    ],
    strengths: [
      "Strong grasp of foundational data analysis concepts",
      "Excellent practical application of Python and Pandas",
      "Clear and effective data visualization skills",
      "Good understanding of statistical methods",
    ],
    nextSkills: [
      { name: "Machine Learning Basics", relevance: "High", duration: "6 weeks" },
      { name: "Advanced SQL", relevance: "Medium", duration: "4 weeks" },
      { name: "Cloud Computing Fundamentals", relevance: "Medium", duration: "5 weeks" },
    ],
    relevanceChange: { before: 68, after: 85 },
  };

  return (
    <div className="min-h-screen bg-gradient-subtle">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Celebration Header */}
          <Card className="shadow-lg border-primary/20">
            <CardContent className="pt-12 pb-8 text-center">
              <div className="mb-6 flex justify-center">
                <div className="relative">
                  <div className="w-24 h-24 rounded-full bg-primary/10 flex items-center justify-center">
                    <CheckCircle2 className="w-12 h-12 text-primary" />
                  </div>
                  <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                    <Award className="w-5 h-5 text-primary-foreground" />
                  </div>
                </div>
              </div>
              
              <h1 className="text-4xl font-bold mb-3">Course Completed!</h1>
              <p className="text-lg text-muted-foreground mb-6">
                Congratulations on completing <span className="text-primary font-medium">{courseName}</span>
              </p>
              
              <Badge className="text-base px-4 py-2">
                100% Complete
              </Badge>
            </CardContent>
          </Card>

          {/* Skill Improvements */}
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-primary" />
                Your Skill Improvements
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {completionData.skillImprovements.map((skill) => (
                  <div key={skill.name}>
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium">{skill.name}</span>
                      <div className="flex items-center gap-3 text-sm">
                        <span className="text-muted-foreground">{skill.before}%</span>
                        <ArrowRight className="w-4 h-4 text-primary" />
                        <span className="text-primary font-medium">{skill.after}%</span>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <Progress value={skill.before} className="h-2 bg-muted" />
                        <p className="text-xs text-muted-foreground mt-1">Before</p>
                      </div>
                      <div>
                        <Progress value={skill.after} className="h-2" />
                        <p className="text-xs text-muted-foreground mt-1">After</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* AI Learning Summary */}
          <Card className="shadow-card border-primary/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-primary" />
                AI Learning Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Strengths */}
              <div>
                <h3 className="font-medium mb-3">Your Strengths</h3>
                <div className="space-y-2">
                  {completionData.strengths.map((strength, index) => (
                    <div key={index} className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                      <p className="text-sm text-foreground">{strength}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Skill Relevance Change */}
              <div className="p-4 bg-primary/5 rounded-lg border border-primary/20">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium">Predicted Skill Relevance</h3>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">
                      {completionData.relevanceChange.before}%
                    </span>
                    <ArrowRight className="w-4 h-4 text-primary" />
                    <span className="text-lg font-bold text-primary">
                      {completionData.relevanceChange.after}%
                    </span>
                  </div>
                </div>
                <Progress value={completionData.relevanceChange.after} className="h-2 mb-2" />
                <p className="text-xs text-muted-foreground">
                  Your skills are now {completionData.relevanceChange.after - completionData.relevanceChange.before}% 
                  more relevant for the next 5 years
                </p>
              </div>

              {/* Recommended Next Skills */}
              <div>
                <h3 className="font-medium mb-3">Recommended Next Skills</h3>
                <div className="space-y-3">
                  {completionData.nextSkills.map((skill) => (
                    <div 
                      key={skill.name}
                      className="p-4 rounded-lg border border-border hover:border-primary/50 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h4 className="font-medium">{skill.name}</h4>
                        <Badge 
                          variant="secondary" 
                          className={
                            skill.relevance === "High" 
                              ? "bg-primary/10 text-primary" 
                              : "bg-muted"
                          }
                        >
                          {skill.relevance} Fit
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">{skill.duration}</p>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button 
              variant="outline"
              onClick={() => navigate("/employee")}
              className="w-full"
            >
              Return to Dashboard
            </Button>
            
            <Button 
              variant="outline"
              className="w-full"
            >
              <Download className="w-4 h-4 mr-2" />
              Download Certificate
            </Button>

            <Button 
              onClick={() => navigate("/employee")}
              className="w-full"
            >
              Explore Courses
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
