'use client'

import { useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  Users,
  FolderOpen,
  Brain,
  TrendingUp,
  Plus,
  ArrowRight,
  Clock,
  CheckCircle,
  AlertCircle,
  MoreHorizontal,
  ExternalLink,
  BarChart3,
  Settings,
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Spinner } from '@/components/ui/spinner'
import { api, type DriveResponse, type DriveDetailResponse, type ApplicantResponse } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [drives, setDrives] = useState<DriveResponse[]>([])
  const [allApplicants, setAllApplicants] = useState<(ApplicantResponse & { driveName?: string })[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        const drivesData = await api.listDrives()
        setDrives(drivesData)

        // Fetch detail for each drive to get applicants
        const applicants: (ApplicantResponse & { driveName?: string })[] = []
        for (const d of drivesData.slice(0, 5)) {
          try {
            const detail = await api.getDrive(d.id)
            for (const a of detail.applicants) {
              applicants.push({ ...a, driveName: d.name })
            }
          } catch { /* skip */ }
        }
        setAllApplicants(applicants)
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const stats = useMemo(() => {
    const activeDrives = drives.filter(d => d.status === 'active').length
    const totalApplicants = drives.reduce((sum, d) => sum + d.applicant_count, 0)
    const interviewed = allApplicants.filter(a => a.interview?.ended_at).length
    const scores = allApplicants
      .filter(a => a.interview?.total_score)
      .map(a => a.interview!.total_score)
    const avgScore = scores.length > 0 ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0

    return [
      {
        title: 'Active Drives',
        value: activeDrives,
        change: `${drives.length} total`,
        icon: FolderOpen,
        color: 'text-primary',
        bgColor: 'bg-primary/8',
        accent: 'bg-primary',
      },
      {
        title: 'Total Applicants',
        value: totalApplicants,
        change: `Across ${drives.length} drives`,
        icon: Users,
        color: 'text-cyan',
        bgColor: 'bg-cyan/8',
        accent: 'bg-cyan',
      },
      {
        title: 'Interviews Completed',
        value: interviewed,
        change: `${allApplicants.length - interviewed} pending`,
        icon: Brain,
        color: 'text-emerald',
        bgColor: 'bg-emerald/8',
        accent: 'bg-emerald',
      },
      {
        title: 'Avg. Score',
        value: avgScore ? `${avgScore}%` : '—',
        change: scores.length > 0 ? `From ${scores.length} interviews` : 'No data yet',
        icon: TrendingUp,
        color: 'text-amber',
        bgColor: 'bg-amber/8',
        accent: 'bg-amber',
      },
    ]
  }, [drives, allApplicants])

  const recentDrives = drives.slice(0, 3)
  const recentApplicants = allApplicants.slice(0, 4)

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner className="h-8 w-8 text-primary" />
      </div>
    )
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-8"
    >
      {/* Welcome Section */}
      <motion.div variants={itemVariants} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">
            {(() => {
              const hour = new Date().getHours()
              return hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'
            })()}{user?.name ? `, ${user.name}` : ''}!
          </h1>
          <p className="text-muted-foreground mt-1">
            Here&apos;s what&apos;s happening with your recruitment drives.
          </p>
        </div>
        <Button asChild className="gradient-primary border-0 hover:opacity-90">
          <Link href="/dashboard/drives/new">
            <Plus className="mr-2 h-4 w-4" />
            Create Drive
          </Link>
        </Button>
      </motion.div>

      {/* Stats Grid */}
      <motion.div variants={itemVariants} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => (
          <Card key={stat.title} className="card-hover border-border/50 bg-card/50 overflow-hidden relative">
            <div className={`absolute top-0 left-0 right-0 h-0.5 ${stat.accent}`} />
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                  <stat.icon className={`h-5 w-5 ${stat.color}`} />
                </div>
                <span className="text-xs text-muted-foreground">{stat.change}</span>
              </div>
              <div className="mt-4">
                <div className="text-3xl font-bold">{stat.value}</div>
                <div className="text-sm text-muted-foreground mt-1">{stat.title}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </motion.div>

      {/* Recent Drives & Applicants */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent Drives */}
        <motion.div variants={itemVariants}>
          <Card className="border-border/50 bg-card/50">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg">Active Drives</CardTitle>
                <CardDescription>Your current recruitment drives</CardDescription>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/dashboard/drives">
                  View all
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              {recentDrives.map((drive) => (
                <div
                  key={drive.id}
                  className="flex items-center justify-between p-4 rounded-lg border border-border/50 hover:border-primary/30 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium truncate">{drive.name}</h3>
                      <Badge
                        variant="secondary"
                        className={
                          drive.status === 'active'
                            ? 'bg-emerald/10 text-emerald border-emerald/20'
                            : 'bg-muted text-muted-foreground'
                        }
                      >
                        {drive.status}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                      <span>{drive.domain}</span>
                      <span className="flex items-center gap-1">
                        <Users className="h-3 w-3" />
                        {drive.applicant_count} applicants
                      </span>
                    </div>
                    <div className="mt-3">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-muted-foreground">Applicants</span>
                        <span className="font-medium">
                          {drive.applicant_count}
                        </span>
                      </div>
                      <Progress
                        value={drive.applicant_count > 0 ? 100 : 0}
                        className="h-1.5"
                      />
                    </div>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="ml-2 flex-shrink-0">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem>
                        <ExternalLink className="mr-2 h-4 w-4" />
                        View Details
                      </DropdownMenuItem>
                      <DropdownMenuItem>Share Link</DropdownMenuItem>
                      <DropdownMenuItem>Edit Drive</DropdownMenuItem>
                      <DropdownMenuItem className="text-destructive">
                        Close Drive
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              ))}
            </CardContent>
          </Card>
        </motion.div>

        {/* Recent Applicants */}
        <motion.div variants={itemVariants}>
          <Card className="border-border/50 bg-card/50">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg">Recent Applicants</CardTitle>
                <CardDescription>Latest candidate applications</CardDescription>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/dashboard/drives">
                  View all
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentApplicants.map((applicant) => (
                  <div
                    key={applicant.id}
                    className="flex items-center justify-between p-3 rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <span className="text-sm font-medium text-primary">
                          {applicant.name.split(' ').map(n => n[0]).join('')}
                        </span>
                      </div>
                      <div className="min-w-0">
                        <div className="font-medium truncate">{applicant.name}</div>
                        <div className="text-xs text-muted-foreground truncate">
                          {applicant.driveName || applicant.primary_domain}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <StatusBadge status={applicant.status} />
                      {applicant.interview?.total_score && (
                        <span className="text-sm font-medium text-emerald">
                          {applicant.interview.total_score}%
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Quick Actions */}
      <motion.div variants={itemVariants}>
        <Card className="border-border/50 bg-card/50">
          <CardHeader>
            <CardTitle className="text-lg">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { icon: Plus, label: 'Create New Drive', href: '/dashboard/drives/new' },
                { icon: Users, label: 'View All Applicants', href: '/dashboard/drives' },
                { icon: BarChart3, label: 'View Analytics', href: '/dashboard/analytics' },
                { icon: Settings, label: 'Organization Settings', href: '/dashboard/settings' },
              ].map((action) => (
                <Button
                  key={action.label}
                  variant="outline"
                  className="h-auto py-4 flex-col gap-2 hover:border-primary/30"
                  asChild
                >
                  <Link href={action.href}>
                    <action.icon className="h-5 w-5" />
                    <span className="text-sm">{action.label}</span>
                  </Link>
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const config = {
    interviewed: {
      icon: CheckCircle,
      className: 'bg-emerald/10 text-emerald border-emerald/20',
      label: 'Interviewed',
    },
    submitted: {
      icon: Clock,
      className: 'bg-primary/10 text-primary border-primary/20',
      label: 'Submitted',
    },
    applied: {
      icon: AlertCircle,
      className: 'bg-cyan/10 text-cyan border-cyan/20',
      label: 'Applied',
    },
  }[status] || {
    icon: AlertCircle,
    className: 'bg-muted text-muted-foreground',
    label: status,
  }

  return (
    <Badge variant="secondary" className={config.className}>
      <config.icon className="mr-1 h-3 w-3" />
      {config.label}
    </Badge>
  )
}
