import {
  Box,
  Grid,
  VStack,
  HStack,
  Text,
  Badge,
  Button,
  Progress,
  SimpleGrid,
  Skeleton,
} from '@chakra-ui/react';
import { Icon } from '../../components/common/Icon';
import {
  Users,
  TrendingUp,
  AlertTriangle,
  Target,
  Download,
  Building2,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { StatCard } from '../../components/common/StatCard';
import { motion } from 'motion/react';
import { useCapability } from '../../hooks/useBackendEndpoints';
import { useMemo } from 'react';

const MotionBox = motion.create(Box);

const DEMO_TEAM_ID = 'SE';

export const OrgWideDashboard = () => {
  // For now, use single team capability data (future: aggregate multiple teams)
  const { data: capability, isLoading, error } = useCapability(DEMO_TEAM_ID);

  // Org-wide metrics (using team data for demo, future: aggregate from multiple teams)
  const orgMetrics = useMemo(() => {
    const teamSummary = capability?.team_summary || {};
    return {
      totalEmployees: teamSummary.total_employees || 0,
      skillCoverage: capability?.avg_coverage || capability?.capability_score || 0,
      criticalShortages: teamSummary.critical_gaps?.length || 0,
      keyRolesAtRisk: 0, // Not available in capability endpoint
    };
  }, [capability]);

  // Department comparison data (for demo, using single team - future: multiple teams)
  const departments = useMemo(() => {
    if (!capability) return [];
    
    const teamSummary = capability.team_summary || {};
    const coverage = capability.avg_coverage || capability.capability_score || 0;
    
    return [{
      name: DEMO_TEAM_ID,
      coverage: Math.round(coverage),
      employees: teamSummary.total_employees || 0,
      shortages: teamSummary.critical_gaps?.length || 0,
      color: coverage >= 90 ? '#4da944' : coverage >= 80 ? '#f59e0b' : '#ef4444',
    }];
  }, [capability]);

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
        <Skeleton height="400px" borderRadius="lg" />
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
            <Text fontWeight="semibold" color="red.800">Failed to load organizational data</Text>
          </HStack>
          <Text fontSize="sm" color="red.700" ml={7}>
            {error instanceof Error ? error.message : 'An unexpected error occurred. Please try again later.'}
          </Text>
        </Box>
      </VStack>
    );
  }

  // Multi-department skill heatmap (simplified)
  const skills = ['Technical', 'Leadership', 'Digital', 'Compliance', 'Innovation'];
  const departmentSkillData = [
    { dept: 'Engineering', scores: [88, 72, 78, 92, 85] },
    { dept: 'Manufacturing', scores: [75, 88, 65, 95, 70] },
    { dept: 'R&D', scores: [92, 68, 82, 78, 90] },
    { dept: 'IT', scores: [95, 75, 92, 88, 82] },
    { dept: 'Quality', scores: [82, 92, 72, 98, 75] },
  ];

  // Strategic workforce planning
  const strategicNeeds = [
    {
      category: 'Hiring Needs',
      items: [
        'Q1 2025: 12 Cloud Architects',
        'Q2 2025: 8 AI/ML Engineers',
        'Q3 2025: 15 Cybersecurity Specialists',
      ],
      icon: Users,
      color: 'blue',
    },
    {
      category: 'Promotion Pipeline',
      items: [
        '18 employees ready for promotion',
        '24 in development pipeline',
        'Est. promotion cost: 4.2M CZK',
      ],
      icon: TrendingUp,
      color: 'green',
    },
    {
      category: 'Training Budget',
      items: [
        '2025 recommended: 12.4M CZK',
        'Critical skills: 6.8M CZK',
        'Leadership dev: 3.2M CZK',
      ],
      icon: Target,
      color: 'purple',
    },
    {
      category: 'Attrition Risk',
      items: [
        '24 employees high flight risk',
        '8 key roles vulnerable',
        'Retention actions needed: 15',
      ],
      icon: AlertTriangle,
      color: 'red',
    },
  ];

  const getSkillColor = (score: number) => {
    if (score >= 90) return '#4da944';
    if (score >= 75) return '#eab308';
    if (score >= 60) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <VStack spacing={6} align="stretch">
      {/* Header */}
      <HStack justify="space-between">
        <Box>
          <Text fontSize="3xl" fontWeight="semibold">
            Organizational Intelligence Dashboard
          </Text>
          <Text color="gray.600" mt={1}>
            Cross-department workforce analytics · Enterprise view (Team {DEMO_TEAM_ID} demo)
          </Text>
        </Box>
        <HStack>
          <Button leftIcon={<Icon as={Download} />} variant="outline" size="sm">
            Export Executive Summary
          </Button>
          <Button colorScheme="brand" size="sm">
            View Forecast
          </Button>
        </HStack>
      </HStack>

      {/* Org-Wide KPIs */}
      <Grid templateColumns="repeat(4, 1fr)" gap={4}>
        <StatCard
          label="Total Employees"
          value={orgMetrics.totalEmployees.toLocaleString()}
          change="+124 YoY (4.6%)"
          trend="up"
          icon={Users}
          badge={<Badge colorScheme="green">+4.6%</Badge>}
        />
        <StatCard
          label="Org Skill Coverage"
          value={`${orgMetrics.skillCoverage}%`}
          change="+6.8% YoY"
          trend="up"
          icon={Target}
          badge={<Badge colorScheme="green">Healthy</Badge>}
        />
        <StatCard
          label="Critical Shortages"
          value={orgMetrics.criticalShortages}
          change="+8 vs Q3 2024"
          icon={AlertTriangle}
          badge={<Badge colorScheme="red">Action Needed</Badge>}
        />
        <StatCard
          label="Key Roles at Risk"
          value={orgMetrics.keyRolesAtRisk}
          change="3 critical"
          icon={Building2}
          badge={<Badge colorScheme="orange">Monitor</Badge>}
        />
      </Grid>

      {/* Department Benchmarking */}
      <MotionBox
        bg="white"
        p={6}
        borderRadius="lg"
        border="1px solid"
        borderColor="gray.200"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <HStack justify="space-between" mb={6}>
          <Box>
            <Text fontSize="xl" fontWeight="semibold">
              Department Performance Ranking
            </Text>
            <Text fontSize="xs" color="gray.600" mt={1}>
              Skill coverage by department (sorted by performance)
            </Text>
          </Box>
          <HStack spacing={3} fontSize="xs">
            <HStack>
              <Box w={3} h={3} bg="#4da944" borderRadius="sm" />
              <Text>≥90% (Excellent)</Text>
            </HStack>
            <HStack>
              <Box w={3} h={3} bg="#f59e0b" borderRadius="sm" />
              <Text>80-89% (Good)</Text>
            </HStack>
            <HStack>
              <Box w={3} h={3} bg="#ef4444" borderRadius="sm" />
              <Text>&lt;80% (Needs Improvement)</Text>
            </HStack>
          </HStack>
        </HStack>

        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={departments} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={120} />
            <Tooltip
              content={({ payload }: any) => {
                if (payload && payload.length > 0) {
                  const data = payload[0].payload;
                  return (
                    <Box
                      bg="white"
                      p={3}
                      borderRadius="md"
                      boxShadow="lg"
                      border="1px solid"
                      borderColor="gray.200"
                    >
                      <Text fontWeight="semibold" fontSize="sm">
                        {data.name}
                      </Text>
                      <Text fontSize="xs" color="gray.600">
                        Coverage: {data.coverage}%
                      </Text>
                      <Text fontSize="xs" color="gray.600">
                        Employees: {data.employees}
                      </Text>
                      <Text fontSize="xs" color="gray.600">
                        Shortages: {data.shortages}
                      </Text>
                    </Box>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="coverage" radius={[0, 4, 4, 0]}>
              {departments.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </MotionBox>

      {/* Multi-Department Skill Heatmap */}
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
        <HStack justify="space-between" mb={6}>
          <Box>
            <Text fontSize="xl" fontWeight="semibold">
              Cross-Department Skill Comparison
            </Text>
            <Text fontSize="xs" color="gray.600" mt={1}>
              5 core competency areas across departments
            </Text>
          </Box>
        </HStack>

        <Box overflowX="auto">
          <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '8px' }}>
            <thead>
              <tr>
                <th
                  style={{
                    textAlign: 'left',
                    padding: '8px',
                    fontSize: '12px',
                    fontWeight: '600',
                    color: '#6b7280',
                  }}
                >
                  Department
                </th>
                {skills.map((skill) => (
                  <th
                    key={skill}
                    style={{
                      textAlign: 'center',
                      padding: '8px',
                      fontSize: '12px',
                      fontWeight: '600',
                      color: '#6b7280',
                      minWidth: '100px',
                    }}
                  >
                    {skill}
                  </th>
                ))}
                <th
                  style={{
                    textAlign: 'center',
                    padding: '8px',
                    fontSize: '12px',
                    fontWeight: '600',
                    color: '#6b7280',
                  }}
                >
                  Avg
                </th>
              </tr>
            </thead>
            <tbody>
              {departmentSkillData.map((dept, idx) => {
                const avg = Math.round(
                  dept.scores.reduce((a, b) => a + b, 0) / dept.scores.length
                );
                return (
                  <tr key={idx}>
                    <td
                      style={{
                        padding: '8px',
                        fontSize: '13px',
                        fontWeight: '600',
                      }}
                    >
                      {dept.dept}
                    </td>
                    {dept.scores.map((score, sIdx) => (
                      <td key={sIdx} style={{ padding: '4px' }}>
                        <Box
                          display="flex"
                          alignItems="center"
                          justifyContent="center"
                          bg={getSkillColor(score)}
                          color="white"
                          borderRadius="md"
                          h="48px"
                          fontWeight="bold"
                          fontSize="lg"
                        >
                          {score}
                        </Box>
                      </td>
                    ))}
                    <td style={{ padding: '4px' }}>
                      <Box
                        display="flex"
                        alignItems="center"
                        justifyContent="center"
                        bg="gray.100"
                        color="gray.700"
                        borderRadius="md"
                        h="48px"
                        fontWeight="bold"
                        fontSize="lg"
                      >
                        {avg}
                      </Box>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Box>
      </MotionBox>

      {/* Strategic Workforce Planning */}
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
        <HStack justify="space-between" mb={6}>
          <Box>
            <Text fontSize="xl" fontWeight="semibold">
              Strategic Workforce Planning (2025)
            </Text>
            <Text fontSize="xs" color="gray.600" mt={1}>
              AI-generated recommendations for org-wide talent strategy
            </Text>
          </Box>
          <Badge colorScheme="purple" fontSize="sm" px={3} py={1}>
            Executive Summary
          </Badge>
        </HStack>

        <SimpleGrid columns={2} spacing={4}>
          {strategicNeeds.map((need, idx) => (
            <Box
              key={idx}
              p={5}
              bg={`${need.color}.50`}
              borderRadius="lg"
              border="1px solid"
              borderColor={`${need.color}.200`}
            >
              <HStack mb={4}>
                <Box
                  w={10}
                  h={10}
                  bg={`${need.color}.500`}
                  borderRadius="lg"
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                >
                  <Icon as={need.icon} w={5} h={5} color="white" />
                </Box>
                <Text fontWeight="semibold">{need.category}</Text>
              </HStack>
              <VStack align="stretch" spacing={2}>
                {need.items.map((item, i) => (
                  <HStack key={i} align="start">
                    <Box
                      w={2}
                      h={2}
                      bg={`${need.color}.500`}
                      borderRadius="full"
                      mt={1.5}
                    />
                    <Text fontSize="sm">{item}</Text>
                  </HStack>
                ))}
              </VStack>
            </Box>
          ))}
        </SimpleGrid>
      </MotionBox>

      {/* Critical Insights */}
      <Box p={6} bg="red.50" borderRadius="lg" border="1px solid" borderColor="red.200">
        <HStack mb={4}>
          <Icon as={AlertTriangle} w={6} h={6} color="red.600" />
          <Text fontSize="lg" fontWeight="semibold">
            Critical Organizational Risks
          </Text>
        </HStack>
        <Grid templateColumns="repeat(3, 1fr)" gap={4}>
          <Box>
            <Text fontSize="sm" fontWeight="semibold" mb={2}>
              R&D Department at Risk
            </Text>
            <Text fontSize="xs" color="gray.600">
              78% skill coverage (lowest). 18 critical shortages. Recommend immediate hiring of 6 specialists and training budget increase.
            </Text>
          </Box>
          <Box>
            <Text fontSize="sm" fontWeight="semibold" mb={2}>
              Leadership Pipeline Weak
            </Text>
            <Text fontSize="xs" color="gray.600">
              12 key roles have no successor. Engineering Manager position at 78% risk. Accelerate leadership development programs.
            </Text>
          </Box>
          <Box>
            <Text fontSize="sm" fontWeight="semibold" mb={2}>
              Q1 2025 Delivery Risk
            </Text>
            <Text fontSize="xs" color="gray.600">
              Cloud Architecture shortage (12 positions) threatens project timeline. Hire external consultants or delay milestones.
            </Text>
          </Box>
        </Grid>
      </Box>
    </VStack>
  );
};