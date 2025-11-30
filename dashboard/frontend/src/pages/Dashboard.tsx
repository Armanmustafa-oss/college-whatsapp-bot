import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import Button from '@/components/Button';
import { LogOut, BarChart3, TrendingUp, PieChart, AlertCircle, Users, Settings } from 'lucide-react';

interface Metric {
  label: string;
  value: string;
  icon: React.ReactNode;
  color: string;
}

export default function Dashboard() {
  const { user, logout, token } = useAuth();
  const navigate = useNavigate();
  const [metrics, setMetrics] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeSection, setActiveSection] = useState('overview');

  useEffect(() => {
    const loadMetrics = async () => {
      try {
        if (token) {
          const data = await apiClient.getDashboardMetrics(token);
          setMetrics(data);
        }
      } catch (error) {
        console.error('Failed to load metrics:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadMetrics();
  }, [token]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const dashboardMetrics: Metric[] = [
    {
      label: 'Monthly Cost Savings',
      value: '$47,500',
      icon: <TrendingUp className="w-6 h-6" />,
      color: 'from-green-500/20 to-green-600/20',
    },
    {
      label: 'Avg Response Time',
      value: '3.2s',
      icon: <BarChart3 className="w-6 h-6" />,
      color: 'from-blue-500/20 to-blue-600/20',
    },
    {
      label: 'Student Satisfaction',
      value: '94%',
      icon: <PieChart className="w-6 h-6" />,
      color: 'from-purple-500/20 to-purple-600/20',
    },
    {
      label: 'Resolution Rate',
      value: '87%',
      icon: <AlertCircle className="w-6 h-6" />,
      color: 'from-orange-500/20 to-orange-600/20',
    },
  ];

  const navigationItems = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'analytics', label: 'Analytics', icon: TrendingUp },
    { id: 'queries', label: 'Queries', icon: PieChart },
    { id: 'alerts', label: 'Alerts', icon: AlertCircle },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0f1419] to-[#1a1f2e]">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-gradient-to-b from-[#1a1f2e] to-[#0f1419] border-b border-[#3b82f6]/20 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-[#7c3aed] to-[#3b82f6] bg-clip-text text-transparent">
              College-Bot Analytics
            </h1>
            <p className="text-xs text-gray-400 mt-1">Dashboard</p>
          </div>

          <div className="flex items-center gap-4">
            {user && (
              <div className="text-right">
                <p className="text-sm font-medium text-white">{user.full_name || user.email}</p>
                <p className="text-xs text-gray-400">{user.role}</p>
              </div>
            )}
            <Button
              onClick={handleLogout}
              variant="secondary"
              size="sm"
              className="flex items-center gap-2"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-gradient-to-b from-[#1a1f2e] to-[#0f1419] border-r border-[#3b82f6]/20 p-4">
          <nav className="space-y-2">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveSection(item.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                    activeSection === item.id
                      ? 'bg-[#3b82f6]/20 text-[#3b82f6] border border-[#3b82f6]/30'
                      : 'text-gray-400 hover:text-white hover:bg-[#3b82f6]/10'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="text-sm font-medium">{item.label}</span>
                </button>
              );
            })}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          {isLoading ? (
            <div className="flex items-center justify-center h-96">
              <div className="text-center">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-[#3b82f6]"></div>
                <p className="text-white mt-4">Loading dashboard...</p>
              </div>
            </div>
          ) : (
            <>
              {activeSection === 'overview' && (
                <div>
                  <h2 className="text-2xl font-bold text-white mb-6">Dashboard Overview</h2>

                  {/* Metrics Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    {dashboardMetrics.map((metric, index) => (
                      <div
                        key={index}
                        className={`bg-gradient-to-br ${metric.color} border border-[#3b82f6]/20 rounded-xl p-6 hover:border-[#3b82f6]/40 transition-all`}
                      >
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <p className="text-gray-400 text-sm">{metric.label}</p>
                            <p className="text-3xl font-bold text-white mt-2">{metric.value}</p>
                          </div>
                          <div className="text-[#3b82f6]">{metric.icon}</div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Welcome Message */}
                  <div className="bg-gradient-to-r from-[#1a1f2e] to-[#0f1419] border border-[#3b82f6]/20 rounded-xl p-8">
                    <h3 className="text-xl font-semibold text-white mb-2">Welcome to College-Bot Analytics</h3>
                    <p className="text-gray-400">
                      This is your central hub for monitoring chatbot performance, analyzing student queries, and optimizing your institution's support system.
                    </p>
                  </div>
                </div>
              )}

              {activeSection === 'analytics' && (
                <div>
                  <h2 className="text-2xl font-bold text-white mb-6">Analytics</h2>
                  <div className="bg-gradient-to-r from-[#1a1f2e] to-[#0f1419] border border-[#3b82f6]/20 rounded-xl p-8">
                    <p className="text-gray-400">Analytics section coming soon...</p>
                  </div>
                </div>
              )}

              {activeSection === 'queries' && (
                <div>
                  <h2 className="text-2xl font-bold text-white mb-6">Query Analysis</h2>
                  <div className="bg-gradient-to-r from-[#1a1f2e] to-[#0f1419] border border-[#3b82f6]/20 rounded-xl p-8">
                    <p className="text-gray-400">Query analysis section coming soon...</p>
                  </div>
                </div>
              )}

              {activeSection === 'alerts' && (
                <div>
                  <h2 className="text-2xl font-bold text-white mb-6">Alerts & Monitoring</h2>
                  <div className="bg-gradient-to-r from-[#1a1f2e] to-[#0f1419] border border-[#3b82f6]/20 rounded-xl p-8">
                    <p className="text-gray-400">Alerts section coming soon...</p>
                  </div>
                </div>
              )}

              {activeSection === 'settings' && (
                <div>
                  <h2 className="text-2xl font-bold text-white mb-6">Settings</h2>
                  <div className="bg-gradient-to-r from-[#1a1f2e] to-[#0f1419] border border-[#3b82f6]/20 rounded-xl p-8">
                    <p className="text-gray-400">Settings section coming soon...</p>
                  </div>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}