import { Badge } from '@chakra-ui/react';

interface RiskBadgeProps {
  level: 'high' | 'medium' | 'low' | 'critical';
  label?: string;
}

export const RiskBadge = ({ level, label }: RiskBadgeProps) => {
  const colors = {
    critical: { bg: 'red.600', color: 'white' },
    high: { bg: 'red.100', color: 'red.700' },
    medium: { bg: 'orange.100', color: 'orange.700' },
    low: { bg: 'green.100', color: 'green.700' },
  };

  const { bg, color } = colors[level];

  return (
    <Badge bg={bg} color={color} px={2} py={0.5} borderRadius="md" fontSize="xs" fontWeight="semibold">
      {label || level.charAt(0).toUpperCase() + level.slice(1)}
    </Badge>
  );
};
