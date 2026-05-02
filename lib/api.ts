const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface Fixture {
  id: number
  home_team: string
  away_team: string
  league: string
  kickoff_utc: string
  status: string
  home_score?: number
  away_score?: number
}

export interface Prediction {
  fixture_id: number
  home_win_prob: number
  draw_prob: number
  away_win_prob: number
  expected_home_goals: number
  expected_away_goals: number
  recommended_market: string
  recommended_pick: string
  confidence_score: number
  primary_reason: string
  why_not_home: string
  why_not_draw: string
  why_not_away: string
  key_risks: string[]
  data_sources_used: string[]
  data_completeness: number
}

export interface MatchStats {
  stats: Record<string, number>
  incidents: Array<{type: string, time: number, player: string}>
  lineups: Record<string, any>
  source: string
}

export async function getFixtures(date?: string): Promise<{fixtures: Fixture[], count: number}> {
  const url = date 
    ? `${API_BASE}/api/v1/fixtures/${date}`
    : `${API_BASE}/api/v1/fixtures/today`
  const res = await fetch(url)
  if (!res.ok) throw new Error('Failed to fetch fixtures')
  return res.json()
}

export async function getLiveMatches(): Promise<{live_matches: any[], count: number}> {
  const res = await fetch(`${API_BASE}/api/v1/live`)
  if (!res.ok) throw new Error('Failed to fetch live matches')
  return res.json()
}

export async function getMatchStats(matchId: string): Promise<MatchStats> {
  const res = await fetch(`${API_BASE}/api/v1/match/${matchId}/stats`)
  if (!res.ok) throw new Error('Failed to fetch match stats')
  return res.json()
}

export async function getHealth(): Promise<Record<string, boolean>> {
  const res = await fetch(`${API_BASE}/api/v1/health`)
  return res.json()
}
