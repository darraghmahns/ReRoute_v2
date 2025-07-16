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
      <div className="flex justify-center w-full mb-4 sticky top-0 z-10">
        <div className="flex space-x-2 px-4 py-2 rounded-2xl shadow-lg bg-white/90 border-2 border-reroute-primary mx-auto" style={{width: 'fit-content', minWidth: 0}}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={
                `px-4 py-2 rounded-full text-sm font-semibold whitespace-nowrap transition-colors ` +
                (activeTab === tab.id
                  ? 'bg-reroute-primary text-white shadow-md'
                  : 'bg-white text-reroute-primary hover:bg-reroute-primary/10 hover:text-reroute-primary')
              }
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div>
        {renderContent()}
      </div>
    </div>
  );
};

export default Main;