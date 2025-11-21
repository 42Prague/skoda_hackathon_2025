import {
  Box,
  Grid,
  VStack,
  HStack,
  Text,
  Badge,
  Button,
  Skeleton,
} from '@chakra-ui/react';
import {
  Target,
  TrendingUp,
  Award,
  BookOpen,
  CheckCircle2,
  Clock,
  Sparkles,
  ChevronRight,
  User,
  AlertTriangle,
} from 'lucide-react';
import { StatCard } from '../../components/common/StatCard';
import { motion } from 'motion/react';
import { Icon } from '../../components/common/Icon';
import { useCareerPath } from '../../hooks/useBackendEndpoints';
import { useMemo } from 'react';

const MotionBox = motion.create(Box);

const DEMO_EMPLOYEE_ID = 9186;

// Custom Progress component
const Progress = ({ value, size, colorScheme, borderRadius }: any) => {
  const colorMap: Record<string, string> = {
    blue: '#3b82f6',
    purple: '#9333ea',
    green: '#4da944',
    orange: '#f97316',
  };

  const height = size === 'sm' ? '8px' : '12px';
  const radius = borderRadius === 'full' ? '9999px' : '0.375rem';

  return (
    <div
      style={{
        width: '100%',
        height: height,
        backgroundColor: '#E2E8F0',
        borderRadius: radius,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          height: '100%',
          width: `${value}%`,
          backgroundColor: colorMap[colorScheme] || colorMap.blue,
          transition: 'width 0.3s ease',
        }}
      />
    </div>
  );
};

// Custom Avatar component
const Avatar = ({ name, size, bg }: { name: string; size: string; bg: string }) => {
  const initials = name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase();

  const sizeMap: Record<string, string> = {
    xl: '80px',
    lg: '60px',
    md: '48px',
    sm: '32px',
  };

  return (
    <Box
      w={sizeMap[size] || sizeMap.md}
      h={sizeMap[size] || sizeMap.md}
      bg={bg}
      borderRadius="full"
      display="flex"
      alignItems="center"
      justifyContent="center"
      color="white"
      fontWeight="bold"
      fontSize={size === 'xl' ? 'xl' : size === 'lg' ? 'lg' : 'md'}
    >
      {initials}
    </Box>
  );
};

// Custom CircularProgress component
const CircularProgress = ({ value, color, size, thickness, children }: any) => {
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  return (
    <Box position="relative" w={size} h={size} display="inline-flex">
      <svg width={size} height={size} viewBox="0 0 120 120">
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          stroke="#E2E8F0"
          strokeWidth={thickness}
        />
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={thickness}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 60 60)"
          style={{ transition: 'stroke-dashoffset 0.3s ease' }}
        />
      </svg>
      <Box
        position="absolute"
        top="50%"
        left="50%"
        transform="translate(-50%, -50%)"
      >
        {children}
      </Box>
    </Box>
  );
};

