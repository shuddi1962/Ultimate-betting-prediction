'use client'

import { useState, useEffect } from 'react'
import { getLiveMatches } from '@/lib/api'

export default function LivePage() {
  const [matches, setMatches] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadLiveMatches()
    const interval = setInterval(loadLiveMatches, 30000)
    return () => clearInterval(interval)
  }, [])

  async function loadLiveMatches() {
    try {
      const res = await getLiveMatches()
      setMatches(res.live_matches || [])
    } catch (error) {
      console.error('Error loading live matches:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Live Scores</h1>
          <p className="text-gray-600">Auto-refreshes every 30s</p>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {loading ? (
          <div className="text-center py-8">Loading live matches...</div>
        ) : matches.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No live matches at the moment</div>
        ) : (
          <div className="space-y-4">
            {matches.map((match, idx) => (
              <div key={idx} className="bg-white rounded-lg shadow p-6">
                <div className="flex justify-between items-center">
                  <div className="flex-1 text-right">
                    <div className="font-bold text-lg">{match.homeTeam || match.home_team}</div>
                  </div>
                  <div className="px-8 text-center">
                    <div className="text-3xl font-bold">
                      {match.homeScore ?? 0} - {match.awayScore ?? 0}
                    </div>
                    <div className="text-sm text-gray-500 mt-1">{match.league || match.competition}</div>
                    <div className="mt-2">
                      <span className="inline-block px-3 py-1 bg-red-500 text-white text-xs rounded-full animate-pulse">
                        LIVE
                      </span>
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="font-bold text-lg">{match.awayTeam || match.away_team}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  )
}
