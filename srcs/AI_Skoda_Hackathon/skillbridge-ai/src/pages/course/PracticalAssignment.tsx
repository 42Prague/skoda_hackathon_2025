import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { CheckCircle2, Upload, Lightbulb, ChevronRight, FileText } from "lucide-react";

export default function PracticalAssignment() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const courseName = searchParams.get("course") || "Advanced Data Analytics";
  const currentModule = parseInt(searchParams.get("module") || "5");
  
  const [submission, setSubmission] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const assignment = {
    title: "Data Analysis Project",
    description: "Apply your newly learned skills to analyze a real-world dataset from Škoda's manufacturing process. Your task is to identify trends, anomalies, and provide actionable insights.",
    requirements: [
      "Analyze the provided dataset using Python and Pandas",
      "Create at least 3 meaningful visualizations",
      "Identify key trends and patterns in the data",
      "Provide 3-5 actionable recommendations based on your findings",
    ],
    score: 87,
  };

  const handleSubmit = () => {
    setSubmitted(true);
  };

  const handleNext = () => {
    navigate(`/course/lesson?course=${encodeURIComponent(courseName)}&module=${currentModule + 1}`);
  };

  const progress = (currentModule / 8) * 100;

  return (
    <div className="min-h-screen bg-gradient-subtle">
      <div className="container mx-auto px-4 py-6">
        <Button 
          variant="ghost" 
          onClick={() => navigate("/employee")}
          className="mb-4"
        >
          ← Exit Course
        </Button>

        <div className="max-w-3xl mx-auto">
          {/* Progress Bar */}
          <Card className="mb-6 shadow-card">
            <CardContent className="pt-6">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-muted-foreground">Course Progress</span>
                <span className="font-medium">{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} className="h-2" />
            </CardContent>
          </Card>

          {/* Assignment Card */}
          <Card className="shadow-card">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Module {currentModule} of 8</p>
                  <CardTitle className="text-2xl">{assignment.title}</CardTitle>
                </div>
                <Badge variant="secondary" className="bg-primary/10 text-primary">
                  Assignment
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Description */}
              <div>
                <h3 className="font-medium mb-2">Assignment Brief</h3>
                <p className="text-sm text-muted-foreground">
                  {assignment.description}
                </p>
              </div>

              {/* Requirements */}
              <div>
                <h3 className="font-medium mb-3">Requirements</h3>
                <div className="space-y-2">
                  {assignment.requirements.map((req, index) => (
                    <div key={index} className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                      <p className="text-sm text-foreground">{req}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Submission Area */}
              {!submitted ? (
                <div className="space-y-4">
                  <div>
                    <h3 className="font-medium mb-3">Your Submission</h3>
                    <Textarea
                      placeholder="Paste your analysis, findings, and recommendations here..."
                      value={submission}
                      onChange={(e) => setSubmission(e.target.value)}
                      className="min-h-[200px] resize-none"
                    />
                  </div>

                  <div className="flex items-center gap-4 p-4 border-2 border-dashed border-border rounded-lg hover:border-primary/50 transition-colors cursor-pointer">
                    <Upload className="w-5 h-5 text-muted-foreground" />
                    <div className="flex-1">
                      <p className="text-sm font-medium">Upload Files (Optional)</p>
                      <p className="text-xs text-muted-foreground">
                        Attach your Python scripts, datasets, or visualizations
                      </p>
                    </div>
                    <Button variant="outline" size="sm">
                      Browse
                    </Button>
                  </div>

                  <Button 
                    onClick={handleSubmit} 
                    disabled={!submission.trim()}
                    className="w-full"
                  >
                    Submit Assignment
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* AI Feedback */}
                  <Card className="border-2 border-primary bg-primary/5">
                    <CardHeader>
                      <CardTitle className="text-lg flex items-center gap-2">
                        <Lightbulb className="w-5 h-5 text-primary" />
                        AI-Generated Feedback
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex items-start gap-2 text-primary">
                        <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5" />
                        <p className="font-medium">Excellent work! Assignment submitted successfully.</p>
                      </div>

                      <div className="space-y-3 text-sm text-foreground">
                        <p>
                          <strong>Strengths:</strong> Your analysis demonstrates a solid understanding of data analytics 
                          principles. The visualizations are clear and effectively communicate key trends. Your 
                          recommendations are actionable and well-justified.
                        </p>
                        
                        <p>
                          <strong>Areas for Improvement:</strong> Consider exploring more advanced statistical methods 
                          for deeper insights. Additional context around industry benchmarks would strengthen your 
                          recommendations.
                        </p>

                        <p>
                          <strong>Key Skills Demonstrated:</strong> Data manipulation, statistical analysis, 
                          visualization, critical thinking, and business communication.
                        </p>
                      </div>

                      <div className="pt-3 border-t">
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-sm font-medium">Your Score</p>
                          <Badge className="text-base px-3 py-1">
                            {assignment.score}/100
                          </Badge>
                        </div>
                        <Progress value={assignment.score} className="h-2" />
                      </div>

                      <div className="flex items-center gap-2 p-3 bg-background rounded-lg border">
                        <FileText className="w-4 h-4 text-primary" />
                        <p className="text-xs text-muted-foreground">
                          Your submission and feedback have been saved to your learning portfolio
                        </p>
                      </div>
                    </CardContent>
                  </Card>

                  <Button onClick={handleNext} className="w-full">
                    Continue to Next Module
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
