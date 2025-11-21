import { 
  Box, 
  HStack, 
  Input, 
  IconButton, 
  Badge,
  Flex,
  Text
} from '@chakra-ui/react';
import { Search, Bell, Globe } from 'lucide-react';
import { useLang } from '../../hooks/useLang';
import { RoleSwitcher } from './RoleSwitcher';

export const TopBar = () => {
  const { language, changeLanguage } = useLang();

  return (
    <Box
      h="64px"
      bg="white"
      borderBottom="1px solid"
      borderColor="gray.200"
      px={6}
      display="flex"
      alignItems="center"
      justifyContent="space-between"
    >
      <HStack spacing={6} flex={1}>
        <Box maxW="400px" position="relative">
          <Box position="absolute" left={3} top="50%" transform="translateY(-50%)" zIndex={1}>
            <Search size={16} color="#9CA3AF" />
          </Box>
          <Input
            placeholder="Search employees, skills, departments..."
            bg="gray.50"
            border="1px solid"
            borderColor="gray.200"
            pl={10}
          />
        </Box>

        <RoleSwitcher />
      </HStack>

      <HStack spacing={4}>
        <HStack spacing={2} px={3} py={1.5} borderRadius="md" border="1px solid" borderColor="gray.200" bg="white">
          <Globe size={16} color="#6B7280" />
          <Box 
            as="select"
            value={language}
            onChange={(e: any) => changeLanguage(e.target.value as 'en' | 'cs')}
            w="60px"
            fontSize="sm"
            border="none"
            outline="none"
            cursor="pointer"
            bg="transparent"
            color="gray.700"
            fontWeight="500"
          >
            <option value="en">EN</option>
            <option value="cs">CZ</option>
          </Box>
        </HStack>

        <Box position="relative">
          <IconButton
            aria-label="Notifications"
            variant="ghost"
            color="gray.600"
            _hover={{ bg: 'gray.100' }}
          >
            <Bell size={20} />
          </IconButton>
          <Badge
            position="absolute"
            top="-1"
            right="-1"
            bg="skoda.green"
            color="white"
            borderRadius="full"
            fontSize="xs"
            px={1.5}
            minW="20px"
            h="20px"
            display="flex"
            alignItems="center"
            justifyContent="center"
          >
            3
          </Badge>
        </Box>

        <Flex align="center" gap={2} px={3} py={1.5} bg="gray.100" borderRadius="lg">
          <Box w={2} h={2} bg="skoda.green" borderRadius="full" animation="pulse 2s infinite" />
          <Text fontSize="xs" color="gray.600">AI Active</Text>
        </Flex>
      </HStack>
    </Box>
  );
};