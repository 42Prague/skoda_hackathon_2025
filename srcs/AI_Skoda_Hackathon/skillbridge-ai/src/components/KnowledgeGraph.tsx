/**
 * Knowledge Graph Component
 * Visualizes employee courses, skills, and education as an interactive graph
 */

import { useMemo, useRef, useEffect } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { GraduationCap, BookOpen, Award } from 'lucide-react';

interface Course {
  code: string;
  name: string;
  startDate?: string | null;
  endDate?: string | null;
}

interface Education {
  educationCategory?: string | null;
  fieldOfStudy?: string | null;
  basicBranch?: string | null;
}

interface KnowledgeGraphProps {
  courses: Course[];
  education?: Education | null;
  skills?: Array<{ skill: string; level: number; category: string }>;
  employeeName?: string;
}

// Map courses to skills (same logic as backend)
function mapCourseToSkills(courseName: string): string[] {
  const courseUpper = courseName.toUpperCase();
  const skills = new Set<string>();
  
  const mappings: Record<string, string[]> = {
    'ISMS': ['Technical Skills', 'Digital'],
    'IT': ['Technical Skills', 'Digital'],
    'OUTLOOK': ['Technical Skills', 'Communication'],
    'EXCEL': ['Technical Skills'],
    'WORD': ['Technical Skills'],
    'POWERPOINT': ['Technical Skills', 'Communication'],
    'OFFICE 365': ['Technical Skills', 'Digital'],
    'CLOUD': ['Technical Skills', 'Digital', 'Innovation'],
    'AI': ['Technical Skills', 'Digital', 'Innovation'],
    'ROBOT': ['Technical Skills', 'Innovation'],
    'DIGITAL': ['Digital'],
    'INTERNET': ['Digital', 'Technical Skills'],
    'COMPUTER': ['Technical Skills'],
    'NETWORK': ['Technical Skills'],
    'BIG DATA': ['Technical Skills', 'Digital', 'Innovation'],
    'VIRTUAL REALITY': ['Technical Skills', 'Innovation'],
    'CONNECTED CAR': ['Technical Skills', 'Innovation'],
    'COMMUNICATION': ['Communication'],
    'TEAM': ['Teamwork'],
    'LEADERSHIP': ['Teamwork', 'Communication'],
    'AGILE': ['Teamwork', 'Adaptability', 'Innovation'],
    'TIME MANAGEMENT': ['Time Management'],
    'STRESS': ['Time Management', 'Adaptability'],
    'MENTORING': ['Communication', 'Teamwork'],
    'COACHING': ['Communication', 'Teamwork'],
    'INNOVATION': ['Innovation'],
    'TRANSFORMATION': ['Innovation', 'Adaptability'],
    'CHANGE': ['Adaptability'],
    'FUTURE': ['Innovation', 'Adaptability'],
    'ENGLISH': ['Communication'],
    'GERMAN': ['Communication'],
    'JAZYKOVÝ TEST': ['Communication'],
    'LANGUAGE': ['Communication'],
    'COMPLIANCE': ['Communication', 'Time Management'],
    'GDPR': ['Digital', 'Technical Skills'],
    'PRIVACY': ['Digital'],
  };
  
  for (const [keyword, skillList] of Object.entries(mappings)) {
    if (courseUpper.includes(keyword)) {
      skillList.forEach(skill => skills.add(skill));
    }
  }
  
  // Default skills for IT-related courses
  if (skills.size === 0 && (
    courseUpper.includes('IT') || 
    courseUpper.includes('TECHNIC') ||
    courseUpper.includes('DIGIT') ||
    courseUpper.includes('COMPUTER') ||
    courseUpper.includes('SYSTÉM') ||
    courseUpper.includes('SYSTEM')
  )) {
    skills.add('Technical Skills');
    skills.add('Digital');
  }
  
  return Array.from(skills);
}

