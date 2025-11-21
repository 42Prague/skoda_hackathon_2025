import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Skill } from "@/contexts/EmployeeDataContext";

interface SkillCardProps {
  skill: Skill;
  onUpdateLevel?: (newLevel: number) => void;
}

export function SkillCard({ skill, onUpdateLevel }: SkillCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const gap = skill.targetLevel - skill.currentLevel;
  
  const getTrendIcon = () => {
    switch (skill.trend) {
      case "rising": return <TrendingUp className="w-4 h-4 text-entity-growth" />;
      case "declining": return <TrendingDown className="w-4 h-4 text-entity-risk" />;
      default: return <Minus className="w-4 h-4 text-muted-foreground" />;
    }
  };

  const getTrendColor = () => {
    switch (skill.trend) {
      case "rising": return "bg-entity-growth/10 text-entity-growth border-entity-growth";
      case "declining": return "bg-entity-risk/10 text-entity-risk border-entity-risk";
      default: return "bg-muted text-muted-foreground border-muted-foreground";
    }
  };

  return (
    <Card 
      className="shadow-card hover:shadow-md transition-all cursor-pointer"
      onClick={() => setIsExpanded(!isExpanded)}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <CardTitle className="text-lg">{skill.name}</CardTitle>
              <Badge variant="outline" className="bg-entity-skill/10 text-entity-skill border-entity-skill">
                {skill.category}
              </Badge>
            </div>
            <CardDescription>Last updated {skill.lastUpdated}</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className={getTrendColor()}>
              {getTrendIcon()}
              <span className="ml-1 capitalize">{skill.trend}</span>
            </Badge>
            {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current Level */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Current Level</span>
            <span className="text-sm font-bold text-foreground">{skill.currentLevel}%</span>
          </div>
          <Progress value={skill.currentLevel} className="h-2" />
        </div>

        {/* Target Level */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Target Level</span>
            <span className="text-sm font-bold text-entity-position">{skill.targetLevel}%</span>
          </div>
          <Progress value={skill.targetLevel} className="h-2 bg-entity-position/20" />
        </div>

        {/* Gap Indicator */}
        <div className={`p-3 rounded-lg ${gap > 20 ? 'bg-entity-risk/10' : 'bg-entity-growth/10'}`}>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Skill Gap</span>
            <Badge variant="outline" className={gap > 20 ? "bg-entity-risk/10 text-entity-risk border-entity-risk" : "bg-entity-growth/10 text-entity-growth border-entity-growth"}>
              {gap}% to target
            </Badge>
          </div>
        </div>

        {/* Expanded Details */}
        {isExpanded && (
          <div className="pt-4 border-t space-y-3 animate-fade-in">
            <div>
              <h4 className="text-sm font-semibold mb-2">Improvement Actions</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Complete 2-3 advanced courses in this area</li>
                <li>• Work on 1-2 practical projects</li>
                <li>• Seek mentorship from senior experts</li>
              </ul>
            </div>
            
            {onUpdateLevel && (
              <div className="flex gap-2">
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={(e) => {
                    e.stopPropagation();
                    onUpdateLevel(Math.min(100, skill.currentLevel + 5));
                  }}
                >
                  +5% Practice
                </Button>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={(e) => {
                    e.stopPropagation();
                    onUpdateLevel(Math.max(0, skill.currentLevel - 5));
                  }}
                >
                  -5% Decay
                </Button>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
