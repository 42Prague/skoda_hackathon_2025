import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CheckCircle2, Circle, BookOpen, Clock, FileText, Award, ChevronLeft, ChevronRight, Lightbulb, Play } from "lucide-react";
import { useEmployeeData } from "@/contexts/EmployeeDataContext";
import { toast } from "@/hooks/use-toast";

export default function LessonViewer() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const courseName = searchParams.get("course") || "AWS Cloud Architecture";
  const currentModuleId = parseInt(searchParams.get("module") || "1");
  
  const { getCourse, updateCourseProgress } = useEmployeeData();
  const course = getCourse(courseName);

  useEffect(() => {
    if (course && currentModuleId > 0) {
      const module = course.modules.find(m => m.id === currentModuleId);
      if (module && module.type === "lesson" && !module.completed) {
        // Mark lesson as completed after viewing for 3 seconds
        const timer = setTimeout(() => {
          updateCourseProgress(course.id, currentModuleId, true);
          toast({
            title: "Module Completed! 🎉",
            description: `You've completed: ${module.title}`,
          });
        }, 3000);
        return () => clearTimeout(timer);
      }
    }
  }, [course, currentModuleId, updateCourseProgress]);

  if (!course) {
    return (
      <div className="min-h-screen bg-gradient-subtle flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="p-6 text-center">
            <p className="text-muted-foreground">Course not found</p>
            <Button onClick={() => navigate("/employee")} className="mt-4">
              Return to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const currentModule = course.modules.find(m => m.id === currentModuleId);
  const progress = (course.modules.filter(m => m.completed).length / course.modules.length) * 100;

  const handleNext = () => {
    if (currentModule?.type === "quiz") {
      navigate(`/course/quiz?course=${encodeURIComponent(courseName)}&module=${currentModuleId}`);
    } else if (currentModule?.type === "assignment") {
      navigate(`/course/assignment?course=${encodeURIComponent(courseName)}&module=${currentModuleId}`);
    } else if (currentModule?.type === "summary") {
      navigate(`/course/completion?course=${encodeURIComponent(courseName)}`);
    } else if (currentModuleId < course.modules.length) {
      navigate(`/course/lesson?course=${encodeURIComponent(courseName)}&module=${currentModuleId + 1}`);
    }
  };

  const handlePrevious = () => {
    if (currentModuleId > 1) {
      navigate(`/course/lesson?course=${encodeURIComponent(courseName)}&module=${currentModuleId - 1}`);
    }
  };

  const getModuleIcon = (type: string) => {
    switch (type) {
      case "lesson": return <BookOpen className="w-4 h-4" />;
      case "quiz": return <FileText className="w-4 h-4" />;
      case "assignment": return <FileText className="w-4 h-4" />;
      case "summary": return <Award className="w-4 h-4" />;
      default: return <Circle className="w-4 h-4" />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-subtle">
      <div className="container mx-auto px-4 py-6">
        <Button 
          variant="ghost" 
          onClick={() => navigate("/employee")}
          className="mb-4 hover:bg-muted"
        >
          <ChevronLeft className="w-4 h-4 mr-2" />
          Exit Course
        </Button>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content Viewer */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="shadow-card">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">
                      Module {currentModuleId} of {course.modules.length}
                    </p>
                    <CardTitle className="text-2xl">{currentModule?.title}</CardTitle>
                    {currentModule?.duration && (
                      <div className="flex items-center gap-2 mt-2 text-sm text-muted-foreground">
                        <Clock className="w-4 h-4" />
                        <span>{currentModule.duration}</span>
                      </div>
                    )}
                  </div>
                  <Badge 
                    variant="secondary" 
                    className="bg-entity-course/10 text-entity-course border-entity-course"
                  >
                    {currentModule?.type}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Video Player */}
                {currentModule?.videoUrl ? (
                  <div className="aspect-video bg-black rounded-lg overflow-hidden shadow-lg">
                    <iframe
                      width="100%"
                      height="100%"
                      src={currentModule.videoUrl}
                      title={currentModule.title}
                      frameBorder="0"
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen
                      className="w-full h-full"
                    />
                  </div>
                ) : (
                  <div className="aspect-video bg-muted rounded-lg flex items-center justify-center border border-border">
                    <div className="text-center">
                      <Play className="w-16 h-16 mx-auto mb-2 text-muted-foreground" />
                      <p className="text-sm text-muted-foreground">No video available for this module</p>
                    </div>
                  </div>
                )}

                {/* Lesson Content */}
                <div className="prose prose-sm max-w-none">
                  <h3 className="text-lg font-semibold mb-3 text-foreground">Learning Objectives</h3>
                  <ul className="text-foreground space-y-2">
                    <li>Understand core concepts and terminology</li>
                    <li>Apply best practices in real-world scenarios</li>
                    <li>Build hands-on experience through practical examples</li>
                    <li>Prepare for industry certifications and assessments</li>
                  </ul>

                  <h3 className="text-lg font-semibold mb-3 mt-6 text-foreground">Key Takeaways</h3>
                  <div className="bg-primary/5 border-l-4 border-primary p-4 rounded">
                    <ul className="list-none space-y-2 text-foreground">
                      <li className="flex items-start gap-2">
                        <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                        <span>Master fundamental principles and frameworks</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                        <span>Develop practical skills through hands-on exercises</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                        <span>Learn industry best practices and standards</span>
                      </li>
                    </ul>
                  </div>
                </div>

                {/* Navigation */}
                <div className="flex items-center justify-between pt-6 border-t">
                  <Button
                    variant="outline"
                    onClick={handlePrevious}
                    disabled={currentModuleId === 1}
                  >
                    <ChevronLeft className="w-4 h-4 mr-2" />
                    Previous
                  </Button>
                  <Button
                    onClick={handleNext}
                    disabled={currentModuleId === course.modules.length}
                    className="bg-primary hover:bg-primary/90"
                  >
                    Next Module
                    <ChevronRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Sidebar */}
          <div className="space-y-6">
            {/* Course Progress */}
            <Card className="shadow-card">
              <CardHeader>
                <CardTitle className="text-lg">Course Progress</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-muted-foreground">Overall</span>
                    <span className="text-sm font-medium text-foreground">{Math.round(progress)}%</span>
                  </div>
                  <Progress value={progress} className="h-2" />
                </div>

                <div className="space-y-2">
                  {course.modules.map((module) => (
                    <div
                      key={module.id}
                      className={`flex items-center gap-3 p-2 rounded transition-colors cursor-pointer ${
                        module.id === currentModuleId
                          ? "bg-primary/10 border border-primary/20"
                          : "hover:bg-muted"
                      }`}
                      onClick={() =>
                        navigate(`/course/lesson?course=${encodeURIComponent(courseName)}&module=${module.id}`)
                      }
                    >
                      <div className={`${module.completed ? "text-entity-growth" : "text-muted-foreground"}`}>
                        {module.completed ? (
                          <CheckCircle2 className="w-5 h-5" />
                        ) : (
                          getModuleIcon(module.type)
                        )}
                      </div>
                      <span
                        className={`text-sm flex-1 ${
                          module.id === currentModuleId
                            ? "font-semibold text-primary"
                            : "text-foreground"
                        }`}
                      >
                        {module.title}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Skills Covered */}
            <Card className="shadow-card">
              <CardHeader>
                <CardTitle className="text-lg">Skills You're Building</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {course.skillsImproved.map((skill) => (
                    <Badge
                      key={skill}
                      variant="outline"
                      className="bg-entity-skill/10 text-entity-skill border-entity-skill"
                    >
                      {skill}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* AI Notes */}
            <Card className="shadow-card bg-gradient-subtle">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Lightbulb className="w-5 h-5 text-primary" />
                  AI Learning Notes
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  This module aligns well with your career goal of becoming a Senior Engineer. 
                  Focus on practical implementation to close your {course.skillsImproved[0]} skill gap by 15%.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
