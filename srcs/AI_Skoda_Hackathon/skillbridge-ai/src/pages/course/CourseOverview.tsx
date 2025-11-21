import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BookOpen, CheckCircle2, Lock, PlayCircle, FileText, Award } from "lucide-react";

export default function CourseOverview() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const courseName = searchParams.get("course") || "Advanced Data Analytics";

  const courseData = {
    title: courseName,
    description: "Master the fundamentals and advanced techniques of data analytics to stay relevant in the evolving automotive industry.",
    duration: "4 weeks",
    skillsImproved: ["Data Analysis", "Python", "Statistical Modeling", "Visualization"],
    modules: [
      { id: 1, type: "lesson", title: "Introduction to Data Analytics", status: "unlocked", icon: BookOpen },
      { id: 2, type: "lesson", title: "Working with Python & Pandas", status: "unlocked", icon: BookOpen },
      { id: 3, type: "quiz", title: "Knowledge Check: Basics", status: "locked", icon: PlayCircle },
      { id: 4, type: "lesson", title: "Statistical Analysis Methods", status: "locked", icon: BookOpen },
      { id: 5, type: "assignment", title: "Practical Assignment: Data Project", status: "locked", icon: FileText },
      { id: 6, type: "lesson", title: "Data Visualization & Reporting", status: "locked", icon: BookOpen },
      { id: 7, type: "quiz", title: "Final Assessment", status: "locked", icon: PlayCircle },
      { id: 8, type: "summary", title: "Course Summary & Certificate", status: "locked", icon: Award },
    ],
  };

  return (
    <div className="min-h-screen bg-gradient-subtle">
      <div className="container mx-auto px-4 py-8">
        <Button 
          variant="ghost" 
          onClick={() => navigate("/employee")}
          className="mb-6"
        >
          ← Back to Dashboard
        </Button>

        <div className="max-w-4xl mx-auto">
          {/* Course Header */}
          <Card className="mb-6 shadow-card">
            <CardHeader>
              <CardTitle className="text-3xl">{courseData.title}</CardTitle>
              <p className="text-muted-foreground mt-2">{courseData.description}</p>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-6 mb-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <BookOpen className="w-4 h-4" />
                  <span>{courseData.duration}</span>
                </div>
              </div>
              
              <div>
                <h3 className="text-sm font-medium mb-2">Skills You'll Improve:</h3>
                <div className="flex flex-wrap gap-2">
                  {courseData.skillsImproved.map((skill) => (
                    <Badge key={skill} variant="secondary" className="bg-primary/10 text-primary">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Course Structure */}
          <Card className="mb-6 shadow-card">
            <CardHeader>
              <CardTitle>Course Structure</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {courseData.modules.map((module, index) => {
                  const Icon = module.icon;
                  const isLocked = module.status === "locked";
                  const isCompleted = module.status === "completed";

                  return (
                    <div
                      key={module.id}
                      className={`flex items-center gap-4 p-4 rounded-lg border transition-colors ${
                        isLocked 
                          ? "bg-muted/30 border-border/50" 
                          : "bg-background border-border hover:border-primary/50"
                      }`}
                    >
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        isCompleted 
                          ? "bg-primary text-primary-foreground" 
                          : isLocked
                          ? "bg-muted text-muted-foreground"
                          : "bg-primary/10 text-primary"
                      }`}>
                        {isCompleted ? (
                          <CheckCircle2 className="w-5 h-5" />
                        ) : isLocked ? (
                          <Lock className="w-5 h-5" />
                        ) : (
                          <Icon className="w-5 h-5" />
                        )}
                      </div>
                      
                      <div className="flex-1">
                        <h4 className={`font-medium ${isLocked ? "text-muted-foreground" : ""}`}>
                          {module.title}
                        </h4>
                        <p className="text-xs text-muted-foreground capitalize">
                          {module.type} • {module.status === "locked" ? "Locked" : module.status === "completed" ? "Completed" : "Ready to start"}
                        </p>
                      </div>

                      {isCompleted && (
                        <Badge variant="secondary" className="bg-primary/10 text-primary">
                          Completed
                        </Badge>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Begin Course Button */}
          <div className="flex justify-center">
            <Button 
              size="lg" 
              className="px-8"
              onClick={() => navigate(`/course/lesson?course=${encodeURIComponent(courseName)}&module=1`)}
            >
              Begin Course
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
