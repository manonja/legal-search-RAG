"use client";

import { useEffect, useState } from "react";
import { constructApiUrl } from "../../lib/utils";

// Admin API endpoints
const API_BASE_URL = constructApiUrl();
const REFRESH_INTERVAL = 30000; // Refresh every 30 seconds

interface UsageData {
  month: string;
  total_queries: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  total_cost: number;
  daily_breakdown: Array<{
    day: string;
    queries: number;
    tokens: number;
    cost: number;
  }>;
}

interface QuotaData {
  limit: number;
  used: number;
  remaining: number;
  percentage_used: number;
}

interface ThresholdData {
  per_query: number;
  daily: number;
  monthly: number;
}

interface DashboardData {
  current_usage: UsageData;
  quota: QuotaData;
  thresholds: ThresholdData;
  previous_month: UsageData;
  month_over_month: {
    queries: number;
    tokens: number;
    cost: number;
  };
  projected_monthly_cost: number;
  cost_per_query: number;
  generated_at: string;
}

export default function AdminDashboard() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState<string>("");
  const [authenticated, setAuthenticated] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/admin/dashboard`, {
        headers: {
          "X-API-Key": apiKey,
        },
        // Prevent caching of dashboard data
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error(
          `Failed to fetch dashboard data: ${response.statusText}`
        );
      }

      const data = await response.json();
      setDashboardData(data.data);
      setAuthenticated(true);
      setLastUpdated(new Date());
    } catch (err: any) {
      setError(err.message);
      if (err.message.includes("401")) {
        setAuthenticated(false);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateQuota = async (newLimit: number) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/admin/quota?new_limit=${newLimit}`,
        {
          method: "PUT",
          headers: {
            "X-API-Key": apiKey,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to update quota: ${response.statusText}`);
      }

      // Refetch dashboard data
      fetchDashboardData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleUpdateThresholds = async (thresholds: ThresholdData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/thresholds`, {
        method: "PUT",
        headers: {
          "X-API-Key": apiKey,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(thresholds),
      });

      if (!response.ok) {
        throw new Error(`Failed to update thresholds: ${response.statusText}`);
      }

      // Refetch dashboard data
      fetchDashboardData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => {
    // Only fetch if API key is set
    if (apiKey) {
      fetchDashboardData();

      // Set up auto-refresh interval
      const intervalId = setInterval(() => {
        fetchDashboardData();
      }, REFRESH_INTERVAL);

      // Cleanup interval on unmount
      return () => clearInterval(intervalId);
    }
  }, [apiKey]);

  // Add event listener for custom search events
  useEffect(() => {
    const handleSearch = () => {
      if (authenticated) {
        fetchDashboardData();
      }
    };

    window.addEventListener("search-performed", handleSearch);
    return () => window.removeEventListener("search-performed", handleSearch);
  }, [authenticated]);

  if (!authenticated) {
    return (
      <div className="container mx-auto px-4 max-w-7xl">
        <section className="text-center py-10">
          <h1 className="text-4xl text-gray-800 font-bold mb-5">
            Admin Dashboard
          </h1>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto mb-8">
            Access the admin dashboard to monitor API usage and manage settings.
          </p>
        </section>

        <div className="border border-gray-200 rounded-xl overflow-hidden shadow-sm">
          <div className="p-6">
            <h2 className="text-xl font-medium text-gray-800 mb-4">
              Authentication Required
            </h2>
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-600 mb-2">
                Enter API Key to Access Dashboard
              </label>
              <div className="flex gap-4">
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="flex-1 border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-gray-400"
                  placeholder="Enter your admin API key"
                />
                <button
                  onClick={() => fetchDashboardData()}
                  className="bg-gray-800 text-white px-6 py-2 rounded-full font-semibold hover:bg-gray-700 transition-colors"
                >
                  Login
                </button>
              </div>
              {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mt-4">
                  {error}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 max-w-7xl">
        <section className="text-center py-10">
          <h1 className="text-4xl text-gray-800 font-bold mb-5">
            Admin Dashboard
          </h1>
          <div className="text-center py-10">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-gray-800"></div>
            <p className="mt-4 text-gray-600">Loading dashboard data...</p>
          </div>
        </section>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="container mx-auto px-4 max-w-7xl">
        <section className="text-center py-10">
          <h1 className="text-4xl text-gray-800 font-bold mb-5">
            Admin Dashboard
          </h1>
          <div className="border border-gray-200 rounded-xl overflow-hidden shadow-sm">
            <div className="p-6">
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-4">
                {error || "Failed to load dashboard data. Please try again."}
              </div>
              <button
                onClick={() => fetchDashboardData()}
                className="bg-gray-800 text-white px-6 py-2 rounded-full font-semibold hover:bg-gray-700 transition-colors"
              >
                Retry
              </button>
            </div>
          </div>
        </section>
      </div>
    );
  }

  // Find max value for scaling charts
  const maxQueries = Math.max(
    ...dashboardData.current_usage.daily_breakdown.map((d) => d.queries)
  );
  const maxCost = Math.max(
    ...dashboardData.current_usage.daily_breakdown.map((d) => d.cost)
  );

  return (
    <div className="container mx-auto px-4 max-w-7xl">
      <section className="text-center py-10">
        <h1 className="text-4xl text-gray-800 font-bold mb-5">
          Admin Dashboard
        </h1>
        <p className="text-lg text-gray-600 max-w-3xl mx-auto mb-8">
          Monitor API usage, manage quotas, and configure system settings.
        </p>
      </section>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="border border-gray-200 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow p-6">
          <h3 className="text-lg font-medium text-gray-800 mb-4">
            Monthly Usage
          </h3>
          <div className="flex justify-between items-end">
            <div>
              <div className="text-3xl font-bold text-gray-900">
                {dashboardData.current_usage.total_queries}
              </div>
              <div className="text-sm text-gray-500">queries this month</div>
            </div>
            <div className="text-right">
              <div className="text-xl font-semibold text-gray-900">
                ${dashboardData.current_usage.total_cost.toFixed(2)}
              </div>
              <div className="text-sm text-gray-500">total cost</div>
            </div>
          </div>
        </div>

        <div className="border border-gray-200 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow p-6">
          <h3 className="text-lg font-medium text-gray-800 mb-4">
            Quota Status
          </h3>
          <div className="flex justify-between items-end">
            <div>
              <div className="text-3xl font-bold text-gray-900">
                {dashboardData.quota.remaining}
              </div>
              <div className="text-sm text-gray-500">queries remaining</div>
            </div>
            <div className="text-right">
              <div className="text-xl font-semibold text-gray-900">
                {dashboardData.quota.percentage_used}%
              </div>
              <div className="text-sm text-gray-500">quota used</div>
            </div>
          </div>
          <div className="mt-4 bg-gray-200 rounded-full h-2">
            <div
              className="bg-gray-800 h-2 rounded-full transition-all duration-500"
              style={{ width: `${dashboardData.quota.percentage_used}%` }}
            ></div>
          </div>
        </div>

        <div className="border border-gray-200 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow p-6">
          <h3 className="text-lg font-medium text-gray-800 mb-4">
            Cost Metrics
          </h3>
          <div className="flex justify-between items-end">
            <div>
              <div className="text-3xl font-bold text-gray-900">
                ${dashboardData.cost_per_query.toFixed(4)}
              </div>
              <div className="text-sm text-gray-500">per query</div>
            </div>
            <div className="text-right">
              <div className="text-xl font-semibold text-gray-900">
                ${dashboardData.projected_monthly_cost.toFixed(2)}
              </div>
              <div className="text-sm text-gray-500">projected cost</div>
            </div>
          </div>
        </div>
      </div>

      {/* Usage Details */}
      <div className="border border-gray-200 rounded-xl overflow-hidden shadow-sm mb-8">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-medium text-gray-800">Usage Details</h2>
            <div className="text-sm text-gray-500">
              Last updated: {lastUpdated.toLocaleString()}
              {authenticated && (
                <button
                  onClick={fetchDashboardData}
                  className="ml-2 text-gray-600 hover:text-gray-800"
                  title="Refresh data"
                >
                  🔄
                </button>
              )}
            </div>
          </div>

          {/* Daily Usage Chart */}
          <div className="mb-8">
            <h3 className="text-lg font-medium text-gray-800 mb-4">
              Daily Usage
            </h3>
            <div className="h-64 relative">
              {dashboardData.current_usage.daily_breakdown.map((day, index) => (
                <div
                  key={index}
                  className="absolute bottom-0 bg-gray-800 hover:bg-gray-700 transition-colors rounded-t"
                  style={{
                    left: `${(index / dashboardData.current_usage.daily_breakdown.length) * 100}%`,
                    width: `${100 / dashboardData.current_usage.daily_breakdown.length}%`,
                    height: `${(day.queries / maxQueries) * 100}%`,
                  }}
                  title={`${day.day}: ${day.queries} queries, $${day.cost.toFixed(2)}`}
                />
              ))}
            </div>
          </div>

          {/* Month over Month Comparison */}
          <div className="border-t border-gray-100 pt-6">
            <h3 className="text-lg font-medium text-gray-800 mb-4">
              Month over Month
            </h3>
            <div className="grid grid-cols-3 gap-6">
              <div>
                <div className="text-sm text-gray-500 mb-1">Queries</div>
                <div className="text-xl font-semibold text-gray-900">
                  {dashboardData.month_over_month.queries > 0 ? "+" : ""}
                  {dashboardData.month_over_month.queries}%
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500 mb-1">Tokens</div>
                <div className="text-xl font-semibold text-gray-900">
                  {dashboardData.month_over_month.tokens > 0 ? "+" : ""}
                  {dashboardData.month_over_month.tokens}%
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500 mb-1">Cost</div>
                <div className="text-xl font-semibold text-gray-900">
                  {dashboardData.month_over_month.cost > 0 ? "+" : ""}
                  {dashboardData.month_over_month.cost}%
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Settings */}
      <div className="border border-gray-200 rounded-xl overflow-hidden shadow-sm">
        <div className="p-6">
          <h2 className="text-xl font-medium text-gray-800 mb-6">Settings</h2>

          {/* Quota Settings */}
          <div className="mb-8">
            <h3 className="text-lg font-medium text-gray-800 mb-4">
              Quota Settings
            </h3>
            <div className="flex gap-4 items-end">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-600 mb-2">
                  Monthly Query Limit
                </label>
                <input
                  type="number"
                  value={dashboardData.quota.limit}
                  onChange={(e) => handleUpdateQuota(parseInt(e.target.value))}
                  className="w-full border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-gray-400"
                />
              </div>
              <button
                onClick={() => handleUpdateQuota(dashboardData.quota.limit)}
                className="bg-gray-800 text-white px-6 py-2 rounded-full font-semibold hover:bg-gray-700 transition-colors"
              >
                Update Quota
              </button>
            </div>
          </div>

          {/* Threshold Settings */}
          <div>
            <h3 className="text-lg font-medium text-gray-800 mb-4">
              Cost Thresholds
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-2">
                  Per Query ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={dashboardData.thresholds.per_query}
                  onChange={(e) =>
                    handleUpdateThresholds({
                      ...dashboardData.thresholds,
                      per_query: parseFloat(e.target.value),
                    })
                  }
                  className="w-full border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-gray-400"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-2">
                  Daily ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={dashboardData.thresholds.daily}
                  onChange={(e) =>
                    handleUpdateThresholds({
                      ...dashboardData.thresholds,
                      daily: parseFloat(e.target.value),
                    })
                  }
                  className="w-full border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-gray-400"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-2">
                  Monthly ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={dashboardData.thresholds.monthly}
                  onChange={(e) =>
                    handleUpdateThresholds({
                      ...dashboardData.thresholds,
                      monthly: parseFloat(e.target.value),
                    })
                  }
                  className="w-full border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-gray-400"
                />
              </div>
            </div>
            <button
              onClick={() => handleUpdateThresholds(dashboardData.thresholds)}
              className="mt-4 bg-gray-800 text-white px-6 py-2 rounded-full font-semibold hover:bg-gray-700 transition-colors"
            >
              Update Thresholds
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
