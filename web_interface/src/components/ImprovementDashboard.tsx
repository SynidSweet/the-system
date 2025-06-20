import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  ArrowUpIcon,
  ArrowDownIcon,
  AlertTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  RefreshCwIcon,
  TrendingUpIcon,
  BrainIcon,
} from 'lucide-react';

interface ImprovementMetrics {
  status: string;
  metrics: {
    entities_improved: number;
    total_improvements: number;
    deployed: number;
    rolled_back: number;
    in_testing: number;
    avg_effectiveness: number;
    last_improvement: string;
  };
  opportunities: {
    total: number;
    high_impact: number;
    medium_impact: number;
    low_impact: number;
  };
  pending_reviews: number;
  system_health: {
    score: number;
    status: string;
    factors: {
      effectiveness: number;
      rollback_rate: number;
      success_rate: number;
    };
  };
}

interface ActiveImprovement {
  improvement_id: string;
  type: string;
  entity: string;
  description: string;
  status: string;
  deployed_at: string | null;
  expected_impact: Record<string, any>;
}

interface ImprovementHistory {
  improvement_id: string;
  type: string;
  entity: string;
  entity_name: string;
  description: string;
  status: string;
  effectiveness: number | null;
  created_at: string;
  deployed_at: string | null;
  evaluated_at: string | null;
}

const COLORS = {
  success: '#10b981',
  error: '#ef4444',
  warning: '#f59e0b',
  info: '#3b82f6',
  neutral: '#6b7280',
};

