import Navbar from "@/components/Navbar";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

// Initialize the Inter font
const inter = Inter({ subsets: ["latin"] });

// Metadata for the application
export const metadata: Metadata = {
  title: "Legal Search RAG",
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
    <html lang="en">
      <body className={inter.className}>
        <div className="container mx-auto px-4 max-w-7xl">
          <Navbar />
          <main className="flex-grow">{children}</main>
          <footer className="bg-white py-6 border-t">
            <div className="container mx-auto px-4 text-center text-gray-500 text-sm">
              © {new Date().getFullYear()} Legal Search RAG. All rights
              reserved.
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
