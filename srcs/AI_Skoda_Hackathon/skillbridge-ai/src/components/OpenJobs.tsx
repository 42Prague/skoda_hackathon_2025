import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Briefcase, MapPin, Clock, Building2, Loader2, ExternalLink } from "lucide-react";
import { jobPositionsAPI } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface JobPosition {
  id: string;
  title: string;
  description?: string;
  department?: string;
  location?: string;
  employmentType?: string;
  status: string;
  requiredExperience?: string;
  postedAt: string;
  closingDate?: string;
  skills: Array<{
    skill: {
      id: string;
      name: string;
      category: string;
    };
    requiredLevel: number;
    weight: number;
    isRequired: boolean;
  }>;
  _count?: {
    applications: number;
  };
}

const OpenJobs = () => {
  const { toast } = useToast();
  const [jobPositions, setJobPositions] = useState<JobPosition[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchJobPositions = async () => {
      try {
        setIsLoading(true);
        const data = await jobPositionsAPI.getJobPositions('OPEN');
        setJobPositions(data.jobPositions || []);
      } catch (error: any) {
        console.error('Failed to fetch job positions:', error);
        toast({
          title: "Error",
          description: error.message || "Failed to load open positions",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchJobPositions();
  }, [toast]);

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
      });
    } catch {
      return dateString;
    }
  };

  if (isLoading) {
    return (
      <Card className="shadow-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-primary" />
            Open Job Positions
          </CardTitle>
          <CardDescription>Available career opportunities</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-primary" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (jobPositions.length === 0) {
    return (
      <Card className="shadow-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-primary" />
            Open Job Positions
          </CardTitle>
          <CardDescription>Available career opportunities</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <Briefcase className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No open positions available at the moment.</p>
            <p className="text-sm mt-2">Check back later for new opportunities.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="shadow-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Briefcase className="w-5 h-5 text-primary" />
          Open Job Positions
        </CardTitle>
        <CardDescription>
          {jobPositions.length} {jobPositions.length === 1 ? 'position' : 'positions'} available
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {jobPositions.map((job) => (
            <div
              key={job.id}
              className="p-4 rounded-lg border bg-card hover:bg-muted/30 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h4 className="font-semibold text-foreground text-lg mb-1">
                    {job.title}
                  </h4>
                  {job.description && (
                    <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
                      {job.description}
                    </p>
                  )}
                  <div className="flex flex-wrap gap-2 items-center text-sm text-muted-foreground">
                    {job.department && (
                      <div className="flex items-center gap-1">
                        <Building2 className="w-4 h-4" />
                        <span>{job.department}</span>
                      </div>
                    )}
                    {job.location && (
                      <div className="flex items-center gap-1">
                        <MapPin className="w-4 h-4" />
                        <span>{job.location}</span>
                      </div>
                    )}
                    {job.employmentType && (
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        <span>{job.employmentType}</span>
                      </div>
                    )}
                  </div>
                </div>
                <Badge variant="outline" className="ml-2 bg-primary/10 text-primary border-primary/20">
                  Open
                </Badge>
              </div>

              {job.skills && job.skills.length > 0 && (
                <div className="mb-3">
                  <p className="text-xs text-muted-foreground mb-2">Required Skills:</p>
                  <div className="flex flex-wrap gap-2">
                    {job.skills.slice(0, 5).map((jobSkill, idx) => (
                      <Badge
                        key={idx}
                        variant="secondary"
                        className="text-xs"
                      >
                        {jobSkill.skill.name}
                        {jobSkill.requiredLevel && (
                          <span className="ml-1 text-muted-foreground">
                            ({Math.round(jobSkill.requiredLevel)}%)
                          </span>
                        )}
                      </Badge>
                    ))}
                    {job.skills.length > 5 && (
                      <Badge variant="secondary" className="text-xs">
                        +{job.skills.length - 5} more
                      </Badge>
                    )}
                  </div>
                </div>
              )}

              <div className="flex items-center justify-between pt-3 border-t">
                <div className="text-xs text-muted-foreground">
                  <span>Posted: {formatDate(job.postedAt)}</span>
                  {job.closingDate && (
                    <span className="ml-3">
                      Closes: {formatDate(job.closingDate)}
                    </span>
                  )}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="gap-2"
                  onClick={() => {
                    // TODO: Navigate to job details or show application modal
                    toast({
                      title: "Job Details",
                      description: `Viewing details for ${job.title}`,
                    });
                  }}
                >
                  View Details
                  <ExternalLink className="w-3 h-3" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default OpenJobs;

