"use client";

import Cal, { getCalApi } from "@calcom/embed-react";
import { useEffect } from "react";

export default function BookDemoPage() {
  useEffect(() => {
    (async function () {
      const cal = await getCalApi({ namespace: "30min" });
      cal("ui", { hideEventTypeDetails: false, layout: "month_view" });
    })();
  }, []);

  return (
    <div className="container mx-auto px-4 max-w-7xl">
      {/* Header Section */}
      <section className="text-center py-10">
        <h1 className="text-4xl text-gray-800 font-bold mb-5">Book a Demo</h1>
        <p className="text-lg text-gray-600 max-w-3xl mx-auto mb-8">
          Schedule a personalized demo to see how Prae8 can transform your legal
          research process
        </p>
      </section>

      {/* Calendar Section */}
      <section className="border border-gray-200 rounded-xl overflow-hidden my-10">
        <div className="p-8">
          <div className="h-[600px]">
            <Cal
              namespace="30min"
              calLink="manonjacquin/30min"
              style={{ width: "100%", height: "100%", overflow: "scroll" }}
              config={{ layout: "month_view" }}
            />
          </div>
        </div>
      </section>
    </div>
  );
}
