'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Settings as SettingsIcon, 
  Building2, 
  Mail, 
  Tag, 
  AlignLeft,
  Save
} from 'lucide-react'
import { toast } from 'sonner'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Spinner } from '@/components/ui/spinner'
import { api, OrgProfile } from '@/lib/api'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'

export default function SettingsPage() {
  const [profile, setProfile] = useState<OrgProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    async function loadProfile() {
      try {
        const data = await api.getMe()
        setProfile(data)
      } catch (err: any) {
        toast.error('Failed to load organisation profile')
      } finally {
        setLoading(false)
      }
    }
    loadProfile()
  }, [])

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    // Simulate API call for saving
    setTimeout(() => {
      setSaving(false)
      toast.success('Settings saved successfully!')
    }, 1000)
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
                 <Input id="name" defaultValue={profile.name} />
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
                 defaultValue={profile.description} 
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
               <Input id="tags" defaultValue={profile.domain_tags.join(', ')} placeholder="Engineering, Marketing, Data Science..." />
             </div>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-4">
          <Button type="button" variant="outline">Cancel</Button>
          <Button type="submit" className="gradient-primary border-0" disabled={saving}>
            {saving ? <Spinner className="h-4 w-4 mr-2" /> : <Save className="h-4 w-4 mr-2" />}
            Save Changes
          </Button>
        </div>
      </form>
    </motion.div>
  )
}
