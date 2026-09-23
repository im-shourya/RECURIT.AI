'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { motion } from 'framer-motion'
import { CheckSquare, Download, Search, Users, XSquare } from 'lucide-react'
import { toast } from 'sonner'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Spinner } from '@/components/ui/spinner'
import { api, ApplicantResponse } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'

const PAGE_SIZE = 25

const STATUSES = [
  'applied',
  'task_sent',
  'submitted',
  'interview_sent',
  'interviewed',
  'selected',
  'rejected',
] as const

const LABEL: Record<string, string> = {
  applied: 'Applied',
  task_sent: 'Task sent',
  submitted: 'Submitted',
  interview_sent: 'Interview sent',
  interviewed: 'Interviewed',
  selected: 'Selected',
  rejected: 'Rejected',
}

const DECIDED = new Set(['selected', 'rejected'])

export default function ApplicantsPage() {
  const driveId = useSearchParams().get('drive_id') ?? undefined
  const { can } = useAuth()

  const [applicants, setApplicants] = useState<ApplicantResponse[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [offset, setOffset] = useState(0)

  const [search, setSearch] = useState('')
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState<string>('all')
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [working, setWorking] = useState(false)

  // Debounced so a query does not fire on every keystroke.
  useEffect(() => {
    const timer = setTimeout(() => {
      setQuery(search)
      setOffset(0)
    }, 300)
    return () => clearTimeout(timer)
  }, [search])

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const page = await api.listApplicants({
        drive_id: driveId,
        status: status === 'all' ? undefined : status,
        q: query || undefined,
        limit: PAGE_SIZE,
        offset,
      })
      setApplicants(page.items)
      setTotal(page.total)
      // Selections refer to the previous page, so clear them on every load
      // rather than acting on rows that are no longer visible.
      setSelected(new Set())
    } catch (err: any) {
      toast.error('Could not load applicants', { description: err.message })
    } finally {
      setLoading(false)
    }
  }, [driveId, status, query, offset])

  useEffect(() => {
    load()
  }, [load])

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  // Only undecided rows can be acted on; the API rejects a second decision.
  const decidable = can('admin')
    ? applicants.filter((a) => !DECIDED.has(a.status))
    : []
  const selectedDecidable = decidable.filter((a) => selected.has(a.id))
  const allDecidableSelected =
    decidable.length > 0 && selectedDecidable.length === decidable.length

  const bulkDecide = async (decision: 'selected' | 'rejected') => {
    const ids = selectedDecidable.map((a) => a.id)
    if (!ids.length) return
    if (
      !confirm(
        `${decision === 'selected' ? 'Select' : 'Reject'} ${ids.length} candidate(s)? ` +
          'Each one is emailed the outcome, and it cannot be undone.',
      )
    ) {
      return
    }

    setWorking(true)
    try {
      const result = await api.bulkDecision(ids, decision)
      toast.success(`${result.updated} candidate(s) updated`, {
        description: result.skipped.length
          ? `${result.skipped.length} skipped — already decided.`
          : undefined,
      })
      await load()
    } catch (err: any) {
      toast.error('Bulk decision failed', { description: err.message })
    } finally {
      setWorking(false)
    }
  }

  const exportCsv = async () => {
    try {
      const blob = await api.exportApplicants({
        drive_id: driveId,
        status: status === 'all' ? undefined : status,
        q: query || undefined,
      })
      // The endpoint needs an Authorization header, so it is fetched as a blob
      // and handed to a temporary link rather than navigated to directly.
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `applicants-${new Date().toISOString().slice(0, 10)}.csv`
      link.click()
      URL.revokeObjectURL(url)
      toast.success('Export downloaded')
    } catch (err: any) {
      toast.error('Export failed', { description: err.message })
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Users className="h-7 w-7 text-primary" />
            Candidates
          </h1>
          <p className="text-muted-foreground mt-1">
            {loading ? 'Loading…' : `Showing ${applicants.length} of ${total}`}
          </p>
        </div>
        <Button variant="outline" onClick={exportCsv} disabled={!total}>
          <Download className="mr-2 h-4 w-4" />
          Export CSV
        </Button>
      </div>

      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search name, email or registration number"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select
          value={status}
          onValueChange={(v) => {
            setStatus(v)
            setOffset(0)
          }}
        >
          <SelectTrigger className="w-[190px]">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            {STATUSES.map((s) => (
              <SelectItem key={s} value={s}>
                {LABEL[s]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {selectedDecidable.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-wrap items-center gap-3 rounded-xl border bg-muted/40 px-4 py-3"
        >
          <span className="text-sm font-medium">
            {selectedDecidable.length} selected
          </span>
          <div className="flex gap-2 ml-auto">
            <Button size="sm" onClick={() => bulkDecide('selected')} disabled={working}>
              <CheckSquare className="mr-2 h-4 w-4" />
              Select all
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => bulkDecide('rejected')}
              disabled={working}
            >
              <XSquare className="mr-2 h-4 w-4" />
              Reject all
            </Button>
          </div>
        </motion.div>
      )}

      {loading ? (
        <div className="flex justify-center py-20">
          <Spinner className="h-8 w-8 text-primary" />
        </div>
      ) : applicants.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <p className="font-medium">No candidates found</p>
            <p className="text-sm text-muted-foreground mt-1">
              {query || status !== 'all'
                ? 'Try a different search or filter.'
                : 'They will appear here once people start applying.'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card className="overflow-hidden">
          <div className="divide-y">
            <div className="flex items-center gap-3 px-4 py-2.5 bg-muted/40 text-xs font-medium text-muted-foreground">
              <Checkbox
                checked={allDecidableSelected}
                onCheckedChange={(checked) =>
                  setSelected(checked ? new Set(decidable.map((a) => a.id)) : new Set())
                }
                disabled={decidable.length === 0}
                aria-label="Select all undecided candidates"
              />
              <span className="flex-1">Candidate</span>
              <span className="w-28 hidden sm:block">Status</span>
              <span className="w-16 text-right hidden sm:block">Score</span>
            </div>

            {applicants.map((a) => (
              <div key={a.id} className="flex items-center gap-3 px-4 py-3 hover:bg-muted/30">
                <Checkbox
                  checked={selected.has(a.id)}
                  onCheckedChange={() => toggle(a.id)}
                  disabled={DECIDED.has(a.status) || !can('admin')}
                  aria-label={`Select ${a.name}`}
                />
                <Link href={`/dashboard/applicants/${a.id}`} className="flex-1 min-w-0">
                  <p className="font-medium truncate">{a.name}</p>
                  <p className="text-sm text-muted-foreground truncate">{a.email}</p>
                </Link>
                <Badge
                  variant={DECIDED.has(a.status) ? 'default' : 'secondary'}
                  className="w-28 justify-center hidden sm:flex"
                >
                  {LABEL[a.status] ?? a.status}
                </Badge>
                <span className="w-16 text-right text-sm tabular-nums hidden sm:block">
                  {a.interview?.ended_at ? a.interview.total_score : '—'}
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {total > PAGE_SIZE && (
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            size="sm"
            disabled={offset === 0 || loading}
            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={offset + PAGE_SIZE >= total || loading}
            onClick={() => setOffset(offset + PAGE_SIZE)}
          >
            Next
          </Button>
        </div>
      )}
    </motion.div>
  )
}
