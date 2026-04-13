'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Users, 
  FolderOpen, 
  Brain, 
  TrendingUp, 
  Activity,
  BarChart3,
  PieChart as PieChartIcon
} from 'lucide-react'
import { 
  LineChart, 
  Line, 
  AreaChart,
  Area,
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend
} from 'recharts'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Spinner } from '@/components/ui/spinner'
import { api, AnalyticsResponse } from '@/lib/api'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { 
    opacity: 1, 
    transition: { staggerChildren: 0.1 } 
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
}

const COLORS = ['#0ea5e9', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#64748b']

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchAnalytics() {
      try {
        const res = await api.getAnalytics()
        setData(res)
      } catch (err: any) {
        setError(err.message || 'Failed to load analytics data')
      } finally {
        setLoading(false)
      }
    }
    fetchAnalytics()
  }, [])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 space-y-4">
        <Spinner className="h-10 w-10 text-primary" />
        <p className="text-muted-foreground animate-pulse">Gathering insights...</p>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex flex-col items-center justify-center py-32 space-y-4">
        <div className="p-4 bg-destructive/10 rounded-full">
          <Activity className="h-8 w-8 text-destructive" />
        </div>
        <h2 className="text-xl font-semibold">Oops, something went wrong</h2>
        <p className="text-muted-foreground">{error}</p>
      </div>
    )
  }

  const highlightCards = [
    {
      title: 'Total Drives',
      value: data.total_drives,
      change: `${data.active_drives} active currently`,
      icon: FolderOpen,
      color: 'text-primary',
      bgColor: 'bg-primary/10',
    },
    {
      title: 'Candidates',
      value: data.total_applicants,
      change: 'All time applications',
      icon: Users,
      color: 'text-cyan',
      bgColor: 'bg-cyan/10',
    },
    {
      title: 'Interviews',
      value: data.total_interviews,
      change: 'Completed sessions',
      icon: Brain,
      color: 'text-emerald',
      bgColor: 'bg-emerald/10',
    },
    {
      title: 'Average Score',
      value: `${data.avg_score}%`,
      change: 'Overall performance',
      icon: TrendingUp,
      color: 'text-amber',
      bgColor: 'bg-amber/10',
    },
  ]

  // Custom tooltips for nice styling
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card border border-border/50 p-3 rounded-lg shadow-xl backdrop-blur-md">
          <p className="text-sm font-medium mb-1">{label}</p>
          <p className="text-sm text-primary">
            {payload[0].name}: <span className="font-bold">{payload[0].value}</span>
          </p>
        </div>
      )
    }
    return null
  }

  const CustomPieTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card border border-border/50 p-3 rounded-lg shadow-xl backdrop-blur-md">
          <p className="text-sm font-medium flex items-center gap-2">
            <span 
              className="w-3 h-3 rounded-full" 
              style={{ backgroundColor: payload[0].payload.fill }} 
            />
            {payload[0].name}: <span className="font-bold">{payload[0].value}</span>
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-8 pb-10"
    >
      {/* Header */}
      <motion.div variants={itemVariants}>
        <h1 className="text-3xl font-bold tracking-tight">Analytics & Reports</h1>
        <p className="text-muted-foreground mt-2">
          Deep dive into your recruitment data and candidate insights.
        </p>
      </motion.div>

      {/* Highlights Grid */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {highlightCards.map((card, index) => (
          <Card key={index} className="card-hover border-border/50 bg-card/50 overflow-hidden relative group">
            <div className="absolute top-0 right-0 -mr-8 -mt-8 w-32 h-32 rounded-full bg-gradient-to-br from-transparent to-primary/5 opacity-50 group-hover:scale-150 transition-transform duration-700 ease-in-out" />
            <CardContent className="p-6 relative z-10">
              <div className="flex items-center justify-between">
                <div className={`p-3 rounded-xl ${card.bgColor}`}>
                  <card.icon className={`h-6 w-6 ${card.color}`} />
                </div>
              </div>
              <div className="mt-4">
                <div className="text-4xl font-bold tracking-tight">{card.value}</div>
                <div className="text-sm font-medium mt-2">{card.title}</div>
                <div className="text-xs text-muted-foreground mt-1">{card.change}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </motion.div>

      {/* Row 1: Trend & Domains */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Trend Area Chart */}
        <motion.div variants={itemVariants} className="lg:col-span-2">
          <Card className="border-border/50 bg-card/50 h-full">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-primary" />
                <CardTitle>Application Trend</CardTitle>
              </div>
              <CardDescription>Number of applications over the last 7 days</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] w-full mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data.recent_trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="opacity-10" />
                    <XAxis 
                      dataKey="name" 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: 'currentColor', opacity: 0.5, fontSize: 12 }} 
                      dy={10}
                    />
                    <YAxis 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: 'currentColor', opacity: 0.5, fontSize: 12 }} 
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Area 
                      type="monotone" 
                      dataKey="value" 
                      name="Applications"
                      stroke="#0ea5e9" 
                      strokeWidth={3}
                      fillOpacity={1} 
                      fill="url(#colorValue)" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Domain Distribution */}
        <motion.div variants={itemVariants} className="lg:col-span-1">
          <Card className="border-border/50 bg-card/50 h-full flex flex-col">
            <CardHeader>
              <div className="flex items-center gap-2">
                <PieChartIcon className="h-5 w-5 text-primary" />
                <CardTitle>Domain Distribution</CardTitle>
              </div>
              <CardDescription>Candidate primary skills</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col items-center justify-center pb-8">
              <div className="h-[250px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={data.domain_distribution}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={5}
                      dataKey="value"
                      stroke="none"
                    >
                      {data.domain_distribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomPieTooltip />} />
                    <Legend 
                      verticalAlign="bottom" 
                      height={36} 
                      iconType="circle"
                      wrapperStyle={{ fontSize: '12px', paddingTop: '20px' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Row 2: Scores & Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Score Distribution */}
        <motion.div variants={itemVariants}>
          <Card className="border-border/50 bg-card/50">
            <CardHeader>
              <div className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-emerald" />
                <CardTitle>Score Distribution</CardTitle>
              </div>
              <CardDescription>Aggregate interview scores across all drives</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] w-full mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.score_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="opacity-10" />
                    <XAxis 
                      dataKey="name" 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: 'currentColor', opacity: 0.5, fontSize: 12 }} 
                      dy={10}
                    />
                    <YAxis 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: 'currentColor', opacity: 0.5, fontSize: 12 }} 
                    />
                    <Tooltip 
                      cursor={{ fill: 'currentColor', opacity: 0.05 }}
                      content={<CustomTooltip />} 
                    />
                    <Bar 
                      dataKey="value" 
                      name="Candidates"
                      fill="#10b981" 
                      radius={[4, 4, 0, 0]} 
                      barSize={40}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Status Distribution */}
        <motion.div variants={itemVariants}>
          <Card className="border-border/50 bg-card/50">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5 text-amber" />
                <CardTitle>Pipeline Status</CardTitle>
              </div>
              <CardDescription>Current stage of all applicants</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] w-full mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart 
                    data={data.status_distribution} 
                    margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                    layout="vertical"
                  >
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="currentColor" className="opacity-10" />
                    <XAxis 
                      type="number"
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: 'currentColor', opacity: 0.5, fontSize: 12 }} 
                    />
                    <YAxis 
                      type="category"
                      dataKey="name" 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: 'currentColor', opacity: 0.8, fontSize: 12 }} 
                      width={100}
                    />
                    <Tooltip 
                      cursor={{ fill: 'currentColor', opacity: 0.05 }}
                      content={<CustomTooltip />} 
                    />
                    <Bar 
                      dataKey="value" 
                      name="Candidates"
                      fill="#f59e0b" 
                      radius={[0, 4, 4, 0]} 
                      barSize={24}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

    </motion.div>
  )
}