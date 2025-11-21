import { 
  Box, 
  Grid, 
  VStack, 
  HStack, 
  Text, 
  Badge,
  Button,
  Input
} from '@chakra-ui/react';
import { Icon } from '../components/common/Icon';
import { Search, Filter, Download, TrendingUp, AlertCircle } from 'lucide-react';
import { HeatmapCell } from '../components/common/HeatmapCell';
import { useLang } from '../hooks/useLang';
import { motion } from 'motion/react';

const MotionBox = motion.create(Box);

export const SkillHeatmapPage = () => {
  const { t } = useLang();

  const skills = [
    'React/Frontend',
    'Backend APIs',
    'Cloud (AWS/Azure)',
    'Database Design',
    'DevOps/CI-CD',
    'Security',
    'Agile/Scrum',
    'Leadership',
  ];

  const employees = [
    { name: 'Jana Nováková', role: 'Senior Developer', skills: [4, 5, 3, 4, 3, 2, 4, 3], trend: 'up', trendValue: '+12%' },
    { name: 'Petr Dvořák', role: 'Team Lead', skills: [4, 4, 4, 3, 4, 3, 5, 5], trend: 'stable', trendValue: 'Stable' },
    { name: 'Eva Svobodová', role: 'QA Engineer', skills: [3, 2, 2, 3, 4, 3, 4, 3], trend: 'down', trendValue: '-5%' },
    { name: 'Martin Černý', role: 'Full Stack Dev', skills: [5, 5, 4, 5, 3, 3, 3, 2], trend: 'up', trendValue: '+8%' },
    { name: 'Lucie Procházková', role: 'DevOps Engineer', skills: [2, 3, 5, 3, 5, 4, 3, 3], trend: 'up', trendValue: '+15%' },
    { name: 'Tomáš Novák', role: 'Junior Developer', skills: [3, 2, 1, 2, 2, 2, 3, 1], trend: 'up', trendValue: '+18%' },
    { name: 'Kateřina Veselá', role: 'Senior Developer', skills: [5, 4, 3, 4, 3, 4, 4, 4], trend: 'stable', trendValue: 'Stable' },
    { name: 'Jan Horáček', role: 'Architect', skills: [5, 5, 5, 5, 4, 5, 4, 5], trend: 'stable', trendValue: 'Stable' },
  ];

  const teamAvg = skills.map((_, idx) => {
    const sum = employees.reduce((acc, emp) => acc + emp.skills[idx], 0);
    return (sum / employees.length).toFixed(1);
  });

  const getSkillLevel = (level: number) => {
    const labels = ['Novice', 'Basic', 'Intermediate', 'Advanced', 'Expert'];
    return labels[level - 1];
  };

  return (
    <VStack spacing={6} align="stretch">
      <HStack justify="space-between">
        <Box>
          <Text fontSize="3xl" fontWeight="semibold">{t('heatmap.title')}</Text>
          <Text color="gray.600" mt={1}>{t('heatmap.subtitle')} · 8 employees</Text>
        </Box>
        <HStack>
          <Button leftIcon={<Icon as={Filter} />} variant="outline">
            {t('common.filter')}
          </Button>
          <Button leftIcon={<Icon as={Download} />} variant="outline">
            {t('common.export')}
          </Button>
        </HStack>
      </HStack>

      <HStack justify="space-between">
        <Box maxW="320px" position="relative">
          <Box position="absolute" left={3} top="50%" transform="translateY(-50%)" zIndex={1}>
            <Icon as={Search} w={4} h={4} color="gray.400" />
          </Box>
          <Input placeholder="Search employee or skill..." bg="white" pl={10} />
        </Box>
        <HStack spacing={4}>
          <Text fontSize="xs" color="gray.600">{t('heatmap.skillLevels')}:</Text>
          {[1, 2, 3, 4, 5].map((level) => (
            <HStack key={level} spacing={1}>
              <Box
                w={8}
                h={6}
                borderRadius="md"
                bg={
                  level === 5 ? '#3a8234' :
                  level === 4 ? '#4da944' :
                  level === 3 ? '#9dd595' :
                  level === 2 ? '#fed7aa' : '#fecaca'
                }
                display="flex"
                alignItems="center"
                justifyContent="center"
                fontSize="xs"
                fontWeight="semibold"
                color={level >= 3 ? (level >= 4 ? 'white' : '#0d1b2a') : level === 2 ? '#9a3412' : '#991b1b'}
              >
                {level}
              </Box>
              <Text fontSize="xs" color="gray.600">{getSkillLevel(level)}</Text>
            </HStack>
          ))}
        </HStack>
      </HStack>

      <MotionBox
        bg="white"
        p={6}
        borderRadius="lg"
        border="1px solid"
        borderColor="gray.200"
        overflowX="auto"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Box as="table" w="full" style={{ borderCollapse: 'collapse' }}>
          <Box as="thead">
            <Box as="tr">
              <Box
                as="th"
                textAlign="left"
                minW="200px"
                py={3}
                px={3}
                borderBottom="2px solid"
                borderColor="gray.200"
              >
                <Text fontSize="sm" fontWeight="semibold">Employee</Text>
              </Box>
              {skills.map((skill, idx) => (
                <Box
                  key={idx}
                  as="th"
                  textAlign="center"
                  minW="120px"
                  px={3}
                  py={3}
                  borderBottom="2px solid"
                  borderColor="gray.200"
                >
                  <Text fontSize="xs" fontWeight="semibold">{skill}</Text>
                </Box>
              ))}
              <Box
                as="th"
                textAlign="center"
                minW="80px"
                px={3}
                py={3}
                borderBottom="2px solid"
                borderColor="gray.200"
              >
                <Text fontSize="xs" fontWeight="semibold">Trend</Text>
              </Box>
            </Box>
          </Box>
          <Box as="tbody">
            {employees.map((emp, empIdx) => (
              <Box
                key={empIdx}
                as="tr"
                _hover={{ bg: 'gray.50' }}
                transition="background 0.2s"
              >
                <Box as="td" py={4} px={3} borderBottom="1px solid" borderColor="gray.200">
                  <Text fontWeight="medium" fontSize="sm">{emp.name}</Text>
                  <Text fontSize="xs" color="gray.600">{emp.role}</Text>
                </Box>
                {emp.skills.map((level, skillIdx) => (
                  <Box key={skillIdx} as="td" px={3} py={4} textAlign="center" borderBottom="1px solid" borderColor="gray.200">
                    <HeatmapCell value={level} employeeName={emp.name} skillName={skills[skillIdx]} />
                  </Box>
                ))}
                <Box as="td" px={3} py={4} textAlign="center" borderBottom="1px solid" borderColor="gray.200">
                  {emp.trend === 'up' && (
                    <VStack spacing={0.5}>
                      <Icon as={TrendingUp} w={4} h={4} color="green.600" />
                      <Text fontSize="xs" color="green.600">{emp.trendValue}</Text>
                    </VStack>
                  )}
                  {emp.trend === 'down' && (
                    <VStack spacing={0.5}>
                      <Icon as={AlertCircle} w={4} h={4} color="red.600" />
                      <Text fontSize="xs" color="red.600">{emp.trendValue}</Text>
                    </VStack>
                  )}
                  {emp.trend === 'stable' && (
                    <Text fontSize="xs" color="gray.600">{emp.trendValue}</Text>
                  )}
                </Box>
              </Box>
            ))}
            <Box as="tr" bg="green.50">
              <Box as="td" py={4} px={3} borderTop="2px solid" borderColor="skoda.green">
                <Text fontWeight="medium" fontSize="sm">Team Average</Text>
                <Text fontSize="xs" color="gray.600">Aggregated skill level</Text>
              </Box>
              {teamAvg.map((avg, idx) => (
                <Box key={idx} as="td" px={3} py={4} textAlign="center" borderTop="2px solid" borderColor="skoda.green">
                  <Text fontSize="sm" fontWeight="semibold">{avg}</Text>
                </Box>
              ))}
              <Box as="td" borderTop="2px solid" borderColor="skoda.green"></Box>
            </Box>
          </Box>
        </Box>
      </MotionBox>

      <Grid templateColumns="repeat(3, 1fr)" gap={4}>
        <MotionBox
          p={5}
          bg="green.50"
          borderRadius="lg"
          border="1px solid"
          borderColor="green.200"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <Text fontSize="lg" fontWeight="semibold" mb={1}>{t('heatmap.strongestSkills')}</Text>
          <Text fontSize="xs" color="gray.600" mb={4}>Team-wide proficiency</Text>
          <VStack spacing={2} align="stretch">
            <HStack justify="space-between">
              <Text fontSize="sm">Backend APIs</Text>
              <Badge colorScheme="green">4.0 avg</Badge>
            </HStack>
            <HStack justify="space-between">
              <Text fontSize="sm">React/Frontend</Text>
              <Badge colorScheme="green">3.9 avg</Badge>
            </HStack>
          </VStack>
        </MotionBox>

        <MotionBox
          p={5}
          bg="red.50"
          borderRadius="lg"
          border="1px solid"
          borderColor="red.200"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <Text fontSize="lg" fontWeight="semibold" mb={1}>{t('heatmap.criticalGaps')}</Text>
          <Text fontSize="xs" color="gray.600" mb={4}>Below target threshold</Text>
          <VStack spacing={2} align="stretch">
            <HStack justify="space-between">
              <Text fontSize="sm">Security</Text>
              <Badge colorScheme="red">3.0 avg</Badge>
            </HStack>
            <HStack justify="space-between">
              <Text fontSize="sm">Cloud (AWS/Azure)</Text>
              <Badge colorScheme="orange">3.3 avg</Badge>
            </HStack>
          </VStack>
        </MotionBox>

        <MotionBox
          p={5}
          bg="white"
          borderRadius="lg"
          border="1px solid"
          borderColor="gray.200"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <Text fontSize="lg" fontWeight="semibold" mb={1}>{t('heatmap.topPerformers')}</Text>
          <Text fontSize="xs" color="gray.600" mb={4}>Highest skill coverage</Text>
          <VStack spacing={2} align="stretch">
            <HStack justify="space-between">
              <Text fontSize="sm">Jan Horáček</Text>
              <Badge variant="outline" colorScheme="green">4.8 avg</Badge>
            </HStack>
            <HStack justify="space-between">
              <Text fontSize="sm">Martin Černý</Text>
              <Badge variant="outline" colorScheme="green">4.0 avg</Badge>
            </HStack>
          </VStack>
        </MotionBox>
      </Grid>
    </VStack>
  );
};