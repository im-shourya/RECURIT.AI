'use client'

import { useRef } from 'react'
import { motion, useScroll, useTransform, useReducedMotion } from 'framer-motion'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Squircle } from '@/components/ui/squircle'
import { FileText, Github, Share2, CheckCircle, Video, User } from 'lucide-react'

const appleEase = [0.25, 0.1, 0.25, 1] as const

// ── Presentation Components (Faithful to actual UI) ──────────────────

function MockDriveCreation() {
  return (
    <Card className="w-full max-w-md mx-auto border-border/60 bg-background/95 backdrop-blur drop-shadow-xl">
      <CardContent className="p-6">
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold mb-1">Create Drive</h3>
            <p className="text-sm text-muted-foreground">Basic Info</p>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label className="text-xs text-muted-foreground">Drive Name</Label>
              <Input value="Senior Frontend Engineer" readOnly className="h-9 bg-card pointer-events-none" />
            </div>

            <div className="space-y-2">
              <Label className="text-xs text-muted-foreground">Domain</Label>
              <Input value="Web Development" readOnly className="h-9 bg-card pointer-events-none" />
            </div>

            <div className="pt-2">
              <Button className="w-full h-9 bg-primary text-primary-foreground pointer-events-none">
                Continue to Task Setup
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}


function MockDriveShare() {
  return (
    <Card className="w-full max-w-md mx-auto border-border/60 bg-background/95 backdrop-blur text-center drop-shadow-xl">
      <CardContent className="p-8">
        <div className="mx-auto w-12 h-12 rounded-full bg-emerald/10 text-emerald flex items-center justify-center mb-4">
          <CheckCircle className="w-6 h-6" />
        </div>
        <h3 className="text-lg font-semibold mb-2">Drive Created Successfully</h3>
        <p className="text-sm text-muted-foreground mb-6">Share this link with candidates to begin.</p>

        <Squircle cornerRadius={8} borderClassName="stroke-border" className="flex items-center gap-2 p-2 bg-card">
          <code className="text-xs truncate flex-1 px-2">recruit.ai/apply/d_7x9Qk2</code>
          <Button size="sm" variant="secondary" className="h-7 px-3 pointer-events-none">
            <Share2 className="w-3 h-3 mr-1.5" />
            Copy
          </Button>
        </Squircle>
      </CardContent>
    </Card>
  )
}

function MockCandidateSubmit() {
  return (
    <Card className="w-full max-w-md mx-auto border-border/60 bg-background/95 backdrop-blur drop-shadow-xl">
      <CardContent className="p-6">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-10 h-10 rounded-full bg-secondary/30 flex items-center justify-center">
            <User className="w-5 h-5 text-muted-foreground" />
          </div>
          <div>
            <h3 className="text-sm font-semibold">Alex Developer</h3>
            <p className="text-xs text-muted-foreground">alex@example.com</p>
          </div>
        </div>

        <div className="space-y-3 mb-6">
          <Squircle cornerRadius={8} borderClassName="stroke-border" className="flex items-center gap-3 p-3 bg-card">
            <Github className="w-5 h-5 text-muted-foreground" />
            <div className="flex-1">
              <p className="text-sm font-medium">github.com/alexdev</p>
              <p className="text-xs text-emerald">Connected</p>
            </div>
            <CheckCircle className="w-4 h-4 text-emerald" />
          </Squircle>
          <Squircle cornerRadius={8} borderClassName="stroke-border" className="flex items-center gap-3 p-3 bg-card">
            <FileText className="w-5 h-5 text-muted-foreground" />
            <div className="flex-1">
              <p className="text-sm font-medium">resume_2026.pdf</p>
              <p className="text-xs text-emerald">Uploaded</p>
            </div>
            <CheckCircle className="w-4 h-4 text-emerald" />
          </Squircle>
        </div>

        <Button className="w-full h-9 pointer-events-none">
          Start Technical Interview
        </Button>
      </CardContent>
    </Card>
  )
}

function MockAIInterview() {
  return (
    <Card className="w-full max-w-lg mx-auto border-border/60 bg-background/95 backdrop-blur overflow-hidden drop-shadow-xl">
      <div className="flex items-center justify-between p-4 border-b border-border/50 bg-card/50">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-rose animate-pulse" />
          <span className="text-xs font-mono font-medium">REC</span>
        </div>
        <Badge variant="outline" className="text-xs font-mono border-primary/20 text-primary bg-primary/5">
          STAGE 2: TECHNICAL DEEP-DIVE
        </Badge>
      </div>
      <CardContent className="p-6">
        <div className="mb-6">
          <p className="text-sm font-medium text-foreground mb-2">Recruiter AI</p>
          <Squircle cornerRadius={12} borderClassName="stroke-border/40" className="p-4 bg-secondary/10 text-sm leading-relaxed">
            I noticed in your recent Next.js repository, you chose to implement a custom caching layer using Redis instead of relying on the built-in Data Cache. Could you walk me through the architectural reasoning behind that decision?
          </Squircle>
        </div>
        <div className="flex justify-end">
          <div className="w-3/4">
            <p className="text-sm font-medium text-foreground mb-2 text-right">Alex Developer</p>
            <Squircle cornerRadius={12} borderClassName="stroke-primary/20" className="p-4 bg-primary/10 text-primary text-sm leading-relaxed">
              <div className="flex gap-1 items-center justify-end mb-2">
                <span className="w-1.5 h-1.5 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="opacity-70">Speaking...</span>
            </Squircle>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ── Scene 02 Component ───────────────────────────────────────────────

export function FeaturesSection() {
  const containerRef = useRef<HTMLDivElement>(null)
  const prefersReducedMotion = useReducedMotion()

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  })

  // We have 4 steps, mapping scroll progress to opacity for each step text
  const text1Op = useTransform(scrollYProgress, [0, 0.1, 0.2, 0.3], [1, 1, 0, 0])
  const text2Op = useTransform(scrollYProgress, [0.2, 0.3, 0.45, 0.55], [0, 1, 1, 0])
  const text3Op = useTransform(scrollYProgress, [0.45, 0.55, 0.7, 0.8], [0, 1, 1, 0])
  const text4Op = useTransform(scrollYProgress, [0.7, 0.8, 1, 1], [0, 1, 1, 1])

  // Map scroll progress to UI component visibility (scale and opacity)
  const ui1Op = useTransform(scrollYProgress, [0, 0.1, 0.2, 0.3], [1, 1, 0, 0])
  const ui1Sc = useTransform(scrollYProgress, [0, 0.2, 0.3], [1, 1, 0.95])
  const ui1Y = useTransform(scrollYProgress, [0, 0.2, 0.3], [0, 0, -20])

  const ui2Op = useTransform(scrollYProgress, [0.2, 0.3, 0.45, 0.55], [0, 1, 1, 0])
  const ui2Sc = useTransform(scrollYProgress, [0.2, 0.3, 0.45, 0.55], [0.95, 1, 1, 0.95])
  const ui2Y = useTransform(scrollYProgress, [0.2, 0.3, 0.45, 0.55], [20, 0, 0, -20])

  const ui3Op = useTransform(scrollYProgress, [0.45, 0.55, 0.7, 0.8], [0, 1, 1, 0])
  const ui3Sc = useTransform(scrollYProgress, [0.45, 0.55, 0.7, 0.8], [0.95, 1, 1, 0.95])
  const ui3Y = useTransform(scrollYProgress, [0.45, 0.55, 0.7, 0.8], [20, 0, 0, -20])

  const ui4Op = useTransform(scrollYProgress, [0.7, 0.8, 1, 1], [0, 1, 1, 1])
  const ui4Sc = useTransform(scrollYProgress, [0.7, 0.8, 1, 1], [0.95, 1, 1, 1])
  const ui4Y = useTransform(scrollYProgress, [0.7, 0.8, 1, 1], [20, 0, 0, 0])

  return (
    <section ref={containerRef} className="relative h-[400vh] bg-background">
      <div className="sticky top-0 h-screen w-full flex items-center justify-center overflow-hidden px-4 sm:px-6 lg:px-8">
        <div className="w-full max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-24 items-center">

          {/* Narrative Column */}
          <div className="relative h-[200px] lg:h-[300px] flex flex-col justify-center text-center lg:text-left">
            <motion.h2
              style={prefersReducedMotion ? { opacity: 1 } : { opacity: text1Op }}
              className="absolute inset-0 flex flex-col justify-center section-title"
            >
              Create a recruitment drive.
            </motion.h2>
            <motion.h2
              style={prefersReducedMotion ? { opacity: 0 } : { opacity: text2Op }}
              className="absolute inset-0 flex flex-col justify-center section-title"
            >
              Share the drive link.
            </motion.h2>
            <motion.h2
              style={prefersReducedMotion ? { opacity: 0 } : { opacity: text3Op }}
              className="absolute inset-0 flex flex-col justify-center section-title"
            >
              Candidates submit their profiles.
            </motion.h2>
            <motion.h2
              style={prefersReducedMotion ? { opacity: 0 } : { opacity: text4Op }}
              className="absolute inset-0 flex flex-col justify-center section-title text-primary"
            >
              AI conducts the interview.
            </motion.h2>
          </div>

          {/* Visual UI Column */}
          <div className="relative h-[400px] w-full max-w-[500px] mx-auto flex items-center justify-center">
            {/* UI 1 */}
            <motion.div
              style={prefersReducedMotion ? { opacity: 1, zIndex: 10 } : { opacity: ui1Op, scale: ui1Sc, y: ui1Y, zIndex: 40 }}
              className="absolute w-full"
            >
              <MockDriveCreation />
            </motion.div>

            {/* UI 2 */}
            <motion.div
              style={prefersReducedMotion ? { opacity: 0, zIndex: 0 } : { opacity: ui2Op, scale: ui2Sc, y: ui2Y, zIndex: 30 }}
              className="absolute w-full"
            >
              <MockDriveShare />
            </motion.div>

            {/* UI 3 */}
            <motion.div
              style={prefersReducedMotion ? { opacity: 0, zIndex: 0 } : { opacity: ui3Op, scale: ui3Sc, y: ui3Y, zIndex: 20 }}
              className="absolute w-full"
            >
              <MockCandidateSubmit />
            </motion.div>

            {/* UI 4 */}
            <motion.div
              style={prefersReducedMotion ? { opacity: 0, zIndex: 0 } : { opacity: ui4Op, scale: ui4Sc, y: ui4Y, zIndex: 10 }}
              className="absolute w-full"
            >
              <MockAIInterview />
            </motion.div>
          </div>

        </div>
      </div>
    </section>
  )
}
