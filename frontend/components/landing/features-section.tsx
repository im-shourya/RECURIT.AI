'use client'

import { useRef } from 'react'
import { motion, useScroll, useTransform, useReducedMotion } from 'framer-motion'
import Image from 'next/image'
import { Squircle } from '@/components/ui/squircle'

import createDriveImg from './assets/creat-drive.png'
import profileImg from './assets/profile.png'
import aiInterviewImg from './assets/ai-interview.jpg'
import evaluateEvidenceImg from './assets/evaluate-evidence.jpg'

const appleEase = [0.25, 0.1, 0.25, 1] as const

// ── Scene 02 Component ───────────────────────────────────────────────

export function FeaturesSection() {
  const containerRef = useRef<HTMLDivElement>(null)
  const prefersReducedMotion = useReducedMotion()

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  })

  // Text opacities
  const text1Op = useTransform(scrollYProgress, [0, 0.15, 0.25, 0.3], [1, 1, 0, 0])
  const text2Op = useTransform(scrollYProgress, [0.2, 0.3, 0.4, 0.5], [0, 1, 1, 0])
  const text3Op = useTransform(scrollYProgress, [0.45, 0.55, 0.65, 0.75], [0, 1, 1, 0])
  const text4Op = useTransform(scrollYProgress, [0.7, 0.8, 1, 1], [0, 1, 1, 1])

  // Image opacities
  const img1Op = useTransform(scrollYProgress, [0, 0.2, 0.3], [1, 1, 0])
  const img2Op = useTransform(scrollYProgress, [0.2, 0.3, 0.45, 0.55], [0, 1, 1, 0])
  const img3Op = useTransform(scrollYProgress, [0.45, 0.55, 0.7, 0.8], [0, 1, 1, 0])
  const img4Op = useTransform(scrollYProgress, [0.7, 0.8, 1, 1], [0, 1, 1, 1])

  return (
    <section ref={containerRef} id="features" className="relative h-[250vh] bg-[#f5f5f7] dark:bg-black">
      <div className="sticky top-0 h-screen w-full flex flex-col items-center justify-center overflow-hidden">
        
        {/* Background Images Layer */}
        <div className="absolute inset-0 z-0">
          <motion.div style={{ opacity: prefersReducedMotion ? 1 : img1Op }} className="absolute inset-0">
            <Image src={createDriveImg} alt="Create Drive" fill className="object-cover" />
          </motion.div>
          <motion.div style={{ opacity: prefersReducedMotion ? 0 : img2Op }} className="absolute inset-0">
            <Image src={profileImg} alt="Submit Profile" fill className="object-cover" />
          </motion.div>
          <motion.div style={{ opacity: prefersReducedMotion ? 0 : img3Op }} className="absolute inset-0">
            <Image src={aiInterviewImg} alt="AI Interview" fill className="object-cover" />
          </motion.div>
          <motion.div style={{ opacity: prefersReducedMotion ? 0 : img4Op }} className="absolute inset-0">
            <Image src={evaluateEvidenceImg} alt="Evaluate Evidence" fill className="object-cover" />
          </motion.div>
          {/* Dark overlay for better text contrast */}
          <div className="absolute inset-0 bg-black/40" />
        </div>

        {/* Narrative Text Layer */}
        <div className="relative z-10 w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col items-center justify-center h-full text-center">
          
          <motion.div
            style={prefersReducedMotion ? { opacity: 1 } : { opacity: text1Op }}
            className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
          >
            <h2 className="text-4xl lg:text-6xl font-bold text-white tracking-tight drop-shadow-md">
              Create a recruitment drive.
            </h2>
          </motion.div>

          <motion.div
            style={prefersReducedMotion ? { opacity: 0 } : { opacity: text2Op }}
            className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
          >
            <h2 className="text-4xl lg:text-6xl font-bold text-white tracking-tight drop-shadow-md">
              Candidates submit profiles.
            </h2>
          </motion.div>

          <motion.div
            style={prefersReducedMotion ? { opacity: 0 } : { opacity: text3Op }}
            className="absolute inset-0 flex flex-col items-center justify-center w-full pointer-events-none"
          >
            <h2 className="text-4xl lg:text-6xl font-bold text-white tracking-tight mb-8 drop-shadow-md">
              AI conducts the interview.
            </h2>
            <Squircle cornerRadius={16} borderClassName="stroke-white/10" className="max-w-3xl text-left bg-black/50 p-8 backdrop-blur-md shadow-2xl">
              <div className="flex items-center gap-3 mb-4">
                <span className="flex h-3 w-3 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                </span>
                <span className="text-white font-mono text-sm tracking-wider font-semibold">LIVE AI INTERVIEW</span>
              </div>
              <p className="text-white/70 font-medium mb-2 text-sm uppercase tracking-widest">Recruiter AI</p>
              <p className="text-xl lg:text-2xl text-white leading-relaxed">
                "I noticed you implemented a custom Redis caching layer in your recent Next.js project. Could you explain the architectural reasoning behind bypassing the built-in cache?"
              </p>
            </Squircle>
          </motion.div>

          <motion.div
            style={prefersReducedMotion ? { opacity: 0 } : { opacity: text4Op }}
            className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
          >
            <h2 className="text-4xl lg:text-6xl font-bold text-white tracking-tight drop-shadow-md">
              Evaluate with evidence.
            </h2>
          </motion.div>

        </div>
      </div>
    </section>
  )
}
