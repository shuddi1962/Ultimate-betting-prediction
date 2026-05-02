'use client'

import { useState, useEffect } from 'react'
import { getFixtures, Fixture } from '@/lib/api'
import Link from 'next/link'

export default function FixturesPage() {
  const [fixtures, setFixtures] = useState<Fixture[]>([])
  const [loading, setLoading] = useState(true)
  const [date, setDate] = useState(new Date().toISOString().split('T')[0])

  useEffect(() => {
    loadFixtures()
  }, [date])

  async function loadFixtures() {
    setLoading(true)
    try {
      const res = await getFixtures(date)
      setFixtures(res.fixtures || [])
    } catch (error) {
      console.error('Error loading fixtures:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Fixtures</h1>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="mb-6 flex gap-4 items-center">
          <label className="text-sm font-medium">Date:</label>
          <input 
            type="date" 
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="px-3 py-2 border rounded"
          />
          <button 
            onClick={loadFixtures}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Load
          </button>
        </div>

        {loading ? (
          <div className="text-center py-8">Loading fixtures...</div>
        ) : fixtures.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No fixtures for this date</div>
        ) : (
          <div className="bg-white rounded-lg shadow">
            <div className="divide-y">
              {fixtures.map((fixture, idx) => (
                <Link 
                  key={fixture.id || idx}
                  href={`/match/${fixture.id}`}
                  className="block p-4 hover:bg-gray-50"
                >
                  <div className="flex justify-between items-center">
                    <div className="flex-1 text-right">
                      <span className="font-medium">{fixture.home_team}</span>
                    </div>
                    <div className="px-6 text-center">
                      <div className="text-gray-500 text-sm">{fixture.league}</div>
                      <div className="font-semibold">vs</div>
                      <div className="text-xs text-gray-400">
                        {new Date(fixture.kickoff_utc).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                      </div>
                    </div>
                    <div className="flex-1">
                      <span className="font-medium">{fixture.away_team}</span>
                    </div>
                    <div className="ml-4">
                      <span className={`px-2 py-1 text-xs rounded ${
                        fixture.status === 'NS' ? 'bg-gray-200' :
                        fixture.status === 'LIVE' ? 'bg-red-500 text-white' :
                        'bg-green-200'
                      }`}>
                        {fixture.status}
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
