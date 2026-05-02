import './globals.css'

export const metadata = {
  title: 'FootballIQ Pro - Free Football Predictions',
  description: 'Football predictions using free web scrapers',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
