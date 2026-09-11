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
      staggerChildren: 0.05,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 15 },
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
      },
      {
        title: 'Total Applicants',
        value: totalApplicants,
        change: `Across ${drives.length} drives`,
        icon: Users,
      },
      {
        title: 'Interviews Completed',
        value: interviewed,
        change: `${allApplicants.length - interviewed} pending`,
        icon: Brain,
      },
      {
        title: 'Avg. Score',
        value: avgScore ? `${avgScore}%` : '—',
        change: scores.length > 0 ? `From ${scores.length} interviews` : 'No data yet',
        icon: TrendingUp,
      },
    ]
  }, [drives, allApplicants])

  const recentDrives = drives.slice(0, 3)
  const recentApplicants = allApplicants.slice(0, 4)

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Spinner className="h-6 w-6 text-primary" />
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
      <motion.div variants={itemVariants} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="section-title">Overview</h2>
          <p className="text-muted-foreground mt-1">
            Metrics and recent activity across all your recruitment drives.
          </p>
        </div>
        <Button asChild size="default" className="bg-primary hover:bg-primary/90 text-primary-foreground font-semibold shrink-0">
          <Link href="/dashboard/drives/new">
            <Plus className="mr-2 h-4 w-4" />
            New Drive
          </Link>
        </Button>
      </motion.div>

      {/* Stats Grid */}
      <motion.div variants={itemVariants} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.title} className="solid-panel p-5 flex flex-col justify-between">
            <div className="flex items-start justify-between mb-4">
              <span className="text-sm font-medium text-muted-foreground">{stat.title}</span>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </div>
            <div>
              <div className="text-3xl font-bold font-mono tracking-tight text-foreground">{stat.value}</div>
              <div className="text-xs text-muted-foreground mt-2">{stat.change}</div>
            </div>
          </div>
        ))}
      </motion.div>

      {/* Main Content Area */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Recent Drives (Takes up 2 columns) */}
        <motion.div variants={itemVariants} className="lg:col-span-2">
          <div className="solid-panel h-full">
            <div className="p-6 border-b border-border flex items-center justify-between bg-secondary/20">
              <div>
                <h3 className="font-semibold text-base text-foreground">Active Drives</h3>
                <p className="text-sm text-muted-foreground mt-1">Your most recent recruitment pipelines</p>
              </div>
              <Button variant="outline" size="sm" asChild className="h-8">
                <Link href="/dashboard/drives">View all</Link>
              </Button>
            </div>
            <div className="divide-y divide-border">
              {recentDrives.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground text-sm">
                  No active drives found. Create one to get started.
                </div>
              ) : (
                recentDrives.map((drive) => (
                  <div key={drive.id} className="p-4 sm:p-6 hover:bg-secondary/20 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-1">
                        <Link href={`/dashboard/drives/${drive.id}`} className="font-semibold text-foreground hover:text-primary transition-colors truncate">
                          {drive.name}
                        </Link>
                        <Badge variant="outline" className={drive.status === 'active' ? 'bg-success-subtle border-success/20 font-medium' : 'bg-secondary text-muted-foreground'}>
                          {drive.status}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground mt-2">
                        <span className="truncate max-w-[200px]">{drive.domain}</span>
                        <span className="flex items-center gap-1.5 shrink-0">
                          <Users className="h-3.5 w-3.5" />
                          <span className="font-mono">{drive.applicant_count}</span> applicants
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Button variant="outline" size="sm" asChild>
                        <Link href={`/dashboard/drives/${drive.id}`}>Manage</Link>
                      </Button>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-9 w-9 text-muted-foreground">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-40">
                          <DropdownMenuItem asChild>
                            <Link href={`/dashboard/drives/${drive.id}`}>
                              <ExternalLink className="mr-2 h-4 w-4" /> Details
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem>Share Link</DropdownMenuItem>
                          <DropdownMenuItem className="text-destructive">Close Drive</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </motion.div>

        {/* Recent Applicants */}
        <motion.div variants={itemVariants} className="lg:col-span-1">
          <div className="solid-panel h-full flex flex-col">
            <div className="p-6 border-b border-border bg-secondary/20">
              <h3 className="font-semibold text-base text-foreground">Latest Candidates</h3>
              <p className="text-sm text-muted-foreground mt-1">Recently applied or interviewed</p>
            </div>
            <div className="flex-1 overflow-auto divide-y divide-border">
              {recentApplicants.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground text-sm">
                  No applicants yet.
                </div>
              ) : (
                recentApplicants.map((applicant) => (
                  <div key={applicant.id} className="p-4 hover:bg-secondary/20 transition-colors flex items-center justify-between">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="h-9 w-9 rounded-full bg-secondary flex items-center justify-center shrink-0 border border-border">
                        <span className="text-xs font-medium text-foreground">
                          {applicant.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                        </span>
                      </div>
                      <div className="min-w-0">
                        <div className="text-sm font-medium text-foreground truncate">{applicant.name}</div>
                        <div className="text-xs text-muted-foreground truncate max-w-[150px]">
                          {applicant.driveName || applicant.primary_domain}
                        </div>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1 shrink-0">
                      <StatusBadge status={applicant.status} />
                      {applicant.interview?.total_score && (
                        <span className="text-xs font-mono font-medium text-success">
                          {applicant.interview.total_score}%
                        </span>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
            <div className="p-4 border-t border-border bg-secondary/10">
              <Button variant="ghost" className="w-full text-sm text-muted-foreground hover:text-foreground" asChild>
                <Link href="/dashboard/drives">View all candidates</Link>
              </Button>
            </div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const config = {
    interviewed: {
      className: 'bg-success-subtle border-success/20 text-success',
      label: 'Interviewed',
    },
    submitted: {
      className: 'bg-primary-subtle border-primary/20 text-primary',
      label: 'Submitted',
    },
    applied: {
      className: 'bg-secondary border-border text-muted-foreground',
      label: 'Applied',
    },
  }[status] || {
    className: 'bg-secondary text-muted-foreground',
    label: status,
  }

  return (
    <Badge variant="outline" className={`text-[10px] px-2 py-0.5 font-medium ${config.className}`}>
      {config.label}
    </Badge>
  )
}
