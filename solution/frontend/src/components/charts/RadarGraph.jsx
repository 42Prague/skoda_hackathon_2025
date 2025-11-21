import { Box, Card, Typography, useTheme, useMediaQuery, Alert, CircularProgress, Tooltip } from '@mui/material';
import { useState, useMemo } from 'react';

/**
 * RadarGraph Component
 * 
 * A reusable radar/spider chart component following ŠKODA Flow Design System guidelines.
 * Uses SVG for rendering to ensure compatibility with the Flow theme.
 * 
 * @param {Object} props
 * @param {Array} props.data - Array of data points: [{ label: string, value: number, max?: number }, ...]
 * @param {Array} props.comparisonData - Optional comparison data for overlay: [{ label: string, value: number }, ...]
 * @param {string} props.title - Chart title
 * @param {number} props.maxValue - Maximum value for the scale (auto-calculated if not provided)
 * @param {number} props.levels - Number of concentric circles/levels
 * @param {boolean} props.loading - Loading state
 * @param {string} props.error - Error message
 * @param {number} props.size - Chart size (responsive if not provided)
 * @param {string} props.color - Color for the radar area (uses theme primary if not provided)
 */
const RadarGraph = ({
  data = [],
  comparisonData = null,
  title,
  maxValue = null,
  levels = 5,
  loading = false,
  error = null,
  size = null,
  color = null,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));

  // Resolve color from theme if it's a theme color name
  const getColor = () => {
    if (!color) return theme.palette.primary.main;
    if (color === 'primary') return theme.palette.primary.main;
    if (color === 'secondary') return theme.palette.secondary.main;
    if (color === 'error') return theme.palette.error.main;
    if (color === 'warning') return theme.palette.warning.main;
    if (color === 'info') return theme.palette.info.main;
    if (color === 'success') return theme.palette.success.main;
    // If it's a direct color value (hex, rgb, etc.), use it as is
    return color;
  };

  // Calculate responsive dimensions
  const chartSize = size || (isMobile ? 280 : isTablet ? 400 : 500);
  const center = chartSize / 2;
  const radius = center - 60; // Leave space for labels

  // Calculate max value if not provided (consider both data and comparisonData)
  const calculatedMaxValue = useMemo(() => {
    if (maxValue !== null) return maxValue;
    if (data.length === 0) return 100;
    const allValues = [
      ...data.map((point) => (point.max !== undefined ? point.max : point.value)),
      ...data.map((point) => point.value),
    ];
    if (comparisonData && comparisonData.length > 0) {
      allValues.push(...comparisonData.map((point) => point.value));
    }
    return Math.max(...allValues) * 1.1; // Add 10% padding
  }, [data, comparisonData, maxValue]);

  // Calculate angles for each data point
  const angleStep = (2 * Math.PI) / data.length;

  // Convert data point to polar coordinates
  const getPoint = (index, value) => {
    const angle = index * angleStep - Math.PI / 2; // Start from top
    const normalizedValue = Math.min(value / calculatedMaxValue, 1);
    const distance = radius * normalizedValue;
    const x = center + distance * Math.cos(angle);
    const y = center + distance * Math.sin(angle);
    return { x, y, angle };
  };

  // Generate path for the radar area
  const generatePath = () => {
    if (data.length === 0) return '';
    const points = data.map((point, index) => getPoint(index, point.value));
    return points
      .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`)
      .join(' ') + ' Z';
  };

  // Generate path for comparison data (Jira actual usage)
  const generateComparisonPath = () => {
    if (!comparisonData || comparisonData.length === 0) return '';
    const points = comparisonData.map((point, index) => getPoint(index, point.value));
    return points
      .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`)
      .join(' ') + ' Z';
  };

  // Generate path for grid circles
  const generateGridCircles = () => {
    const circles = [];
    for (let i = 1; i <= levels; i++) {
      const levelRadius = (radius * i) / levels;
      circles.push(
        <circle
          key={i}
          cx={center}
          cy={center}
          r={levelRadius}
          fill="none"
          stroke={theme.palette.divider}
          strokeWidth={1}
        />
      );
    }
    return circles;
  };

  // Generate grid lines (spokes)
  const generateGridLines = () => {
    return data.map((_, index) => {
      const point = getPoint(index, calculatedMaxValue);
      return (
        <line
          key={index}
          x1={center}
          y1={center}
          x2={point.x}
          y2={point.y}
          stroke={theme.palette.divider}
          strokeWidth={1}
        />
      );
    });
  };

  // Skill descriptions for tooltips
  const getSkillDescription = (skillName) => {
    const descriptions = {
      'Communication': 'Ability to effectively convey information, ideas, and feedback to team members and stakeholders.',
      'Project Management': 'Skills in planning, organizing, and managing resources to achieve specific project goals.',
      'Problem Solving': 'Capability to identify, analyze, and solve complex problems systematically.',
      'Team Collaboration': 'Effectiveness in working together with others to achieve common objectives.',
      'Analytical Thinking': 'Ability to break down complex information and data into smaller components for analysis.',
      'Leadership': 'Capability to guide, motivate, and influence team members toward achieving goals.',
      'Time Management': 'Skills in organizing and prioritizing tasks to meet deadlines efficiently.',
      'Adaptability': 'Ability to adjust to new conditions, changes, and challenges in the work environment.',
      'Technical Skills': 'Proficiency in using tools, technologies, and methods specific to the job role.',
      'Innovation': 'Capability to generate new ideas, approaches, and creative solutions to challenges.',
    };
    return descriptions[skillName] || 'Skill description not available.';
  };

  // Mock Jira subtask data mapped to skills (based on jira2.json structure)
  const getJiraUsageDetails = (skillName) => {
    const jiraData = {
      'Communication': [
        { project_key: 'ANAL', project_name: 'Analytics System', subtask_key: 'ANAL-2', subtask_title: 'Develop Backend REST API Endpoint', story_points: 5, assignees: ['DZCLPT6'] },
        { project_key: 'DIGI', project_name: 'Digital Service', subtask_key: 'DIGI-3', subtask_title: 'Session Creation and Participant Assignment', story_points: 5, assignees: ['DZCLPT6'] },
      ],
      'Project Management': [
        { project_key: 'ANAL', project_name: 'Analytics System', subtask_key: 'ANAL-1', subtask_title: 'Implement Interactive Dashboard', story_points: 1, assignees: ['DZCLPT6'] },
        { project_key: 'DIGI', project_name: 'Digital Service', subtask_key: 'DIGI-2', subtask_title: 'Session Creation Workflow', story_points: 2, assignees: ['DZCMF39'] },
      ],
      'Problem Solving': [
        { project_key: 'ANAL', project_name: 'Analytics System', subtask_key: 'ANAL-3', subtask_title: 'Implement Skill Gap Visualization', story_points: 3, assignees: ['DZCIS17', 'DZCHM26'] },
        { project_key: 'ANAL', project_name: 'Analytics System', subtask_key: 'ANAL-7', subtask_title: 'Skill Development Progress Visualization', story_points: 3, assignees: ['DZCPS1Z'] },
      ],
      'Team Collaboration': [
        { project_key: 'DIGI', project_name: 'Digital Service', subtask_key: 'DIGI-3', subtask_title: 'Session Creation and Participant Assignment', story_points: 5, assignees: ['DZCLPT6'] },
        { project_key: 'DIGI', project_name: 'Digital Service', subtask_key: 'DIGI-6', subtask_title: 'Role-Based Task Assignment & Progress Visualization', story_points: 2, assignees: ['US1PWZL', 'DZCHM26'] },
      ],
      'Analytical Thinking': [
        { project_key: 'ANAL', project_name: 'Analytics System', subtask_key: 'ANAL-5', subtask_title: 'Department-Wise Career Progression Visualization', story_points: 2, assignees: ['DZCLPT6', 'DZCIS17'] },
        { project_key: 'ANAL', project_name: 'Analytics System', subtask_key: 'ANAL-2', subtask_title: 'Develop Backend REST API Endpoint', story_points: 5, assignees: ['DZCLPT6'] },
      ],
      'Leadership': [
        { project_key: 'ANAL', project_name: 'Analytics System', subtask_key: 'ANAL-2', subtask_title: 'Develop Centralized Dashboard', story_points: 2, assignees: ['DZCIH08', 'DZCLPT6'] },
        { project_key: 'DIGI', project_name: 'Digital Service', subtask_key: 'DIGI-2', subtask_title: 'Career Management Workflow Dashboard', story_points: 5, assignees: ['DZCIH08'] },
      ],
      'Time Management': [
        { project_key: 'ANAL', project_name: 'Analytics System', subtask_key: 'ANAL-4', subtask_title: 'Implement Learning Progress Visualization', story_points: 3, assignees: ['DZCLPT6'] },
        { project_key: 'DIGI', project_name: 'Digital Service', subtask_key: 'DIGI-2', subtask_title: 'Session Creation Workflow', story_points: 2, assignees: ['DZCMF39'] },
      ],
      'Adaptability': [
        { project_key: 'DIGI', project_name: 'Digital Service', subtask_key: 'DIGI-5', subtask_title: 'RBAC and Authentication', story_points: 3, assignees: ['DZCMF39', 'DZCIS17'] },
        { project_key: 'ANAL', project_name: 'Analytics System', subtask_key: 'ANAL-6', subtask_title: 'Skill Development Timeline Visualization', story_points: 5, assignees: ['DZCIS17', 'DZCLPT6'] },
      ],
      'Technical Skills': [
        { project_key: 'ANAL', project_name: 'Analytics System', subtask_key: 'ANAL-2', subtask_title: 'Develop Backend REST API Endpoint', story_points: 5, assignees: ['DZCLPT6'] },
        { project_key: 'ANAL', project_name: 'Analytics System', subtask_key: 'ANAL-3', subtask_title: 'Implement Skill Gap Visualization', story_points: 3, assignees: ['DZCIS17', 'DZCHM26'] },
        { project_key: 'ANAL', project_name: 'Analytics System', subtask_key: 'ANAL-6', subtask_title: 'Skill Development Timeline Visualization', story_points: 5, assignees: ['DZCIS17', 'DZCLPT6'] },
      ],
      'Innovation': [
        { project_key: 'ANAL', project_name: 'Analytics System', subtask_key: 'ANAL-6', subtask_title: 'Skill Development Timeline Visualization', story_points: 5, assignees: ['DZCIS17', 'DZCLPT6'] },
        { project_key: 'ANAL', project_name: 'Analytics System', subtask_key: 'ANAL-7', subtask_title: 'Skill Development Progress Visualization', story_points: 3, assignees: ['DZCPS1Z'] },
      ],
    };
    return jiraData[skillName] || [];
  };

  // Generate labels with tooltips using foreignObject for HTML tooltips
  const generateLabels = () => {
    return data.map((point, index) => {
      const labelPoint = getPoint(index, calculatedMaxValue * 1.15);
      const angle = index * angleStep - Math.PI / 2;
      const textAnchor = Math.abs(Math.cos(angle)) < 0.1 ? 'middle' : Math.cos(angle) > 0 ? 'start' : 'end';
      const dy = Math.abs(Math.sin(angle)) < 0.1 ? '0.35em' : '0';

      const currentValue = point.value;
      const jiraValue = comparisonData && comparisonData[index] ? comparisonData[index].value : null;
      const jiraDetails = getJiraUsageDetails(point.label);

      // Create tooltip content with detailed Jira information
      const tooltipContent = (
        <Box sx={{ p: 1.5, maxWidth: 400 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, color: 'text.primary' }}>
            {point.label}
          </Typography>
          <Typography variant="body2" sx={{ mb: 1.5, color: 'text.secondary', fontSize: '0.875rem' }}>
            {getSkillDescription(point.label)}
          </Typography>
          
          {/* Current vs Jira Usage Values */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75, mt: 1.5, pt: 1.5, borderTop: 1, borderColor: 'divider' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                Current Skills:
              </Typography>
              <Typography variant="caption" sx={{ fontWeight: 600, color: radarColor }}>
                {Math.round(currentValue)}
              </Typography>
            </Box>
            {jiraValue !== null && (
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  Jira Usage:
                </Typography>
                <Typography variant="caption" sx={{ fontWeight: 600, color: '#757575' }}>
                  {Math.round(jiraValue)}
                </Typography>
              </Box>
            )}
          </Box>

          {/* Jira Subtask Details */}
          {jiraDetails && jiraDetails.length > 0 && (
            <Box sx={{ mt: 2, pt: 1.5, borderTop: 1, borderColor: 'divider' }}>
              <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.primary', mb: 1, display: 'block' }}>
                Jira Subtasks:
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {jiraDetails.map((subtask, idx) => (
                  <Box key={idx} sx={{ backgroundColor: 'rgba(0, 0, 0, 0.02)', p: 1, borderRadius: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                      <Typography variant="caption" sx={{ fontWeight: 600, color: '#1976d2' }}>
                        {subtask.project_key}
                      </Typography>
                      <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                        {subtask.subtask_key}
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#757575', fontWeight: 600 }}>
                        {subtask.story_points} pts
                      </Typography>
                    </Box>
                    <Typography variant="caption" sx={{ color: 'text.primary', display: 'block', mb: 0.5 }}>
                      {subtask.subtask_title}
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem', display: 'block' }}>
                      {subtask.project_name}
                    </Typography>
                    {subtask.assignees && subtask.assignees.length > 0 && (
                      <Box sx={{ mt: 0.5, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                        {subtask.assignees.map((assignee, aIdx) => (
                          <Typography key={aIdx} variant="caption" sx={{ color: '#757575', fontSize: '0.7rem' }}>
                            {assignee}
                            {aIdx < subtask.assignees.length - 1 && ', '}
                          </Typography>
                        ))}
                      </Box>
                    )}
                  </Box>
                ))}
              </Box>
            </Box>
          )}
        </Box>
      );

      // Use foreignObject to render HTML with Tooltip inside SVG
      // Calculate foreignObject position based on text anchor
      let foreignX = labelPoint.x;
      let foreignY = labelPoint.y - 12;
      let foreignWidth = 150;
      
      if (textAnchor === 'middle') {
        foreignX = labelPoint.x - 75;
      } else if (textAnchor === 'start') {
        foreignX = labelPoint.x - 10;
      } else {
        foreignX = labelPoint.x - 140;
      }

      return (
        <g key={index}>
          <foreignObject
            x={foreignX}
            y={foreignY}
            width={foreignWidth}
            height="24"
            style={{ overflow: 'visible', pointerEvents: 'all' }}
          >
            <Tooltip
              title={tooltipContent}
              arrow
              placement={textAnchor === 'start' ? 'right' : textAnchor === 'end' ? 'left' : 'top'}
              componentsProps={{
                tooltip: {
                  sx: {
                    maxWidth: 350,
                    backgroundColor: 'background.paper',
                    color: 'text.primary',
                    boxShadow: 3,
                  },
                },
              }}
            >
              <Box
                component="span"
                sx={{
                  display: 'inline-block',
                  cursor: 'pointer',
                  userSelect: 'none',
                  fontSize: isMobile ? 12 : 14,
                  fontWeight: 500,
                  color: theme.palette.text.primary,
                  textAlign: textAnchor === 'middle' ? 'center' : textAnchor === 'start' ? 'left' : 'right',
                  width: '100%',
                  '&:hover': {
                    color: theme.palette.primary.main,
                    textDecoration: 'underline',
                  },
                }}
              >
                {point.label}
              </Box>
            </Tooltip>
          </foreignObject>
        </g>
      );
    });
  };

  // Generate value labels on axes
  const generateValueLabels = () => {
    const labels = [];
    for (let i = 1; i <= levels; i++) {
      const value = (calculatedMaxValue * i) / levels;
      const labelPoint = getPoint(0, value);
      labels.push(
        <text
          key={i}
          x={labelPoint.x - 5}
          y={labelPoint.y}
          textAnchor="end"
          fill={theme.palette.text.secondary}
          fontSize={10}
        >
          {Math.round(value)}
        </text>
      );
    }
    return labels;
  };

  const radarColor = getColor();
  const pathData = generatePath();

  if (loading) {
    return (
      <Card
        sx={{
          p: 3,
          backgroundColor: 'background.paper',
          boxShadow: 2,
          height: '100%',
        }}
      >
        {title && (
          <Typography
            variant="h6"
            component="h3"
            sx={{
              mb: 2,
              color: 'text.primary',
            }}
          >
            {title}
          </Typography>
        )}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: chartSize,
          }}
        >
          <CircularProgress />
        </Box>
      </Card>
    );
  }

  if (error) {
    return (
      <Card
        sx={{
          p: 3,
          backgroundColor: 'background.paper',
          boxShadow: 2,
          height: '100%',
        }}
      >
        {title && (
          <Typography
            variant="h6"
            component="h3"
            sx={{
              mb: 2,
              color: 'text.primary',
            }}
          >
            {title}
          </Typography>
        )}
        <Alert severity="error">Error loading chart: {error}</Alert>
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card
        sx={{
          p: 3,
          backgroundColor: 'background.paper',
          boxShadow: 2,
          height: '100%',
        }}
      >
        {title && (
          <Typography
            variant="h6"
            component="h3"
            sx={{
              mb: 2,
              color: 'text.primary',
            }}
          >
            {title}
          </Typography>
        )}
        <Alert severity="info">No data available for this chart.</Alert>
      </Card>
    );
  }

  return (
    <Card
      sx={{
        p: 3,
        backgroundColor: 'background.paper',
        boxShadow: 2,
        height: '100%',
      }}
    >
      {title && (
        <Typography
          variant="h6"
          component="h3"
          sx={{
            mb: 2,
            color: 'text.primary',
          }}
        >
          {title}
        </Typography>
      )}
      <Box
        sx={{
          width: '100%',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          overflow: 'auto',
        }}
      >
        <svg
          width={chartSize}
          height={chartSize}
          viewBox={`0 0 ${chartSize} ${chartSize}`}
          style={{ maxWidth: '100%', height: 'auto' }}
        >
          {/* Grid circles */}
          {generateGridCircles()}

          {/* Grid lines (spokes) */}
          {generateGridLines()}

          {/* Value labels */}
          {generateValueLabels()}

          {/* Comparison radar area (Jira actual usage) - rendered first so it's behind */}
          {comparisonData && comparisonData.length > 0 && generateComparisonPath() && (
            <>
              <path
                d={generateComparisonPath()}
                fill="#9e9e9e"
                fillOpacity={0.25}
                stroke="#757575"
                strokeWidth={2}
                strokeDasharray="5,5"
              />
              {comparisonData.map((point, index) => {
                const pointCoords = getPoint(index, point.value);
                return (
                  <circle
                    key={`comparison-${index}`}
                    cx={pointCoords.x}
                    cy={pointCoords.y}
                    r={3}
                    fill="#757575"
                    stroke={theme.palette.background.paper}
                    strokeWidth={1.5}
                  />
                );
              })}
            </>
          )}

          {/* Main radar area */}
          {pathData && (
            <path
              d={pathData}
              fill={radarColor}
              fillOpacity={0.3}
              stroke={radarColor}
              strokeWidth={2}
            />
          )}

          {/* Data points */}
          {data.map((point, index) => {
            const pointCoords = getPoint(index, point.value);
            return (
              <circle
                key={index}
                cx={pointCoords.x}
                cy={pointCoords.y}
                r={4}
                fill={radarColor}
                stroke={theme.palette.background.paper}
                strokeWidth={2}
              />
            );
          })}

          {/* Labels */}
          {generateLabels()}
        </svg>
      </Box>

      {/* Legend/Explanation */}
      {comparisonData && comparisonData.length > 0 && (
        <Box
          sx={{
            mt: 3,
            display: 'flex',
            flexDirection: 'column',
            gap: 1.5,
            alignItems: 'center',
          }}
        >
          <Typography
            variant="subtitle2"
            sx={{
              fontWeight: 600,
              color: 'text.primary',
              mb: 0.5,
            }}
          >
            Legend:
          </Typography>
          <Box
            sx={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 3,
              justifyContent: 'center',
              alignItems: 'center',
            }}
          >
            {/* Current Skills Legend */}
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
              }}
            >
              <Box
                sx={{
                  width: 16,
                  height: 16,
                  backgroundColor: radarColor,
                  borderRadius: '50%',
                  border: `2px solid ${radarColor}`,
                }}
              />
              <Typography
                variant="body2"
                sx={{
                  color: 'text.primary',
                }}
              >
                Current Skills Profile
              </Typography>
            </Box>

            {/* Jira Actual Usage Legend */}
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
              }}
            >
              <Box
                sx={{
                  width: 16,
                  height: 16,
                  backgroundColor: '#9e9e9e',
                  borderRadius: '50%',
                  border: '2px dashed #757575',
                  opacity: 0.6,
                }}
              />
              <Typography
                variant="body2"
                sx={{
                  color: 'text.secondary',
                }}
              >
                Jira Actual Skills Usage
              </Typography>
            </Box>
          </Box>
        </Box>
      )}
    </Card>
  );
};

export default RadarGraph;

