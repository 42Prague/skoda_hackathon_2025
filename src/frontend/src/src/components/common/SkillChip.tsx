import { Badge } from '@chakra-ui/react';

interface SkillChipProps {
  skill: string;
  level?: number;
  variant?: 'solid' | 'outline';
}

export const SkillChip = ({ skill, level, variant = 'outline' }: SkillChipProps) => {
  return (
    <Badge
      variant={variant}
      colorScheme={level && level >= 4 ? 'green' : 'gray'}
      px={2}
      py={0.5}
      borderRadius="md"
      fontSize="xs"
    >
      {skill} {level && `(${level}/5)`}
    </Badge>
  );
};
