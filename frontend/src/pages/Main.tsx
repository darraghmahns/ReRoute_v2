import React, { useState } from 'react';
import Dashboard from './Dashboard';
import RoutesPage from './Routes';
import TrainingPage from './Training';
import ChatPage from './Chat';
import { MessageCircle, Calendar, Map, TrendingUp } from 'lucide-react';

const tabs = [
  { id: 'ai', label: 'AI Assistant', icon: MessageCircle },
  { id: 'training', label: 'Training Plan', icon: Calendar },
  { id: 'routes', label: 'Routes', icon: Map },
  { id: 'performance', label: 'Performance', icon: TrendingUp },
] as const;

type TabId = typeof tabs[number]['id'];

const Main: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabId>('ai');

  const renderContent = () => {
    switch (activeTab) {
      case 'ai':
        return <ChatPage />;
      case 'training':
        return <TrainingPage />;
      case 'routes':
        return <RoutesPage />;
      case 'performance':
        return <Dashboard />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-full">
      {/* Slider / Tab nav */}
      <div className="flex justify-center w-full mb-4 sticky top-4 z-10">
        <div className="flex gap-2 px-2 py-2 rounded-xl bg-reroute-tabbar shadow-lg" style={{width: 'fit-content', minWidth: 0}}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-6 py-2 rounded-lg font-medium transition-colors text-base
                ${activeTab === tab.id
                  ? 'bg-reroute-tab-active text-white shadow'
                  : 'bg-transparent text-white/80 hover:bg-white/10'}
              `}
            >
              <tab.icon className={`w-5 h-5 ${activeTab === tab.id ? 'text-white' : 'text-white/80'}`} />
              <span>{tab.label}</span>
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