import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle } from 'lucide-react';

export default function GapsTab({ gaps, isLoading }) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Analyzing gaps...</div>
      </div>
    );
  }

  if (!gaps) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">
          Select both employee and target role to see gaps
        </div>
      </div>
    );
  }

  const {
    role,
    required_qualifications = [],
    employee_qualifications = [],
    missing_qualifications = [],
    employee_skills = [],
    role_skills = [],
    missing_skills = [],
  } = gaps;

  return (
    <div className="space-y-6">
      {/* Target Role Info */}
      <Card>
        <CardHeader>
          <CardTitle>Target Role</CardTitle>
          <CardDescription>{role?.name}</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Role ID: <span className="font-medium text-foreground">{role?.role_id}</span>
          </p>
        </CardContent>
      </Card>

      {/* Gap Summary */}
      {missing_qualifications.length > 0 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-orange-600" />
              <CardTitle className="text-orange-900">Gap Summary</CardTitle>
            </div>
            <CardDescription className="text-orange-700">
              You need {missing_qualifications.length} additional qualification
              {missing_qualifications.length !== 1 ? 's' : ''} for this role
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      {/* Qualifications Comparison */}
      <Card>
        <CardHeader>
          <CardTitle>Qualification Requirements</CardTitle>
          <CardDescription>
            Comparing required qualifications with your current qualifications
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Required Qualifications */}
            <div>
              <h4 className="text-sm font-semibold mb-3 text-muted-foreground">
                Required ({required_qualifications.length})
              </h4>
              <div className="space-y-2">
                {required_qualifications.length > 0 ? (
                  required_qualifications.map((qual, index) => {
                    const isMissing = missing_qualifications.some(
                      (mq) => mq.id === qual.id || mq.name === qual.name
                    );
                    return (
                      <Badge
                        key={index}
                        variant={isMissing ? 'warning' : 'default'}
                        className="w-full justify-start text-left"
                      >
                        {qual.name || qual}
                        {isMissing && ' ⚠️'}
                      </Badge>
                    );
                  })
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No specific qualifications required
                  </p>
                )}
              </div>
            </div>

            {/* Employee Qualifications */}
            <div>
              <h4 className="text-sm font-semibold mb-3 text-muted-foreground">
                My Qualifications ({employee_qualifications.length})
              </h4>
              <div className="space-y-2">
                {employee_qualifications.length > 0 ? (
                  employee_qualifications.map((qual, index) => (
                    <Badge
                      key={index}
                      variant="outline"
                      className="w-full justify-start text-left"
                    >
                      {qual.name || qual}
                    </Badge>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No qualifications on record
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Missing Qualifications Highlight */}
          {missing_qualifications.length > 0 && (
            <div className="mt-6 pt-6 border-t">
              <h4 className="text-sm font-semibold mb-3 text-orange-700">
                Missing Qualifications
              </h4>
              <div className="flex flex-wrap gap-2">
                {missing_qualifications.map((qual, index) => (
                  <Badge key={index} variant="warning">
                    {qual.name || qual}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Skills Comparison (if available) */}
      {(role_skills?.length > 0 || employee_skills?.length > 0) && (
        <Card>
          <CardHeader>
            <CardTitle>Skill Requirements</CardTitle>
            <CardDescription>
              Skills comparison for the target role
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Role Skills */}
              <div>
                <h4 className="text-sm font-semibold mb-3 text-muted-foreground">
                  Role Skills
                </h4>
                <div className="flex flex-wrap gap-2">
                  {role_skills.length > 0 ? (
                    role_skills.map((skill, index) => (
                      <Badge key={index} variant="secondary">
                        {skill}
                      </Badge>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      No specific skills defined
                    </p>
                  )}
                </div>
              </div>

              {/* Employee Skills */}
              <div>
                <h4 className="text-sm font-semibold mb-3 text-muted-foreground">
                  My Skills
                </h4>
                <div className="flex flex-wrap gap-2">
                  {employee_skills.length > 0 ? (
                    employee_skills.slice(0, 10).map((skill, index) => (
                      <Badge key={index} variant="outline">
                        {skill.name || skill}
                      </Badge>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      No skills on record
                    </p>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
