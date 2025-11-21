import { Box } from '@chakra-ui/react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export const MainLayout = () => {
  return (
    <Box minH="100vh" bg="skoda.sand">
      <Sidebar />
      <Box ml="260px">
        <TopBar />
        <Box p={8}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
};
