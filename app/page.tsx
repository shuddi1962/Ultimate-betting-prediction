'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

export default function HomePage() {
  const [fixtures, setFixtures] = useState<any[]>([])
  const [liveMatches, setLiveMatches] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'today' | 'live'>('today')

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const [fixturesRes, liveRes] = await Promise.all([
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/fixtures/today`),
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/live`)
      ])
      const fixturesData = fixturesRes.ok ? await fixturesRes.json() : { fixtures: []}
      const liveData = liveRes.ok ? await liveRes.json() : { live_matches: []}
      setFixtures(fixturesData.fixtures || [])
      setLiveMatches(liveData.live_matches || [])
    } catch (error) {
      console.warn('API not available, showing empty state')
      setFixtures([])
      setLiveMatches([])
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="p-8 text-center">Loading...</div>

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">FootballIQ Pro</h1>
          <p className="text-gray-600">Free football predictions from scraped data</p>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex gap-4 mb-6">
          <button 
            onClick={() => setActiveTab('today')}
            className={`px-4 py-2 rounded ${activeTab === 'today' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700'}`}
          >
            Today's Fixtures ({fixtures.length})
          </button>
          <button 
            onClick={() => setActiveTab('live')}
            className={`px-4 py-2 rounded ${activeTab === 'live' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700'}`}
          >
            Live Matches ({liveMatches.length})
          </button>
        </div>

        {activeTab === 'today' && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4">Today's Fixtures ({fixtures.length})</h2>
              {fixtures.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>No fixtures available yet</p>
                  <p className="text-sm mt-2">Start the backend to see today's matches</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {fixtures.map((fixture: any, idx: number) => (
                    <a 
                      key={fixture.id || idx}
                      href={`/match/${fixture.id}`}
                      className="block p-4 border rounded hover:bg-gray-50"
                    >
                      <div className="flex justify-between items-center">
                        <div className="flex-1 text-right">
                          <span className="font-medium">{fixture.home_team}</span>
                        </div>
                        <div className="px-4 text-center">
                          <div className="text-gray-500 text-sm">{fixture.league}</div>
                          <div className="font-semibold">vs</div>
                        </div>
                        <div className="flex-1">
                          <span className="font-medium">{fixture.away_team}</span>
                        </div>
                      </div>
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'live' && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4">Live Matches</h2>
              {liveMatches.length === 0 ? (
                <div className="text-center py-8 text-gray-500">No live matches</div>
              ) : (
                <div className="space-y-3">
                  {liveMatches.map((match: any, idx: number) => (
                    <div key={idx} className="p-4 border rounded">
                      <div className="flex justify-between items-center">
                        <div className="flex-1 text-right">
                          <span className="font-medium">{match.homeTeam || match.home_team}</span>
                        </div>
                        <div className="px-6 text-center">
                          <div className="text-2xl font-bold">{match.homeScore ?? 0} - {match.awayScore ?? 0}</div>
                          <span className="inline-block px-2 py-1 text-xs bg-red-500 text-white rounded">LIVE</span>
                        </div>
                        <div className="flex-1">
                          <span className="font-medium">{match.awayTeam || match.away_team}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
