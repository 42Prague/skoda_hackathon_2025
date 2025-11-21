import { Box, Text } from '@chakra-ui/react';
import { motion } from 'motion/react';
import { useState } from 'react';

const MotionBox = motion.create(Box);

interface HeatmapCellProps {
  value: number;
  employeeName?: string;
  skillName?: string;
}

export const HeatmapCell = ({ value, employeeName, skillName }: HeatmapCellProps) => {
  const [showTooltip, setShowTooltip] = useState(false);
  
  const getColor = (level: number) => {
    if (level === 5) return { bg: '#3a8234', color: 'white' };
    if (level === 4) return { bg: '#4da944', color: 'white' };
    if (level === 3) return { bg: '#9dd595', color: '#0d1b2a' };
    if (level === 2) return { bg: '#fed7aa', color: '#9a3412' };
    return { bg: '#fecaca', color: '#991b1b' };
  };

  const { bg, color } = getColor(value);
  const tooltipText = `${employeeName || ''} - ${skillName || ''}: Level ${value}`.trim();

  return (
    <Box position="relative" display="inline-block">
      <MotionBox
        w={12}
        h={12}
        bg={bg}
        color={color}
        borderRadius="lg"
        display="flex"
        alignItems="center"
        justifyContent="center"
        fontWeight="semibold"
        cursor="pointer"
        whileHover={{ scale: 1.1 }}
        transition={{ duration: 0.2 }}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        title={tooltipText}
      >
        <Text>{value}</Text>
      </MotionBox>
      {showTooltip && (
        <Box
          position="absolute"
          bottom="calc(100% + 8px)"
          left="50%"
          transform="translateX(-50%)"
          px={2}
          py={1}
          bg="#1a202c"
          color="white"
          fontSize="xs"
          borderRadius="md"
          whiteSpace="nowrap"
          zIndex={1000}
          pointerEvents="none"
          boxShadow="lg"
          _after={{
            content: '""',
            position: 'absolute',
            top: '100%',
            left: '50%',
            transform: 'translateX(-50%)',
            borderLeft: '6px solid transparent',
            borderRight: '6px solid transparent',
            borderTop: '6px solid #1a202c',
          }}
        >
          {tooltipText}
        </Box>
      )}
    </Box>
  );
};
