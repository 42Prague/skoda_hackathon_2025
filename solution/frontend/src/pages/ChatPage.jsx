import { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  Card, 
  CardContent,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Paper,
  List,
  ListItem,
  ListItemText,
  Divider
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import { useAuth } from '../context/AuthContext';
import { chatbotAPI } from '../services/api';

const ChatPage = () => {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId] = useState(() => `session-${Date.now()}`);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || loading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setError(null);

    // Add user message to chat
    const newUserMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: userMessage,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newUserMessage]);

    setLoading(true);

    try {
      const response = await chatbotAPI.sendMessage(
        userMessage,
        user?.personalNumber || user?.id || null,
        sessionId,
        true // use_context
      );

      // Add assistant response to chat
      const assistantMessage = {
        id: response.message_id || `msg-${Date.now()}-assistant`,
        role: 'assistant',
        content: response.reply,
        contextUsed: response.context_used,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      setError(err.message || 'Failed to send message');
      console.error('Chat error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Box
      sx={{
        minHeight: 'calc(100vh - 64px)',
        backgroundColor: 'background.default',
        color: 'text.primary',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Container maxWidth="lg" sx={{ py: 4, flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Typography 
          variant="h4" 
          component="h1" 
          sx={{ 
            mb: 4,
            color: 'text.primary',
            fontWeight: 600
          }}
        >
          Chat Assistant
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Card sx={{ boxShadow: 2, flex: 1, display: 'flex', flexDirection: 'column' }}>
          <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 0 }}>
            {/* Messages Area */}
            <Box
              sx={{
                flex: 1,
                overflowY: 'auto',
                p: 3,
                minHeight: 400,
                maxHeight: '60vh',
              }}
            >
              {messages.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 8 }}>
                  <Typography variant="body1" color="text.secondary">
                    Start a conversation by typing a message below.
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                    Ask about courses, career paths, or skills development.
                  </Typography>
                </Box>
              ) : (
                <List>
                  {messages.map((message, index) => (
                    <Box key={message.id}>
                      <ListItem
                        sx={{
                          justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                          px: 0,
                        }}
                      >
                        <Paper
                          elevation={1}
                          sx={{
                            p: 2,
                            maxWidth: '70%',
                            backgroundColor: message.role === 'user' 
                              ? 'primary.light' 
                              : 'background.paper',
                            color: message.role === 'user' 
                              ? 'primary.contrastText' 
                              : 'text.primary',
                          }}
                        >
                          <ListItemText
                            primary={message.content}
                            secondary={
                              message.contextUsed ? (
                                <Typography variant="caption" sx={{ mt: 0.5, display: 'block' }}>
                                  Used course context
                                </Typography>
                              ) : null
                            }
                            primaryTypographyProps={{
                              sx: {
                                whiteSpace: 'pre-wrap',
                                wordBreak: 'break-word',
                              },
                            }}
                          />
                        </Paper>
                      </ListItem>
                      {index < messages.length - 1 && <Divider />}
                    </Box>
                  ))}
                  {loading && (
                    <ListItem sx={{ justifyContent: 'flex-start', px: 0 }}>
                      <CircularProgress size={24} />
                    </ListItem>
                  )}
                  <div ref={messagesEndRef} />
                </List>
              )}
            </Box>

            {/* Input Area */}
            <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  multiline
                  maxRows={4}
                  placeholder="Type your message..."
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={loading}
                  variant="outlined"
                  size="small"
                />
                <Button
                  variant="contained"
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim() || loading}
                  startIcon={loading ? <CircularProgress size={16} /> : <SendIcon />}
                  sx={{ minWidth: 100 }}
                >
                  Send
                </Button>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
};

export default ChatPage;

