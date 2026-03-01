import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' })
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' })

export const metadata: Metadata = {
  title: 'TriageNet | Emergency Intelligence',
  description: 'Multi-caller emergency dispatch system powered by Mistral and ElevenLabs.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${jetbrainsMono.variable} font-sans dark:bg-[#050505] bg-gray-50 text-black dark:text-white overflow-hidden selection:bg-blue-500/30`}>
        {/* Technical Grid Background */}
        <div className="fixed inset-0 pointer-events-none z-[-1] opacity-[0.15] dark:opacity-[0.03]" 
             style={{ 
               backgroundImage: `linear-gradient(to right, currentColor 1px, transparent 1px), linear-gradient(to bottom, currentColor 1px, transparent 1px)`, 
               backgroundSize: '24px 24px' 
             }}>
        </div>
        
        {children}
      </body>
    </html>
  )
}
