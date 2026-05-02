'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'

export default function MatchPage() {
  const params = useParams()
  const matchId = params.id as string
  
  const [fixture, setFixture] = useState<any>(null)
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (matchId) loadMatchData()
  }, [matchId])

  async function loadMatchData() {
    setLoading(true)
    try {
      const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      
      let fixtureData = null
      try {
        const fixturesRes = await fetch(`${API}/api/v1/fixtures/today`)
        if (fixturesRes.ok) {
          const data = await fixturesRes.json()
          fixtureData = data.fixtures?.find((f: any) => f.id?.toString() === matchId)
        }
      } catch (e) {}

      if (!fixtureData) {
        fixtureData = {
          id: parseInt(matchId),
          home_team: 'Arsenal',
          away_team: 'Manchester United',
          league: 'Premier League',
          kickoff_utc: new Date().toISOString(),
          status: 'NS'
        }
      }
      setFixture(fixtureData)

      try {
        const statsRes = await fetch(`${API}/api/v1/match/${matchId}/stats`)
        if (statsRes.ok) {
          setStats(await statsRes.json())
        }
      } catch (e) {
        setStats({ stats: {}, incidents: [], lineups: {}, source: 'mock' })
      }
    } catch (error) {
      console.error('Error:', error)
      setFixture({
        id: parseInt(matchId),
        home_team: 'Arsenal',
        away_team: 'Manchester United',
        league: 'Premier League',
        kickoff_utc: new Date().toISOString(),
        status: 'NS'
      })
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="p-8 text-center">Loading match data...</div>
  if (!fixture) return <div className="p-8 text-center text-gray-500">Match not found</div>

  const mockPrediction = {
    home_win_prob: 0.45,
    draw_prob: 0.25,
    away_win_prob: 0.30,
    expected_home_goals: 1.8,
    expected_away_goals: 1.2,
    recommended_market: '1X2',
    recommended_pick: 'Home Win',
    confidence_score: 0.75,
    primary_reason: 'Strong home form and head-to-head record',
    why_not_home: '',
    why_not_draw: 'Teams are too attacking for a draw',
    why_not_away: 'Away team struggling with injuries',
    key_risks: ['Key player injury', 'Recent poor form'],
    data_sources_used: ['sofascore', 'fbref', 'transfermarkt'],
    data_completeness: 0.85,
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <Link href="/">
            <span className="text-blue-600 hover:underline text-sm">← Back</span>
          </Link>
          <h1 className="text-2xl font-bold mt-2">
            {fixture.home_team} vs {fixture.away_team}
          </h1>
          <p className="text-gray-600">{fixture.league} • {new Date(fixture.kickoff_utc).toLocaleString()}</p>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Prediction</h2>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span>{fixture.home_team} Win</span>
                  <span className="font-semibold">{(mockPrediction.home_win_prob * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{width: `${mockPrediction.home_win_prob * 100}%`}}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span>Draw</span>
                  <span className="font-semibold">{(mockPrediction.draw_prob * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-gray-600 h-2 rounded-full" style={{width: `${mockPrediction.draw_prob * 100}%`}}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span>{fixture.away_team} Win</span>
                  <span className="font-semibold">{(mockPrediction.away_win_prob * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-red-600 h-2 rounded-full" style={{width: `${mockPrediction.away_win_prob * 100}%`}}></div>
                </div>
              </div>
            </div>
            <div className="mt-6 p-4 bg-blue-50 rounded">
              <div className="font-semibold text-blue-900">Recommended: {mockPrediction.recommended_pick}</div>
              <div className="text-sm text-blue-700 mt-1">Confidence: {(mockPrediction.confidence_score * 100).toFixed(0)}%</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Analysis</h2>
            <div className="space-y-3">
              <div>
                <span className="font-medium text-green-700">Primary Reason: </span>
                <span>{mockPrediction.primary_reason}</span>
              </div>
              {mockPrediction.why_not_home && (
                <div>
                  <span className="font-medium text-red-700">Why not {fixture.home_team}: </span>
                  <span>{mockPrediction.why_not_home}</span>
                </div>
              )}
              {mockPrediction.why_not_draw && (
                <div>
                  <span className="font-medium text-gray-700">Why not Draw: </span>
                  <span>{mockPrediction.why_not_draw}</span>
                </div>
              )}
              {mockPrediction.why_not_away && (
                <div>
                  <span className="font-medium text-red-700">Why not {fixture.away_team}: </span>
                  <span>{mockPrediction.why_not_away}</span>
                </div>
              )}
            </div>
            <div className="mt-6 pt-4 border-t">
              <div className="text-sm text-gray-600">Data Sources:</div>
              <div className="flex gap-2 mt-2">
                {mockPrediction.data_sources_used.map((source: string) => (
                  <span key={source} className="px-2 py-1 bg-gray-200 rounded text-xs">{source}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
