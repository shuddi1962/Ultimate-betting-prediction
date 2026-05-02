'use client'

import { useState, useEffect } from 'react'

export default function LeaguesPage() {
  const [leagues, setLeagues] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadLeagues() }, [])

  async function loadLeagues() {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/leagues`)
      if (res.ok) {
        const data = await res.json()
        setLeagues(data.leagues || [])
      } else {
        setLeagues([
          { id: 1, name: 'Premier League', country: 'England' },
          { id: 2, name: 'La Liga', country: 'Spain' },
          { id: 3, name: 'Serie A', country: 'Italy' },
        ])
      }
    } catch (error) {
      setLeagues([
        { id: 1, name: 'Premier League', country: 'England' },
        { id: 2, name: 'La Liga', country: 'Spain' },
        { id: 3, name: 'Serie A', country: 'Italy' },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Leagues</h1>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {loading ? (
          <div className="text-center py-8">Loading leagues...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {leagues.map((league) => (
              <div key={league.id} className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition">
                <h3 className="font-bold text-lg">{league.name}</h3>
                <p className="text-gray-600">{league.country}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
