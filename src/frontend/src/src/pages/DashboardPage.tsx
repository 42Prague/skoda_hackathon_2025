import { 
  Box, 
  Grid, 
  VStack, 
  HStack, 
  Text, 
  Badge,
  Button,
  Progress,
  useToast
} from '@chakra-ui/react';
import { Icon } from '../components/common/Icon';
import { Users, Target, Award, Brain, TrendingUp, AlertTriangle, Download } from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  PolarRadiusAxis, 
  Radar,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { StatCard } from '../components/common/StatCard';
import { RiskBadge } from '../components/common/RiskBadge';
import { useLang } from '../hooks/useLang';
import { useDashboardMetrics, useTeamSkills, useRiskEmployees, usePredictedGaps } from '../hooks/useDashboard';
import { motion } from 'motion/react';

const MotionBox = motion.create(Box);

export const DashboardPage = () => {
  const { t } = useLang();
  const toast = useToast();

  const mockMetrics = {
    teamMembers: { value: 24, change: '+2', trend: 'up' },
    skillCoverage: { value: '82%', change: '+5%', trend: 'up' },
    qualificationsDue: { value: 8, change: '3 urgent', trend: 'down' },
    aiRecommendations: { value: 12, change: 'New', trend: 'neutral' },
  };

  const skillReadinessData = [
    { skill: 'Software Architecture', current: 85, target: 90 },
    { skill: 'Cloud Computing', current: 72, target: 85 },
    { skill: 'Data Analysis', current: 68, target: 80 },
    { skill: 'Leadership', current: 78, target: 85 },
    { skill: 'Agile Methods', current: 88, target: 90 },
    { skill: 'Cybersecurity', current: 62, target: 80 },
  ];

  const radarData = [
    { skill: 'Technical', A: 85, fullMark: 100 },
    { skill: 'Leadership', A: 72, fullMark: 100 },
    { skill: 'Communication', A: 88, fullMark: 100 },
    { skill: 'Innovation', A: 68, fullMark: 100 },
    { skill: 'Compliance', A: 92, fullMark: 100 },
    { skill: 'Digital', A: 78, fullMark: 100 },
  ];

  const riskEmployees = [
    { name: 'Jana Nováková', role: 'Senior Developer', risk: 'high', reason: '3 mandatory certifications expired', skills: 67 },
    { name: 'Petr Dvořák', role: 'Team Lead', risk: 'medium', reason: 'Cloud skills gap vs role requirements', skills: 74 },
    { name: 'Eva Svobodová', role: 'QA Engineer', risk: 'medium', reason: 'Automation skills below threshold', skills: 71 },
  ];

  const upcomingGaps = [
    { month: 'Dec 2024', gap: 'Cloud Architecture', impact: '2 projects', severity: 'high' },
    { month: 'Jan 2025', gap: 'AI/ML Basics', impact: '1 project', severity: 'medium' },
    { month: 'Feb 2025', gap: 'Security Compliance', impact: 'Audit risk', severity: 'high' },
  ];

  const generatePDF = () => {
    toast({
      title: 'Generating PDF Summary',
      description: 'Your dashboard summary is being created...',
      status: 'info',
      duration: 3000,
    });
  };

  return (
    <VStack spacing={6} align="stretch">
      <HStack justify="space-between">
        <Box>
          <Text fontSize="3xl" fontWeight="semibold">{t('dashboard.title')}</Text>
          <Text color="gray.600" mt={1}>{t('dashboard.subtitle')}</Text>
        </Box>
        <Button leftIcon={<Icon as={Download} />} colorScheme="brand" onClick={generatePDF}>
          Export PDF Summary
        </Button>
      </HStack>

      <Grid templateColumns="repeat(4, 1fr)" gap={4}>
        <StatCard
          label={t('dashboard.teamMembers')}
          value={mockMetrics.teamMembers.value}
          change={mockMetrics.teamMembers.change}
          trend="up"
          icon={Users}
          badge={<Badge colorScheme="green">{mockMetrics.teamMembers.change}</Badge>}
        />
        <StatCard
          label={t('dashboard.avgSkillCoverage')}
          value={mockMetrics.skillCoverage.value}
          change={mockMetrics.skillCoverage.change}
          trend="up"
          icon={Target}
          badge={<Badge colorScheme="green">{mockMetrics.skillCoverage.change}</Badge>}
        />
        <StatCard
          label={t('dashboard.qualificationsDue')}
          value={mockMetrics.qualificationsDue.value}
          change={mockMetrics.qualificationsDue.change}
          trend="down"
          icon={Award}
          badge={<Badge colorScheme="red">{mockMetrics.qualificationsDue.change}</Badge>}
        />
        <StatCard
          label={t('dashboard.aiRecommendations')}
          value={mockMetrics.aiRecommendations.value}
          change={mockMetrics.aiRecommendations.change}
          icon={Brain}
          badge={<Badge colorScheme="blue">{mockMetrics.aiRecommendations.change}</Badge>}
        />
      </Grid>

      <Grid templateColumns="2fr 1fr" gap={6}>
        <MotionBox
          bg="white"
          p={6}
          borderRadius="lg"
          border="1px solid"
          borderColor="gray.200"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <HStack justify="space-between" mb={6}>
            <Box>
              <Text fontSize="xl" fontWeight="semibold">{t('dashboard.teamSkillReadiness')}</Text>
              <Text fontSize="xs" color="gray.600" mt={1}>{t('dashboard.currentVsTarget')}</Text>
            </Box>
            <Badge variant="outline" colorScheme="green">6 skills tracked</Badge>
          </HStack>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={skillReadinessData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="skill" tick={{ fontSize: 11 }} angle={-20} textAnchor="end" height={80} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="current" fill="#4da944" name="Current" radius={[4, 4, 0, 0]} />
              <Bar dataKey="target" fill="#d1d5db" name="Target" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </MotionBox>

        <MotionBox
          bg="white"
          p={6}
          borderRadius="lg"
          border="1px solid"
          borderColor="gray.200"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <Box mb={6}>
            <Text fontSize="xl" fontWeight="semibold">{t('dashboard.teamCapability')}</Text>
            <Text fontSize="xs" color="gray.600" mt={1}>Aggregate team strengths</Text>
          </Box>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis dataKey="skill" tick={{ fontSize: 11 }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
              <Radar name="Team" dataKey="A" stroke="#4da944" fill="#4da944" fillOpacity={0.5} />
            </RadarChart>
          </ResponsiveContainer>
        </MotionBox>
      </Grid>

      <Grid templateColumns="repeat(2, 1fr)" gap={6}>
        <MotionBox
          bg="white"
          p={6}
          borderRadius="lg"
          border="1px solid"
          borderColor="gray.200"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <HStack mb={5}>
            <Icon as={AlertTriangle} w={5} h={5} color="red.500" />
            <Text fontSize="xl" fontWeight="semibold">{t('dashboard.highPriorityInterventions')}</Text>
          </HStack>
          <VStack spacing={4} align="stretch">
            {riskEmployees.map((emp, idx) => (
              <Box key={idx} p={4} bg="gray.50" borderRadius="lg" border="1px solid" borderColor="gray.200">
                <HStack justify="space-between" mb={2}>
                  <Box>
                    <Text fontWeight="medium">{emp.name}</Text>
                    <Text fontSize="xs" color="gray.600">{emp.role}</Text>
                  </Box>
                  <RiskBadge level={emp.risk as any} />
                </HStack>
                <Text fontSize="xs" color="gray.600" mb={2}>{emp.reason}</Text>
                <HStack>
                  <Progress value={emp.skills} flex={1} h={2} colorScheme="green" borderRadius="full" />
                  <Text fontSize="xs" color="gray.600">{emp.skills}%</Text>
                </HStack>
              </Box>
            ))}
          </VStack>
        </MotionBox>

        <MotionBox
          bg="white"
          p={6}
          borderRadius="lg"
          border="1px solid"
          borderColor="gray.200"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <HStack mb={5}>
            <Icon as={Brain} w={5} h={5} color="skoda.green" />
            <Text fontSize="xl" fontWeight="semibold">{t('dashboard.aiPredictedGaps')}</Text>
          </HStack>
          <VStack spacing={3} align="stretch" mb={6}>
            {upcomingGaps.map((gap, idx) => (
              <Box 
                key={idx} 
                p={4} 
                bg="white" 
                borderRadius="lg" 
                border="1px solid" 
                borderColor="gray.200"
                _hover={{ borderColor: 'skoda.green' }}
                transition="all 0.2s"
              >
                <HStack justify="space-between" mb={2}>
                  <Box>
                    <Text fontWeight="medium" fontSize="sm">{gap.gap}</Text>
                    <Text fontSize="xs" color="gray.600" mt={0.5}>{gap.month}</Text>
                  </Box>
                  <Box w={2} h={2} borderRadius="full" bg={gap.severity === 'high' ? 'red.500' : 'orange.400'} />
                </HStack>
                <Text fontSize="xs" color="gray.600">Impact: {gap.impact}</Text>
              </Box>
            ))}
          </VStack>

          <Box p={4} bg="green.50" borderRadius="lg" border="1px solid" borderColor="green.200">
            <Text fontSize="xs" mb={3}>
              <strong style={{ color: '#4da944' }}>AI Recommendation:</strong>
            </Text>
            <Text fontSize="xs" color="gray.600" mb={2}>
              Enroll 4 team members in "AWS Cloud Architect" course by Dec 15 to prevent Q1 2025 bottleneck. Estimated cost: 24,000 CZK.
            </Text>
            <HStack mt={3} spacing={2}>
              <Button size="sm" colorScheme="brand">Schedule Training</Button>
              <Button size="sm" variant="outline">View Details</Button>
            </HStack>
          </Box>
        </MotionBox>
      </Grid>
    </VStack>
  );
};
