'use client'

import { useCallback, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Settings as SettingsIcon, 
  Building2, 
  Mail, 
  Tag, 
  AlignLeft,
  Save,
  KeyRound,
  AlertTriangle
} from 'lucide-react'
import { toast } from 'sonner'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Spinner } from '@/components/ui/spinner'
import { api, OrgProfile } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'

export default function SettingsPage() {
  const router = useRouter()
  const { can, logout } = useAuth()

  const [profile, setProfile] = useState<OrgProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  // Change password
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [changingPassword, setChangingPassword] = useState(false)

  // Delete account
  const [deletePassword, setDeletePassword] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState('')
  const [deleting, setDeleting] = useState(false)

  const loadProfile = useCallback(async () => {
    try {
      setProfile(await api.getMe())
    } catch (err: any) {
      toast.error('Failed to load organisation profile')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadProfile()
  }, [loadProfile])

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    if (newPassword !== confirmPassword) {
      toast.error('The new passwords do not match')
      return
    }

    setChangingPassword(true)
    try {
      await api.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      })
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      // Existing tokens stay valid server-side, so say so rather than implying
      // other sessions were signed out.
      toast.success('Password changed', {
        description: 'Sessions already signed in stay signed in.',
      })
    } catch (err: any) {
      toast.error('Could not change the password', { description: err.message })
    } finally {
      setChangingPassword(false)
    }
  }

  const handleDeleteAccount = async (e: React.FormEvent) => {
    e.preventDefault()
    setDeleting(true)
    try {
      await api.deleteAccount({ current_password: deletePassword, confirm: true })
      toast.success('Organisation deleted')
      logout()
      router.push('/')
    } catch (err: any) {
      toast.error('Could not delete the organisation', { description: err.message })
    } finally {
      setDeleting(false)
    }
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!profile) return

    setSaving(true)
    try {
      const updated = await api.updateMe({
        name: profile.name,
        description: profile.description,
        domain_tags: profile.domain_tags,
      })
      setProfile(updated)
      toast.success('Settings saved successfully!')
    } catch (err: any) {
      toast.error('Failed to save settings', { description: err.message })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 space-y-4">
        <Spinner className="h-10 w-10 text-primary" />
        <p className="text-muted-foreground animate-pulse">Loading settings...</p>
      </div>
    )
  }

  if (!profile) return null

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8 max-w-4xl"
    >
      <div>
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <SettingsIcon className="h-8 w-8 text-primary" />
          Organisation Settings
        </h1>
        <p className="text-muted-foreground mt-2">
          Manage your account profile and organisation information.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Profile Card */}
        <Card className="border-border/50 bg-card/50">
          <CardHeader>
            <CardTitle>Generals</CardTitle>
            <CardDescription>Update your public facing organisation identity</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center gap-6 pb-6 border-b border-border/50">
              <Avatar className="h-24 w-24">
                <AvatarImage src={profile.logo_url} alt={profile.name} />
                <AvatarFallback className="text-2xl font-bold bg-primary/10 text-primary">
                  {profile.name.charAt(0)}
                </AvatarFallback>
              </Avatar>
              <div className="space-y-2">
                <h3 className="font-medium text-sm">Organisation Logo</h3>
                <p className="text-sm text-muted-foreground">Upload a logo to display on your forms.</p>
                <div className="flex gap-2">
                  <Button type="button" variant="outline" size="sm">Upload new</Button>
                  <Button type="button" variant="ghost" size="sm" className="text-destructive">Remove</Button>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
               <div className="space-y-2">
                 <Label htmlFor="name" className="flex items-center gap-2">
                   <Building2 className="h-4 w-4" /> Organisation Name
                 </Label>
                 <Input 
                   id="name" 
                   value={profile.name} 
                   onChange={e => setProfile({ ...profile, name: e.target.value })} 
                 />
               </div>
               <div className="space-y-2">
                 <Label htmlFor="email" className="flex items-center gap-2">
                   <Mail className="h-4 w-4" /> Account Email
                 </Label>
                 <Input id="email" defaultValue={profile.email} disabled className="bg-muted/50 cursor-not-allowed" />
                 <p className="text-xs text-muted-foreground">Contact support to change your account email.</p>
               </div>
            </div>

            <div className="space-y-2">
               <Label htmlFor="description" className="flex items-center gap-2">
                 <AlignLeft className="h-4 w-4" /> Description
               </Label>
               <Textarea 
                 id="description" 
                 value={profile.description} 
                 onChange={e => setProfile({ ...profile, description: e.target.value })} 
                 rows={4} 
                 placeholder="Tell candidates about your organisation..."
               />
            </div>
          </CardContent>
        </Card>

        {/* Preferences */}
        <Card className="border-border/50 bg-card/50">
          <CardHeader>
            <CardTitle>Tags & Domains</CardTitle>
            <CardDescription>Categorize your organisation to help candidates find you</CardDescription>
          </CardHeader>
          <CardContent>
             <div className="space-y-2">
               <Label htmlFor="tags" className="flex items-center gap-2">
                 <Tag className="h-4 w-4" /> Domain Tags (comma separated)
               </Label>
               <Input 
                 id="tags" 
                 value={profile.domain_tags.join(', ')} 
                 onChange={e => setProfile({ ...profile, domain_tags: e.target.value.split(',').map(t => t.trim()).filter(Boolean) })} 
                 placeholder="Engineering, Marketing, Data Science..." 
               />
             </div>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-4">
          <Button type="button" variant="outline" onClick={() => loadProfile()}>
            Reset
          </Button>
          <Button type="submit" className="gradient-primary border-0" disabled={saving}>
            {saving ? <Spinner className="h-4 w-4 mr-2" /> : <Save className="h-4 w-4 mr-2" />}
            Save Changes
          </Button>
        </div>
      </form>

      {/* Password — applies to the signed-in user, not the organisation, so it
          is a separate form rather than part of Save Changes. */}
      <Card className="border-border/50 bg-card/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <KeyRound className="h-5 w-5" /> Password
          </CardTitle>
          <CardDescription>
            Change the password for {profile.user_email ?? 'your account'}.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleChangePassword} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="current-password">Current password</Label>
              <Input
                id="current-password"
                type="password"
                autoComplete="current-password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="new-password">New password</Label>
                <Input
                  id="new-password"
                  type="password"
                  autoComplete="new-password"
                  minLength={8}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                />
                <p className="text-xs text-muted-foreground">At least 8 characters.</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirm-password">Confirm new password</Label>
                <Input
                  id="confirm-password"
                  type="password"
                  autoComplete="new-password"
                  minLength={8}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="flex justify-end">
              <Button
                type="submit"
                variant="outline"
                disabled={changingPassword || !currentPassword || !newPassword}
              >
                {changingPassword && <Spinner className="h-4 w-4 mr-2" />}
                Change password
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Owner-only, and irreversible. */}
      {can('owner') && (
        <Card className="border-destructive/40">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" /> Delete this organisation
            </CardTitle>
            <CardDescription>
              Permanently erases every drive, candidate, submission, interview
              transcript and audit entry. This cannot be undone.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleDeleteAccount} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="delete-password">Your password</Label>
                <Input
                  id="delete-password"
                  type="password"
                  autoComplete="current-password"
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                  required
                />
                <p className="text-xs text-muted-foreground">
                  Required even though you are signed in, so a borrowed session
                  cannot trigger this.
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="delete-confirm">
                  Type <span className="font-mono font-semibold">{profile.name}</span> to confirm
                </Label>
                <Input
                  id="delete-confirm"
                  value={deleteConfirm}
                  onChange={(e) => setDeleteConfirm(e.target.value)}
                  placeholder={profile.name}
                  required
                />
              </div>

              <div className="flex justify-end">
                <Button
                  type="submit"
                  variant="destructive"
                  disabled={
                    deleting || !deletePassword || deleteConfirm !== profile.name
                  }
                >
                  {deleting && <Spinner className="h-4 w-4 mr-2" />}
                  Delete organisation permanently
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}
    </motion.div>
  )
}
