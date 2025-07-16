import React, { useState } from 'react';
import Dashboard from './Dashboard';
import RoutesPage from './Routes';
import TrainingPage from './Training';
import ChatPage from './Chat';

const tabs = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'routes', label: 'Routes' },
  { id: 'training', label: 'Training' },
  { id: 'chat', label: 'Chat' },
] as const;

type TabId = typeof tabs[number]['id'];

const Main: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabId>('dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'routes':
        return <RoutesPage />;
      case 'training':
        return <TrainingPage />;
      case 'chat':
        return <ChatPage />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-full">
      {/* Slider / Tab nav */}
      <div className="flex justify-center space-x-2 mb-4 overflow-x-auto px-2 py-2 bg-reroute-card border-b border-reroute-card sticky top-0 z-10">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={
              `px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors ` +
              (activeTab === tab.id
                ? 'bg-reroute-primary text-white'
                : 'bg-reroute-card text-gray-400 hover:text-white hover:bg-reroute-card/80')
            }
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div>
        {renderContent()}
      </div>
    </div>
  );
};

export default Main;