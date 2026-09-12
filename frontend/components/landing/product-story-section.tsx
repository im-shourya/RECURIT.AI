'use client'

import { useRef, useState } from 'react'
import { motion, useScroll, useMotionValueEvent, useReducedMotion, AnimatePresence } from 'framer-motion'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { CheckCircle, User, Brain, FileSearch, Code, Share2 } from 'lucide-react'

const appleEase = [0.25, 0.1, 0.25, 1] as const

// ── Presentation Components (Apple-style Refined Panels) ─────────────

function PanelWrapper({ children, title }: { children: React.ReactNode, title: string }) {
  return (
    <div className="w-full max-w-md mx-auto bg-surface border border-border rounded-xl shadow-sm overflow-hidden">
      <div className="px-5 py-3 border-b border-border/50 bg-background/50 flex items-center justify-between">
        <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">{title}</span>
        <div className="flex gap-1.5">
          <div className="w-2 h-2 rounded-full bg-border" />
          <div className="w-2 h-2 rounded-full bg-border" />
          <div className="w-2 h-2 rounded-full bg-border" />
        </div>
      </div>
      <div className="p-6 bg-background">
        {children}
      </div>
    </div>
  )
}

function UI_Create() {
  return (
    <PanelWrapper title="Drive Configuration">
      <div className="space-y-5">
        <div className="space-y-1.5">
          <Label className="text-xs font-medium text-muted-foreground">Role Title</Label>
          <Input value="Senior Frontend Engineer" readOnly className="h-9 bg-surface border-border pointer-events-none text-sm" />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs font-medium text-muted-foreground">Evaluation Domain</Label>
          <Input value="Web Development" readOnly className="h-9 bg-surface border-border pointer-events-none text-sm" />
        </div>
        <div className="pt-2">
          <div className="w-full h-9 rounded-md bg-primary text-primary-foreground flex items-center justify-center text-sm font-medium">
            Generate Drive
          </div>
        </div>
      </div>
    </PanelWrapper>
  )
}

function UI_Candidate() {
  return (
    <PanelWrapper title="Applicant Profile">
      <div className="flex items-start gap-4 mb-6">
        <div className="w-12 h-12 rounded-full bg-surface border border-border flex items-center justify-center flex-shrink-0">
          <User className="w-5 h-5 text-muted-foreground" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-foreground">Alex Developer</h3>
          <p className="text-xs text-muted-foreground mb-2">alex@example.com</p>
          <div className="flex gap-2">
            <span className="px-2 py-0.5 rounded border border-border bg-surface text-[10px] font-medium text-muted-foreground">Frontend</span>
            <span className="px-2 py-0.5 rounded border border-border bg-surface text-[10px] font-medium text-muted-foreground">React</span>
          </div>
        </div>
      </div>
      <div className="space-y-2">
        <div className="flex items-center gap-3 p-2.5 rounded-lg border border-border bg-surface">
          <Share2 className="w-4 h-4 text-muted-foreground" />
          <span className="text-xs font-medium flex-1">github.com/alexdev</span>
          <CheckCircle className="w-3.5 h-3.5 text-primary" />
        </div>
      </div>
    </PanelWrapper>
  )
}

function UI_Interview() {
  return (
    <PanelWrapper title="Live AI Interview">
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <Brain className="w-4 h-4 text-primary" />
          <span className="text-xs font-medium text-foreground">Recruiter AI</span>
        </div>
        <div className="p-3 rounded-lg rounded-tl-none bg-surface border border-border text-sm leading-relaxed text-muted-foreground">
          I noticed you implemented a custom Redis caching layer in your recent Next.js project. Could you explain the architectural reasoning behind bypassing the built-in cache?
        </div>
      </div>
      <div className="flex flex-col items-end">
        <span className="text-xs font-medium text-foreground mb-2">Alex Developer</span>
        <div className="p-3 rounded-lg rounded-tr-none bg-primary/10 border border-primary/20 text-sm leading-relaxed text-primary">
          <div className="flex gap-1 items-center justify-end mb-1">
            <span className="w-1.5 h-1.5 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-1.5 h-1.5 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-1.5 h-1.5 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      </div>
    </PanelWrapper>
  )
}

