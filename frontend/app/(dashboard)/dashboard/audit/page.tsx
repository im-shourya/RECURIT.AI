'use client'

import { useCallback, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  CheckSquare,
  FileText,
  KeyRound,
  ScrollText,
  Trash2,
  UserMinus,
  UserPlus,
  XSquare,
} from 'lucide-react'
import { toast } from 'sonner'

import { Card, CardContent } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Spinner } from '@/components/ui/spinner'
import { api, AuditEntry } from '@/lib/api'

/** Action -> how it reads in the timeline, and the icon that carries it. */
const ACTIONS: Record<string, { label: string; icon: typeof CheckSquare; tone: string }> = {
  'applicant.selected': { label: 'selected', icon: CheckSquare, tone: 'text-emerald' },
  'applicant.rejected': { label: 'rejected', icon: XSquare, tone: 'text-muted-foreground' },
  'applicant.deleted': { label: 'erased', icon: Trash2, tone: 'text-destructive' },
  'drive.created': { label: 'created drive', icon: FileText, tone: 'text-primary' },
  'drive.updated': { label: 'updated drive', icon: FileText, tone: 'text-muted-foreground' },
  'drive.deleted': { label: 'deleted drive', icon: Trash2, tone: 'text-destructive' },
  'member.invited': { label: 'invited', icon: UserPlus, tone: 'text-primary' },
  'member.role_changed': { label: 'changed role of', icon: UserPlus, tone: 'text-muted-foreground' },
  'member.removed': { label: 'removed', icon: UserMinus, tone: 'text-destructive' },
  'org.password_changed': { label: 'changed password', icon: KeyRound, tone: 'text-muted-foreground' },
}

function when(iso: string): string {
  const then = new Date(iso)
  const minutes = Math.floor((Date.now() - then.getTime()) / 60000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  if (minutes < 1440) return `${Math.floor(minutes / 60)}h ago`
  if (minutes < 10080) return `${Math.floor(minutes / 1440)}d ago`
  return then.toLocaleDateString()
}

export default function AuditPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [action, setAction] = useState('all')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      setEntries(
        await api.listAudit({
          action: action === 'all' ? undefined : action,
          limit: 100,
        }),
      )
    } catch (err: any) {
      toast.error('Could not load the audit trail', { description: err.message })
    } finally {
      setLoading(false)
    }
  }, [action])

  useEffect(() => {
    load()
  }, [load])

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6 max-w-4xl"
    >
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <ScrollText className="h-7 w-7 text-primary" />
            Activity
          </h1>
          <p className="text-muted-foreground mt-1">
            Who did what, and when. Entries cannot be edited or deleted.
          </p>
        </div>

        <Select value={action} onValueChange={setAction}>
          <SelectTrigger className="w-[210px]">
            <SelectValue placeholder="All activity" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All activity</SelectItem>
            {Object.entries(ACTIONS).map(([value, { label }]) => (
              <SelectItem key={value} value={value}>
                {label[0].toUpperCase() + label.slice(1)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <Spinner className="h-8 w-8 text-primary" />
        </div>
      ) : entries.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <p className="font-medium">Nothing recorded yet</p>
            <p className="text-sm text-muted-foreground mt-1">
              Decisions, drive changes and team updates will appear here.
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card className="overflow-hidden">
          <div className="divide-y">
            {entries.map((entry) => {
              const meta = ACTIONS[entry.action] ?? {
                label: entry.action,
                icon: ScrollText,
                tone: 'text-muted-foreground',
              }
              const Icon = meta.icon
              const actor =
                (entry.detail?.changed_by as string) ??
                (entry.detail?.invited_by as string) ??
                (entry.detail?.removed_by as string)

              return (
                <div key={entry.id} className="flex items-start gap-3 px-5 py-4">
                  <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                    <Icon className={`h-4 w-4 ${meta.tone}`} />
                  </div>

                  <div className="min-w-0 flex-1">
                    <p className="text-sm">
                      {actor && <span className="font-medium">{actor} </span>}
                      <span className={actor ? '' : 'font-medium'}>{meta.label}</span>{' '}
                      {/* Captured when the entry was written, so it still reads
                          correctly after the subject has been deleted. */}
                      <span className="font-medium">{entry.entity_label || entry.entity_type}</span>
                    </p>

                    {entry.detail?.drive ? (
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {String(entry.detail.drive)}
                        {entry.detail?.bulk ? ' · bulk action' : ''}
                      </p>
                    ) : entry.detail?.from && entry.detail?.to ? (
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {String(entry.detail.from)} → {String(entry.detail.to)}
                      </p>
                    ) : null}
                  </div>

                  <time
                    className="shrink-0 text-xs text-muted-foreground"
                    dateTime={entry.created_at}
                    title={new Date(entry.created_at).toLocaleString()}
                  >
                    {when(entry.created_at)}
                  </time>
                </div>
              )
            })}
          </div>
        </Card>
      )}
    </motion.div>
  )
}
