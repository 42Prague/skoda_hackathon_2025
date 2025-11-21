import { Box, Grid, VStack, HStack, Text, Badge, Button, Progress, Avatar } from '@chakra-ui/react';
import { Icon } from '../components/common/Icon';
import { AlertTriangle, TrendingUp, Users, Target, CheckCircle2 } from 'lucide-react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, Legend } from 'recharts';
import { StatCard } from '../components/common/StatCard';
import { RiskBadge } from '../components/common/RiskBadge';
import { useLang } from '../hooks/useLang';
import { motion } from 'motion/react';

const MotionBox = motion.create(Box);

export const SuccessionPage = () => {
  const { t } = useLang();

  const radarData = [
    { skill: 'Technical Excellence', current: 85, target: 90 },
    { skill: 'Leadership', current: 72, target: 85 },
    { skill: 'Strategic Thinking', current: 68, target: 80 },
    { skill: 'Stakeholder Mgmt', current: 78, target: 85 },
    { skill: 'Innovation', current: 82, target: 85 },
    { skill: 'Team Development', current: 75, target: 85 },
  ];

  const keyRoles = [
    { role: 'Engineering Manager', incumbent: 'Martin Kovář', risk: 'medium', retirementDate: '2026-08', readyCandidates: 2, pipelineCandidates: 3 },
    { role: 'Principal Architect', incumbent: 'Jan Horáček', risk: 'low', retirementDate: '2028-03', readyCandidates: 3, pipelineCandidates: 2 },
    { role: 'DevOps Lead', incumbent: 'Lucie Procházková', risk: 'high', retirementDate: '2025-12', readyCandidates: 0, pipelineCandidates: 2 },
  ];

  const candidates = [
    { name: 'Jana Nováková', currentRole: 'Senior Developer', targetRole: 'Engineering Manager', readiness: 85, gap: 'Leadership training needed', timeline: '8 months', strengths: ['Technical', 'Communication'] },
    { name: 'Petr Dvořák', currentRole: 'Team Lead', targetRole: 'Engineering Manager', readiness: 78, gap: 'Budget management, strategic planning', timeline: '12 months', strengths: ['Leadership', 'Agile'] },
    { name: 'Martin Černý', currentRole: 'Full Stack Dev', targetRole: 'Principal Architect', readiness: 88, gap: 'Enterprise architecture patterns', timeline: '6 months', strengths: ['System Design', 'Mentoring'] },
    { name: 'Kateřina Veselá', currentRole: 'Senior Developer', targetRole: 'Principal Architect', readiness: 82, gap: 'Large-scale system experience', timeline: '10 months', strengths: ['Technical', 'Documentation'] },
  ];

  return (
    <VStack spacing={6} align="stretch">
      <Box>
        <Text fontSize="3xl" fontWeight="semibold">{t('succession.title')}</Text>
        <Text color="gray.600" mt={1}>Key role coverage · Talent pipeline · Risk assessment</Text>
      </Box>

      <Grid templateColumns="repeat(4, 1fr)" gap={4}>
        <StatCard label={t('succession.keyRolesCovered')} value={12} icon={Target} badge={<Badge colorScheme="green">Good</Badge>} />
        <StatCard label={t('succession.readySuccessors')} value={8} change="+3" trend="up" icon={CheckCircle2} badge={<Badge colorScheme="green">+3</Badge>} />
        <StatCard label={t('succession.highRiskRoles')} value={3} icon={AlertTriangle} badge={<Badge colorScheme="red">Urgent</Badge>} />
        <StatCard label={t('succession.pipelineStrength')} value="82%" change="+15%" trend="up" icon={TrendingUp} badge={<Badge colorScheme="green">+15%</Badge>} />
      </Grid>

      <MotionBox bg="white" p={6} borderRadius="lg" border="1px solid" borderColor="gray.200" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <HStack justify="space-between" mb={5}>
          <Text fontSize="xl" fontWeight="semibold">{t('succession.criticalRoleCoverage')}</Text>
          <Button variant="outline" size="sm">View All Roles</Button>
        </HStack>
        <VStack spacing={3} align="stretch">
          {keyRoles.map((role, idx) => (
            <Box key={idx} p={4} bg="gray.50" borderRadius="lg" border="1px solid" borderColor="gray.200">
              <HStack justify="space-between" mb={3}>
                <Box flex={1}>
                  <HStack mb={1}>
                    <Text fontSize="lg" fontWeight="semibold">{role.role}</Text>
                    <RiskBadge level={role.risk as any} label={`${role.risk.charAt(0).toUpperCase() + role.risk.slice(1)} Risk`} />
                  </HStack>
                  <Text fontSize="xs" color="gray.600">Current: {role.incumbent} · Est. Vacancy: {new Date(role.retirementDate).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}</Text>
                </Box>
              </HStack>
              <Grid templateColumns="repeat(3, 1fr)" gap={4}>
                <Box>
                  <Text fontSize="xs" color="gray.600" mb={2}>Ready Now</Text>
                  <HStack>
                    <Box w={10} h={10} borderRadius="lg" display="flex" alignItems="center" justifyContent="center" bg={role.readyCandidates > 0 ? 'green.100' : 'red.100'} color={role.readyCandidates > 0 ? 'green.700' : 'red.700'} fontWeight="semibold">{role.readyCandidates}</Box>
                    <Text fontSize="xs" color="gray.600">candidates</Text>
                  </HStack>
                </Box>
                <Box>
                  <Text fontSize="xs" color="gray.600" mb={2}>In Pipeline</Text>
                  <HStack>
                    <Box w={10} h={10} borderRadius="lg" bg="blue.100" color="blue.700" display="flex" alignItems="center" justifyContent="center" fontWeight="semibold">{role.pipelineCandidates}</Box>
                    <Text fontSize="xs" color="gray.600">developing</Text>
                  </HStack>
                </Box>
                <Box>
                  <Text fontSize="xs" color="gray.600" mb={2}>Bench Strength</Text>
                  <Progress value={(role.readyCandidates / 3) * 100} h={2} mt={3} colorScheme="green" borderRadius="full" />
                </Box>
              </Grid>
            </Box>
          ))}
        </VStack>
      </MotionBox>

      <Grid templateColumns="1fr 2fr" gap={6}>
        <MotionBox bg="white" p={6} borderRadius="lg" border="1px solid" borderColor="gray.200" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Text fontSize="xl" fontWeight="semibold" mb={4}>{t('succession.successorReadiness')}</Text>
          <ResponsiveContainer width="100%" height={280}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis dataKey="skill" tick={{ fontSize: 10 }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 9 }} />
              <Radar name="Current" dataKey="current" stroke="#4da944" fill="#4da944" fillOpacity={0.5} />
              <Radar name="Target" dataKey="target" stroke="#0d1b2a" fill="#0d1b2a" fillOpacity={0.2} />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
            </RadarChart>
          </ResponsiveContainer>
        </MotionBox>

        <MotionBox bg="white" p={6} borderRadius="lg" border="1px solid" borderColor="gray.200" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <Text fontSize="xl" fontWeight="semibold" mb={5}>{t('succession.highPotentialSuccessors')}</Text>
          <VStack spacing={3} align="stretch">
            {candidates.map((candidate, idx) => (
              <Box key={idx} p={4} bg="white" borderRadius="lg" border="1px solid" borderColor="gray.200" _hover={{ borderColor: 'skoda.green' }} transition="all 0.2s">
                <HStack spacing={4}>
                  <Avatar size="md" name={candidate.name} bg="skoda.green" color="white" />
                  <Box flex={1}>
                    <HStack justify="space-between" mb={2}>
                      <Box>
                        <Text fontWeight="medium">{candidate.name}</Text>
                        <Text fontSize="xs" color="gray.600">{candidate.currentRole} → {candidate.targetRole}</Text>
                      </Box>
                      <Box textAlign="right">
                        <HStack justify="flex-end" mb={1}>
                          <Text fontSize="sm">{candidate.readiness}%</Text>
                          <Box w={3} h={3} borderRadius="full" bg={candidate.readiness >= 85 ? 'green.500' : 'orange.400'} />
                        </HStack>
                        <Text fontSize="xs" color="gray.600">{candidate.timeline}</Text>
                      </Box>
                    </HStack>
                    <HStack mb={2}>
                      {candidate.strengths.map((strength, sIdx) => (
                        <Badge key={sIdx} variant="outline" colorScheme="green" fontSize="xs">{strength}</Badge>
                      ))}
                    </HStack>
                    <Text fontSize="xs" color="gray.600"><strong>Gap:</strong> {candidate.gap}</Text>
                    <Progress value={candidate.readiness} h={1.5} mt={2} colorScheme="green" borderRadius="full" />
                  </Box>
                </HStack>
              </Box>
            ))}
          </VStack>
        </MotionBox>
      </Grid>
    </VStack>
  );
};
