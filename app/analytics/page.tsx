'use client'

import { useState, useEffect } from 'react'

export default function AnalyticsPage() {
  const [stats, setStats] = useState({
    totalPredictions: 0,
    accuracyRate: 0.0,
    activeLeagues: 0,
    dataSources: [] as string[],
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadAnalytics() }, [])

  async function loadAnalytics() {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/analytics/summary`)
      if (res.ok) {
        const data = await res.json()
        setStats(data)
      } else {
        setStats({
          totalPredictions: 0,
          accuracyRate: 0.0,
          activeLeagues: 3,
          dataSources: ['sofascore', 'fotmob', 'fbref'],
        })
      }
    } catch (error) {
      setStats({
        totalPredictions: 0,
        accuracyRate: 0.0,
        activeLeagues: 3,
        dataSources: ['sofascore', 'fotmob', 'fbref'],
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {loading ? (
          <div className="text-center py-8">Loading analytics...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600">Total Predictions</div>
              <div className="text-3xl font-bold mt-2">{stats.totalPredictions}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600">Accuracy Rate</div>
              <div className="text-3xl font-bold mt-2">{(stats.accuracyRate * 100).toFixed(1)}%</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600">Active Leagues</div>
              <div className="text-3xl font-bold mt-2">{stats.activeLeagues}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600">Data Sources</div>
              <div className="text-3xl font-bold mt-2">{stats.dataSources.length}</div>
              <div className="mt-2 space-y-1">
                {stats.dataSources.map((source: string) => (
                  <div key={source} className="text-xs text-gray-500">{source}</div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
