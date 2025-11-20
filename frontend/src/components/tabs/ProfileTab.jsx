import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function ProfileTab({ profile, isLoading, selectedRoleId, roles = [] }) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading profile...</div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">
          Select an employee to view their profile
        </div>
      </div>
    );
  }

  const { employee, skills = [], qualifications = [] } = profile;

  return (
    <div className="space-y-6">
      {/* Employee Info */}
      <Card>
        <CardHeader>
          <CardTitle>Employee Information</CardTitle>
          <CardDescription>Current position and details</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                Employee ID
              </p>
              <p className="text-base">{employee.user_name}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                Personal Number
              </p>
              <p className="text-base">{employee.personal_number}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                Current Profession
              </p>
              <p className="text-base">{employee.profession || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                {selectedRoleId ? 'Target Role' : 'Planned Position'}
              </p>
              <p className="text-base">
                {selectedRoleId 
                  ? roles.find(r => r.role_id === selectedRoleId)?.name || 'N/A'
                  : employee.planned_position || 'N/A'
                }
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Skills */}
      <Card>
        <CardHeader>
          <CardTitle>My Skills</CardTitle>
          <CardDescription>
            Skills acquired from courses and learning activities
          </CardDescription>
        </CardHeader>
        <CardContent>
          {skills.length > 0 ? (
            <div className="space-y-3">
              {skills.slice(0, 10).map((skill, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{skill.name}</span>
                    <Badge variant="secondary" className="text-xs">
                      {skill.source}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    {skill.count && (
                      <span className="text-sm text-muted-foreground">
                        {skill.count}x
                      </span>
                    )}
                    <div className="w-24 h-2 bg-secondary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary"
                        style={{
                          width: `${Math.min(100, (skill.count || 1) * 20)}%`,
                        }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No skills data available</p>
          )}
        </CardContent>
      </Card>

      {/* Qualifications */}
      <Card>
        <CardHeader>
          <CardTitle>My Qualifications</CardTitle>
          <CardDescription>Active certifications and qualifications</CardDescription>
        </CardHeader>
        <CardContent>
          {qualifications.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {qualifications.map((qual, index) => (
                <Badge
                  key={index}
                  variant={qual.active ? 'default' : 'outline'}
                  className="text-sm"
                >
                  {qual.name}
                </Badge>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              No qualifications data available
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
