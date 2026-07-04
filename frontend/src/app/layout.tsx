import { AuthProvider } from '@/hooks/useAuth';
import { AppLayout } from '@/components/layout/AppLayout';
import '@/styles/globals.css';

export const metadata = {
  title: 'Antigravity Job Scheduler',
  description: 'Production-inspired distributed background job scheduler',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-950 antialiased">
        <AuthProvider>
          <AppLayout>{children}</AppLayout>
        </AuthProvider>
      </body>
    </html>
  );
}
