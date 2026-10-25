import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'Agentic Marketing Orchestrator', description: 'Plan, draft, review and approve marketing campaigns.' };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
