'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from '@/components/ui/sheet'
import {
  LayoutDashboard,
  Plus,
  FolderOpen,
  BarChart3,
  Users,
  ScrollText,
  Settings,
  Bell,
  Menu,
  LogOut,
  User,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/lib/auth-context'
import { Spinner } from '@/components/ui/spinner'

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', href: '/dashboard' },
  { icon: Plus, label: 'Create Drive', href: '/dashboard/drives/new' },
  { icon: FolderOpen, label: 'All Drives', href: '/dashboard/drives' },
  { icon: Users, label: 'Candidates', href: '/dashboard/applicants' },
  { icon: BarChart3, label: 'Analytics', href: '/dashboard/analytics' },
  { icon: ScrollText, label: 'Activity', href: '/dashboard/audit' },
  { icon: Users, label: 'Team', href: '/dashboard/team' },
  { icon: Settings, label: 'Settings', href: '/dashboard/settings' },
]

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const { user, isLoading, logout } = useAuth()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [isMobileOpen, setIsMobileOpen] = useState(false)

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Spinner className="h-8 w-8 text-primary" />
      </div>
    )
  }

  if (!user) return null

  const NavContent = ({ mobile = false }: { mobile?: boolean }) => (
    <div className="flex flex-col h-full bg-sidebar">
      <div className={cn(
        "flex items-center px-4 h-16 border-b border-border",
        isCollapsed && !mobile && "justify-center px-3"
      )}>
        {(!isCollapsed || mobile) ? (
          <span className="text-lg font-bold tracking-tight text-foreground">
            RECRUIT<span className="text-primary">.AI</span>
          </span>
        ) : (
          <span className="text-lg font-bold text-primary">R.</span>
        )}
      </div>

      {/* Nav Items */}
      <nav className="flex-1 py-6 space-y-1 px-3">
        {navItems.map((item) => {
          const isActive = pathname === item.href || 
            (item.href !== '/dashboard' && pathname.startsWith(item.href))
          
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => mobile && setIsMobileOpen(false)}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors relative",
                isActive
                  ? "bg-secondary text-foreground font-semibold"
                  : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground font-medium",
                isCollapsed && !mobile && "justify-center px-2"
              )}
            >
              <item.icon className="h-5 w-5 flex-shrink-0" />
              {(!isCollapsed || mobile) && <span>{item.label}</span>}
              {isActive && (!isCollapsed || mobile) && (
                <div className="absolute left-0 top-1.5 bottom-1.5 w-1 bg-primary rounded-r-md" />
              )}
            </Link>
          )
        })}
      </nav>


      {/* Collapse Toggle - Desktop Only */}
      {!mobile && (
        <div className="p-3 border-t border-border">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className={cn(
              "w-full text-muted-foreground hover:bg-secondary/50",
              isCollapsed ? "justify-center" : "justify-start"
            )}
          >
            {isCollapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <>
                <ChevronLeft className="h-4 w-4 mr-2" />
                Collapse
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  )

  return (
    <div className="min-h-screen bg-background">
      {/* Desktop Sidebar */}
      <aside
        className={cn(
          "fixed left-0 top-0 z-40 h-screen border-r border-border bg-sidebar transition-all duration-300 hidden lg:block",
          isCollapsed ? "w-16" : "w-64"
        )}
      >
        <NavContent />
      </aside>

      {/* Mobile Header */}
      <header className="lg:hidden sticky top-0 z-50 flex items-center justify-between h-16 px-4 border-b border-border bg-background">
        <div className="flex items-center gap-3">
          <Sheet open={isMobileOpen} onOpenChange={setIsMobileOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-64 p-0">
              <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
              <NavContent mobile />
            </SheetContent>
          </Sheet>
          <span className="text-base font-bold tracking-tight text-foreground">
            RECRUIT<span className="text-primary">.AI</span>
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="relative text-muted-foreground">
            <Bell className="h-5 w-5" />
            <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-primary border-2 border-background" />
          </Button>
          <UserMenu user={user} onLogout={logout} />
        </div>
      </header>

      {/* Main Content */}
      <main
        className={cn(
          "transition-all duration-300",
          isCollapsed ? "lg:pl-16" : "lg:pl-64"
        )}
      >
        {/* Desktop Top Bar */}
        <header className="hidden lg:flex items-center justify-between h-16 px-8 border-b border-border bg-background sticky top-0 z-30">
          <div>
            <h1 className="text-lg font-semibold text-foreground">
              {(() => {
                const hour = new Date().getHours()
                const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'
                return `${greeting}${user?.name ? `, ${user.name}` : ''}`
              })()}
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" className="relative text-muted-foreground hover:bg-secondary/50">
              <Bell className="h-5 w-5" />
              <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-primary border-2 border-background" />
            </Button>
            <UserMenu user={user} onLogout={logout} />
          </div>
        </header>

        {/* Page Content */}
        <div className="p-6 lg:p-10 max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  )
}

function UserMenu({ user, onLogout }: { user: { name: string; email: string } | null; onLogout: () => void }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-9 w-9 rounded-full bg-secondary/50 hover:bg-secondary">
          <Avatar className="h-9 w-9">
            <AvatarImage src="" alt="User" />
            <AvatarFallback className="bg-primary/10 text-primary font-medium">
              {user?.name?.slice(0, 2).toUpperCase() || 'OR'}
            </AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="end" forceMount>
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">{user?.name || 'My Organization'}</p>
            <p className="text-xs text-muted-foreground mt-1">{user?.email || ''}</p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem className="cursor-pointer">
          <User className="mr-2 h-4 w-4" />
          Profile
        </DropdownMenuItem>
        <DropdownMenuItem className="cursor-pointer">
          <Settings className="mr-2 h-4 w-4" />
          Settings
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem className="text-destructive cursor-pointer" onClick={onLogout}>
          <LogOut className="mr-2 h-4 w-4" />
          Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
