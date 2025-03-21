"use client";

import { useEffect, useState } from "react";

// Admin API endpoints
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/admin/dashboard`, {
        headers: {
          "X-API-Key": apiKey,
        },
      });

      if (!response.ok) {
        throw new Error(
          `Failed to fetch dashboard data: ${response.statusText}`
        );
      }

      const data = await response.json();
      setDashboardData(data.data);
      setAuthenticated(true);
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
    }
  }, [apiKey]);

  if (!authenticated) {
    return (
      <div className="min-h-screen bg-gray-100 p-6">
        <div className="max-w-4xl mx-auto bg-white rounded-lg shadow p-6">
          <h1 className="text-2xl font-bold mb-6">Admin Dashboard</h1>
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Enter API Key to Access Dashboard
            </label>
            <div className="flex gap-4">
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="border border-gray-300 rounded-md px-4 py-2 flex-grow"
                placeholder="Enter your admin API key"
              />
              <button
                onClick={() => fetchDashboardData()}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                Login
              </button>
            </div>
            {error && <p className="text-red-500 mt-2">{error}</p>}
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 p-6 flex items-center justify-center">
        <div className="text-xl font-medium">Loading dashboard data...</div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="min-h-screen bg-gray-100 p-6">
        <div className="max-w-4xl mx-auto bg-white rounded-lg shadow p-6">
          <h1 className="text-2xl font-bold mb-6">Admin Dashboard</h1>
          <div className="text-red-500">
            {error || "Failed to load dashboard data. Please try again."}
          </div>
          <button
            onClick={() => fetchDashboardData()}
            className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
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
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold">API Usage Dashboard</h1>
            <div className="text-sm text-gray-500">
              Last updated:{" "}
              {new Date(dashboardData.generated_at).toLocaleString()}
            </div>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-100">
              <h3 className="text-lg font-medium mb-2">Monthly Usage</h3>
              <div className="flex justify-between items-end">
                <div>
                  <div className="text-3xl font-bold">
                    {dashboardData.current_usage.total_queries}
                  </div>
                  <div className="text-sm text-gray-500">
                    queries this month
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-semibold">
                    ${dashboardData.current_usage.total_cost.toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-500">total cost</div>
                </div>
              </div>
            </div>

            <div className="bg-green-50 rounded-lg p-4 border border-green-100">
              <h3 className="text-lg font-medium mb-2">Quota</h3>
              <div className="flex justify-between items-end">
                <div>
                  <div className="text-3xl font-bold">
                    {dashboardData.quota.remaining}
                  </div>
                  <div className="text-sm text-gray-500">queries remaining</div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-semibold">
                    {dashboardData.quota.percentage_used}%
                  </div>
                  <div className="text-sm text-gray-500">quota used</div>
                </div>
              </div>

              {/* Simple CSS progress bar */}
              <div className="w-full bg-gray-200 rounded-full h-2.5 mt-2">
                <div
                  className="bg-green-600 h-2.5 rounded-full"
                  style={{ width: `${dashboardData.quota.percentage_used}%` }}
                ></div>
              </div>
            </div>

            <div className="bg-purple-50 rounded-lg p-4 border border-purple-100">
              <h3 className="text-lg font-medium mb-2">Projected Cost</h3>
              <div className="flex justify-between items-end">
                <div>
                  <div className="text-3xl font-bold">
                    ${dashboardData.projected_monthly_cost.toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-500">
                    projected this month
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-semibold">
                    ${dashboardData.cost_per_query.toFixed(4)}
                  </div>
                  <div className="text-sm text-gray-500">avg. per query</div>
                </div>
              </div>
            </div>
          </div>

          {/* Usage Charts - Daily Usage */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-4">Daily Usage</h2>
            <div className="h-80 w-full border rounded-lg p-4 bg-white">
              <div className="flex justify-between mb-2 text-sm text-gray-500">
                <div>Daily breakdown</div>
                <div className="flex gap-4">
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-indigo-500 rounded-full mr-1"></div>
                    <span>Queries</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-green-500 rounded-full mr-1"></div>
                    <span>Cost ($)</span>
                  </div>
                </div>
              </div>

              <div className="relative h-64 flex">
                {/* Y-axis labels */}
                <div className="w-12 h-full flex flex-col justify-between text-xs text-gray-500">
                  <div>Max</div>
                  <div>0</div>
                </div>

                {/* X-axis and bars */}
                <div className="flex-1 border-l border-b border-gray-200 relative">
                  {/* Horizontal grid lines */}
                  <div className="absolute w-full h-1/4 border-t border-gray-100"></div>
                  <div className="absolute w-full h-2/4 border-t border-gray-100"></div>
                  <div className="absolute w-full h-3/4 border-t border-gray-100"></div>

                  {/* Bars for daily data */}
                  <div className="absolute inset-0 flex items-end">
                    {dashboardData.current_usage.daily_breakdown.map(
                      (day, index) => (
                        <div
                          key={day.day}
                          className="flex-1 flex flex-col items-center"
                        >
                          {/* Query bar */}
                          <div
                            className="w-5 bg-indigo-500 mb-1"
                            style={{
                              height: `${(day.queries / maxQueries) * 100}%`,
                              opacity: day.queries === 0 ? 0 : 1,
                            }}
                          ></div>

                          {/* Cost bar */}
                          <div
                            className="w-5 bg-green-500 mb-1"
                            style={{
                              height: `${(day.cost / maxCost) * 100}%`,
                              opacity: day.cost === 0 ? 0 : 1,
                            }}
                          ></div>

                          {/* X-axis label */}
                          <div className="text-xs text-gray-500 mt-1 transform -rotate-45 origin-top-left">
                            {day.day.split("-")[2]}
                          </div>
                        </div>
                      )
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Token Usage */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-4">Token Usage</h2>
            <div className="h-80 w-full border rounded-lg p-4 bg-white">
              <div className="flex justify-between mb-2 text-sm text-gray-500">
                <div>Token Distribution</div>
                <div className="flex gap-4">
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-indigo-500 rounded-full mr-1"></div>
                    <span>Input Tokens</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-green-500 rounded-full mr-1"></div>
                    <span>Output Tokens</span>
                  </div>
                </div>
              </div>

              <div className="relative h-64">
                {/* Simple horizontal bar chart */}
                <div className="h-24 flex flex-col justify-around mt-8">
                  <div>
                    <div className="mb-1 text-sm">
                      Input Tokens: {dashboardData.current_usage.input_tokens}
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-6">
                      <div
                        className="bg-indigo-500 h-6 rounded-full px-2 text-white text-xs flex items-center"
                        style={{
                          width: `${(dashboardData.current_usage.input_tokens / (dashboardData.current_usage.input_tokens + dashboardData.current_usage.output_tokens)) * 100}%`,
                        }}
                      >
                        {Math.round(
                          (dashboardData.current_usage.input_tokens /
                            (dashboardData.current_usage.input_tokens +
                              dashboardData.current_usage.output_tokens)) *
                            100
                        )}
                        %
                      </div>
                    </div>
                  </div>

                  <div className="mt-4">
                    <div className="mb-1 text-sm">
                      Output Tokens: {dashboardData.current_usage.output_tokens}
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-6">
                      <div
                        className="bg-green-500 h-6 rounded-full px-2 text-white text-xs flex items-center"
                        style={{
                          width: `${(dashboardData.current_usage.output_tokens / (dashboardData.current_usage.input_tokens + dashboardData.current_usage.output_tokens)) * 100}%`,
                        }}
                      >
                        {Math.round(
                          (dashboardData.current_usage.output_tokens /
                            (dashboardData.current_usage.input_tokens +
                              dashboardData.current_usage.output_tokens)) *
                            100
                        )}
                        %
                      </div>
                    </div>
                  </div>
                </div>

                {/* Total tokens */}
                <div className="mt-6 text-center">
                  <div className="text-sm text-gray-500">Total Tokens</div>
                  <div className="text-2xl font-bold">
                    {dashboardData.current_usage.total_tokens}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Settings Section */}
          <div className="border-t pt-6 mt-6">
            <h2 className="text-xl font-semibold mb-4">Settings</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Quota Management */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-medium mb-3">
                  Monthly Query Quota
                </h3>
                <div className="flex items-end gap-4">
                  <div className="flex-grow">
                    <label className="block text-sm text-gray-500 mb-1">
                      Current limit: {dashboardData.quota.limit}
                    </label>
                    <input
                      type="number"
                      min="1"
                      defaultValue={dashboardData.quota.limit}
                      id="quotaInput"
                      className="border border-gray-300 rounded px-3 py-2 w-full"
                    />
                  </div>
                  <button
                    onClick={() => {
                      const input = document.getElementById(
                        "quotaInput"
                      ) as HTMLInputElement;
                      const value = parseInt(input.value);
                      if (value > 0) {
                        handleUpdateQuota(value);
                      }
                    }}
                    className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                  >
                    Update
                  </button>
                </div>
              </div>

              {/* Cost Thresholds */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-medium mb-3">Cost Thresholds</h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-gray-500 mb-1">
                      Per Query ($)
                    </label>
                    <input
                      type="number"
                      min="0.01"
                      step="0.01"
                      defaultValue={dashboardData.thresholds.per_query}
                      id="perQueryThreshold"
                      className="border border-gray-300 rounded px-3 py-2 w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-500 mb-1">
                      Daily ($)
                    </label>
                    <input
                      type="number"
                      min="0.1"
                      step="0.1"
                      defaultValue={dashboardData.thresholds.daily}
                      id="dailyThreshold"
                      className="border border-gray-300 rounded px-3 py-2 w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-500 mb-1">
                      Monthly ($)
                    </label>
                    <input
                      type="number"
                      min="1"
                      step="1"
                      defaultValue={dashboardData.thresholds.monthly}
                      id="monthlyThreshold"
                      className="border border-gray-300 rounded px-3 py-2 w-full"
                    />
                  </div>
                  <button
                    onClick={() => {
                      const perQuery = parseFloat(
                        (
                          document.getElementById(
                            "perQueryThreshold"
                          ) as HTMLInputElement
                        ).value
                      );
                      const daily = parseFloat(
                        (
                          document.getElementById(
                            "dailyThreshold"
                          ) as HTMLInputElement
                        ).value
                      );
                      const monthly = parseFloat(
                        (
                          document.getElementById(
                            "monthlyThreshold"
                          ) as HTMLInputElement
                        ).value
                      );

                      handleUpdateThresholds({
                        per_query: perQuery,
                        daily: daily,
                        monthly: monthly,
                      });
                    }}
                    className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 w-full"
                  >
                    Update Thresholds
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
