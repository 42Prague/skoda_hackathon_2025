import { Box, VStack, HStack, Text, Button, Textarea, Badge, Avatar, Grid } from '@chakra-ui/react';
import { Icon } from '../components/common/Icon';
import { Sparkles, Send, Users, TrendingUp, Target, ChevronRight, Clock, AlertCircle } from 'lucide-react';
import { useLang } from '../hooks/useLang';
import { useState } from 'react';
import { motion } from 'motion/react';

const MotionBox = motion.create(Box);

export const AIAssistantPage = () => {
  const { t } = useLang();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    {
      type: 'assistant',
      content: "Hello! I'm your Škoda AI Skill Coach assistant. I can help you analyze team skills, predict future gaps, compare departments, and identify candidates for specific roles. What would you like to know?",
      timestamp: '10:23',
    },
  ]);

  const suggestedQueries = [
    {
      category: 'Team Analysis',
      icon: Users,
      queries: [
        'What are the critical skill gaps in Engineering team?',
        'Show me employees at risk of qualification expiry',
        'Which team members are ready for promotion?',
      ],
    },
    {
      category: 'Predictions',
      icon: TrendingUp,
      queries: [
        'Forecast skill needs for Q2 2025',
        'Predict attrition risk in next 6 months',
        'What skills will be obsolete by 2026?',
      ],
    },
    {
      category: 'Comparisons',
      icon: Target,
      queries: [
        'Compare Engineering vs Manufacturing skill coverage',
        'Benchmark our AI/ML skills against industry',
        'Show department skill heatmap comparison',
      ],
    },
  ];

  const recentInsights = [
    {
      title: 'Cloud Architecture Shortage Detected',
      insight: '12 positions short of Q1 2025 requirements. 3 employees in pipeline.',
      severity: 'high',
      department: 'Engineering',
      timestamp: '2 hours ago',
    },
    {
      title: 'Leadership Development Opportunity',
      insight: 'Jana Nováková is 85% ready for Engineering Manager role. Recommend leadership training.',
      severity: 'medium',
      department: 'Engineering',
      timestamp: '5 hours ago',
    },
    {
      title: 'Qualification Compliance Alert',
      insight: '8 mandatory certifications expiring in next 30 days across all departments.',
      severity: 'high',
      department: 'All',
      timestamp: '1 day ago',
    },
  ];

  const deepDiveTopics = [
    { title: 'Succession Risk Analysis', description: 'Identify vulnerable key roles' },
    { title: 'Skill Atrophy Detection', description: 'Find underutilized competencies' },
    { title: 'Training ROI Analysis', description: 'Measure course effectiveness' },
    { title: 'Career Path Simulation', description: 'Model employee progressions' },
  ];

  const handleSendMessage = () => {
    if (!input.trim()) return;

    setMessages([
      ...messages,
      {
        type: 'user',
        content: input,
        timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }),
      },
    ]);

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          type: 'assistant',
          content: "Based on current analysis, Engineering team has 3 critical skill gaps: Cloud Architecture (12 positions short), Cybersecurity (8 positions), and AI/ML (6 positions). These gaps are projected to impact Q1 2025 deliverables. I recommend prioritizing Cloud Architecture training for senior developers.",
          timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }),
        },
      ]);
    }, 1000);

    setInput('');
  };

  const handleSuggestedQuery = (query: string) => {
    setInput(query);
  };

  return (
    <VStack spacing={6} align="stretch">
      <Box>
        <HStack>
          <Icon as={Sparkles} w={8} h={8} color="skoda.green" />
          <Text fontSize="3xl" fontWeight="semibold">{t('assistant.title')}</Text>
        </HStack>
        <Text color="gray.600" mt={1}>{t('assistant.subtitle')}</Text>
      </Box>

      <Grid templateColumns="2fr 1fr" gap={6}>
        <MotionBox
          bg="white"
          borderRadius="lg"
          border="1px solid"
          borderColor="gray.200"
          display="flex"
          flexDirection="column"
          h="700px"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <Box p={4} borderBottom="1px solid" borderColor="gray.200" bg="skoda.navy" borderTopRadius="lg">
            <HStack>
              <Box w={10} h={10} borderRadius="full" bg="skoda.green" display="flex" alignItems="center" justifyContent="center">
                <Icon as={Sparkles} w={5} h={5} color="white" />
              </Box>
              <Box>
                <Text fontWeight="semibold" color="white">Škoda AI Coach</Text>
                <Text fontSize="xs" color="gray.300">Powered by predictive intelligence</Text>
              </Box>
              <Box ml="auto" display="flex" alignItems="center" gap={2}>
                <Box w={2} h={2} bg="green.400" borderRadius="full" animation="pulse 2s infinite" />
                <Text fontSize="xs" color="white">Online</Text>
              </Box>
            </HStack>
          </Box>

          <VStack flex={1} overflowY="auto" p={6} spacing={4} align="stretch">
            {messages.map((message, idx) => (
              <HStack
                key={idx}
                justify={message.type === 'user' ? 'flex-end' : 'flex-start'}
                align="start"
              >
                {message.type === 'assistant' && (
                  <Box w={8} h={8} borderRadius="full" bg="green.50" display="flex" alignItems="center" justifyContent="center" flexShrink={0}>
                    <Icon as={Sparkles} w={4} h={4} color="skoda.green" />
                  </Box>
                )}
                <Box
                  maxW="80%"
                  p={4}
                  borderRadius="lg"
                  bg={message.type === 'user' ? 'skoda.green' : 'gray.50'}
                  color={message.type === 'user' ? 'white' : 'skoda.navy'}
                >
                  <Text fontSize="sm">{message.content}</Text>
                  <Text fontSize="xs" opacity={0.7} mt={2}>{message.timestamp}</Text>
                </Box>
              </HStack>
            ))}
          </VStack>

          <Box p={4} borderTop="1px solid" borderColor="gray.200">
            <HStack>
              <Textarea
                placeholder="Ask about team skills, gaps, predictions, or candidates..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                resize="none"
                rows={2}
              />
              <Button colorScheme="brand" px={6} h="100%" onClick={handleSendMessage}>
                <Icon as={Send} w={4} h={4} />
              </Button>
            </HStack>
          </Box>
        </MotionBox>

        <VStack spacing={4} align="stretch">
          <MotionBox
            bg="white"
            p={5}
            borderRadius="lg"
            border="1px solid"
            borderColor="gray.200"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <Text fontSize="lg" fontWeight="semibold" mb={4}>{t('assistant.suggestedQueries')}</Text>
            <VStack spacing={4} align="stretch">
              {suggestedQueries.map((category, idx) => (
                <Box key={idx}>
                  <HStack mb={2}>
                    <Icon as={category.icon} w={4} h={4} color="skoda.green" />
                    <Text fontSize="xs" fontWeight="medium" color="gray.600">{category.category}</Text>
                  </HStack>
                  <VStack spacing={1} align="stretch">
                    {category.queries.map((query, qIdx) => (
                      <Button
                        key={qIdx}
                        variant="ghost"
                        size="sm"
                        justifyContent="flex-start"
                        fontSize="xs"
                        onClick={() => handleSuggestedQuery(query)}
                        _hover={{ bg: 'green.50', color: 'skoda.green' }}
                      >
                        {query}
                      </Button>
                    ))}
                  </VStack>
                </Box>
              ))}
            </VStack>
          </MotionBox>

          <MotionBox
            bg="white"
            p={5}
            borderRadius="lg"
            border="1px solid"
            borderColor="gray.200"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Text fontSize="lg" fontWeight="semibold" mb={4}>{t('assistant.deepDive')}</Text>
            <VStack spacing={2} align="stretch">
              {deepDiveTopics.map((topic, idx) => (
                <Button
                  key={idx}
                  variant="ghost"
                  p={3}
                  h="auto"
                  justifyContent="space-between"
                  borderRadius="lg"
                  _hover={{ bg: 'green.50', borderColor: 'skoda.green' }}
                >
                  <Box textAlign="left">
                    <Text fontSize="sm" fontWeight="semibold">{topic.title}</Text>
                    <Text fontSize="xs" color="gray.600">{topic.description}</Text>
                  </Box>
                  <Icon as={ChevronRight} w={4} h={4} color="gray.400" />
                </Button>
              ))}
            </VStack>
          </MotionBox>
        </VStack>
      </Grid>

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
          <Text fontSize="xl" fontWeight="semibold">{t('assistant.recentInsights')}</Text>
          <Button variant="outline" size="sm">View All Insights</Button>
        </HStack>

        <Grid templateColumns="repeat(3, 1fr)" gap={4}>
          {recentInsights.map((insight, idx) => (
            <Box
              key={idx}
              p={4}
              borderRadius="lg"
              border="1px solid"
              bg={insight.severity === 'high' ? 'red.50' : 'orange.50'}
              borderColor={insight.severity === 'high' ? 'red.200' : 'orange.200'}
            >
              <HStack justify="space-between" mb={2}>
                <Icon as={AlertCircle} w={5} h={5} color={insight.severity === 'high' ? 'red.600' : 'orange.600'} />
                <Badge variant="outline" fontSize="xs">{insight.department}</Badge>
              </HStack>
              <Text fontSize="lg" fontWeight="semibold" mb={2}>{insight.title}</Text>
              <Text fontSize="xs" color="gray.600" mb={3}>{insight.insight}</Text>
              <HStack justify="space-between">
                <HStack fontSize="xs" color="gray.600">
                  <Icon as={Clock} w={3} h={3} />
                  <Text>{insight.timestamp}</Text>
                </HStack>
                <Button size="sm" variant="ghost" fontSize="xs">View Details</Button>
              </HStack>
            </Box>
          ))}
        </Grid>
      </MotionBox>
    </VStack>
  );
};
