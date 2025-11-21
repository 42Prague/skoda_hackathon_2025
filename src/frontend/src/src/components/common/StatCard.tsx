import { Box, HStack, VStack, Text } from '@chakra-ui/react';
import { LucideIcon } from 'lucide-react';
import { motion } from 'motion/react';
import { Icon } from './Icon';

const MotionBox = motion.create(Box);

interface StatCardProps {
  label: string;
  value: string | number;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
  icon: LucideIcon;
  badge?: React.ReactNode;
}

export const StatCard = ({ label, value, change, trend, icon, badge }: StatCardProps) => {
  return (
    <MotionBox
      bg="white"
      p={5}
      borderRadius="lg"
      border="1px solid"
      borderColor="gray.200"
      whileHover={{ y: -2, shadow: 'md' }}
      transition={{ duration: 0.2 }}
    >
      <HStack justify="space-between" align="start" mb={3}>
        <Box w={10} h={10} borderRadius="lg" bg="brand.50" display="flex" alignItems="center" justifyContent="center">
          <Icon as={icon} w={5} h={5} color="skoda.green" />
        </Box>
        {badge}
      </HStack>
      <VStack align="start" spacing={1}>
        <Text fontSize="2xl" fontWeight="semibold">{value}</Text>
        <Text fontSize="xs" color="gray.600">{label}</Text>
        {change && (
          <Text 
            fontSize="xs" 
            color={trend === 'up' ? 'green.600' : trend === 'down' ? 'red.600' : 'gray.600'}
          >
            {change}
          </Text>
        )}
      </VStack>
    </MotionBox>
  );
};
