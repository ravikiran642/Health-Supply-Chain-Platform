import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Header } from './components/Header';
import { LoginScreen } from './components/LoginScreen';
import { DashboardScreen } from './components/DashboardScreen';
import { EndpointSettingsModal } from './components/EndpointSettingsModal';
import { ApiLogsDrawer } from './components/ApiLogsDrawer';

const AppContent: React.FC = () => {
  const { isAuthenticated, apiLogs } = useAuth();
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [isLogsOpen, setIsLogsOpen] = useState<boolean>(false);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-teal-500 selection:text-white">
      {/* Top Navigation */}
      <Header
        onOpenSettings={() => setIsSettingsOpen(true)}
        onToggleLogs={() => setIsLogsOpen(!isLogsOpen)}
        logsCount={apiLogs.length}
      />

      {/* Main View Area: Auth Screen or Authenticated Dashboard */}
      <main className="flex-1">
        {isAuthenticated ? <DashboardScreen /> : <LoginScreen />}
      </main>

      {/* Endpoint Configuration Modal */}
      <EndpointSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />

      {/* Request & Response Logs Drawer */}
      <ApiLogsDrawer
        isOpen={isLogsOpen}
        onClose={() => setIsLogsOpen(false)}
      />
    </div>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
