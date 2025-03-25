"use client";

import { useAuth } from "@/contexts/AuthContext";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Menu, Transition } from "@headlessui/react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Fragment, useEffect, useState } from "react";

export default function Navbar() {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuth();
  const [tenantInfo, setTenantInfo] = useState<{
    tenant_id: string;
    environment_tenant: string;
  } | null>(null);

  // Fetch tenant info
  useEffect(() => {
    const fetchTenantInfo = async () => {
      try {
        const info = await api.getTenantInfo();
        setTenantInfo(info);
      } catch (error) {
        console.error("Failed to fetch tenant info:", error);
      }
    };

    fetchTenantInfo();
  }, []);

  // Base navigation items for everyone
  const navItems = [
    { name: "Document Search", href: "/search" },
    { name: "Ask Legal Questions", href: "/rag-search" },
  ];

  // Add dashboard for authenticated users
  if (isAuthenticated) {
    navItems.unshift({ name: "Dashboard", href: "/dashboard" });
  }

  // Public nav items for all users
  navItems.push(
    { name: "About", href: "/about" },
    { name: "Book Demo", href: "/book-demo" }
  );

  // Handle logout
  const handleLogout = async () => {
    await logout();
    window.location.href = "/";
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
      <div className="flex items-center justify-center space-x-8 flex-1 mx-10">
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

      {/* User Menu - Right */}
      <div className="flex items-center">
        {isAuthenticated && tenantInfo && (
          <span className="text-sm text-gray-500 mr-4">
            Tenant: {tenantInfo.tenant_id.substring(0, 8)}...
          </span>
        )}

        {isAuthenticated ? (
          <Menu as="div" className="relative ml-3">
            <div>
              <Menu.Button className="flex rounded-full bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2">
                <span className="sr-only">Open user menu</span>
                <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold">
                  {user?.full_name?.[0] || user?.email?.[0] || "U"}
                </div>
              </Menu.Button>
            </div>
            <Transition
              as={Fragment}
              enter="transition ease-out duration-200"
              enterFrom="transform opacity-0 scale-95"
              enterTo="transform opacity-100 scale-100"
              leave="transition ease-in duration-75"
              leaveFrom="transform opacity-100 scale-100"
              leaveTo="transform opacity-0 scale-95"
            >
              <Menu.Items className="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                <div className="px-4 py-2 text-sm text-gray-700 border-b">
                  <p className="font-medium">{user?.full_name || "User"}</p>
                  <p className="truncate">{user?.email}</p>
                </div>
                <Menu.Item>
                  {({ active }) => (
                    <Link
                      href="/dashboard"
                      className={cn(
                        active ? "bg-gray-100" : "",
                        "block px-4 py-2 text-sm text-gray-700"
                      )}
                    >
                      Dashboard
                    </Link>
                  )}
                </Menu.Item>
                {user?.is_admin && (
                  <Menu.Item>
                    {({ active }) => (
                      <Link
                        href="/tenant/new"
                        className={cn(
                          active ? "bg-gray-100" : "",
                          "block px-4 py-2 text-sm text-gray-700"
                        )}
                      >
                        Create New Tenant
                      </Link>
                    )}
                  </Menu.Item>
                )}
                <Menu.Item>
                  {({ active }) => (
                    <button
                      onClick={handleLogout}
                      className={cn(
                        active ? "bg-gray-100" : "",
                        "block w-full text-left px-4 py-2 text-sm text-gray-700"
                      )}
                    >
                      Sign out
                    </button>
                  )}
                </Menu.Item>
              </Menu.Items>
            </Transition>
          </Menu>
        ) : (
          <Link
            href="/login"
            className="inline-flex items-center rounded-md bg-blue-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-600"
          >
            Login
          </Link>
        )}
      </div>
    </nav>
  );
}
