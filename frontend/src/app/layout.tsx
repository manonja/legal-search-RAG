import ErrorBoundary from "@/components/ErrorBoundary";
import Footer from "@/components/Footer";
import Navbar from "@/components/Navbar";
import TokenProvider from "@/components/providers/TokenProvider";
import SentryMonitor from "@/components/SentryMonitor";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";

// Initialize the Inter font
const inter = Inter({ subsets: ["latin"] });

// Metadata for the application
export const metadata: Metadata = {
  title: "Prae8",
  description:
    "Search legal documents with semantic similarity and AI-powered answers",
};

// Root layout component
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} min-h-full flex flex-col`}>
        <AuthProvider>
          <TokenProvider>
            <SentryMonitor />
            <div className="container mx-auto px-4 max-w-7xl flex flex-col flex-grow">
              <Navbar />
              <main className="flex-grow">
                <ErrorBoundary>
                  {children}
                </ErrorBoundary>
              </main>
              <Footer />
            </div>
          </TokenProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
