import { Box } from '@chakra-ui/react';
import { 
  ComposedChart, 
  Line, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';

interface PredictiveChartProps {
  data: any[];
  height?: number;
}

export const PredictiveChart = ({ data, height = 300 }: PredictiveChartProps) => {
  return (
    <Box w="100%" h={`${height}px`}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="period" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} domain={[70, 100]} />
          <Tooltip />
          <Area type="monotone" dataKey="upper" stroke="none" fill="#4da944" fillOpacity={0.1} />
          <Area type="monotone" dataKey="lower" stroke="none" fill="white" />
          <Line type="monotone" dataKey="actual" stroke="#0d1b2a" strokeWidth={2} dot={{ r: 4 }} />
          <Line 
            type="monotone" 
            dataKey="forecast" 
            stroke="#4da944" 
            strokeWidth={2} 
            strokeDasharray="5 5" 
            dot={{ r: 4 }} 
          />
        </ComposedChart>
      </ResponsiveContainer>
    </Box>
  );
};
