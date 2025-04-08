"use client";

import { cn } from "@/lib/utils";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function Navbar() {
  const pathname = usePathname();
  const { currentUser, firebaseUser, loading, logout } = useAuth();
  const router = useRouter();

  // Add debug logs to check auth state
  useEffect(() => {
    console.log("[Navbar] Auth state:", {
      currentUser: currentUser ? currentUser.uid : null,
      firebaseUser: firebaseUser ? firebaseUser.uid : null,
      loading
    });
  }, [currentUser, firebaseUser, loading]);

  const navItems = [
    { name: "Document Search", href: "/search" },
    { name: "Ask Legal Questions", href: "/rag-search" },
    { name: "Book Demo", href: "/book-demo" },
  ];

  const handleLogout = async () => {
    try {
      console.log("Logging out...");
      await logout();

      console.log("Clearing session cookie...");
      await axios.delete("/api/auth/session");

      console.log("Logout successful, refreshing page...");
      // Force a full page reload to clear all state
      window.location.href = '/?logout=true';
    } catch (error) {
      console.error("Failed to logout from Navbar:", error);
    }
  };

  return (
    <nav className="flex items-center justify-between py-5 border-b border-gray-200 px-4 md:px-8">
      {/* Logo - Left */}
      <Link
        href="/"
        className="text-2xl font-bold text-blue-400 flex items-center"
      >
        Prae8
        <Image
          src="/feather.png"
          alt="Prae8 Logo"
          width={28}
          height={28}
          className="mr-2"
        />
      </Link>

      {/* Navigation Items - Center */}
      <div className="hidden sm:flex items-center justify-center space-x-8 flex-1 mx-10">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium",
              pathname === item.href
                ? "border-blue-400 text-blue-400"
                : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
            )}
          >
            {item.name}
          </Link>
        ))}
      </div>

      {/* Auth Links/Actions - Right */}
      <div className="flex items-center space-x-4">
        {loading ? (
          <div className="h-8 w-24 bg-gray-200 rounded animate-pulse"></div>
        ) : currentUser ? (
          <>
            {currentUser.role === "admin" && (
              <Link
                href="/admin"
                className="text-sm font-medium text-gray-500 hover:text-blue-400"
              >
                Admin
              </Link>
            )}
            <Link
              href="/dashboard"
              className="text-sm font-medium text-gray-500 hover:text-blue-400"
            >
              Dashboard
            </Link>
            <button
              onClick={handleLogout}
              className="text-sm font-medium text-red-600 hover:text-red-500"
            >
              Logout
            </button>
          </>
        ) : (
          <>
            <Link
              href="/login?bypassAuthRedirect=true"
              className="text-sm font-medium text-gray-500 hover:text-blue-400"
            >
              Login
            </Link>
            <Link
              href="/signup?bypassAuthRedirect=true"
              className="ml-4 bg-gray-800 text-white px-6 py-2 rounded-full font-semibold hover:bg-gray-700 transition-colors inline-block text-sm"
            >
              Sign Up
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}
