import React from 'react';
import ReactDOM from 'react-dom/client';
import { SkodaThemeProvider } from '@skodaflow/web-library';
import { CssBaseline } from '@mui/material';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <SkodaThemeProvider globalBaseline>
      <CssBaseline />
      <App />
    </SkodaThemeProvider>
  </React.StrictMode>
);