export const MyCareerDashboard = () => {
  const { data: careerPath, isLoading, error } = useCareerPath(DEMO_EMPLOYEE_ID);

  // Transform backend data to match component requirements
  const employee = useMemo(() => {
    return {
      name: careerPath?.employee_id || `Employee ${DEMO_EMPLOYEE_ID}`,
      role: careerPath?.current_role || 'Unknown Role',
      level: 'L4',
      tenure: '4 years 7 months',
      skillCoverage: 78,
      mandatoryCompliance: 87,
    };
  }, [careerPath]);

  // Transform career paths from backend
  const careerPaths = useMemo(() => {
    if (!careerPath?.career_paths) {
      return [];
    }

    return careerPath.career_paths.slice(0, 3).map((path: any, idx: number) => {
      const readiness = path.readiness_percentage || 0;
      let match = 'Exploratory';
      let color = 'purple';
      if (readiness >= 85) {
        match = 'Best Fit';
        color = 'green';
      } else if (readiness >= 70) {
        match = 'Alternative Path';
        color = 'blue';
      }

      return {
        role: path.role_name || 'Target Role',
        readiness: Math.round(readiness),
        timeline: path.timeline_to_reach || path.timeline_months 
          ? `${path.timeline_months || 12} months`
          : 'TBD',
        match,
        color,
        gaps: path.skill_gaps || [],
        strengths: path.strengths || [],
        requiredSkills: path.required_skills || [],
      };
    });
  }, [careerPath]);

  // Generate AI recommendations from career path gaps
  const aiRecommendations = useMemo(() => {
    if (!careerPath?.career_paths || careerPath.career_paths.length === 0) {
      return [];
    }

    const primaryPath = careerPath.career_paths[0];
    const trainings = primaryPath?.required_trainings || [];

    return trainings.slice(0, 3).map((training: any, idx: number) => ({
      priority: idx === 0 ? 'high' : 'medium',
      title: typeof training === 'string' ? training : training.name || 'Training Required',
      description: typeof training === 'string' 
        ? `Required for ${primaryPath.role_name || 'career path'}`
        : training.description || 'Complete this training to progress',
      action: 'Enroll Now',
      hours: 'TBD',
      deadline: 'Q1 2025',
    }));
  }, [careerPath]);

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
        <Skeleton height="600px" borderRadius="lg" />
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
            <Text fontWeight="semibold" color="red.800">Failed to load career path data</Text>
          </HStack>
          <Text fontSize="sm" color="red.700" ml={7}>
            {error instanceof Error ? error.message : 'An unexpected error occurred. Please try again later.'}
          </Text>
        </Box>
      </VStack>
    );
  }

  // Mock AI recommendations removed - now using backend data
  const mockAiRecommendations = [
    {
      priority: 'high',
      title: 'Renew ISO 27001 Security Certification',
      description: 'Your certification expires in 14 days. This is mandatory for your role.',
      action: 'Enroll Now',
      hours: '8 hours',
      deadline: 'Dec 15, 2024',
    },
    {
      priority: 'high',
      title: 'Complete AWS Advanced Networking Course',
      description: 'Close your cloud computing gap to reach 95% for Principal Engineer path.',
      action: 'Start Course',
      hours: '16 hours',
      deadline: 'Jan 2025',
    },
    {
      priority: 'medium',
      title: 'Join Leadership Skills Workshop',
      description: 'Required for L5 promotion. Next cohort starts January 2025.',
      action: 'Reserve Spot',
      hours: '24 hours',
      deadline: 'Q1 2025',
    },
  ];

  return (
    <VStack spacing={6} align="stretch">
      {/* Header */}
      <Box>
        <HStack justify="space-between">
          <Box>
            <Text fontSize="3xl" fontWeight="semibold">
              My Career Dashboard
            </Text>
            <Text color="gray.600" mt={1}>
              Personal development · Career progression · AI coaching
            </Text>
          </Box>
          <Avatar size="xl" name={employee.name} bg="skoda.green" />
        </HStack>
      </Box>

      {/* Personal Stats */}
      <Grid templateColumns="repeat(4, 1fr)" gap={4}>
        <StatCard
          label="Current Level"
          value={employee.level}
          icon={Target}
          badge={<Badge colorScheme="green">Senior</Badge>}
        />
        <StatCard
          label="Skill Coverage"
          value={`${employee.skillCoverage}%`}
          change="+8% this year"
          trend="up"
          icon={TrendingUp}
          badge={<Badge colorScheme="green">+8%</Badge>}
        />
        <StatCard
          label="Certifications"
          value="5/6"
          change="1 expiring soon"
          icon={Award}
          badge={<Badge colorScheme="orange">Action Needed</Badge>}
        />
        <StatCard
          label="Learning Hours"
          value="48"
          change="This year"
          icon={BookOpen}
          badge={<Badge colorScheme="blue">2024</Badge>}
        />
      </Grid>

      {/* Career Path Visual Tree */}
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
              Your Career Path Options
            </Text>
            <Text fontSize="xs" color="gray.600" mt={1}>
              3 progression paths based on your skills and interests
            </Text>
          </Box>
          <Badge colorScheme="green" fontSize="sm" px={3} py={1}>
            Principal Engineer Recommended
          </Badge>
        </HStack>

        {/* Current Role (Center) */}
        <VStack spacing={6}>
          <Box
            p={5}
            bg="skoda.green"
            color="white"
            borderRadius="lg"
            boxShadow="lg"
            textAlign="center"
            minW="250px"
          >
            <Text fontWeight="bold" fontSize="lg">
              {employee.role}
            </Text>
            <Text fontSize="xs" opacity={0.9} mt={1}>
              Current Position · {employee.level}
            </Text>
          </Box>

          {/* Branching Paths */}
          <Grid templateColumns="repeat(3, 1fr)" gap={4} w="full">
            {careerPaths.length > 0 ? (
              careerPaths.map((path, idx) => (
              <MotionBox
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
              >
                <Box
                  p={5}
                  bg="white"
                  borderRadius="lg"
                  border="2px solid"
                  borderColor={`${path.color}.300`}
                  cursor="pointer"
                  _hover={{
                    borderColor: `${path.color}.500`,
                    boxShadow: 'lg',
                    transform: 'translateY(-4px)',
                  }}
                  transition="all 0.2s"
                  h="full"
                >
                  {/* Header */}
                  <HStack justify="space-between" mb={4}>
                    <Badge colorScheme={path.color}>{path.match}</Badge>
                    <CircularProgress
                      value={path.readiness}
                      color={path.color === 'green' ? '#4da944' : path.color === 'blue' ? '#3b82f6' : '#9333ea'}
                      size="60px"
                      thickness="8px"
                    >
                      <Text fontSize="sm" fontWeight="bold">
                        {path.readiness}%
                      </Text>
                    </CircularProgress>
                  </HStack>

                  <Text fontWeight="bold" fontSize="lg" mb={1}>
                    {path.role}
                  </Text>
                  <HStack mb={4} fontSize="xs" color="gray.600">
                    <Icon as={Clock} w={3} h={3} />
                    <Text>{path.timeline} to ready</Text>
                  </HStack>

                  {/* Strengths */}
                  <Box mb={3}>
                    <Text fontSize="xs" fontWeight="semibold" mb={2} color="green.600">
                      Your Strengths:
                    </Text>
                    {path.strengths.map((strength, i) => (
                      <HStack key={i} fontSize="xs" mb={1}>
                        <Icon as={CheckCircle2} w={3} h={3} color="green.600" />
                        <Text>{strength}</Text>
                      </HStack>
                    ))}
                  </Box>

                  {/* Gaps */}
                  <Box mb={4}>
                    <Text fontSize="xs" fontWeight="semibold" mb={2} color="orange.600">
                      Skills to Develop:
                    </Text>
                    {path.gaps.map((gap, i) => (
                      <HStack key={i} fontSize="xs" mb={1}>
                        <Box w={2} h={2} bg="orange.400" borderRadius="full" />
                        <Text>{gap}</Text>
                      </HStack>
                    ))}
                  </Box>

                  <Button
                    size="sm"
                    colorScheme={path.color}
                    variant="outline"
                    w="full"
                    rightIcon={<Icon as={ChevronRight} />}
                  >
                    View Roadmap
                  </Button>
                </Box>
              </MotionBox>
              ))
            ) : (
              <Box p={8} textAlign="center" bg="gray.50" borderRadius="lg" gridColumn="1 / -1">
                <Text color="gray.500" fontSize="sm">No career paths available</Text>
              </Box>
            )}
          </Grid>
        </VStack>
      </MotionBox>

      {/* Detailed Skill Gap for Primary Path */}
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
              Principal Engineer Readiness
            </Text>
            <Text fontSize="xs" color="gray.600" mt={1}>
              Your progress toward target role
            </Text>
          </Box>
          <Badge colorScheme="green" fontSize="lg" px={4} py={2}>
            85% Ready
          </Badge>
        </HStack>

        <VStack spacing={4} align="stretch">
          {careerPaths.length > 0 && careerPaths[0].requiredSkills.length > 0 ? (
            careerPaths[0].requiredSkills.map((skill: any, idx: number) => {
              const skillName = typeof skill === 'string' ? skill : skill.skill || skill.name || 'Skill';
              const current = typeof skill === 'object' ? (skill.current || 0) : 0;
              const target = typeof skill === 'object' ? (skill.target || 100) : 100;
              
              return (
                <Box key={idx}>
                  <HStack justify="space-between" mb={2}>
                    <Text fontSize="sm" fontWeight="medium">
                      {skillName}
                    </Text>
                    <HStack>
                      <Text fontSize="sm" color={current >= target ? 'green.600' : 'orange.600'}>
                        {current}% / {target}%
                      </Text>
                    </HStack>
                  </HStack>
                  <Box position="relative" h={3} bg="gray.200" borderRadius="full" overflow="hidden">
                    <Box
                      position="absolute"
                      top={0}
                      left={0}
                      h="full"
                      bg={current >= target ? 'green.500' : 'orange.400'}
                      borderRadius="full"
                      w={`${target > 0 ? (current / target) * 100 : 0}%`}
                      transition="all 0.3s"
                    />
                    <Box
                      position="absolute"
                      top={0}
                      left={`${target}%`}
                      h="full"
                      w="2px"
                      bg="gray.700"
                      opacity={0.5}
                    />
                  </Box>
                </Box>
              );
            })
          ) : (
            <Text fontSize="sm" color="gray.500" textAlign="center" py={4}>
              No skills data available
            </Text>
          )}
        </VStack>

        <Box mt={6} p={4} bg="green.50" borderRadius="lg">
          <Text fontSize="sm" fontWeight="semibold" mb={2}>
            🎯 Next Steps to Close Gaps:
          </Text>
          <VStack align="stretch" spacing={2} fontSize="sm">
            <Text>1. Complete "Enterprise Architecture Patterns" course (12 hours)</Text>
            <Text>2. Mentor 2 junior developers for 3 months</Text>
            <Text>3. Lead 1 cross-team technical initiative</Text>
          </VStack>
        </Box>
      </MotionBox>

      {/* AI Coaching Recommendations */}
      <MotionBox
        bg="gradient-to-br"
        bgGradient="linear(to-br, green.50, white)"
        p={6}
        borderRadius="lg"
        border="1px solid"
        borderColor="gray.200"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <HStack mb={5}>
          <Icon as={Sparkles} w={6} h={6} color="skoda.green" />
          <Text fontSize="xl" fontWeight="semibold">
            AI Personalized Recommendations
          </Text>
        </HStack>

        <VStack spacing={3} align="stretch">
          {aiRecommendations.length > 0 ? (
            aiRecommendations.map((rec, idx) => (
            <Box
              key={idx}
              p={4}
              bg="white"
              borderRadius="lg"
              border="1px solid"
              borderColor={rec.priority === 'high' ? 'red.200' : 'orange.200'}
            >
              <HStack justify="space-between" mb={2}>
                <HStack>
                  <Badge colorScheme={rec.priority === 'high' ? 'red' : 'orange'}>
                    {rec.priority.toUpperCase()} PRIORITY
                  </Badge>
                  <HStack fontSize="xs" color="gray.600">
                    <Icon as={Clock} w={3} h={3} />
                    <Text>{rec.hours}</Text>
                  </HStack>
                </HStack>
                <Text fontSize="xs" color="gray.600">
                  Deadline: {rec.deadline}
                </Text>
              </HStack>

              <Text fontWeight="semibold" fontSize="sm" mb={2}>
                {rec.title}
              </Text>
              <Text fontSize="sm" color="gray.600" mb={3}>
                {rec.description}
              </Text>

              <HStack>
                <Button size="sm" colorScheme="brand">
                  {rec.action}
                </Button>
                <Button size="sm" variant="outline">
                  Learn More
                </Button>
              </HStack>
            </Box>
            ))
          ) : (
            <Box p={4} bg="gray.50" borderRadius="lg" textAlign="center">
              <Text color="gray.500" fontSize="sm">No recommendations available</Text>
            </Box>
          )}
        </VStack>
      </MotionBox>

      {/* Learning Progress */}
      <Grid templateColumns="repeat(2, 1fr)" gap={6}>
        <Box p={6} bg="white" borderRadius="lg" border="1px solid" borderColor="gray.200">
          <Text fontSize="lg" fontWeight="semibold" mb={4}>
            In Progress Courses
          </Text>
          <VStack spacing={3} align="stretch">
            <Box p={3} bg="blue.50" borderRadius="md">
              <Text fontSize="sm" fontWeight="medium" mb={1}>
                AWS Advanced Networking
              </Text>
              <HStack justify="space-between" mb={2}>
                <Text fontSize="xs" color="gray.600">
                  Progress: 65%
                </Text>
                <Text fontSize="xs" color="gray.600">
                  12 hours remaining
                </Text>
              </HStack>
              <Progress value={65} size="sm" colorScheme="blue" borderRadius="full" />
            </Box>

            <Box p={3} bg="purple.50" borderRadius="md">
              <Text fontSize="sm" fontWeight="medium" mb={1}>
                Enterprise Architecture Patterns
              </Text>
              <HStack justify="space-between" mb={2}>
                <Text fontSize="xs" color="gray.600">
                  Progress: 30%
                </Text>
                <Text fontSize="xs" color="gray.600">
                  21 hours remaining
                </Text>
              </HStack>
              <Progress value={30} size="sm" colorScheme="purple" borderRadius="full" />
            </Box>
          </VStack>
        </Box>

        <Box p={6} bg="white" borderRadius="lg" border="1px solid" borderColor="gray.200">
          <Text fontSize="lg" fontWeight="semibold" mb={4}>
            Recent Achievements
          </Text>
          <VStack spacing={3} align="stretch">
            <HStack p={3} bg="green.50" borderRadius="md">
              <Icon as={Award} w={6} h={6} color="green.600" />
              <Box>
                <Text fontSize="sm" fontWeight="medium">
                  AWS Solutions Architect Certified
                </Text>
                <Text fontSize="xs" color="gray.600">
                  Completed Nov 2024
                </Text>
              </Box>
            </HStack>

            <HStack p={3} bg="green.50" borderRadius="md">
              <Icon as={Award} w={6} h={6} color="green.600" />
              <Box>
                <Text fontSize="sm" fontWeight="medium">
                  Scrum Master Certification
                </Text>
                <Text fontSize="xs" color="gray.600">
                  Completed Sep 2024
                </Text>
              </Box>
            </HStack>
          </VStack>
        </Box>
      </Grid>
    </VStack>
  );
};