export default function KnowledgeGraph({ courses, education, skills, employeeName }: KnowledgeGraphProps) {
  const graphRef = useRef<any>();
  
  // Build graph data structure
  const graphData = useMemo(() => {
    const nodes: Array<{ id: string; type: 'employee' | 'course' | 'skill' | 'education'; label: string; size?: number; color?: string }> = [];
    const links: Array<{ source: string; target: string; type?: string }> = [];
    const nodeMap = new Map<string, any>();
    
    // Add employee node (center)
    const employeeId = 'employee';
    nodes.push({
      id: employeeId,
      type: 'employee',
      label: employeeName || 'Employee',
      size: 20,
      color: '#3b82f6', // Primary blue
    });
    nodeMap.set(employeeId, { type: 'employee' });
    
    // Add education node if available
    if (education) {
      const educationId = 'education';
      const educationLabel = [
        education.educationCategory,
        education.fieldOfStudy,
        education.basicBranch,
      ].filter(Boolean).join(' / ') || 'Education';
      
      nodes.push({
        id: educationId,
        type: 'education',
        label: educationLabel,
        size: 15,
        color: '#10b981', // Green
      });
      nodeMap.set(educationId, { type: 'education' });
      links.push({ source: employeeId, target: educationId, type: 'has_education' });
    }
    
    // Process courses and their skills
    const skillCounts = new Map<string, number>();
    const courseSkillMap = new Map<string, Set<string>>();
    
    courses.forEach((course, index) => {
      const courseId = `course_${index}`;
      const courseLabel = course.name.length > 30 
        ? course.name.substring(0, 27) + '...' 
        : course.name;
      
      nodes.push({
        id: courseId,
        type: 'course',
        label: courseLabel,
        size: 8,
        color: '#8b5cf6', // Purple
      });
      nodeMap.set(courseId, { type: 'course', course });
      
      // Link course to employee
      links.push({ source: employeeId, target: courseId, type: 'completed' });
      
      // Map course to skills
      const courseSkills = mapCourseToSkills(course.name);
      courseSkillMap.set(courseId, new Set(courseSkills));
      
      courseSkills.forEach(skill => {
        skillCounts.set(skill, (skillCounts.get(skill) || 0) + 1);
      });
    });
    
    // Add skill nodes (only skills that appear in courses)
    skillCounts.forEach((count, skillName) => {
      const skillId = `skill_${skillName}`;
      
      // Get skill level from props if available
      const skillData = skills?.find(s => s.skill === skillName);
      const skillLevel = skillData?.level || Math.min(count * 10, 100);
      
      nodes.push({
        id: skillId,
        type: 'skill',
        label: skillName,
        size: 6 + (count * 2), // Size based on frequency
        color: skillLevel >= 70 ? '#10b981' : skillLevel >= 40 ? '#f59e0b' : '#ef4444', // Green/Amber/Red
      });
      nodeMap.set(skillId, { type: 'skill', level: skillLevel });
      
      // Link skill to employee
      links.push({ source: employeeId, target: skillId, type: 'has_skill' });
      
      // Link courses to skills
      courseSkillMap.forEach((courseSkills, courseId) => {
        if (courseSkills.has(skillName)) {
          links.push({ source: courseId, target: skillId, type: 'teaches' });
        }
      });
    });
    
    return { nodes, links };
  }, [courses, education, skills, employeeName]);
  
  // Handle node hover
  const handleNodeHover = (node: any) => {
    if (graphRef.current) {
      graphRef.current.getGraph().nodeRelSize = node ? 1.5 : 1;
    }
  };
  
  // Node paint function for custom styling
  const nodePaint = (node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const label = node.label || node.id;
    const size = node.size || 5;
    
    // Draw node circle
    ctx.beginPath();
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI, false);
    ctx.fillStyle = node.color || '#666';
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2 / globalScale;
    ctx.stroke();
    
    // Draw label
    if (globalScale > 0.5) {
      ctx.fillStyle = '#333';
      ctx.font = `${12 / globalScale}px Sans-Serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(label, node.x, node.y + size + 12 / globalScale);
    }
  };
  
  if (courses.length === 0 && !education) {
    return (
      <Card className="shadow-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GraduationCap className="w-5 h-5 text-primary" />
            Knowledge Graph
          </CardTitle>
          <CardDescription>Course and skill visualization</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            No course or education data available for this employee.
          </p>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card className="shadow-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <GraduationCap className="w-5 h-5 text-primary" />
          Knowledge Graph
        </CardTitle>
        <CardDescription>
          Interactive visualization of courses, skills, and education
          {courses.length > 0 && ` • ${courses.length} courses`}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Legend */}
          <div className="flex flex-wrap gap-4 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <span>Employee</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span>Education</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-purple-500"></div>
              <span>Course</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-400"></div>
              <span>Skill (High)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-amber-500"></div>
              <span>Skill (Medium)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span>Skill (Low)</span>
            </div>
          </div>
          
          {/* Graph */}
          <div className="border rounded-lg overflow-hidden" style={{ height: '500px' }}>
            <ForceGraph2D
              ref={graphRef}
              graphData={graphData}
              nodeLabel={(node: any) => `${node.label}\n${node.type}`}
              nodeColor={(node: any) => node.color || '#666'}
              linkColor={() => 'rgba(0, 0, 0, 0.2)'}
              linkWidth={1}
              nodeRelSize={8}
              onNodeHover={handleNodeHover}
              nodeCanvasObject={nodePaint}
              cooldownTicks={100}
              onEngineStop={() => {
                if (graphRef.current) {
                  graphRef.current.zoomToFit(400, 20);
                }
              }}
            />
          </div>
          
          {/* Summary Stats */}
          <div className="grid grid-cols-3 gap-4 pt-4 border-t">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">{courses.length}</div>
              <div className="text-xs text-muted-foreground">Courses</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {new Set(graphData.nodes.filter((n: any) => n.type === 'skill').map((n: any) => n.label)).size}
              </div>
              <div className="text-xs text-muted-foreground">Skills</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">{education ? 1 : 0}</div>
              <div className="text-xs text-muted-foreground">Degrees</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

