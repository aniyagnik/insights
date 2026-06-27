export default function Home() {
  return (
    <main className="flex flex-col items-center justify-center min-h-screen p-6 text-center">
      <div className="max-w-xl p-8 bg-white rounded-xl shadow-md border border-slate-100">
        <h1 className="text-3xl font-extrabold text-indigo-600 mb-4">
          Analytics & Reporting Platform
        </h1>
        <p className="text-slate-600 mb-6 leading-relaxed">
          App Router initialization is complete. 
          Ready to configure auth states, dynamic Recharts widgets, and ingestion portals.
        </p>
        <div className="inline-flex items-center px-4 py-1.5 text-sm font-semibold text-indigo-700 bg-indigo-50 rounded-full">
          Status: Ready for Frontend Development
        </div>
      </div>
    </main>
  );
}