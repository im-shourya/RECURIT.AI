/**
 * The frames of the pipeline scrub, as data.
 *
 * Apple's product pages scrub through a pre-rendered image sequence. This
 * page has no renders to ship, so each frame is described here instead and
 * drawn on a canvas: the same idea of "scroll position picks frame N", with
 * nothing to download.
 *
 * Everything is deterministic. The cohort comes from a fixed seed, and a
 * frame depends only on its index, so frame 60 looks the same on every visit
 * and scrubbing backwards retraces exactly what scrubbing forwards drew.
 *
 * The cohort is illustrative. It shows the shape of a drive, not real data.
 */

export const FRAME_COUNT = 120

export const STAGES = ['Applied', 'Task', 'Interview', 'Decision'] as const

/** Where each phase of the story begins, as a fraction of the whole scrub. */
export const PHASE_STARTS = [0, 0.25, 0.5, 0.75] as const

/** How long one card takes to travel between columns, as a fraction of the scrub. */
const TRAVEL = 0.08

type Candidate = {
  /** When the card appears in Applied. */
  applyAt: number
  /** When it moves into each later column; Infinity if it never does. */
  moveAt: [number, number, number]
  selected: boolean
}

/** A small seeded generator, so the cohort is identical on every load. */
function seeded(seed: number) {
  let state = seed
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296
    return state / 4294967296
  }
}

function buildCohort(): Candidate[] {
  const random = seeded(20261015)
  const size = 18
  // How far the cohort gets: most do the task, fewer are invited to
  // interview, and a few are selected.
  const reachTask = 14
  const reachInterview = 8
  const selected = 3

  const order = Array.from({ length: size }, (_, i) => i).sort(() => random() - 0.5)
  return Array.from({ length: size }, (_, i) => {
    const rank = order.indexOf(i)
    const within = (start: number) => start + 0.02 + random() * 0.12
    return {
      applyAt: 0.01 + (i / size) * 0.18,
      moveAt: [
        rank < reachTask ? within(PHASE_STARTS[1]) : Infinity,
        rank < reachInterview ? within(PHASE_STARTS[2]) : Infinity,
        rank < reachInterview ? within(PHASE_STARTS[3]) : Infinity,
      ],
      selected: rank < selected,
    }
  })
}

export const COHORT = buildCohort()

export type CardState = {
  /** Column position: 0 = Applied … 3 = Decision; fractional while moving. */
  column: number
  /** Row within that column, in card heights; fractional while others leave. */
  row: number
  /** 0 → 1 as the card fades in. */
  presence: number
  /** True once the card has stopped short of the decision. */
  stalled: boolean
  /** Set at the decision: selected cards take the accent. */
  outcome: 'selected' | 'declined' | null
}

const ease = (x: number) => (x <= 0 ? 0 : x >= 1 ? 1 : 1 - Math.pow(1 - x, 3))

/** Progress through a move that starts at `at`, eased: 0 before, 1 after. */
const moved = (t: number, at: number) => ease((t - at) / TRAVEL)

/** Which column the card belongs to at time t, before any travel. */
function settledColumn(c: Candidate, t: number) {
  let column = 0
  for (const at of c.moveAt) if (t >= at) column += 1
  return column
}

/** Card states for one frame index (0 … FRAME_COUNT - 1). */
export function frameAt(index: number): { t: number; cards: CardState[] } {
  const t = index / (FRAME_COUNT - 1)

  const cards = COHORT.map((c) => {
    // Continuous column: whole columns already reached, plus the eased part
    // of the move in progress.
    const column = c.moveAt.reduce((sum, at) => sum + moved(t, at), 0)
    const reached = settledColumn(c, t)
    const nextMove = c.moveAt[reached] ?? Infinity
    // A card stalls once the cohort it would have moved with has gone on.
    const stalled = reached < 3 && t > PHASE_STARTS[Math.min(reached + 1, 3)] + 0.18
    const decided = reached === 3 && t >= c.moveAt[2] + TRAVEL
    return {
      column,
      row: 0,
      presence: ease((t - c.applyAt) / 0.05),
      stalled: stalled && nextMove === Infinity,
      outcome: decided ? (c.selected ? 'selected' : 'declined') : null,
    } satisfies CardState
  })

  // Rows: each card sits below the cards that reached its column before it.
  // Weighting by how far each of those has *left* lets the column close up
  // smoothly behind a departing card, instead of jumping. A card in transit
  // blends between its row in the column it is leaving and the one ahead.
  const arrivedAt = (c: Candidate, column: number) =>
    column === 0 ? c.applyAt : c.moveAt[column - 1]

  const rowIn = (i: number, column: number) => {
    const mine = arrivedAt(COHORT[i], column)
    let row = 0
    COHORT.forEach((other, j) => {
      const theirs = arrivedAt(other, column)
      if (j === i || !(theirs < mine) || t < theirs) return
      const leaving = column < 3 ? moved(t, other.moveAt[column]) : 0
      const arriving = column === 0 ? cards[j].presence : moved(t, theirs)
      row += arriving * (1 - leaving)
    })
    return row
  }

  cards.forEach((card, i) => {
    const from = Math.min(Math.floor(card.column), 3)
    const along = card.column - from
    card.row = along > 0 && from < 3
      ? rowIn(i, from) + (rowIn(i, from + 1) - rowIn(i, from)) * along
      : rowIn(i, from)
  })

  return { t, cards }
}

/** The story beat a frame belongs to: 0 … 3. */
export function phaseAt(index: number) {
  const t = index / (FRAME_COUNT - 1)
  let phase = 0
  PHASE_STARTS.forEach((start, i) => {
    if (t >= start) phase = i
  })
  return phase
}
