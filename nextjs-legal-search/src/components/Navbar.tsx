"use client";

import { cn } from "@/lib/utils";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navbar() {
  const pathname = usePathname();

  const navItems = [
    { name: "Document Search", href: "/search" },
    { name: "Ask Legal Questions", href: "/rag-search" },
    { name: "About", href: "/about" },
    { name: "Contact", href: "/contact" },
  ];

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
      <div className="hidden md:flex items-center justify-center space-x-8 flex-1 mx-10">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "inline-flex items-center px-1 pt-1 border-b text-sm font-medium",
              pathname === item.href
                ? "border-blue-400 text-gray-900"
                : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
            )}
          >
            {item.name}
          </Link>
        ))}
      </div>

      {/* Login Button - Right */}
      <Link
        href="/login"
        className="bg-black text-white px-5 py-2 rounded-full font-semibold hover:bg-gray-800 transition-colors"
      >
        Log in
      </Link>
    </nav>
  );
}
