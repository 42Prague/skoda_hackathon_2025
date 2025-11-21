import {
  Box,
  Grid,
  VStack,
  HStack,
  Text,
  Badge,
  Button,
  Input,
  Skeleton,
} from '@chakra-ui/react';
import {
  Search,
  Filter,
  Download,
  TrendingUp,
  ChevronDown,
  MoreVertical,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
} from 'lucide-react';
import { motion } from 'motion/react';
import { useState, useMemo } from 'react';
import { usePromotionReadiness } from '../../hooks/useBackendEndpoints';

const MotionBox = motion.create(Box);

// Custom Checkbox component
const Checkbox = ({ isChecked, onChange, ...props }: any) => {
  return (
    <input
      type="checkbox"
      checked={isChecked}
      onChange={onChange}
      style={{
        width: '16px',
        height: '16px',
        cursor: 'pointer',
        accentColor: '#4da944',
      }}
      {...props}
    />
  );
};

// Custom Select component  
const CustomSelect = ({ value, onChange, children, maxW, placeholder, ...props }: any) => {
  return (
    <div style={{ maxWidth: maxW, ...props.style }}>
      <select
        value={value}
        onChange={onChange}
        style={{
          width: '100%',
          padding: '8px 12px',
          borderRadius: '6px',
          border: '1px solid #E2E8F0',
          fontSize: '14px',
          backgroundColor: 'white',
          cursor: 'pointer',
        }}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {children}
      </select>
    </div>
  );
};

import { Icon } from '../../components/common/Icon';

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

