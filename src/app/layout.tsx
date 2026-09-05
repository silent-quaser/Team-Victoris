import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'GridGuard',
  description: 'Impact-Aware Grid Recovery Under Uncertainty',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.variable} font-sans antialiased`}>
        <Sidebar />
        <div className="ml-56 min-h-screen bg-slate-50">
          <Header />
          <main className="p-5">{children}</main>
        </div>
      </body>
    </html>
  );
}
