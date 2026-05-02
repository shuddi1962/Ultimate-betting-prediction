import Link from 'next/link'

export default function Sidebar() {
  return (
    <aside className="w-64 bg-gray-900 text-white min-h-screen p-6 space-y-6">
      <div className="text-2xl font-bold">FootballIQ</div>
      <nav className="space-y-2">
        <Link href="/">
          <span className="block py-2 px-4 rounded hover:bg-gray-800">Home</span>
        </Link>
        <Link href="/fixtures">
          <span className="block py-2 px-4 rounded hover:bg-gray-800">Fixtures</span>
        </Link>
        <Link href="/live">
          <span className="block py-2 px-4 rounded hover:bg-gray-800">Live Scores</span>
        </Link>
        <Link href="/leagues">
          <span className="block py-2 px-4 rounded hover:bg-gray-800">Leagues</span>
        </Link>
        <Link href="/analytics">
          <span className="block py-2 px-4 rounded hover:bg-gray-800">Analytics</span>
        </Link>
      </nav>
      <div className="pt-6 border-t border-gray-700">
        <p className="text-xs text-gray-400">Data Sources</p>
        <div className="mt-2 space-y-1 text-xs text-gray-300">
          <div>• Sofascore</div>
          <div>• FotMob</div>
          <div>• FBref</div>
          <div>• Understat</div>
        </div>
      </div>
    </aside>
  )
}
