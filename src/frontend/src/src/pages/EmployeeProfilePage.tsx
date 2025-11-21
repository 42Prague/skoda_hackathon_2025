import { 
  Box, 
  Grid, 
  VStack, 
  HStack, 
  Text, 
  Badge,
  Button,
  Progress,
  Avatar
} from '@chakra-ui/react';
import { Icon } from '../components/common/Icon';
import { Award, TrendingUp, Target, CheckCircle2, XCircle, AlertCircle, Sparkles } from 'lucide-react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts';
import { RiskBadge } from '../components/common/RiskBadge';
import { SkillChip } from '../components/common/SkillChip';
import { useLang } from '../hooks/useLang';
import { useParams } from 'react-router-dom';
import { motion } from 'motion/react';

const MotionBox = motion.create(Box);

export const EmployeeProfilePage = () => {
  const { t } = useLang();
  const { id } = useParams();

  const employee = {
    name: 'Jana Nováková',
    role: 'Senior Software Developer',
    department: 'Engineering · Powertrain Team',
    tenure: '4 years 7 months',
    skillCoverage: 78,
    mandatoryCompliance: 87,
    careerLevel: 'L4 → L5 Ready',
  };

  const qualifications = [
    { name: 'AWS Solutions Architect', status: 'obtained', expiry: 'Jun 2025', mandatory: true },
    { name: 'Scrum Master Certified', status: 'obtained', expiry: 'No expiry', mandatory: false },
    { name: 'ISO 27001 Security Training', status: 'expired', expiry: 'Expired Oct 2024', mandatory: true },
    { name: 'Leadership Foundations', status: 'missing', expiry: 'Required for L5', mandatory: true },
    { name: 'Advanced React Patterns', status: 'obtained', expiry: 'No expiry', mandatory: false },
  ];

  const skills = [
    { name: 'React/Frontend Development', level: 5, target: 5, category: 'Technical' },
    { name: 'Cloud Computing (AWS)', level: 4, target: 5, category: 'Technical' },
    { name: 'Backend APIs (Node.js)', level: 4, target: 4, category: 'Technical' },
    { name: 'Team Leadership', level: 3, target: 4, category: 'Leadership' },
    { name: 'System Architecture', level: 3, target: 4, category: 'Technical' },
    { name: 'Cybersecurity Practices', level: 2, target: 4, category: 'Compliance' },
  ];

  const careerPaths = [
    { role: 'Engineering Manager', probability: 72, timeframe: '12-18 months', gaps: 'Leadership, Budget Mgmt' },
    { role: 'Principal Engineer', probability: 85, timeframe: '8-12 months', gaps: 'System Design, Mentoring' },
    { role: 'Solution Architect', probability: 68, timeframe: '15-20 months', gaps: 'Enterprise Architecture' },
  ];

  const aiRecommendations = [
    {
      priority: 'high',
      title: 'Renew ISO 27001 Security Training',
      description: 'Mandatory certification expired. Complete by Dec 15 to maintain compliance.',
      action: 'Enroll in Course',
      hours: '8 hours',
    },
    {
      priority: 'medium',
      title: 'AWS Advanced Networking',
      description: 'Close cloud computing gap. Aligns with Q1 2025 project requirements.',
      action: 'View Course',
      hours: '16 hours',
    },
    {
      priority: 'medium',
      title: 'Leadership Skills Workshop',
      description: 'Required for L5 promotion. Next cohort starts Jan 2025.',
      action: 'Reserve Spot',
      hours: '24 hours',
    },
  ];

  const getStatusIcon = (status: string) => {
    if (status === 'obtained') return CheckCircle2;
    if (status === 'expired') return XCircle;
    return AlertCircle;
  };

  const getStatusColor = (status: string) => {
    if (status === 'obtained') return 'green.600';
    if (status === 'expired') return 'red.600';
    return 'orange.600';
  };

  return (
    <VStack spacing={6} align="stretch">
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
        <HStack spacing={6} align="start">
          <Avatar size="xl" name={employee.name} bg="skoda.green" color="white" />
          <Box flex={1}>
            <HStack justify="space-between" mb={3}>
              <Box>
                <Text fontSize="2xl" fontWeight="semibold" mb={1}>{employee.name}</Text>
                <Text color="gray.600">{employee.role}</Text>
                <Text fontSize="xs" color="gray.600" mt={1}>{employee.department} · {employee.tenure}</Text>
              </Box>
              <Badge colorScheme="green" px={3} py={1}>{employee.careerLevel}</Badge>
            </HStack>

            <Grid templateColumns="repeat(3, 1fr)" gap={6} mt={6}>
              <Box>
                <Text fontSize="xs" color="gray.600" mb={2}>{t('employee.skillCoverage')}</Text>
                <HStack>
                  <Progress value={employee.skillCoverage} flex={1} h={2} colorScheme="green" borderRadius="full" />
                  <Text fontWeight="semibold">{employee.skillCoverage}%</Text>
                </HStack>
              </Box>
              <Box>
                <Text fontSize="xs" color="gray.600" mb={2}>{t('employee.mandatoryCompliance')}</Text>
                <HStack>
                  <Progress value={employee.mandatoryCompliance} flex={1} h={2} colorScheme="green" borderRadius="full" />
                  <Text fontWeight="semibold">{employee.mandatoryCompliance}%</Text>
                </HStack>
              </Box>
              <Box>
                <Text fontSize="xs" color="gray.600" mb={2}>{t('employee.careerReadiness')}</Text>
                <HStack>
                  <Icon as={TrendingUp} w={5} h={5} color="green.600" />
                  <Text fontWeight="semibold" color="green.600">Ready for L5</Text>
                </HStack>
              </Box>
            </Grid>
          </Box>
        </HStack>
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
        <HStack justify="space-between" mb={5}>
          <HStack>
            <Icon as={Award} w={5} h={5} color="skoda.green" />
            <Text fontSize="xl" fontWeight="semibold">{t('employee.qualifications')}</Text>
          </HStack>
          <Button variant="outline" size="sm">View All Courses</Button>
        </HStack>

        <VStack spacing={3} align="stretch">
          {qualifications.map((qual, idx) => (
            <Box
              key={idx}
              p={4}
              borderRadius="lg"
              border="1px solid"
              bg={qual.status === 'expired' || qual.status === 'missing' ? 'red.50' : 'white'}
              borderColor={qual.status === 'expired' || qual.status === 'missing' ? 'red.200' : 'gray.200'}
            >
              <HStack justify="space-between">
                <HStack spacing={3} flex={1}>
                  <Icon as={getStatusIcon(qual.status)} w={4} h={4} color={getStatusColor(qual.status)} />
                  <Box flex={1}>
                    <HStack mb={1}>
                      <Text fontWeight="medium" fontSize="sm">{qual.name}</Text>
                      {qual.mandatory && (
                        <Badge variant="outline" fontSize="xs">Mandatory</Badge>
                      )}
                    </HStack>
                    <Text fontSize="xs" color="gray.600">{qual.expiry}</Text>
                  </Box>
                </HStack>
                <Badge
                  colorScheme={
                    qual.status === 'obtained' ? 'green' :
                    qual.status === 'expired' ? 'red' : 'orange'
                  }
                >
                  {qual.status.charAt(0).toUpperCase() + qual.status.slice(1)}
                </Badge>
              </HStack>
            </Box>
          ))}
        </VStack>
      </MotionBox>

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
            <Icon as={Target} w={5} h={5} color="skoda.green" />
            <Text fontSize="xl" fontWeight="semibold">{t('employee.skillLevels')}</Text>
          </HStack>

          <VStack spacing={4} align="stretch">
            {skills.map((skill, idx) => (
              <Box key={idx}>
                <HStack justify="space-between" mb={2}>
                  <Box>
                    <Text fontWeight="medium" fontSize="sm">{skill.name}</Text>
                    <Text fontSize="xs" color="gray.600">{skill.category}</Text>
                  </Box>
                  <HStack>
                    <Text fontSize="sm">{skill.level}/5</Text>
                    {skill.level < skill.target && (
                      <Text fontSize="xs" color="orange.600">Target: {skill.target}</Text>
                    )}
                  </HStack>
                </HStack>
                <Box position="relative" h={2} bg="gray.200" borderRadius="full" overflow="hidden">
                  <Box
                    position="absolute"
                    top={0}
                    left={0}
                    h="full"
                    bg={skill.level >= skill.target ? 'skoda.green' : 'orange.400'}
                    borderRadius="full"
                    w={`${(skill.level / 5) * 100}%`}
                  />
                  <Box
                    position="absolute"
                    top={0}
                    left={0}
                    h="full"
                    borderRight="2px solid"
                    borderColor="skoda.navy"
                    opacity={0.3}
                    w={`${(skill.target / 5) * 100}%`}
                  />
                </Box>
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
            <Icon as={TrendingUp} w={5} h={5} color="skoda.green" />
            <Text fontSize="xl" fontWeight="semibold">{t('employee.careerPath')}</Text>
          </HStack>

          <VStack spacing={3} align="stretch">
            {careerPaths.map((path, idx) => (
              <Box
                key={idx}
                p={4}
                bg="gray.50"
                borderRadius="lg"
                border="1px solid"
                borderColor="gray.200"
                _hover={{ borderColor: 'skoda.green' }}
                transition="all 0.2s"
                cursor="pointer"
              >
                <HStack justify="space-between" mb={2}>
                  <Box>
                    <Text fontWeight="medium" fontSize="sm">{path.role}</Text>
                    <Text fontSize="xs" color="gray.600">{path.timeframe}</Text>
                  </Box>
                  <Box
                    w={12}
                    h={12}
                    borderRadius="full"
                    bg="white"
                    border="4px solid"
                    borderColor="skoda.green"
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                  >
                    <Text fontSize="sm" fontWeight="semibold">{path.probability}%</Text>
                  </Box>
                </HStack>
                <Text fontSize="xs" color="gray.600">
                  <strong>Gaps:</strong> {path.gaps}
                </Text>
              </Box>
            ))}
          </VStack>
        </MotionBox>
      </Grid>

      <MotionBox
        bg="gradient-to-br"
        bgGradient="linear(to-br, green.50, white)"
        p={6}
        borderRadius="lg"
        border="1px solid"
        borderColor="gray.200"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.4 }}
      >
        <HStack mb={5}>
          <Icon as={Sparkles} w={5} h={5} color="skoda.green" />
          <Text fontSize="xl" fontWeight="semibold">{t('employee.aiCoaching')}</Text>
        </HStack>

        <VStack spacing={3} align="stretch">
          {aiRecommendations.map((rec, idx) => (
            <Box key={idx} p={4} bg="white" borderRadius="lg" border="1px solid" borderColor="gray.200">
              <HStack mb={2}>
                <RiskBadge level={rec.priority as any} label={`${rec.priority.charAt(0).toUpperCase() + rec.priority.slice(1)} Priority`} />
                <Text fontSize="xs" color="gray.600">{rec.hours}</Text>
              </HStack>
              <Text fontWeight="medium" fontSize="sm" mb={1}>{rec.title}</Text>
              <Text fontSize="xs" color="gray.600" mb={3}>{rec.description}</Text>
              <HStack spacing={2}>
                <Button size="sm" colorScheme="brand">{rec.action}</Button>
                <Button size="sm" variant="outline">Learn More</Button>
              </HStack>
            </Box>
          ))}
        </VStack>
      </MotionBox>
    </VStack>
  );
};
