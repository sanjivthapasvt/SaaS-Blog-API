import type { Metadata } from 'next';
import Link from 'next/link';

import './globals.css';

export const metadata: Metadata = {
  title: 'SaaS Blog Frontend',
  description: 'Next.js frontend for the SaaS Blog API'
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <header>
          <nav>
            <Link href="/">Home</Link>
            <Link href="/login">Login</Link>
          </nav>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
