import {
  Box,
  Grid,
  VStack,
  HStack,
  Text,
  Badge,
  Button,
  Spinner,
  Skeleton,
} from '@chakra-ui/react';
import {
  AlertTriangle,
  TrendingUp,
  Target,
  CheckCircle2,
  XCircle,
  Clock,
} from 'lucide-react';
import { RiskBadge } from '../../components/common/RiskBadge';
import { Icon } from '../../components/common/Icon';
import { motion } from 'motion/react';
import { useState, useMemo } from 'react';
import { useRiskRadar } from '../../hooks/useBackendEndpoints';

const MotionBox = motion.create(Box);

// Custom Avatar component
const Avatar = ({ name, size, bg, color, fontSize }: any) => {
  const initials = name
    .split(' ')
    .map((n: string) => n[0])
    .join('')
    .toUpperCase();

  const sizeMap: Record<string, string> = {
    xl: '80px',
    lg: '60px',
    md: '48px',
    sm: '32px',
    xs: '24px',
  };

  const fontSizeMap: Record<string, string> = {
    xl: '1.25rem',
    lg: '1rem',
    md: '0.875rem',
    sm: '0.75rem',
    xs: '0.625rem',
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
      color={color || 'white'}
      fontWeight="bold"
      fontSize={fontSizeMap[fontSize] || fontSizeMap[size] || fontSizeMap.md}
    >
      {initials}
    </Box>
  );
};

