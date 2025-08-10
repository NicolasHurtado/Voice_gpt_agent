import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'Voice GPT Agent',
  description: 'AI-powered voice assistant with real-time conversation',
  keywords: ['AI', 'voice', 'assistant', 'GPT', 'speech recognition'],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang='en'>
      <body className={`${inter.variable} font-sans antialiased`}>
        <div className='min-h-screen bg-gray-50'>{children}</div>
      </body>
    </html>
  );
}
