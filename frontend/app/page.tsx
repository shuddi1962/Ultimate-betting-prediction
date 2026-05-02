'use client'

import { useState, useEffect } from 'react'
import { getFixtures, getLiveMatches, Fixture } from '@/lib/api'
import Link from 'next/link'

export default function HomePage() {
  const [fixtures, setFixtures] = useState<Fixture[]>([])
  const [liveMatches, setLiveMatches] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'today' | 'live'>('today')

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const [fixturesRes, liveRes] = await Promise.all([
        getFixtures(),
        getLiveMatches()
      ])
      setFixtures(fixturesRes.fixtures || [])
      setLiveMatches(liveRes.live_matches || [])
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="p-8">Loading...</div>

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">FootballIQ Pro</h1>
          <p className="text-gray-600">Free football predictions from scraped data</p>
        </div>
      </header>

      <nav className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex gap-4">
          <Link href="/fixtures" className="text-blue-600 hover:underline">Fixtures</Link>
          <Link href="/live" className="text-blue-600 hover:underline">Live Scores</Link>
          <Link href="/leagues" className="text-blue-600 hover:underline">Leagues</Link>
          <Link href="/analytics" className="text-blue-600 hover:underline">Analytics</Link>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex gap-4 mb-6">
          <button 
            onClick={() => setActiveTab('today')}
            className={`px-4 py-2 rounded ${activeTab === 'today' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700'}`}
          >
            Today's Fixtures
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
                <p className="text-gray-500">No fixtures available</p>
              ) : (
                <div className="space-y-3">
                  {fixtures.map((fixture, idx) => (
                    <Link 
                      key={fixture.id || idx}
                      href={`/match/${fixture.id}`}
                      className="block p-4 border rounded hover:bg-gray-50"
                    >
                      <div className="flex justify-between items-center">
                        <div className="flex-1 text-right">
                          <span className="font-medium">{fixture.home_team}</span>
                        </div>
                        <div className="px-4 text-gray-500">vs</div>
                        <div className="flex-1">
                          <span className="font-medium">{fixture.away_team}</span>
                        </div>
                        <div className="ml-4 text-sm text-gray-500">
                          {fixture.league}
                        </div>
                      </div>
                    </Link>
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
                <p className="text-gray-500">No live matches</p>
              ) : (
                <div className="space-y-3">
                  {liveMatches.map((match, idx) => (
                    <div key={idx} className="p-4 border rounded">
                      <div className="flex justify-between items-center">
                        <div className="flex-1 text-right">
                          <span className="font-medium">{match.homeTeam || match.home_team}</span>
                        </div>
                        <div className="px-4 font-bold">
                          {match.homeScore ?? 0} - {match.awayScore ?? 0}
                        </div>
                        <div className="flex-1">
                          <span className="font-medium">{match.awayTeam || match.away_team}</span>
                        </div>
                        <div className="ml-4">
                          <span className="inline-block px-2 py-1 text-xs bg-red-500 text-white rounded">LIVE</span>
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
    </main>
  )
}