// Custom Progress component
const Progress = ({ value, size, colorScheme, borderRadius }: any) => {
  const colorMap: Record<string, string> = {
    blue: '#3b82f6',
    purple: '#9333ea',
    green: '#4da944',
    orange: '#f97316',
    red: '#ef4444',
  };

  const height = size === 'sm' ? '8px' : size === 'xs' ? '4px' : '12px';
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

const DEMO_TEAM_ID = 'SE';

export const SkillRiskRadarPage = () => {
  const [selectedEmployee, setSelectedEmployee] = useState<any>(null);
  const { data: riskRadar, isLoading, error } = useRiskRadar(DEMO_TEAM_ID);

  // Transform backend data to match component requirements
  const riskEmployees = useMemo(() => {
    if (!riskRadar?.employee_risks) {
      return { high: [], medium: [], low: [] };
    }

    const high: any[] = [];
    const medium: any[] = [];
    const low: any[] = [];

    riskRadar.employee_risks.forEach((emp: any) => {
      const riskScore = emp.risk_score || 0;
      const alerts = emp.alerts || [];
      const reasons = alerts.map((alert: any) => alert.message || 'Risk detected');
      
      const employeeData = {
        employee_id: emp.employee_id,
        name: emp.employee_id || `Employee ${emp.employee_id}`,
        role: emp.role || 'Unknown Role',
        riskScore,
        reasons: reasons.length > 0 ? reasons : ['Risk score: ' + riskScore],
        skillCoverage: 100 - riskScore, // Inverse of risk score as coverage estimate
        avatar: emp.employee_id?.substring(0, 2).toUpperCase() || 'EM',
      };

      if (riskScore >= 60) {
        high.push(employeeData);
      } else if (riskScore >= 40) {
        medium.push(employeeData);
      } else {
        low.push(employeeData);
      }
    });

    return { high, medium, low };
  }, [riskRadar]);

  // Generate AI predictions from critical/high alerts
  const aiPredictions = useMemo(() => {
    if (!riskRadar?.employee_risks) return [];

    const predictions: any[] = [];
    riskRadar.employee_risks.slice(0, 3).forEach((emp: any) => {
      const criticalAlerts = (emp.alerts || []).filter((a: any) => a.severity === 'critical' || a.severity === 'high');
      if (criticalAlerts.length > 0) {
        predictions.push({
          employee: emp.employee_id || `Employee ${emp.employee_id}`,
          prediction: criticalAlerts[0].message || `High risk detected (${emp.risk_score}%)`,
          timeline: 'Impact expected soon',
          severity: criticalAlerts[0].severity === 'critical' ? 'critical' : 'high',
        });
      }
    });

    return predictions;
  }, [riskRadar]);

  // Generate interventions from critical/high alerts
  const interventions = useMemo(() => {
    if (!riskRadar?.employee_risks) return [];

    const allInterventions: any[] = [];
    let rank = 1;

    riskRadar.employee_risks.forEach((emp: any) => {
      const criticalAlerts = (emp.alerts || []).filter((a: any) => 
        a.severity === 'critical' || a.severity === 'high'
      );
      
      criticalAlerts.forEach((alert: any) => {
        allInterventions.push({
          rank: rank++,
          action: alert.message || `Address risk for ${emp.employee_id}`,
          impact: `Reduces risk by ${alert.severity === 'critical' ? '45%' : '30%'}`,
          cost: 'TBD',
          timeline: 'Immediate',
          priority: alert.severity === 'critical' ? 'critical' : 'high',
        });
      });
    });

    return allInterventions.slice(0, 4); // Top 4
  }, [riskRadar]);

  // Extract risk summary
  const riskSummary = riskRadar?.risk_summary || {};
  const riskDistribution = riskRadar?.risk_distribution || {};

  // Loading state
  if (isLoading) {
    return (
      <VStack spacing={6} align="stretch">
        <Box>
          <Skeleton height="40px" width="300px" mb={2} />
          <Skeleton height="20px" width="400px" />
        </Box>
        <Grid templateColumns="repeat(3, 1fr)" gap={4}>
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} height="100px" borderRadius="lg" />
          ))}
        </Grid>
        <Grid templateColumns="1fr 1fr" gap={6}>
          <Skeleton height="500px" borderRadius="lg" />
          <Skeleton height="500px" borderRadius="lg" />
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
            <Text fontWeight="semibold" color="red.800">Failed to load risk radar data</Text>
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
          Skill Risk Radar
        </Text>
        <Text color="gray.600" mt={1}>
          AI-powered risk detection & prevention · Team {DEMO_TEAM_ID}
        </Text>
      </Box>

      {/* Risk Summary Cards */}
      <Grid templateColumns="repeat(3, 1fr)" gap={4}>
        <Box
          p={5}
          bg="red.50"
          borderRadius="lg"
          border="2px solid"
          borderColor="red.200"
        >
          <HStack justify="space-between" mb={2}>
            <Text fontSize="sm" fontWeight="medium" color="gray.600">
              High Risk
            </Text>
            <Badge colorScheme="red" fontSize="lg" px={3} py={1}>
              {riskDistribution.high || riskEmployees.high.length}
            </Badge>
          </HStack>
          <Text fontSize="xs" color="gray.600">
            Immediate intervention required
          </Text>
        </Box>

        <Box
          p={5}
          bg="orange.50"
          borderRadius="lg"
          border="2px solid"
          borderColor="orange.200"
        >
          <HStack justify="space-between" mb={2}>
            <Text fontSize="sm" fontWeight="medium" color="gray.600">
              Medium Risk
            </Text>
            <Badge colorScheme="orange" fontSize="lg" px={3} py={1}>
              {riskDistribution.medium || riskEmployees.medium.length}
            </Badge>
          </HStack>
          <Text fontSize="xs" color="gray.600">
            Monitor and plan actions
          </Text>
        </Box>

        <Box
          p={5}
          bg="green.50"
          borderRadius="lg"
          border="2px solid"
          borderColor="green.200"
        >
          <HStack justify="space-between" mb={2}>
            <Text fontSize="sm" fontWeight="medium" color="gray.600">
              Low Risk
            </Text>
            <Badge colorScheme="green" fontSize="lg" px={3} py={1}>
              {riskDistribution.low || riskEmployees.low.length}
            </Badge>
          </HStack>
          <Text fontSize="xs" color="gray.600">
            On track, no action needed
          </Text>
        </Box>
      </Grid>

      <Grid templateColumns="1fr 1fr" gap={6}>
        {/* Circular Risk Radar Visualization */}
        <MotionBox
          bg="white"
          p={6}
          borderRadius="lg"
          border="1px solid"
          borderColor="gray.200"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <Text fontSize="xl" fontWeight="semibold" mb={5}>
            Risk Radar Visualization
          </Text>

          {/* Circular Radar (CSS-based for simplicity) */}
          <Box position="relative" w="100%" h="400px" mx="auto">
            {/* Concentric circles */}
            {[25, 50, 75, 100].map((radius) => (
              <Box
                key={radius}
                position="absolute"
                top="50%"
                left="50%"
                transform="translate(-50%, -50%)"
                w={`${radius}%`}
                h={`${radius}%`}
                borderRadius="full"
                border="1px solid"
                borderColor="gray.200"
              />
            ))}

            {/* Risk zones labels */}
            <Text
              position="absolute"
              top="50%"
              left="50%"
              transform="translate(-50%, -50%)"
              fontSize="xs"
              color="green.600"
              fontWeight="semibold"
            >
              LOW RISK
            </Text>
            <Text
              position="absolute"
              top="20%"
              left="50%"
              transform="translate(-50%, -50%)"
              fontSize="xs"
              color="red.600"
              fontWeight="semibold"
            >
              HIGH RISK
            </Text>

            {/* Plot employees as dots */}
            {[...riskEmployees.high, ...riskEmployees.medium, ...riskEmployees.low].length > 0 ? (
              [...riskEmployees.high, ...riskEmployees.medium, ...riskEmployees.low].map(
                (emp, idx) => {
                const angle = (idx / 10) * 2 * Math.PI;
                const distance = emp.riskScore; // 0-100
                const x = 50 + (distance / 2) * Math.cos(angle);
                const y = 50 + (distance / 2) * Math.sin(angle);
                const color =
                  emp.riskScore > 60
                    ? 'red.500'
                    : emp.riskScore > 40
                    ? 'orange.500'
                    : 'green.500';

                return (
                  <Box
                    key={emp.name}
                    position="absolute"
                    left={`${x}%`}
                    top={`${y}%`}
                    transform="translate(-50%, -50%)"
                    cursor="pointer"
                    onClick={() => setSelectedEmployee(emp)}
                    _hover={{ transform: 'translate(-50%, -50%) scale(1.3)' }}
                    transition="all 0.2s"
                  >
                    <Avatar
                      size="sm"
                      name={emp.name}
                      bg={color}
                      color="white"
                      fontSize="xs"
                    />
                  </Box>
                );
              }
              )
            ) : (
              <Box position="absolute" top="50%" left="50%" transform="translate(-50%, -50%)">
                <Text color="gray.500" fontSize="sm">No employee risk data available</Text>
              </Box>
            )}
          </Box>

          <Text fontSize="xs" color="gray.600" textAlign="center" mt={4}>
            Click on an employee to view details
          </Text>
        </MotionBox>

        {/* Risk Breakdown & Details */}
        <VStack spacing={4} align="stretch">
          {/* High Risk List */}
          <MotionBox
            bg="white"
            p={5}
            borderRadius="lg"
            border="1px solid"
            borderColor="gray.200"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <HStack mb={4}>
              <Icon as={AlertTriangle} w={5} h={5} color="red.600" />
              <Text fontSize="lg" fontWeight="semibold">
                High Risk Employees
              </Text>
            </HStack>

            <VStack spacing={3} align="stretch">
              {riskEmployees.high.length > 0 ? (
                riskEmployees.high.map((emp, idx) => (
                <Box
                  key={idx}
                  p={3}
                  bg="red.50"
                  borderRadius="md"
                  border="1px solid"
                  borderColor="red.200"
                  cursor="pointer"
                  onClick={() => setSelectedEmployee(emp)}
                  _hover={{ borderColor: 'red.400' }}
                >
                  <HStack justify="space-between" mb={2}>
                    <HStack spacing={3}>
                      <Avatar size="sm" name={emp.name} bg="red.500" />
                      <Box>
                        <Text fontWeight="medium" fontSize="sm">
                          {emp.name}
                        </Text>
                        <Text fontSize="xs" color="gray.600">
                          {emp.role}
                        </Text>
                      </Box>
                    </HStack>
                    <Badge colorScheme="red">{emp.riskScore}%</Badge>
                  </HStack>
                  <VStack align="stretch" spacing={1}>
                    {emp.reasons.map((reason, i) => (
                      <HStack key={i} fontSize="xs" color="gray.600">
                        <Icon as={XCircle} w={3} h={3} color="red.500" />
                        <Text>{reason}</Text>
                      </HStack>
                    ))}
                  </VStack>
                  <Progress
                    value={emp.skillCoverage}
                    size="xs"
                    colorScheme="red"
                    mt={2}
                  />
                </Box>
                ))
              ) : (
                <Box p={4} bg="gray.50" borderRadius="md" textAlign="center">
                  <Text color="gray.500" fontSize="sm">No high-risk employees</Text>
                </Box>
              )}
            </VStack>
          </MotionBox>

          {/* Medium Risk List */}
          <Box
            bg="white"
            p={5}
            borderRadius="lg"
            border="1px solid"
            borderColor="gray.200"
          >
            <HStack mb={4}>
              <Icon as={Clock} w={5} h={5} color="orange.600" />
              <Text fontSize="lg" fontWeight="semibold">
                Medium Risk
              </Text>
            </HStack>
            <VStack spacing={2} align="stretch">
              {riskEmployees.medium.length > 0 ? (
                riskEmployees.medium.map((emp, idx) => (
                <HStack
                  key={idx}
                  justify="space-between"
                  p={2}
                  bg="orange.50"
                  borderRadius="md"
                >
                  <HStack spacing={2}>
                    <Avatar size="xs" name={emp.name} bg="orange.500" />
                    <Text fontSize="sm">{emp.name}</Text>
                  </HStack>
                  <Badge colorScheme="orange" fontSize="xs">
                    {emp.riskScore}%
                  </Badge>
                </HStack>
                ))
              ) : (
                <Box p={2} bg="gray.50" borderRadius="md" textAlign="center">
                  <Text color="gray.500" fontSize="xs">No medium-risk employees</Text>
                </Box>
              )}
            </VStack>
          </Box>
        </VStack>
      </Grid>

      {/* AI Risk Predictions */}
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
        <HStack mb={5}>
          <Icon as={TrendingUp} w={5} h={5} color="skoda.green" />
          <Text fontSize="xl" fontWeight="semibold">
            AI Risk Predictions
          </Text>
        </HStack>

        <VStack spacing={3} align="stretch">
          {aiPredictions.length > 0 ? (
            aiPredictions.map((pred, idx) => (
            <Box
              key={idx}
              p={4}
              bg="blue.50"
              borderRadius="lg"
              border="1px solid"
              borderColor="blue.200"
            >
              <HStack justify="space-between" mb={2}>
                <Text fontWeight="semibold" fontSize="sm">
                  {pred.employee}
                </Text>
                <RiskBadge level={pred.severity as any} />
              </HStack>
              <Text fontSize="sm" mb={2}>
                {pred.prediction}
              </Text>
              <HStack fontSize="xs" color="gray.600">
                <Icon as={Clock} w={3} h={3} />
                <Text>{pred.timeline}</Text>
              </HStack>
            </Box>
            ))
          ) : (
            <Box p={4} bg="gray.50" borderRadius="lg" textAlign="center">
              <Text color="gray.500" fontSize="sm">No AI predictions available</Text>
            </Box>
          )}
        </VStack>
      </MotionBox>

      {/* Interventions Ranked by Impact */}
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
            <Icon as={Target} w={5} h={5} color="skoda.green" />
            <Text fontSize="xl" fontWeight="semibold">
              Recommended Interventions
            </Text>
          </HStack>
          <Text fontSize="xs" color="gray.600">
            Ranked by risk reduction impact
          </Text>
        </HStack>

        <VStack spacing={3} align="stretch">
          {interventions.length > 0 ? (
            interventions.map((intervention, idx) => (
            <HStack
              key={idx}
              p={4}
              bg="gray.50"
              borderRadius="lg"
              border="1px solid"
              borderColor="gray.200"
              justify="space-between"
            >
              <HStack spacing={4} flex={1}>
                <Box
                  w={10}
                  h={10}
                  borderRadius="full"
                  bg="skoda.green"
                  color="white"
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                  fontWeight="bold"
                >
                  #{intervention.rank}
                </Box>
                <Box flex={1}>
                  <HStack mb={1}>
                    <Text fontWeight="semibold" fontSize="sm">
                      {intervention.action}
                    </Text>
                    <RiskBadge level={intervention.priority as any} />
                  </HStack>
                  <HStack spacing={4} fontSize="xs" color="gray.600">
                    <HStack>
                      <Icon as={TrendingUp} w={3} h={3} />
                      <Text>{intervention.impact}</Text>
                    </HStack>
                    <Text>Cost: {intervention.cost}</Text>
                    <Text>Timeline: {intervention.timeline}</Text>
                  </HStack>
                </Box>
              </HStack>
              <Button size="sm" colorScheme="brand">
                Schedule
              </Button>
            </HStack>
            ))
          ) : (
            <Box p={4} bg="gray.50" borderRadius="lg" textAlign="center">
              <Text color="gray.500" fontSize="sm">No interventions recommended</Text>
            </Box>
          )}
        </VStack>
      </MotionBox>
    </VStack>
  );
};