export default function ImprovementDashboard() {
  const [metrics, setMetrics] = useState<ImprovementMetrics | null>(null);
  const [activeImprovements, setActiveImprovements] = useState<ActiveImprovement[]>([]);
  const [history, setHistory] = useState<ImprovementHistory[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      setRefreshing(true);
      
      // Fetch all data in parallel
      const [statusRes, activeRes, historyRes, analyticsRes] = await Promise.all([
        fetch('/api/improvements/status'),
        fetch('/api/improvements/active'),
        fetch('/api/improvements/history?limit=20'),
        fetch('/api/improvements/analytics?hours=168'),
      ]);

      const [status, active, historyData, analyticsData] = await Promise.all([
        statusRes.json(),
        activeRes.json(),
        historyRes.json(),
        analyticsRes.json(),
      ]);

      setMetrics(status);
      setActiveImprovements(active.active_improvements);
      setHistory(historyData.improvements);
      setAnalytics(analyticsData);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch improvement data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'excellent':
        return COLORS.success;
      case 'good':
        return COLORS.info;
      case 'fair':
        return COLORS.warning;
      case 'needs_attention':
        return COLORS.error;
      default:
        return COLORS.neutral;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'deployed':
        return <CheckCircleIcon className="w-4 h-4 text-green-500" />;
      case 'rolled_back':
        return <XCircleIcon className="w-4 h-4 text-red-500" />;
      case 'testing':
        return <RefreshCwIcon className="w-4 h-4 text-blue-500 animate-spin" />;
      default:
        return <AlertTriangleIcon className="w-4 h-4 text-yellow-500" />;
    }
  };

  const formatEffectiveness = (value: number | null) => {
    if (value === null) return 'N/A';
    const percentage = (value * 100).toFixed(1);
    if (value > 0) {
      return (
        <span className="text-green-600 flex items-center gap-1">
          <ArrowUpIcon className="w-3 h-3" />
          {percentage}%
        </span>
      );
    } else if (value < 0) {
      return (
        <span className="text-red-600 flex items-center gap-1">
          <ArrowDownIcon className="w-3 h-3" />
          {Math.abs(parseFloat(percentage))}%
        </span>
      );
    }
    return <span className="text-gray-500">{percentage}%</span>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCwIcon className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <BrainIcon className="w-8 h-8 text-purple-600" />
          <h1 className="text-3xl font-bold">Self-Improvement Dashboard</h1>
        </div>
        <Button
          onClick={fetchDashboardData}
          disabled={refreshing}
          variant="outline"
          size="sm"
        >
          <RefreshCwIcon className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* System Health Card */}
      {metrics && (
        <Card>
          <CardHeader>
            <CardTitle>System Health</CardTitle>
            <CardDescription>Overall self-improvement system status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <div className="text-2xl font-bold mb-2">
                  Health Score: {metrics.system_health.score}%
                </div>
                <Progress 
                  value={metrics.system_health.score} 
                  className="h-3"
                  style={{
                    '--progress-color': getHealthColor(metrics.system_health.status),
                  } as React.CSSProperties}
                />
                <Badge 
                  className="mt-2"
                  style={{ 
                    backgroundColor: getHealthColor(metrics.system_health.status),
                    color: 'white' 
                  }}
                >
                  {metrics.system_health.status.replace('_', ' ').toUpperCase()}
                </Badge>
              </div>
              
              <div className="space-y-2">
                <div className="text-sm text-gray-600">Key Factors</div>
                <div className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span>Effectiveness</span>
                    <span>{(metrics.system_health.factors.effectiveness * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Success Rate</span>
                    <span>{(metrics.system_health.factors.success_rate * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Rollback Rate</span>
                    <span className={metrics.system_health.factors.rollback_rate > 0.2 ? 'text-red-600' : ''}>
                      {(metrics.system_health.factors.rollback_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="text-sm text-gray-600">Opportunities</div>
                <div className="flex items-center gap-2">
                  <div className="text-2xl font-bold">{metrics.opportunities.total}</div>
                  <div className="text-sm text-gray-500">pending</div>
                </div>
                <div className="flex gap-2">
                  <Badge variant="destructive" className="text-xs">
                    High: {metrics.opportunities.high_impact}
                  </Badge>
                  <Badge variant="secondary" className="text-xs">
                    Med: {metrics.opportunities.medium_impact}
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    Low: {metrics.opportunities.low_impact}
                  </Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Metrics Overview */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total Improvements</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.metrics.total_improvements}</div>
              <p className="text-xs text-gray-600 mt-1">
                {metrics.metrics.entities_improved} entities improved
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {metrics.metrics.deployed > 0 
                  ? ((metrics.metrics.deployed / metrics.metrics.total_improvements) * 100).toFixed(1)
                  : 0}%
              </div>
              <p className="text-xs text-gray-600 mt-1">
                {metrics.metrics.deployed} deployed successfully
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Average Effectiveness</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatEffectiveness(metrics.metrics.avg_effectiveness)}
              </div>
              <p className="text-xs text-gray-600 mt-1">
                Performance improvement
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Active Improvements</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.metrics.in_testing}</div>
              <p className="text-xs text-gray-600 mt-1">
                Currently being tested
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Analytics Charts */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Improvements by Type */}
          <Card>
            <CardHeader>
              <CardTitle>Improvements by Type</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analytics.by_type}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="improvement_type" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill={COLORS.info} />
                  <Bar dataKey="deployed" fill={COLORS.success} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Daily Trends */}
          <Card>
            <CardHeader>
              <CardTitle>Daily Trends</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={analytics.daily_trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="improvements_created" 
                    stroke={COLORS.info} 
                    name="Created"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="deployed" 
                    stroke={COLORS.success} 
                    name="Deployed"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Active Improvements */}
      {activeImprovements.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Active Improvements</CardTitle>
            <CardDescription>Currently being tested or validated</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {activeImprovements.map((improvement) => (
                <div
                  key={improvement.improvement_id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    {getStatusIcon(improvement.status)}
                    <div>
                      <div className="font-medium">{improvement.description}</div>
                      <div className="text-sm text-gray-600">
                        {improvement.entity} • {improvement.type.replace('_', ' ')}
                      </div>
                    </div>
                  </div>
                  <Badge variant="outline">{improvement.status}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent History */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Improvement History</CardTitle>
          <CardDescription>Latest improvement attempts and results</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Status</th>
                  <th className="text-left p-2">Description</th>
                  <th className="text-left p-2">Entity</th>
                  <th className="text-left p-2">Type</th>
                  <th className="text-left p-2">Effectiveness</th>
                  <th className="text-left p-2">Date</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item) => (
                  <tr key={item.improvement_id} className="border-b">
                    <td className="p-2">{getStatusIcon(item.status)}</td>
                    <td className="p-2">{item.description}</td>
                    <td className="p-2 text-sm text-gray-600">{item.entity_name || item.entity}</td>
                    <td className="p-2">
                      <Badge variant="outline" className="text-xs">
                        {item.type.replace('_', ' ')}
                      </Badge>
                    </td>
                    <td className="p-2">{formatEffectiveness(item.effectiveness)}</td>
                    <td className="p-2 text-sm text-gray-600">
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}