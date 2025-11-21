import {
  Box,
  Grid,
  VStack,
  HStack,
  Text,
  Badge,
  Button,
  Progress,
  Spinner,
  Skeleton,
} from '@chakra-ui/react';
import { Icon } from '../../components/common/Icon';
import {
  Users,
  Target,
  AlertTriangle,
  Award,
  TrendingUp,
  ChevronRight,
  CheckCircle2,
} from 'lucide-react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ZAxis,
} from 'recharts';
import { StatCard } from '../../components/common/StatCard';
import { RiskBadge } from '../../components/common/RiskBadge';
import { motion } from 'motion/react';
import { useNavigate } from 'react-router-dom';
import { useCapability } from '../../hooks/useBackendEndpoints';
import { useMemo } from 'react';

const MotionBox = motion.create(Box);

const DEMO_TEAM_ID = 'SE';

export const TeamCapabilityDashboard = () => {
  const navigate = useNavigate();
  const { data: capability, isLoading, error } = useCapability(DEMO_TEAM_ID);

  // Transform backend data to match chart requirements
  const capabilityData = useMemo(() => {
    if (!capability?.capability_vector) {
      // Fallback data with all zeros
      return [
        { dimension: 'Skill Coverage', current: 0, target: 90 },
        { dimension: 'Skill Diversity', current: 0, target: 85 },
        { dimension: 'Skill Depth', current: 0, target: 85 },
        { dimension: 'Skill Distribution', current: 0, target: 90 },
        { dimension: 'Requirement Alignment', current: 0, target: 90 },
        { dimension: 'Skill Maturity', current: 0, target: 85 },
      ];
    }

    const vector = capability.capability_vector;
    return [
      { dimension: 'Skill Coverage', current: Math.round(vector.skill_coverage || 0), target: 90 },
      { dimension: 'Skill Diversity', current: Math.round(vector.skill_diversity || 0), target: 85 },
      { dimension: 'Skill Depth', current: Math.round(vector.skill_depth || 0), target: 85 },
      { dimension: 'Skill Distribution', current: Math.round(vector.skill_distribution || 0), target: 90 },
      { dimension: 'Requirement Alignment', current: Math.round(vector.requirement_alignment || 0), target: 90 },
      { dimension: 'Skill Maturity', current: Math.round(vector.skill_maturity || 0), target: 85 },
    ];
  }, [capability]);

  // Transform skill coverage to risk matrix format
  const riskMatrixData = useMemo(() => {
    if (!capability?.skill_coverage) return [];

    const skillCoverage = capability.skill_coverage || {};
    const criticalGaps = capability.team_summary?.critical_gaps || [];
    
    return Object.entries(skillCoverage)
      .map(([skill, coverage]: [string, any]) => {
        const coverageNum = typeof coverage === 'number' ? coverage : parseFloat(coverage) || 0;
        // Calculate criticality based on coverage (inverse relationship)
        const criticality = Math.max(50, 100 - coverageNum);
        // Estimate severity based on coverage
        let severity: 'critical' | 'high' | 'medium' | 'low' = 'low';
        if (coverageNum < 30) severity = 'critical';
        else if (coverageNum < 50) severity = 'high';
        else if (coverageNum < 70) severity = 'medium';

        // Check if mentioned in critical gaps
        const isCritical = criticalGaps.some((gap: string) => gap.toLowerCase().includes(skill.toLowerCase()));
        if (isCritical) severity = 'critical';

        return {
          skill,
          supply: Math.round(coverageNum),
          criticality: Math.round(criticality),
          employees: Math.ceil((capability.team_summary?.total_employees || 20) * (coverageNum / 100)),
          severity,
        };
      })
      .slice(0, 8) // Top 8 skills for visualization
      .sort((a, b) => b.criticality - a.criticality);
  }, [capability]);

  // Generate action recommendations from backend data
  const topActions = useMemo(() => {
    if (!capability?.team_summary?.critical_gaps) {
      return [];
    }

    const gaps = capability.team_summary.critical_gaps.slice(0, 3);
    return gaps.map((gap: string, idx: number) => {
      const isCritical = idx === 0;
      return {
        priority: isCritical ? 'critical' : 'high',
        title: gap.includes('coverage') ? `Address skill gap: ${gap}` : `Action required: ${gap}`,
        impact: `+${15 - idx * 3}% team capability`,
        timeline: 'Complete within 30 days',
        cost: 'TBD',
      };
    });
  }, [capability]);

  // Extract team summary for stats
  const teamSummary = capability?.team_summary || {};
  const capabilityScore = capability?.capability_score || 0;
  const avgCoverage = capability?.avg_coverage || 0;

  const getSeverityColor = (severity: string) => {
    if (severity === 'critical') return '#dc2626';
    if (severity === 'high') return '#f59e0b';
    if (severity === 'medium') return '#eab308';
    return '#4da944';
  };

  // Loading state
  if (isLoading) {
    return (
      <VStack spacing={6} align="stretch">
        <Box>
          <Skeleton height="40px" width="300px" mb={2} />
          <Skeleton height="20px" width="400px" />
        </Box>
        <Grid templateColumns="repeat(4, 1fr)" gap={4}>
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} height="120px" borderRadius="lg" />
          ))}
        </Grid>
        <Grid templateColumns="1fr 1fr" gap={6}>
          <Skeleton height="400px" borderRadius="lg" />
          <Skeleton height="400px" borderRadius="lg" />
        </Grid>
      </VStack>
    );
  }

  // Error state
  if (error) {
    return (
      <VStack spacing={6} align="stretch">
        <Box p={4} bg="red.50" border="1px solid" borderColor="red.200" borderRadius="lg">
          <HStack mb={2}>
            <Icon as={AlertTriangle} w={5} h={5} color="red.600" />
            <Text fontWeight="semibold" color="red.800">Failed to load team capability data</Text>
          </HStack>
          <Text fontSize="sm" color="red.700" ml={7}>
            {error instanceof Error ? error.message : 'An unexpected error occurred. Please try again later.'}
          </Text>
        </Box>
      </VStack>
    );
  }

  return (
    <VStack spacing={6} align="stretch">
      {/* Header */}
      <Box>
        <Text fontSize="3xl" fontWeight="semibold">
          Team Capability Dashboard
        </Text>
        <Text color="gray.600" mt={1}>
          Team {DEMO_TEAM_ID} · {teamSummary.total_employees || 0} members · Updated just now
        </Text>
      </Box>

      {/* KPI Cards */}
      <Grid templateColumns="repeat(4, 1fr)" gap={4}>
        <StatCard
          label="Team Members"
          value={teamSummary.total_employees || 0}
          icon={Users}
          badge={<Badge colorScheme="blue">Team {DEMO_TEAM_ID}</Badge>}
        />
        <StatCard
          label="Capability Score"
          value={`${Math.round(capabilityScore)}%`}
          icon={Target}
          badge={<Badge colorScheme={capabilityScore >= 70 ? 'green' : capabilityScore >= 50 ? 'orange' : 'red'}>
            {capability?.capability_level_name || 'Unknown'}
          </Badge>}
        />
        <StatCard
          label="Avg Skill Coverage"
          value={`${Math.round(avgCoverage)}%`}
          icon={Target}
          badge={<Badge colorScheme={avgCoverage >= 70 ? 'green' : 'orange'}>Coverage</Badge>}
        />
        <StatCard
          label="Critical Gaps"
          value={teamSummary.critical_gaps?.length || 0}
          icon={AlertTriangle}
          badge={<Badge colorScheme="red">Action Needed</Badge>}
        />
      </Grid>

          {/* Hero Section: Radar + Risk Matrix */}
      <Grid templateColumns="1fr 1fr" gap={6}>
        {/* Team Capability Radar */}
        <MotionBox
          bg="white"
          p={6}
          borderRadius="lg"
          border="1px solid"
          borderColor="gray.200"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <HStack justify="space-between" mb={5}>
            <Box>
              <Text fontSize="xl" fontWeight="semibold">
                Team Capability Profile
              </Text>
              <Text fontSize="xs" color="gray.600" mt={1}>
                6-dimensional team strength assessment
              </Text>
            </Box>
            <Badge colorScheme="green" fontSize="sm" px={3} py={1}>
              {Math.round(capabilityScore)}% Overall
            </Badge>
          </HStack>

          {capabilityData.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <RadarChart data={capabilityData}>
                <PolarGrid stroke="#e5e7eb" />
                <PolarAngleAxis
                  dataKey="dimension"
                  tick={{ fontSize: 11, fill: '#4b5563' }}
                />
                <PolarRadiusAxis
                  angle={90}
                  domain={[0, 100]}
                  tick={{ fontSize: 10 }}
                />
                <Radar
                  name="Current"
                  dataKey="current"
                  stroke="#4da944"
                  fill="#4da944"
                  fillOpacity={0.6}
                />
                <Radar
                  name="Target"
                  dataKey="target"
                  stroke="#0d1b2a"
                  fill="#0d1b2a"
                  fillOpacity={0.2}
                  strokeDasharray="5 5"
                />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          ) : (
            <Box height="320px" display="flex" alignItems="center" justifyContent="center">
              <Text color="gray.500">No capability data available</Text>
            </Box>
          )}

          <HStack justify="center" spacing={6} mt={4} fontSize="xs">
            <HStack>
              <Box w={3} h={3} bg="skoda.green" borderRadius="full" />
              <Text>Current Level</Text>
            </HStack>
            <HStack>
              <Box w={3} h={3} bg="skoda.navy" borderRadius="full" opacity={0.3} />
              <Text>Target Level</Text>
            </HStack>
          </HStack>
        </MotionBox>

        {/* Skill Risk Matrix (2x2) */}
        <MotionBox
          bg="white"
          p={6}
          borderRadius="lg"
          border="1px solid"
          borderColor="gray.200"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <HStack justify="space-between" mb={5}>
            <Box>
              <Text fontSize="xl" fontWeight="semibold">
                Skill Risk Matrix
              </Text>
              <Text fontSize="xs" color="gray.600" mt={1}>
                Supply vs Criticality (bubble size = affected employees)
              </Text>
            </Box>
            <Button
              size="sm"
              variant="outline"
              rightIcon={<Icon as={ChevronRight} w={4} h={4} />}
              onClick={() => navigate('/risk-radar')}
            >
              View Radar
            </Button>
          </HStack>

          {riskMatrixData.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  type="number"
                  dataKey="supply"
                  name="Supply"
                  domain={[0, 100]}
                  tick={{ fontSize: 11 }}
                  label={{ value: 'Supply →', position: 'bottom', style: { fontSize: 11 } }}
                />
                <YAxis
                  type="number"
                  dataKey="criticality"
                  name="Criticality"
                  domain={[0, 100]}
                  tick={{ fontSize: 11 }}
                  label={{ value: '← Criticality', angle: -90, position: 'left', style: { fontSize: 11 } }}
                />
                <ZAxis type="number" dataKey="employees" range={[100, 1000]} />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  content={({ payload }: any) => {
                    if (payload && payload.length > 0) {
                      const data = payload[0].payload;
                      return (
                        <Box bg="white" p={3} borderRadius="md" boxShadow="lg" border="1px solid" borderColor="gray.200">
                          <Text fontWeight="semibold" fontSize="sm">{data.skill}</Text>
                          <Text fontSize="xs" color="gray.600">Supply: {data.supply}%</Text>
                          <Text fontSize="xs" color="gray.600">Criticality: {data.criticality}%</Text>
                          <Text fontSize="xs" color="gray.600">{data.employees} employees</Text>
                        </Box>
                      );
                    }
                    return null;
                  }}
                />
                <Scatter data={riskMatrixData}>
                  {riskMatrixData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getSeverityColor(entry.severity)} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          ) : (
            <Box height="320px" display="flex" alignItems="center" justifyContent="center">
              <Text color="gray.500">No skill data available</Text>
            </Box>
          )}

          <HStack justify="center" spacing={4} mt={4} fontSize="xs">
            <HStack><Box w={3} h={3} bg="#dc2626" borderRadius="full" /><Text>Critical</Text></HStack>
            <HStack><Box w={3} h={3} bg="#f59e0b" borderRadius="full" /><Text>High</Text></HStack>
            <HStack><Box w={3} h={3} bg="#eab308" borderRadius="full" /><Text>Medium</Text></HStack>
            <HStack><Box w={3} h={3} bg="#4da944" borderRadius="full" /><Text>Low</Text></HStack>
          </HStack>
        </MotionBox>
      </Grid>

      {/* Top 3 Action Recommendations */}
      <MotionBox
        bg="white"
        p={6}
        borderRadius="lg"
        border="1px solid"
        borderColor="gray.200"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <HStack justify="space-between" mb={5}>
          <HStack>
            <Icon as={TrendingUp} w={5} h={5} color="skoda.green" />
            <Text fontSize="xl" fontWeight="semibold">
              Top 3 Recommended Actions
            </Text>
          </HStack>
          <Text fontSize="xs" color="gray.600">
            AI-ranked by impact and urgency
          </Text>
        </HStack>

        <VStack spacing={3} align="stretch">
          {topActions.length > 0 ? (
            topActions.map((action, idx) => (
            <Box
              key={idx}
              p={4}
              bg={action.priority === 'critical' ? 'red.50' : 'orange.50'}
              borderRadius="lg"
              border="1px solid"
              borderColor={action.priority === 'critical' ? 'red.200' : 'orange.200'}
            >
              <HStack justify="space-between" mb={2}>
                <HStack spacing={3} flex={1}>
                  <RiskBadge level={action.priority as any} />
                  <Box flex={1}>
                    <Text fontWeight="semibold" fontSize="sm">
                      {action.title}
                    </Text>
                    <HStack spacing={4} mt={1} fontSize="xs" color="gray.600">
                      <HStack>
                        <Icon as={TrendingUp} w={3} h={3} />
                        <Text>{action.impact}</Text>
                      </HStack>
                      <HStack>
                        <Icon as={CheckCircle2} w={3} h={3} />
                        <Text>{action.timeline}</Text>
                      </HStack>
                      <Text>Cost: {action.cost}</Text>
                    </HStack>
                  </Box>
                </HStack>
                <Button size="sm" colorScheme="brand">
                  Take Action
                </Button>
              </HStack>
            </Box>
            ))
          ) : (
            <Box p={4} bg="gray.50" borderRadius="lg" textAlign="center">
              <Text color="gray.500" fontSize="sm">No action recommendations available</Text>
            </Box>
          )}
        </VStack>
      </MotionBox>

      {/* Quick Navigation */}
      <Grid templateColumns="repeat(4, 1fr)" gap={4}>
        <Button
          h="auto"
          py={4}
          variant="outline"
          justifyContent="space-between"
          onClick={() => navigate('/risk-radar')}
        >
          <VStack align="start" spacing={1}>
            <Text fontWeight="semibold" fontSize="sm">Risk Radar</Text>
            <Text fontSize="xs" color="gray.600">View detailed risk analysis</Text>
          </VStack>
          <Icon as={ChevronRight} w={5} h={5} />
        </Button>

        <Button
          h="auto"
          py={4}
          variant="outline"
          justifyContent="space-between"
          onClick={() => navigate('/promotion-readiness')}
        >
          <VStack align="start" spacing={1}>
            <Text fontWeight="semibold" fontSize="sm">Promotion Readiness</Text>
            <Text fontSize="xs" color="gray.600">View promotion candidates</Text>
          </VStack>
          <Icon as={ChevronRight} w={5} h={5} />
        </Button>

        <Button
          h="auto"
          py={4}
          variant="outline"
          justifyContent="space-between"
          onClick={() => navigate('/heatmap')}
        >
          <VStack align="start" spacing={1}>
            <Text fontWeight="semibold" fontSize="sm">Skills Heatmap</Text>
            <Text fontSize="xs" color="gray.600">Full team matrix</Text>
          </VStack>
          <Icon as={ChevronRight} w={5} h={5} />
        </Button>

        <Button
          h="auto"
          py={4}
          variant="outline"
          justifyContent="space-between"
          onClick={() => navigate('/employees/1')}
        >
          <VStack align="start" spacing={1}>
            <Text fontWeight="semibold" fontSize="sm">Employee Profiles</Text>
            <Text fontSize="xs" color="gray.600">Individual details</Text>
          </VStack>
          <Icon as={ChevronRight} w={5} h={5} />
        </Button>
      </Grid>
    </VStack>
  );
};