export const PromotionReadinessPage = () => {
  const [selectedEmployees, setSelectedEmployees] = useState<string[]>([]);
  const [filterRole, setFilterRole] = useState('all');
  const [filterReadiness, setFilterReadiness] = useState('all');
  const { data: promotionReadiness, isLoading, error } = usePromotionReadiness(DEMO_TEAM_ID);

  // Transform backend data to match component requirements
  const employees = useMemo(() => {
    if (!promotionReadiness?.candidates) {
      return [];
    }

    return promotionReadiness.candidates.map((candidate: any, idx: number) => {
      const readiness = candidate.readiness_score || 0;
      let status: 'ready' | 'in-progress' | 'needs-support' = 'needs-support';
      if (readiness >= 85) status = 'ready';
      else if (readiness >= 70) status = 'in-progress';

      return {
        id: candidate.employee_id || `emp-${idx}`,
        name: candidate.employee_id || `Employee ${candidate.employee_id}`,
        currentRole: candidate.current_role || 'Unknown Role',
        targetRole: candidate.target_role || candidate.job_family_id || 'Target Role',
        readiness: Math.round(readiness),
        timeline: candidate.estimated_timeline || candidate.timeline_months 
          ? `${candidate.timeline_months || 12} months`
          : 'TBD',
        gaps: candidate.skill_gaps || candidate.gaps || [],
        strengths: candidate.strengths || [],
        status,
      };
    });
  }, [promotionReadiness]);

  // Calculate summary stats
  const summaryStats = useMemo(() => {
    const readyNow = employees.filter(e => e.readiness >= 85).length;
    const inProgress = employees.filter(e => e.readiness >= 70 && e.readiness < 85).length;
    const needsSupport = employees.filter(e => e.readiness < 70).length;
    const avgTimeline = employees.length > 0
      ? (employees.reduce((sum, e) => {
          const months = parseInt(e.timeline) || 12;
          return sum + months;
        }, 0) / employees.length).toFixed(1)
      : '0';

    return { readyNow, inProgress, needsSupport, avgTimeline };
  }, [employees]);

  // Filter employees
  const filteredEmployees = useMemo(() => {
    let filtered = employees;

    if (filterReadiness !== 'all') {
      if (filterReadiness === 'ready') {
        filtered = filtered.filter(e => e.readiness >= 85);
      } else if (filterReadiness === 'progress') {
        filtered = filtered.filter(e => e.readiness >= 70 && e.readiness < 85);
      } else if (filterReadiness === 'support') {
        filtered = filtered.filter(e => e.readiness < 70);
      }
    }

    return filtered;
  }, [employees, filterReadiness]);

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
            <Skeleton key={i} height="100px" borderRadius="lg" />
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
            <Text fontWeight="semibold" color="red.800">Failed to load promotion readiness data</Text>
          </HStack>
          <Text fontSize="sm" color="red.700" ml={7}>
            {error instanceof Error ? error.message : 'An unexpected error occurred. Please try again later.'}
          </Text>
        </Box>
      </VStack>
    );
  }

  // Mock data removed - now using backend data via usePromotionReadiness hook

  const getReadinessColor = (readiness: number) => {
    if (readiness >= 85) return 'green';
    if (readiness >= 70) return 'orange';
    return 'red';
  };

  const getStatusBadge = (status: string) => {
    if (status === 'ready') return <Badge colorScheme="green">Ready Now</Badge>;
    if (status === 'in-progress') return <Badge colorScheme="blue">In Progress</Badge>;
    return <Badge colorScheme="red">Needs Support</Badge>;
  };

  const handleSelectAll = () => {
    if (selectedEmployees.length === filteredEmployees.length) {
      setSelectedEmployees([]);
    } else {
      setSelectedEmployees(filteredEmployees.map((e) => e.id));
    }
  };

  const handleSelectEmployee = (id: string) => {
    if (selectedEmployees.includes(id)) {
      setSelectedEmployees(selectedEmployees.filter((e) => e !== id));
    } else {
      setSelectedEmployees([...selectedEmployees, id]);
    }
  };

  return (
    <VStack spacing={6} align="stretch">
      {/* Header */}
      <HStack justify="space-between">
        <Box>
          <Text fontSize="3xl" fontWeight="semibold">
            Promotion Readiness
          </Text>
          <Text color="gray.600" mt={1}>
            Team-wide promotion planning & succession pipeline
          </Text>
        </Box>
        <HStack>
          <Button
            variant="outline"
            size="sm"
          >
            <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Download size={16} />
              <span>Export PDF</span>
            </span>
          </Button>
        </HStack>
      </HStack>

      {/* Summary Cards */}
      <Grid templateColumns="repeat(4, 1fr)" gap={4}>
        <Box p={5} bg="green.50" borderRadius="lg" border="1px solid" borderColor="green.200">
          <Text fontSize="xs" color="gray.600" mb={2}>Ready Now (≥85%)</Text>
          <HStack justify="space-between">
            <Text fontSize="3xl" fontWeight="bold" color="green.600">{summaryStats.readyNow}</Text>
            <CheckCircle2 size={32} color="#16a34a" />
          </HStack>
        </Box>
        <Box p={5} bg="blue.50" borderRadius="lg" border="1px solid" borderColor="blue.200">
          <Text fontSize="xs" color="gray.600" mb={2}>In Progress (70-84%)</Text>
          <HStack justify="space-between">
            <Text fontSize="3xl" fontWeight="bold" color="blue.600">{summaryStats.inProgress}</Text>
            <Clock size={32} color="#2563eb" />
          </HStack>
        </Box>
        <Box p={5} bg="orange.50" borderRadius="lg" border="1px solid" borderColor="orange.200">
          <Text fontSize="xs" color="gray.600" mb={2}>Needs Support (&lt;70%)</Text>
          <HStack justify="space-between">
            <Text fontSize="3xl" fontWeight="bold" color="orange.600">{summaryStats.needsSupport}</Text>
            <XCircle size={32} color="#ea580c" />
          </HStack>
        </Box>
        <Box p={5} bg="white" borderRadius="lg" border="1px solid" borderColor="gray.200">
          <Text fontSize="xs" color="gray.600" mb={2}>Avg Timeline</Text>
          <HStack justify="space-between">
            <Text fontSize="3xl" fontWeight="bold">{summaryStats.avgTimeline}</Text>
            <Text fontSize="sm" color="gray.600">months</Text>
          </HStack>
        </Box>
      </Grid>

      {/* Filters & Actions */}
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
          <HStack spacing={4}>
            <Box maxW="300px" position="relative">
              <Box position="absolute" left={3} top="50%" transform="translateY(-50%)" zIndex={1}>
                <Search size={16} color="#9ca3af" />
              </Box>
              <Input placeholder="Search employees..." pl={10} />
            </Box>

            <CustomSelect
              value={filterRole}
              onChange={(e) => setFilterRole(e.target.value)}
              maxW="200px"
              placeholder="All Target Roles"
            >
              <option value="all">All Target Roles</option>
              <option value="manager">Engineering Manager</option>
              <option value="principal">Principal Engineer</option>
              <option value="lead">Tech Lead</option>
            </CustomSelect>

            <CustomSelect
              value={filterReadiness}
              onChange={(e) => setFilterReadiness(e.target.value)}
              maxW="200px"
              placeholder="All Readiness Levels"
            >
              <option value="all">All Readiness Levels</option>
              <option value="ready">Ready (≥85%)</option>
              <option value="progress">In Progress (70-84%)</option>
              <option value="support">Needs Support (&lt;70%)</option>
            </CustomSelect>
          </HStack>

          {selectedEmployees.length > 0 && (
            <HStack>
              <Text fontSize="sm" color="gray.600">
                {selectedEmployees.length} selected
              </Text>
              <Button
                size="sm"
                colorScheme="brand"
              >
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>Bulk Actions</span>
                  <ChevronDown size={16} />
                </span>
              </Button>
            </HStack>
          )}
        </HStack>

        {/* Employee Table */}
        <VStack spacing={2} align="stretch">
          {/* Header Row */}
          <HStack
            px={4}
            py={2}
            bg="gray.100"
            borderRadius="md"
            spacing={4}
            fontSize="xs"
            fontWeight="semibold"
            color="gray.600"
          >
            <Box w={8}>
              <Checkbox
                isChecked={selectedEmployees.length === filteredEmployees.length && filteredEmployees.length > 0}
                onChange={handleSelectAll}
              />
            </Box>
            <Box flex={1}>Employee</Box>
            <Box w="120px">Current Role</Box>
            <Box w="140px">Target Role</Box>
            <Box w="100px" textAlign="center">Readiness</Box>
            <Box w="80px">Timeline</Box>
            <Box w="100px">Status</Box>
            <Box w="150px">Key Gaps</Box>
            <Box w="80px" textAlign="center">Actions</Box>
          </HStack>

          {/* Employee Rows */}
          {filteredEmployees.length > 0 ? (
            filteredEmployees.map((emp) => (
            <HStack
              key={emp.id}
              px={4}
              py={3}
              bg="white"
              borderRadius="md"
              border="1px solid"
              borderColor="gray.200"
              spacing={4}
              _hover={{ bg: 'gray.50', borderColor: 'gray.300' }}
              transition="all 0.2s"
            >
              <Box w={8}>
                <Checkbox
                  isChecked={selectedEmployees.includes(emp.id)}
                  onChange={() => handleSelectEmployee(emp.id)}
                />
              </Box>
              <HStack flex={1} spacing={3}>
                <Avatar size="sm" name={emp.name} bg="skoda.green" />
                <Text fontWeight="medium" fontSize="sm">
                  {emp.name}
                </Text>
              </HStack>
              <Box w="120px">
                <Text fontSize="sm">{emp.currentRole}</Text>
              </Box>
              <Box w="140px">
                <Text fontSize="sm" fontWeight="medium">
                  {emp.targetRole}
                </Text>
              </Box>
              <Box w="100px">
                <VStack spacing={1}>
                  <Text
                    fontSize="lg"
                    fontWeight="bold"
                    color={`${getReadinessColor(emp.readiness)}.600`}
                  >
                    {emp.readiness}%
                  </Text>
                  <Progress
                    value={emp.readiness}
                    size="sm"
                    colorScheme={getReadinessColor(emp.readiness)}
                    w="full"
                    borderRadius="full"
                  />
                </VStack>
              </Box>
              <Box w="80px">
                <Text fontSize="sm">{emp.timeline}</Text>
              </Box>
              <Box w="100px">{getStatusBadge(emp.status)}</Box>
              <Box w="150px">
                <VStack align="start" spacing={0.5}>
                  {emp.gaps.slice(0, 2).map((gap, idx) => (
                    <Text key={idx} fontSize="xs" color="gray.600">
                      • {gap}
                    </Text>
                  ))}
                  {emp.gaps.length > 2 && (
                    <Text fontSize="xs" color="gray.500">
                      +{emp.gaps.length - 2} more
                    </Text>
                  )}
                </VStack>
              </Box>
              <Box w="80px" textAlign="center">
                <Button size="sm" variant="ghost">
                  <MoreVertical size={16} />
                </Button>
              </Box>
            </HStack>
            ))
          ) : (
            <Box p={8} textAlign="center" bg="gray.50" borderRadius="md">
              <Text color="gray.500" fontSize="sm">No employees match the selected filters</Text>
            </Box>
          )}
        </VStack>
      </MotionBox>

      {/* AI Recommendations */}
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
          <TrendingUp size={20} color="#4da944" />
          <Text fontSize="xl" fontWeight="semibold">
            AI Promotion Recommendations
          </Text>
        </HStack>

        <VStack spacing={3} align="stretch">
          {employees.filter(e => e.readiness >= 70).slice(0, 3).map((emp, idx) => (
            <Box
              key={emp.id}
              p={4}
              bg={emp.readiness >= 85 ? 'green.50' : emp.readiness >= 80 ? 'blue.50' : 'orange.50'}
              borderRadius="lg"
              border="1px solid"
              borderColor={emp.readiness >= 85 ? 'green.200' : emp.readiness >= 80 ? 'blue.200' : 'orange.200'}
            >
              <HStack justify="space-between" mb={2}>
                <Text fontWeight="semibold" fontSize="sm">
                  {emp.name} → {emp.targetRole}
                </Text>
                <Badge colorScheme={emp.readiness >= 85 ? 'green' : 'orange'}>
                  {emp.readiness}% Ready
                </Badge>
              </HStack>
              <Text fontSize="sm" color="gray.600" mb={2}>
                Timeline: {emp.timeline}
                {emp.gaps.length > 0 && ` · Gaps: ${emp.gaps.slice(0, 2).join(', ')}`}
              </Text>
              <HStack>
                <Button size="sm" colorScheme="brand">
                  View Details
                </Button>
                <Button size="sm" variant="outline">
                  View Career Path
                </Button>
              </HStack>
            </Box>
          ))}
          {employees.filter(e => e.readiness >= 70).length === 0 && (
            <Box p={4} bg="gray.50" borderRadius="lg" textAlign="center">
              <Text color="gray.500" fontSize="sm">No promotion recommendations available</Text>
            </Box>
          )}
        </VStack>
      </MotionBox>
    </VStack>
  );
};