import { Box, Grid, VStack, HStack, Text, Badge, Button, Select } from '@chakra-ui/react';
import { Icon } from '../components/common/Icon';
import { TrendingUp, TrendingDown, AlertTriangle, Target } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { PredictiveChart } from '../components/charts/PredictiveChart';
import { StatCard } from '../components/common/StatCard';
import { RiskBadge } from '../components/common/RiskBadge';
import { useLang } from '../hooks/useLang';
import { motion } from 'motion/react';

const MotionBox = motion.create(Box);

export const PredictiveAnalyticsPage = () => {
  const { t } = useLang();

  const skillTrendData = [
    { year: '2013', cloud: 15, ai: 5, mobile: 45, legacy: 85 },
    { year: '2014', cloud: 22, ai: 8, mobile: 52, legacy: 78 },
    { year: '2015', cloud: 31, ai: 12, mobile: 58, legacy: 72 },
    { year: '2016', cloud: 42, ai: 18, mobile: 65, legacy: 65 },
    { year: '2017', cloud: 55, ai: 25, mobile: 72, legacy: 58 },
    { year: '2018', cloud: 68, ai: 35, mobile: 78, legacy: 48 },
    { year: '2019', cloud: 75, ai: 48, mobile: 82, legacy: 38 },
    { year: '2020', cloud: 82, ai: 62, mobile: 85, legacy: 28 },
    { year: '2021', cloud: 88, ai: 75, mobile: 88, legacy: 22 },
    { year: '2022', cloud: 92, ai: 85, mobile: 90, legacy: 15 },
    { year: '2023', cloud: 95, ai: 92, mobile: 92, legacy: 10 },
    { year: '2024', cloud: 97, ai: 96, mobile: 93, legacy: 8 },
  ];

  const forecastData = [
    { period: 'Nov 2024', actual: 82, forecast: null, upper: null, lower: null },
    { period: 'Dec 2024', actual: 83, forecast: null, upper: null, lower: null },
    { period: 'Jan 2025', actual: null, forecast: 84, upper: 88, lower: 80 },
    { period: 'Feb 2025', actual: null, forecast: 85, upper: 90, lower: 81 },
    { period: 'Mar 2025', actual: null, forecast: 86, upper: 91, lower: 82 },
    { period: 'Apr 2025', actual: null, forecast: 87, upper: 93, lower: 82 },
    { period: 'May 2025', actual: null, forecast: 88, upper: 94, lower: 83 },
    { period: 'Jun 2025', actual: null, forecast: 89, upper: 95, lower: 84 },
  ];

  const qualificationComplianceData = [
    { department: 'Engineering', compliance: 87, trend: 5 },
    { department: 'Manufacturing', compliance: 92, trend: 2 },
    { department: 'Quality', compliance: 95, trend: 1 },
    { department: 'R&D', compliance: 78, trend: -3 },
    { department: 'IT', compliance: 88, trend: 8 },
    { department: 'Supply Chain', compliance: 85, trend: 4 },
  ];

  const emergingSkills = [
    { skill: 'Generative AI', growth: 245, employees: 156, priority: 'critical' },
    { skill: 'Cybersecurity', growth: 180, employees: 234, priority: 'high' },
    { skill: 'Data Science', growth: 165, employees: 198, priority: 'high' },
    { skill: 'Electric Powertrain', growth: 142, employees: 287, priority: 'critical' },
    { skill: 'Sustainability', growth: 128, employees: 312, priority: 'medium' },
  ];

  const decliningSkills = [
    { skill: 'Legacy Systems', decline: -65, employees: 45, action: 'Upskill/Transition' },
    { skill: 'Manual Testing', decline: -48, employees: 67, action: 'Automation Training' },
    { skill: 'Waterfall PM', decline: -42, employees: 89, action: 'Agile Certification' },
  ];

  const jobTransitions = [
    { from: 'Developer', to: 'Senior Developer', count: 28, avgTime: '2.3 years' },
    { from: 'Senior Developer', to: 'Tech Lead', count: 12, avgTime: '3.1 years' },
    { from: 'Tech Lead', to: 'Engineering Manager', count: 8, avgTime: '2.8 years' },
    { from: 'QA Engineer', to: 'QA Lead', count: 6, avgTime: '3.5 years' },
    { from: 'Junior Developer', to: 'Developer', count: 34, avgTime: '1.8 years' },
  ];

  const shortageForecasts = [
    { skill: 'Cloud Architecture', shortage: 12, timeframe: 'Q1 2025', severity: 'high' },
    { skill: 'AI/ML Engineering', shortage: 8, timeframe: 'Q2 2025', severity: 'critical' },
    { skill: 'Security Specialists', shortage: 15, timeframe: 'Q1 2025', severity: 'high' },
    { skill: 'DevOps Engineers', shortage: 6, timeframe: 'Q3 2025', severity: 'medium' },
  ];

  return (
    <VStack spacing={6} align="stretch">
      <HStack justify="space-between">
        <Box>
          <Text fontSize="3xl" fontWeight="semibold">{t('analytics.title')}</Text>
          <Text color="gray.600" mt={1}>{t('analytics.subtitle')}</Text>
        </Box>
        <HStack>
          <Select w="160px" defaultValue="all">
            <option value="all">All Departments</option>
            <option value="eng">Engineering</option>
            <option value="mfg">Manufacturing</option>
            <option value="rd">R&D</option>
          </Select>
          <Button variant="outline">Export Report</Button>
        </HStack>
      </HStack>

      <Grid templateColumns="repeat(4, 1fr)" gap={4}>
        <StatCard label={t('analytics.totalEmployees')} value="2,847" change="+124 YoY (4.6%)" trend="up" icon={TrendingUp} />
        <StatCard label={t('analytics.skillCoverage')} value="84.2%" change="+6.8% YoY" trend="up" icon={Target} />
        <StatCard label={t('analytics.qualificationRate')} value="88.5%" change="+3.2% YoY" trend="up" icon={TrendingUp} />
        <StatCard label={t('analytics.criticalShortages')} value={41} change="+8 vs Q3 2024" trend="down" icon={AlertTriangle} badge={<Badge colorScheme="red">+8</Badge>} />
      </Grid>

      <MotionBox bg="white" p={6} borderRadius="lg" border="1px solid" borderColor="gray.200" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <HStack justify="space-between" mb={6}>
          <Box>
            <Text fontSize="xl" fontWeight="semibold">{t('analytics.skillEvolution')}</Text>
            <Text fontSize="xs" color="gray.600" mt={1}>Skill adoption rates across organization (2013-2024)</Text>
          </Box>
          <HStack spacing={4} fontSize="xs">
            <HStack><Box w={3} h={3} borderRadius="full" bg="skoda.green" /><Text>Cloud Computing</Text></HStack>
            <HStack><Box w={3} h={3} borderRadius="full" bg="blue.500" /><Text>AI/ML</Text></HStack>
            <HStack><Box w={3} h={3} borderRadius="full" bg="purple.500" /><Text>Mobile</Text></HStack>
            <HStack><Box w={3} h={3} borderRadius="full" bg="gray.400" /><Text>Legacy Systems</Text></HStack>
          </HStack>
        </HStack>
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={skillTrendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="year" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} label={{ value: 'Adoption %', angle: -90, position: 'insideLeft', style: { fontSize: 11 } }} />
            <Tooltip />
            <Line type="monotone" dataKey="cloud" stroke="#4da944" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="ai" stroke="#3b82f6" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="mobile" stroke="#a855f7" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="legacy" stroke="#9ca3af" strokeWidth={2} strokeDasharray="5 5" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </MotionBox>

      <Grid templateColumns="repeat(2, 1fr)" gap={6}>
        <MotionBox bg="white" p={6} borderRadius="lg" border="1px solid" borderColor="gray.200" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Text fontSize="xl" fontWeight="semibold" mb={5}>{t('analytics.forecastTitle')}</Text>
          <PredictiveChart data={forecastData} height={240} />
        </MotionBox>

        <MotionBox bg="white" p={6} borderRadius="lg" border="1px solid" borderColor="gray.200" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <Text fontSize="xl" fontWeight="semibold" mb={5}>Qualification Compliance by Department</Text>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={qualificationComplianceData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis type="number" tick={{ fontSize: 11 }} domain={[0, 100]} />
              <YAxis type="category" dataKey="department" tick={{ fontSize: 11 }} width={100} />
              <Tooltip />
              <Bar dataKey="compliance" radius={[0, 4, 4, 0]}>
                {qualificationComplianceData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.compliance >= 90 ? '#4da944' : entry.compliance >= 80 ? '#f59e0b' : '#ef4444'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </MotionBox>
      </Grid>

      <Grid templateColumns="repeat(2, 1fr)" gap={6}>
        <MotionBox bg="white" p={6} borderRadius="lg" border="1px solid" borderColor="gray.200" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <HStack mb={5}>
            <Icon as={TrendingUp} w={5} h={5} color="green.600" />
            <Text fontSize="xl" fontWeight="semibold">{t('analytics.emergingSkills')}</Text>
          </HStack>
          <VStack spacing={3} align="stretch">
            {emergingSkills.map((skill, idx) => (
              <Box key={idx} p={3} bg="green.50" borderRadius="lg" border="1px solid" borderColor="green.200">
                <HStack justify="space-between" mb={2}>
                  <Box>
                    <Text fontWeight="medium" fontSize="sm">{skill.skill}</Text>
                    <Text fontSize="xs" color="gray.600">{skill.employees} employees</Text>
                  </Box>
                  <HStack>
                    <RiskBadge level={skill.priority as any} />
                    <Text fontSize="sm" fontWeight="semibold" color="green.600">+{skill.growth}%</Text>
                  </HStack>
                </HStack>
              </Box>
            ))}
          </VStack>
        </MotionBox>

        <MotionBox bg="white" p={6} borderRadius="lg" border="1px solid" borderColor="gray.200" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
          <HStack mb={5}>
            <Icon as={TrendingDown} w={5} h={5} color="orange.600" />
            <Text fontSize="xl" fontWeight="semibold">{t('analytics.decliningSkills')}</Text>
          </HStack>
          <VStack spacing={3} align="stretch">
            {decliningSkills.map((skill, idx) => (
              <Box key={idx} p={3} bg="orange.50" borderRadius="lg" border="1px solid" borderColor="orange.200">
                <HStack justify="space-between" mb={2}>
                  <Box>
                    <Text fontWeight="medium" fontSize="sm">{skill.skill}</Text>
                    <Text fontSize="xs" color="gray.600">{skill.employees} employees affected</Text>
                  </Box>
                  <Text fontSize="sm" fontWeight="semibold" color="orange.600">{skill.decline}%</Text>
                </HStack>
                <Badge variant="outline" fontSize="xs">{skill.action}</Badge>
              </Box>
            ))}
          </VStack>
        </MotionBox>
      </Grid>

      <MotionBox bg="red.50" p={6} borderRadius="lg" border="1px solid" borderColor="red.200" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
        <HStack mb={5}>
          <Box w={10} h={10} borderRadius="lg" bg="red.600" display="flex" alignItems="center" justifyContent="center">
            <Icon as={AlertTriangle} w={5} h={5} color="white" />
          </Box>
          <Box>
            <Text fontSize="xl" fontWeight="semibold">{t('analytics.predictedShortages')}</Text>
            <Text fontSize="xs" color="gray.600" mt={1}>Skills at risk based on project pipeline, attrition forecast, and market trends</Text>
          </Box>
        </HStack>
        <Grid templateColumns="repeat(2, 1fr)" gap={3}>
          {shortageForecasts.map((shortage, idx) => (
            <Box key={idx} p={4} bg="white" borderRadius="lg" border="1px solid" borderColor="red.200">
              <HStack justify="space-between" mb={2}>
                <Box>
                  <Text fontWeight="medium">{shortage.skill}</Text>
                  <Text fontSize="xs" color="gray.600">Expected {shortage.timeframe}</Text>
                </Box>
                <RiskBadge level={shortage.severity as any} />
              </HStack>
              <HStack>
                <Box w={12} h={12} borderRadius="lg" bg="red.100" display="flex" alignItems="center" justifyContent="center">
                  <Text fontWeight="semibold" color="red.700">-{shortage.shortage}</Text>
                </Box>
                <Text fontSize="xs" color="gray.600">positions short of requirement</Text>
              </HStack>
            </Box>
          ))}
        </Grid>
      </MotionBox>
    </VStack>
  );
};
