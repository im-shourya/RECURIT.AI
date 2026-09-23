'use client'

import { useCallback, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Mail, ShieldCheck, Trash2, UserPlus, Users } from 'lucide-react'
import { toast } from 'sonner'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Spinner } from '@/components/ui/spinner'
import { api, TeamMember } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'

const ROLE_DESCRIPTION: Record<string, string> = {
  owner: 'Everything, including managing members',
  admin: 'Create drives and decide on candidates',
  member: 'Review candidates, but cannot decide',
}

export default function TeamPage() {
  // Every member can see who else is here; only the owner can change it.
  const { can } = useAuth()
  const [members, setMembers] = useState<TeamMember[]>([])
  const [loading, setLoading] = useState(true)
  const [inviteOpen, setInviteOpen] = useState(false)
  const [inviting, setInviting] = useState(false)

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<'admin' | 'member'>('member')

  const load = useCallback(async () => {
    try {
      setMembers(await api.listTeam())
    } catch (err: any) {
      toast.error('Could not load the team', { description: err.message })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const invite = async (e: React.FormEvent) => {
    e.preventDefault()
    setInviting(true)
    try {
      await api.inviteMember({ name, email, role })
      toast.success('Invitation sent', {
        description: `${email} can set their own password from the emailed link.`,
      })
      setName('')
      setEmail('')
      setRole('member')
      setInviteOpen(false)
      await load()
    } catch (err: any) {
      toast.error('Could not invite', { description: err.message })
    } finally {
      setInviting(false)
    }
  }

  const changeRole = async (member: TeamMember, next: string) => {
    // Promoting to owner transfers ownership — the current owner is demoted
    // in the same operation, so it is worth confirming.
    if (next === 'owner') {
      if (
        !confirm(
          `Make ${member.email} the owner? You will be demoted to admin, and ` +
            'only they will be able to manage members afterwards.',
        )
      ) {
        return
      }
    }

    try {
      await api.updateMemberRole(member.id, next as 'owner' | 'admin' | 'member')
      toast.success('Role updated')
      await load()
    } catch (err: any) {
      toast.error('Could not change the role', { description: err.message })
    }
  }

  const remove = async (member: TeamMember) => {
    if (!confirm(`Remove ${member.email}? Any pending invite link stops working.`)) return
    try {
      await api.removeMember(member.id)
      toast.success('Member removed')
      await load()
    } catch (err: any) {
      toast.error('Could not remove', { description: err.message })
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6 max-w-4xl"
    >
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Users className="h-7 w-7 text-primary" />
            Team
          </h1>
          <p className="text-muted-foreground mt-1">
            People who can sign in to this organisation.
          </p>
        </div>

        {can('owner') && (
        <Dialog open={inviteOpen} onOpenChange={setInviteOpen}>
          <DialogTrigger asChild>
            <Button>
              <UserPlus className="mr-2 h-4 w-4" />
              Invite member
            </Button>
          </DialogTrigger>
          <DialogContent>
            <form onSubmit={invite}>
              <DialogHeader>
                <DialogTitle>Invite a member</DialogTitle>
                <DialogDescription>
                  They receive a link to set their own password. No password is
                  chosen for them or sent by email.
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="invite-name">Name</Label>
                  <Input
                    id="invite-name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Alex Recruiter"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="invite-email">Email</Label>
                  <Input
                    id="invite-email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="alex@company.com"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="invite-role">Role</Label>
                  <Select value={role} onValueChange={(v) => setRole(v as 'admin' | 'member')}>
                    <SelectTrigger id="invite-role">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="member">Member — review only</SelectItem>
                      <SelectItem value="admin">Admin — run recruitment</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    Ownership is transferred separately, never granted by invitation.
                  </p>
                </div>
              </div>

              <DialogFooter>
                <Button type="submit" disabled={inviting || !email}>
                  <Mail className="mr-2 h-4 w-4" />
                  {inviting ? 'Sending…' : 'Send invitation'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
        )}
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <Spinner className="h-8 w-8 text-primary" />
        </div>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {members.length} member{members.length === 1 ? '' : 's'}
            </CardTitle>
            <CardDescription>
              Roles are ranked: owner can do everything an admin can, and admin
              everything a member can.
            </CardDescription>
          </CardHeader>
          <CardContent className="divide-y p-0">
            {members.map((m) => (
              <div key={m.id} className="flex flex-wrap items-center gap-3 px-6 py-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-medium truncate">{m.name || m.email}</p>
                    {m.role === 'owner' && (
                      <ShieldCheck className="h-4 w-4 text-primary" aria-label="Owner" />
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground truncate">{m.email}</p>
                  {!m.has_accepted_invite && (
                    <Badge variant="secondary" className="mt-1.5 font-normal">
                      Invitation pending
                    </Badge>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <Select
                    value={m.role}
                    onValueChange={(v) => changeRole(m, v)}
                    disabled={!can('owner')}
                  >
                    <SelectTrigger className="w-[130px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {(['owner', 'admin', 'member'] as const).map((r) => (
                        <SelectItem key={r} value={r}>
                          {r[0].toUpperCase() + r.slice(1)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => remove(m)}
                    // The owner cannot be removed — that would leave the
                    // organisation with nobody able to manage it.
                    disabled={m.role === 'owner' || !can('owner')}
                    aria-label={`Remove ${m.email}`}
                    className="text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <div className="grid gap-3 sm:grid-cols-3">
        {(['owner', 'admin', 'member'] as const).map((r) => (
          <div key={r} className="rounded-xl border p-4">
            <p className="font-medium capitalize">{r}</p>
            <p className="text-sm text-muted-foreground mt-1">{ROLE_DESCRIPTION[r]}</p>
          </div>
        ))}
      </div>
    </motion.div>
  )
}
