'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  Users,
  Calendar,
  QrCode,
  Link2,
  Edit,
  Trash2,
  Eye,
  Copy,
} from 'lucide-react'
import { toast } from 'sonner'
import { Spinner } from '@/components/ui/spinner'
import { api, type DriveResponse } from '@/lib/api'

export default function DrivesPage() {
  const [drives, setDrives] = useState<DriveResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  useEffect(() => {
    api.listDrives()
      .then(setDrives)
      .catch(err => toast.error('Failed to load drives'))
      .finally(() => setLoading(false))
  }, [])

  const filteredDrives = drives.filter((drive) => {
    const matchesSearch = drive.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      drive.domain.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = statusFilter === 'all' || drive.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const copyLink = (token: string) => {
    navigator.clipboard.writeText(`${window.location.origin}/apply/${token}`)
    toast.success('Link copied to clipboard!')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner className="h-8 w-8 text-primary" />
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">All Drives</h1>
          <p className="text-muted-foreground mt-1">
            Manage your recruitment drives
          </p>
        </div>
        <Button asChild className="gradient-primary border-0 hover:opacity-90">
          <Link href="/dashboard/drives/new">
            <Plus className="mr-2 h-4 w-4" />
            Create Drive
          </Link>
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search drives..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-40">
            <Filter className="mr-2 h-4 w-4" />
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="closed">Closed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Drives Grid */}
      <div className="grid gap-4 md:grid-cols-2">
        {filteredDrives.map((drive, index) => (
          <motion.div
            key={drive.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
          >
            <Card className="card-hover border-border/50 bg-card/50 overflow-hidden">
              <CardContent className="p-6">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-lg">{drive.name}</h3>
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
                    <div className="flex items-center gap-3 text-sm text-muted-foreground">
                      <span>{drive.domain}</span>
                      <span className="text-border">|</span>
                      <span className="capitalize">{drive.question_level}</span>
                    </div>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem asChild>
                        <Link href={`/dashboard/drives/${drive.id}`}>
                          <Eye className="mr-2 h-4 w-4" />
                          View Details
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => copyLink(drive.link_token)}>
                        <Copy className="mr-2 h-4 w-4" />
                        Copy Link
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <QrCode className="mr-2 h-4 w-4" />
                        Show QR Code
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem>
                        <Edit className="mr-2 h-4 w-4" />
                        Edit Drive
                      </DropdownMenuItem>
                      <DropdownMenuItem className="text-destructive">
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete Drive
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <div className="text-2xl font-bold">{drive.applicant_count}</div>
                    <div className="text-xs text-muted-foreground">Applicants</div>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <div className="text-2xl font-bold">{drive.task_type}</div>
                    <div className="text-xs text-muted-foreground">Task Type</div>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <div className="text-2xl font-bold capitalize">{drive.question_level}</div>
                    <div className="text-xs text-muted-foreground">Level</div>
                  </div>
                </div>

                {/* Progress */}
                <div className="mb-4">
                  <div className="flex items-center justify-between text-xs mb-2">
                    <span className="text-muted-foreground">Applicant count</span>
                    <span className="font-medium">
                      {drive.applicant_count}
                    </span>
                  </div>
                  <Progress
                    value={drive.applicant_count > 0 ? 100 : 0}
                    className="h-2"
                  />
                </div>

                {/* Meta */}
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-1 text-muted-foreground">
                    <Calendar className="h-4 w-4" />
                    <span>Deadline: {new Date(drive.apply_deadline).toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyLink(drive.link_token)}
                    >
                      <Link2 className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="sm">
                      <QrCode className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Empty State */}
      {filteredDrives.length === 0 && (
        <Card className="border-border/50 bg-card/50">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center mb-4">
              <Users className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold mb-2">No drives found</h3>
            <p className="text-muted-foreground text-center max-w-sm mb-4">
              {searchQuery || statusFilter !== 'all'
                ? 'Try adjusting your filters to find what you\'re looking for.'
                : 'Get started by creating your first recruitment drive.'}
            </p>
            {!searchQuery && statusFilter === 'all' && (
              <Button asChild className="gradient-primary border-0">
                <Link href="/dashboard/drives/new">
                  <Plus className="mr-2 h-4 w-4" />
                  Create Drive
                </Link>
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </motion.div>
  )
}
