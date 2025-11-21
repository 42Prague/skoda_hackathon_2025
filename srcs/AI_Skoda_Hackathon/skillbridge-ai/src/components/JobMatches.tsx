/**
 * Job Matches Component
 * Displays job matches with three-tier classification:
 * - Perfect Match (≥85%): Selected for Interview
 * - Middle Match (50-84%): Courses Suggested
 * - Low Match (<50%): Roadmap Suggested
 */

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  CheckCircle2, 
  BookOpen, 
  TrendingUp, 
  AlertCircle,
  MapPin,
  Building2,
  ExternalLink,
  Loader2,
  Award,
  Target
} from "lucide-react";
import { dashboardAPI } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";

interface JobMatch {
  jobPositionId: string;
  jobTitle: string;
  jobDescription?: string;
  department?: string;
  location?: string;
  fitnessScore: number;
  matchTier: 'HIGH' | 'MIDDLE' | 'LOW';
  recommendedAction: 'INTERVIEW' | 'COURSES' | 'ROADMAP';
  skillGaps: Array<{
    skillName: string;
    currentLevel: number;
    requiredLevel: number;
    gap: number;
  }>;
  recommendedCourses?: string[];
}

interface JobMatchesProps {
  userId: string;
}

const JobMatches: React.FC<JobMatchesProps> = ({ userId }) => {
  const { toast } = useToast();
  const { user } = useAuth();
  const [matches, setMatches] = useState<JobMatch[]>([]);
  const [perfectMatches, setPerfectMatches] = useState<JobMatch[]>([]);
  const [middleMatches, setMiddleMatches] = useState<JobMatch[]>([]);
  const [lowMatches, setLowMatches] = useState<JobMatch[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [applyingJobId, setApplyingJobId] = useState<string | null>(null);

  useEffect(() => {
    const fetchMatches = async () => {
      try {
        setIsLoading(true);
        const data = await dashboardAPI.getJobMatches(userId);
        setMatches(data.matches || []);
        setPerfectMatches(data.perfectMatches || []);
        setMiddleMatches(data.middleMatches || []);
        setLowMatches(data.lowMatches || []);
      } catch (error: any) {
        console.error('Failed to fetch job matches:', error);
        toast({
          title: "Error",
          description: error.message || "Failed to load job matches",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    if (userId) {
      fetchMatches();
    }
  }, [userId, toast]);

  const handleApplyForJob = async (jobPositionId: string) => {
    if (!userId) return;

    try {
      setApplyingJobId(jobPositionId);
      const result = await dashboardAPI.applyForJob(userId, jobPositionId);
      
      toast({
        title: "Application Submitted",
        description: result.message || "Your application has been submitted successfully",
      });

      // Refresh matches to update status
      const data = await dashboardAPI.getJobMatches(userId);
      setMatches(data.matches || []);
      setPerfectMatches(data.perfectMatches || []);
      setMiddleMatches(data.middleMatches || []);
      setLowMatches(data.lowMatches || []);
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to submit application",
        variant: "destructive",
      });
    } finally {
      setApplyingJobId(null);
    }
  };

  const getMatchTierBadge = (tier: string, fitnessScore: number) => {
    if (tier === 'HIGH') {
      return (
        <Badge className="bg-green-100 text-green-800 border-green-300">
          <CheckCircle2 className="w-3 h-3 mr-1" />
          Perfect Match ({fitnessScore}%)
        </Badge>
      );
    } else if (tier === 'MIDDLE') {
      return (
        <Badge className="bg-yellow-100 text-yellow-800 border-yellow-300">
          <BookOpen className="w-3 h-3 mr-1" />
          Middle Match ({fitnessScore}%)
        </Badge>
      );
    } else {
      return (
        <Badge className="bg-orange-100 text-orange-800 border-orange-300">
          <TrendingUp className="w-3 h-3 mr-1" />
          Low Match ({fitnessScore}%)
        </Badge>
      );
    }
  };

  const renderMatchCard = (match: JobMatch, isApplying: boolean) => {
    return (
      <Card key={match.jobPositionId} className="shadow-card hover:shadow-lg transition-shadow">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="text-lg mb-2">{match.jobTitle}</CardTitle>
              <div className="flex items-center gap-2 mb-2">
                {getMatchTierBadge(match.matchTier, match.fitnessScore)}
              </div>
              {match.department && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                  <Building2 className="w-4 h-4" />
                  {match.department}
                </div>
              )}
              {match.location && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <MapPin className="w-4 h-4" />
                  {match.location}
                </div>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Fitness Score */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Fitness Score</span>
              <span className="text-sm font-bold">{match.fitnessScore}%</span>
            </div>
            <Progress value={match.fitnessScore} className="h-2" />
          </div>

          {/* Description */}
          {match.jobDescription && (
            <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
              {match.jobDescription}
            </p>
          )}

          {/* Recommended Action */}
          {match.matchTier === 'HIGH' && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
              <div className="flex items-start gap-2">
                <Award className="w-5 h-5 text-green-600 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-semibold text-green-900 mb-1">Selected for Interview!</h4>
                  <p className="text-sm text-green-700">
                    Your skills match this position perfectly. You've been selected for an interview.
                  </p>
                </div>
              </div>
              <Button
                className="w-full mt-3 bg-green-600 hover:bg-green-700"
                onClick={() => handleApplyForJob(match.jobPositionId)}
                disabled={isApplying && applyingJobId === match.jobPositionId}
              >
                {isApplying && applyingJobId === match.jobPositionId ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Applying...
                  </>
                ) : (
                  <>
                    Apply for Interview
                    <ExternalLink className="w-4 h-4 ml-2" />
                  </>
                )}
              </Button>
            </div>
          )}

          {match.matchTier === 'MIDDLE' && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
              <div className="flex items-start gap-2">
                <BookOpen className="w-5 h-5 text-yellow-600 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-semibold text-yellow-900 mb-1">Courses Suggested</h4>
                  <p className="text-sm text-yellow-700 mb-2">
                    Complete recommended courses to improve your fit for this position.
                  </p>
                  {match.recommendedCourses && match.recommendedCourses.length > 0 && (
                    <p className="text-xs text-yellow-600">
                      {match.recommendedCourses.length} course(s) recommended
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {match.matchTier === 'LOW' && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-4">
              <div className="flex items-start gap-2">
                <Target className="w-5 h-5 text-orange-600 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-semibold text-orange-900 mb-1">Growth Roadmap Suggested</h4>
                  <p className="text-sm text-orange-700">
                    A personalized roadmap will help you develop the skills needed for this position.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Skill Gaps */}
          {match.skillGaps.length > 0 && (
            <div className="mt-4">
              <h5 className="text-sm font-semibold mb-2">Top Skill Gaps</h5>
              <div className="space-y-2">
                {match.skillGaps.slice(0, 3).map((gap, idx) => (
                  <div key={idx} className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">{gap.skillName}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground">
                        {gap.currentLevel}/{gap.requiredLevel}
                      </span>
                      <Badge variant="outline" className="text-xs">
                        Gap: {gap.gap}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  if (isLoading) {
    return (
      <Card className="shadow-card">
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    );
  }

  if (matches.length === 0) {
    return (
      <Card className="shadow-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5 text-primary" />
            Job Matches
          </CardTitle>
          <CardDescription>Find open positions that match your skills</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <AlertCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No job matches found.</p>
            <p className="text-sm mt-2">Check back later for new opportunities.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-8">
      {/* Perfect Matches */}
      {perfectMatches.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle2 className="w-5 h-5 text-green-600" />
            <h2 className="text-2xl font-bold">Perfect Matches</h2>
            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-300">
              {perfectMatches.length}
            </Badge>
          </div>
          <p className="text-muted-foreground mb-4">
            These positions are an excellent fit for your skills. You've been selected for an interview!
          </p>
          <div className="grid md:grid-cols-2 gap-4">
            {perfectMatches.map(match => renderMatchCard(match, true))}
          </div>
        </div>
      )}

      {/* Middle Matches */}
      {middleMatches.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <BookOpen className="w-5 h-5 text-yellow-600" />
            <h2 className="text-2xl font-bold">Middle Matches</h2>
            <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-300">
              {middleMatches.length}
            </Badge>
          </div>
          <p className="text-muted-foreground mb-4">
            Complete recommended courses to improve your fit for these positions.
          </p>
          <div className="grid md:grid-cols-2 gap-4">
            {middleMatches.map(match => renderMatchCard(match, true))}
          </div>
        </div>
      )}

      {/* Low Matches */}
      {lowMatches.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-orange-600" />
            <h2 className="text-2xl font-bold">Growth Opportunities</h2>
            <Badge variant="outline" className="bg-orange-50 text-orange-700 border-orange-300">
              {lowMatches.length}
            </Badge>
          </div>
          <p className="text-muted-foreground mb-4">
            A personalized roadmap will help you develop the skills needed for these positions.
          </p>
          <div className="grid md:grid-cols-2 gap-4">
            {lowMatches.map(match => renderMatchCard(match, true))}
          </div>
        </div>
      )}
    </div>
  );
};

export default JobMatches;

