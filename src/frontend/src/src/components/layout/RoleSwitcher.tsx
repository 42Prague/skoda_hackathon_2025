import { HStack, Button, Box, Text } from '@chakra-ui/react';
import { Target, BarChart3, User } from 'lucide-react';
import { useRoleStore, UserRole } from '../../state/store';
import { useNavigate } from 'react-router-dom';

export const RoleSwitcher = () => {
  const { currentRole, setCurrentRole } = useRoleStore();
  const navigate = useNavigate();

  const handleRoleChange = (role: UserRole) => {
    setCurrentRole(role);
    
    // Navigate to role-specific landing page
    if (role === 'manager') {
      navigate('/');
    } else if (role === 'hrbp') {
      navigate('/hrbp/dashboard');
    } else if (role === 'employee') {
      navigate('/employee/career');
    }
  };

  const roles = [
    { id: 'manager' as UserRole, label: 'MANAGER', icon: Target },
    { id: 'hrbp' as UserRole, label: 'HRBP', icon: BarChart3 },
    { id: 'employee' as UserRole, label: 'EMPLOYEE', icon: User },
  ];

  return (
    <HStack spacing={2} bg="white" p={1} borderRadius="lg" boxShadow="sm">
      {roles.map((role) => {
        const RoleIcon = role.icon;
        const isActive = currentRole === role.id;
        
        return (
          <Button
            key={role.id}
            size="sm"
            variant={isActive ? 'solid' : 'ghost'}
            bg={isActive ? 'skoda.green' : 'transparent'}
            color={isActive ? 'white' : 'gray.600'}
            _hover={{
              bg: isActive ? 'skoda.greenDark' : 'gray.100',
            }}
            leftIcon={<RoleIcon size={16} />}
            onClick={() => handleRoleChange(role.id)}
            fontWeight={isActive ? 'bold' : 'medium'}
            px={4}
            transition="all 0.2s"
          >
            {role.label}
          </Button>
        );
      })}
    </HStack>
  );
};
