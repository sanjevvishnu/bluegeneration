import type { Metadata } from "next";
import "./globals.css";
import { ClerkProvider } from '@clerk/nextjs'
import { Toaster } from "sonner";
import { FontProvider } from "@/components/providers/font-provider";

export const metadata: Metadata = {
  title: "Coimbatore - Master Tech Interviews with AI",
  description: "Practice voice interviews with AI interviewers from top tech companies. Get real-time feedback and land your dream job.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider
      publishableKey={process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY}
    >
      <html lang="en">
        <head>
          <link href="https://api.fontshare.com/v2/css?f[]=satoshi@1,2,3,4,5,6,7,8,9&display=swap" rel="stylesheet" />
          <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&display=swap" rel="stylesheet" />
        </head>
        <body className="antialiased">
          <FontProvider>
            {children}
            <Toaster 
              position="top-right"
              toastOptions={{
                style: {
                  background: 'rgba(245, 158, 11, 0.9)',
                  color: 'white',
                  border: '1px solid rgba(245, 158, 11, 0.2)',
                },
              }}
            />
          </FontProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}