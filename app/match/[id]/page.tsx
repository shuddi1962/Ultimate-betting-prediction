'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { getMatchStats, getFixtures, Fixture, Prediction, MatchStats } from '@/lib/api'
import Link from 'next/link'

export default function MatchPage() {
  const params = useParams()
  const matchId = params.id as string
  
  const [fixture, setFixture] = useState<Fixture | null>(null)
  const [stats, setStats] = useState<MatchStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (matchId) {
      loadMatchData()
    }
  }, [matchId])

  async function loadMatchData() {
    setLoading(true)
    try {
      const [fixturesRes, statsRes] = await Promise.all([
        getFixtures(),
        getMatchStats(matchId).catch(() => null)
      ])
      
      const found = fixturesRes.fixtures?.find((f: Fixture) => f.id.toString() === matchId)
      setFixture(found || null)
      setStats(statsRes)
    } catch (error) {
      console.error('Error loading match data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="p-8 text-center">Loading match data...</div>
  if (!fixture) return <div className="p-8 text-center text-gray-500">Match not found</div>

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <Link href="/" className="text-blue-600 hover:underline text-sm">← Back</Link>
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
                  <span className="font-semibold">{(fixture as any).home_win_prob ? ((fixture as any).home_win_prob * 100).toFixed(1) : 'N/A'}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{width: `${(fixture as any).home_win_prob ? (fixture as any).home_win_prob * 100 : 0}%`}}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span>Draw</span>
                  <span className="font-semibold">{(fixture as any).draw_prob ? ((fixture as any).draw_prob * 100).toFixed(1) : 'N/A'}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-gray-600 h-2 rounded-full" style={{width: `${(fixture as any).draw_prob ? (fixture as any).draw_prob * 100 : 0}%`}}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span>{fixture.away_team} Win</span>
                  <span className="font-semibold">{(fixture as any).away_win_prob ? ((fixture as any).away_win_prob * 100).toFixed(1) : 'N/A'}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-red-600 h-2 rounded-full" style={{width: `${(fixture as any).away_win_prob ? (fixture as any).away_win_prob * 100 : 0}%`}}></div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Match Stats</h2>
            {stats ? (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span>Source:</span>
                  <span className="font-medium">{stats.source}</span>
                </div>
                {stats.stats && Object.entries(stats.stats).slice(0, 8).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-600">{key}:</span>
                    <span className="font-medium">{String(value)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No stats available</p>
            )}
          </div>
        </div>

        {(fixture as any).primary_reason && (
          <div className="mt-6 bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Analysis</h2>
            <div className="space-y-3">
              <div>
                <span className="font-medium text-green-700">Primary Reason: </span>
                <span>{(fixture as any).primary_reason}</span>
              </div>
              {(fixture as any).why_not_home && (
                <div>
                  <span className="font-medium text-red-700">Why not {fixture.home_team}: </span>
                  <span>{(fixture as any).why_not_home}</span>
                </div>
              )}
              {(fixture as any).why_not_draw && (
                <div>
                  <span className="font-medium text-gray-700">Why not Draw: </span>
                  <span>{(fixture as any).why_not_draw}</span>
                </div>
              )}
              {(fixture as any).why_not_away && (
                <div>
                  <span className="font-medium text-red-700">Why not {fixture.away_team}: </span>
                  <span>{(fixture as any).why_not_away}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
