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

const MOCK_FIXTURES: Fixture[] = [
  { id: 1, home_team: 'Arsenal', away_team: 'Manchester United', league: 'Premier League', kickoff_utc: new Date().toISOString(), status: 'NS' },
  { id: 2, home_team: 'Liverpool', away_team: 'Chelsea', league: 'Premier League', kickoff_utc: new Date(Date.now() + 86400000).toISOString(), status: 'NS' },
  { id: 3, home_team: 'Barcelona', away_team: 'Real Madrid', league: 'La Liga', kickoff_utc: new Date(Date.now() + 172800000).toISOString(), status: 'NS' },
]

export async function getFixtures(date?: string): Promise<{fixtures: Fixture[], count: number}> {
  try {
    const url = date 
      ? `${API_BASE}/api/v1/fixtures/${date}`
      : `${API_BASE}/api/v1/fixtures/today`
    const res = await fetch(url)
    if (!res.ok) throw new Error('API not available')
    const data = await res.json()
    return { fixtures: data.fixtures || [], count: data.count || 0 }
  } catch (e) {
    console.warn('Using mock fixtures data')
    return { fixtures: MOCK_FIXTURES, count: MOCK_FIXTURES.length }
  }
}

export async function getLiveMatches(): Promise<{live_matches: any[], count: number}> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/live`)
    if (!res.ok) throw new Error('API not available')
    const data = await res.json()
    return { live_matches: data.live_matches || [], count: data.count || 0 }
  } catch (e) {
    return { live_matches: [], count: 0 }
  }
}

export async function getMatchStats(matchId: string): Promise<MatchStats> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/match/${matchId}/stats`)
    if (!res.ok) throw new Error('API not available')
    return await res.json()
  } catch (e) {
    return { stats: {}, incidents: [], lineups: {}, source: 'mock' }
  }
}

export async function getLeagues() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/leagues`)
    if (!res.ok) throw new Error('API not available')
    const data = await res.json()
    return data.leagues || []
  } catch (e) {
    return [
      { id: 1, name: 'Premier League', country: 'England' },
      { id: 2, name: 'La Liga', country: 'Spain' },
      { id: 3, name: 'Serie A', country: 'Italy' },
    ]
  }
}

export async function getAnalyticsSummary() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/analytics/summary`)
    if (!res.ok) throw new Error('API not available')
    return await res.json()
  } catch (e) {
    return {
      totalPredictions: 0,
      accuracyRate: 0.0,
      activeLeagues: 3,
      dataSources: ['sofascore', 'fotmob', 'fbref'],
    }
  }
}
