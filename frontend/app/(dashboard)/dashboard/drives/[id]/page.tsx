'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { QRCodeSVG } from 'qrcode.react'
import {
  ArrowLeft,
  Copy,
  ExternalLink,
  Users,
  Brain,
  Link as LinkIcon,
  CheckCircle,
  AlertCircle,
  Clock,
  MoreHorizontal
} from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu'
import { toast } from 'sonner'
import { api, DriveDetailResponse } from '@/lib/api'

export default function DriveDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const id = params.id as string
  
  const [drive, setDrive] = useState<DriveDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchDrive() {
      try {
        const data = await api.getDrive(id)
        setDrive(data)
      } catch (err: any) {
        setError(err.message || 'Failed to fetch drive')
      } finally {
        setLoading(false)
      }
    }
    if (id) fetchDrive()
  }, [id])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 space-y-4">
        <Spinner className="h-10 w-10 text-primary" />
        <p className="text-muted-foreground animate-pulse">Loading drive details...</p>
      </div>
    )
  }

  if (error || !drive) {
    return (
      <div className="flex flex-col items-center justify-center py-32 space-y-4">
        <div className="p-4 bg-destructive/10 rounded-full">
          <AlertCircle className="h-8 w-8 text-destructive" />
        </div>
        <h2 className="text-xl font-semibold">Drive not found</h2>
        <p className="text-muted-foreground">{error}</p>
        <Button variant="outline" onClick={() => router.push('/dashboard/drives')}>
          Back to Drives
        </Button>
      </div>
    )
  }

  const applyLink = typeof window !== 'undefined' ? `${window.location.origin}/apply/${drive.link_token}` : ''

  const copyLink = () => {
    navigator.clipboard.writeText(applyLink)
    toast.success('Apply link copied to clipboard!')
  }

  const toggleStatus = async () => {
    try {
      const newStatus = drive.status === 'active' ? 'closed' : 'active'
      await api.updateDriveStatus(drive.id, newStatus)
      setDrive({ ...drive, status: newStatus })
      toast.success(`Drive is now ${newStatus}`)
    } catch (err: any) {
      toast.error('Failed to update status', { description: err.message })
    }
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8 pb-10"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Button variant="ghost" onClick={() => router.back()} className="mb-2 -ml-3">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight">{drive.name}</h1>
            <Badge 
              variant="secondary" 
              className={drive.status === 'active' ? 'bg-emerald/10 text-emerald' : 'bg-muted text-muted-foreground'}
            >
              {drive.status}
            </Badge>
          </div>
          <p className="text-muted-foreground mt-1">
            {drive.domain} • Created {new Date(drive.created_at).toLocaleDateString()}
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={copyLink}>
            <Copy className="mr-2 h-4 w-4" />
            Copy Link
          </Button>
          <Button 
            variant={drive.status === 'active' ? 'destructive' : 'default'} 
            onClick={toggleStatus}
          >
            {drive.status === 'active' ? 'Close Drive' : 'Reopen Drive'}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Drive Info */}
        <Card className="lg:col-span-2 border-border/50 bg-card/50">
          <CardHeader>
            <CardTitle>Drive Configuration</CardTitle>
            <CardDescription>Settings and details for this recruitment drive</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <span className="text-sm text-muted-foreground">Task Type</span>
                <p className="font-medium capitalize flex items-center gap-2">
                  <Brain className="h-4 w-4 text-primary" /> {drive.task_type}
                </p>
              </div>
              <div className="space-y-1">
                <span className="text-sm text-muted-foreground">Level</span>
                <p className="font-medium capitalize">{drive.question_level}</p>
              </div>
              <div className="space-y-1">
                <span className="text-sm text-muted-foreground">Apply Deadline</span>
                <p className="font-medium">{new Date(drive.apply_deadline).toLocaleDateString()}</p>
              </div>
              <div className="space-y-1">
                <span className="text-sm text-muted-foreground">Task Deadline</span>
                <p className="font-medium">
                  {drive.task_deadline ? new Date(drive.task_deadline).toLocaleDateString() : 'N/A'}
                </p>
              </div>
            </div>

            {drive.task_description && (
              <div className="space-y-2 pt-4 border-t border-border/50">
                <span className="text-sm text-muted-foreground">Task Description</span>
                <p className="text-sm p-4 rounded-lg bg-muted/30">{drive.task_description}</p>
              </div>
            )}
            
            <div className="space-y-2 pt-4 border-t border-border/50">
              <span className="text-sm text-muted-foreground">Public Apply Link</span>
              <div className="flex items-center gap-2">
                <code className="text-sm bg-muted/50 p-2 rounded flex-1 truncate">{applyLink}</code>
                <Button size="icon" variant="ghost" onClick={copyLink}><Copy className="h-4 w-4" /></Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* QR Code & Pulse */}
        <Card className="border-border/50 bg-card/50 flex items-center justify-center p-6 lg:col-span-1">
          <div className="text-center space-y-4">
            <h3 className="font-medium">Scan to Apply</h3>
            <div className="bg-white p-4 rounded-xl inline-block shadow-sm">
              <QRCodeSVG
                value={applyLink}
                size={160}
                bgColor="#ffffff"
                fgColor="#000000"
                level="H"
              />
            </div>
            <p className="text-xs text-muted-foreground px-4">
              Candidates can scan this on any device to open the application portal.
            </p>
          </div>
        </Card>
      </div>

      {/* Applicants List */}
      <Card className="border-border/50 bg-card/50">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-primary" />
              Applicants
            </CardTitle>
            <CardDescription>Manage and review all {drive.applicants.length} candidates</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          {drive.applicants.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground">
              No applicants yet. Share your drive link to get started!
            </div>
          ) : (
            <div className="space-y-4">
              {drive.applicants.map((candidate) => (
               <div key={candidate.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border border-border/50 rounded-lg hover:border-primary/30 transition-colors gap-4">
                 <div className="flex items-center gap-4">
                   <div className="h-10 w-10 bg-primary/10 rounded-full flex items-center justify-center text-primary font-bold">
                     {candidate.name.charAt(0)}
                   </div>
                   <div>
                     <p className="font-semibold">{candidate.name}</p>
                     <p className="text-sm text-muted-foreground flex items-center gap-2">
                       {candidate.email} • {new Date(candidate.applied_at).toLocaleDateString()}
                     </p>
                   </div>
                 </div>
                 
                 <div className="flex items-center gap-4 justify-between sm:justify-end">
                   <div className="flex gap-2">
                     <StatusBadge status={candidate.status} />
                     {candidate.interview?.total_score && (
                       <Badge variant="outline" className="text-emerald border-emerald/20 bg-emerald/5">
                         Score: {candidate.interview.total_score}%
                       </Badge>
                     )}
                   </div>
                   
                   <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon"><MoreHorizontal className="h-4 w-4" /></Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        {candidate.github_url && (
                          <DropdownMenuItem onClick={() => window.open(candidate.github_url, '_blank')}>
                            <LinkIcon className="h-4 w-4 mr-2" /> View GitHub
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuItem>
                          <ExternalLink className="h-4 w-4 mr-2" /> View Full Profile
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                   </DropdownMenu>
                 </div>
               </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      
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
    label: status.replace('_', ' '),
  }

  return (
    <Badge variant="secondary" className={config.className}>
      <config.icon className="mr-1 h-3 w-3" />
      <span className="capitalize">{config.label}</span>
    </Badge>
  )
}
