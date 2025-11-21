import { Box, VStack, HStack, Text, Flex } from '@chakra-ui/react';
import { Icon } from '../common/Icon';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Users, 
  UserCircle, 
  Target, 
  TrendingUp, 
  Sparkles,
  Network,
  Globe2,
  FlaskConical,
  Settings,
  AlertCircle
} from 'lucide-react';
import { useLang } from '../../hooks/useLang';
import { useRoleStore } from '../../state/store';

export const Sidebar = () => {
  const { t } = useLang();
  const { currentRole } = useRoleStore();

  // Manager navigation items
  const managerNavItems = [
    { id: 'dashboard', icon: LayoutDashboard, label: 'Team Capability', path: '/' },
    { id: 'risk', icon: AlertCircle, label: 'Risk Radar', path: '/risk-radar' },
    { id: 'promotion', icon: TrendingUp, label: 'Promotion Readiness', path: '/promotion-readiness' },
    { id: 'heatmap', icon: Users, label: 'Skills Heatmap', path: '/heatmap' },
    { id: 'ai', icon: Sparkles, label: 'AI Assistant', path: '/assistant' },
  ];

  // HRBP navigation items
  const hrbpNavItems = [
    { id: 'hrbp-dashboard', icon: LayoutDashboard, label: 'Org Dashboard', path: '/hrbp/dashboard' },
    { id: 'forecast', icon: TrendingUp, label: 'Future Forecast', path: '/hrbp/forecast' },
    { id: 'ai', icon: Sparkles, label: 'AI Assistant', path: '/assistant' },
  ];

  // Employee navigation items
  const employeeNavItems = [
    { id: 'career', icon: Target, label: 'My Career', path: '/employee/career' },
    { id: 'ai', icon: Sparkles, label: 'AI Assistant', path: '/assistant' },
  ];

  // Select nav items based on current role
  const navItems = currentRole === 'manager' 
    ? managerNavItems 
    : currentRole === 'hrbp' 
    ? hrbpNavItems 
    : employeeNavItems;

  return (
    <Box
      position="fixed"
      left={0}
      top={0}
      h="100vh"
      w="260px"
      bg="skoda.navy"
      borderRight="1px solid"
      borderColor="skoda.navyLight"
      display="flex"
      flexDirection="column"
    >
      <Box p={6} borderBottom="1px solid" borderColor="skoda.navyLight">
        <HStack spacing={3} mb={1}>
          <Flex w={8} h={8} bg="skoda.green" borderRadius="md" align="center" justify="center">
            <Text color="white" fontWeight="bold">Š</Text>
          </Flex>
          <Box>
            <Text color="white" fontWeight="semibold" fontSize="lg">Skill Coach</Text>
            <Text color="gray.400" fontSize="xs">AI-Powered Talent Intelligence</Text>
          </Box>
        </HStack>
      </Box>

      <VStack flex={1} p={4} spacing={1} align="stretch" overflowY="auto">
        {navItems.map((item) => (
          <NavLink
            key={item.id}
            to={item.path}
            style={{ textDecoration: 'none' }}
          >
            {({ isActive }) => (
              <HStack
                px={3}
                py={2.5}
                borderRadius="lg"
                bg={isActive ? 'skoda.green' : 'transparent'}
                color={isActive ? 'white' : 'gray.300'}
                _hover={{ bg: isActive ? 'skoda.green' : 'skoda.navyLight', color: 'white' }}
                transition="all 0.2s"
                cursor="pointer"
              >
                <Icon as={item.icon} w={5} h={5} />
                <Text fontSize="sm">{item.label}</Text>
              </HStack>
            )}
          </NavLink>
        ))}
      </VStack>

      <Box p={4} borderTop="1px solid" borderColor="skoda.navyLight">
        <HStack spacing={3}>
          <Box 
            w="32px" 
            h="32px" 
            borderRadius="full" 
            bg="skoda.green" 
            display="flex" 
            alignItems="center" 
            justifyContent="center"
            color="white"
            fontSize="sm"
            fontWeight="600"
          >
            MK
          </Box>
          <Box flex={1} minW={0}>
            <Text color="white" fontSize="sm" fontWeight="medium" isTruncated>Martin Kovář</Text>
            <Text color="gray.400" fontSize="xs">Engineering Manager</Text>
          </Box>
          <Settings size={16} color="#9CA3AF" style={{ cursor: 'pointer' }} />
        </HStack>
      </Box>
    </Box>
  );
};