function UI_Evidence() {
  return (
    <PanelWrapper title="Evidence & Integrity">
      <div className="space-y-4">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-surface border border-border flex items-center justify-center flex-shrink-0 mt-0.5">
            <Code className="w-4 h-4 text-primary" />
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">Code Consistency</p>
            <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
              Interview responses align deeply with the structural complexity of the submitted GitHub repositories.
            </p>
          </div>
        </div>
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-surface border border-border flex items-center justify-center flex-shrink-0 mt-0.5">
            <FileSearch className="w-4 h-4 text-primary" />
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">Identity Verification</p>
            <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
              Continuous gaze tracking and visual analysis confirm single-user presence. No anomalies detected.
            </p>
          </div>
        </div>
      </div>
    </PanelWrapper>
  )
}

// ── Scene 03 Component ───────────────────────────────────────────────

const scenes = [
  { id: 0, title: 'Create a recruitment drive.', ui: UI_Create },
  { id: 1, title: 'Candidates submit profiles.', ui: UI_Candidate },
  { id: 2, title: 'AI conducts the interview.', ui: UI_Interview },
  { id: 3, title: 'Evaluate with evidence.', ui: UI_Evidence },
]

export function ProductStorySection() {
  const containerRef = useRef<HTMLDivElement>(null)
  const prefersReducedMotion = useReducedMotion()
  const [activeIndex, setActiveIndex] = useState(0)

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  })

  useMotionValueEvent(scrollYProgress, "change", (latest) => {
    if (prefersReducedMotion) return
    if (latest < 0.25) setActiveIndex(0)
    else if (latest < 0.5) setActiveIndex(1)
    else if (latest < 0.75) setActiveIndex(2)
    else setActiveIndex(3)
  })

  // For reduced motion or mobile without sticky, we'll render a static stack.
  // But for the sticky desktop view, we use AnimatePresence.
  const activeScene = scenes[activeIndex]
  const ActiveUI = activeScene.ui

  return (
    <section ref={containerRef} id="how-it-works" className="relative bg-background sm:h-[250vh]">
      <div className="sm:sticky sm:top-0 sm:h-screen w-full flex items-center justify-center overflow-hidden px-4 sm:px-6 lg:px-8 py-24 sm:py-0">
        
        {/* Desktop Sticky View */}
        <div className="hidden sm:grid w-full max-w-7xl mx-auto grid-cols-2 gap-24 items-center">
          
          {/* Narrative Column */}
          <div className="relative h-[200px] flex flex-col justify-center text-left">
            <AnimatePresence mode="wait" initial={false}>
              <motion.h2
                key={`text-${activeScene.id}`}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -16 }}
                transition={{ duration: 0.4, ease: appleEase }}
                className="section-title text-foreground absolute"
              >
                {activeScene.title}
              </motion.h2>
            </AnimatePresence>
          </div>

          {/* Visual UI Column */}
          <div className="relative h-[400px] w-full flex items-center justify-center">
            <AnimatePresence mode="wait" initial={false}>
              <motion.div
                key={`ui-${activeScene.id}`}
                initial={{ opacity: 0, y: 24, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -20, scale: 0.985 }}
                transition={{ duration: 0.5, ease: appleEase }}
                className="absolute w-full"
              >
                <ActiveUI />
              </motion.div>
            </AnimatePresence>
          </div>
          
        </div>

        {/* Mobile Static View */}
        <div className="sm:hidden flex flex-col gap-24 w-full">
          {scenes.map((scene) => {
            const SceneUI = scene.ui
            return (
              <div key={`mobile-${scene.id}`} className="flex flex-col gap-8 text-center">
                <h2 className="text-3xl font-semibold tracking-tight text-foreground">
                  {scene.title}
                </h2>
                <div className="w-full">
                  <SceneUI />
                </div>
              </div>
            )
          })}
        </div>

      </div>
    </section>
  )
}
