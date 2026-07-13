import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-gradient-to-b from-amber-50 to-white">
      <div className="text-center max-w-xl">
        <div className="flex items-center justify-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-600 shadow-lg">
            <svg className="h-7 w-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0 1 12 15a9.065 9.065 0 0 0-6.23.693L5 14.5m14.8.8 1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0 1 12 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
            </svg>
          </div>
          <h1 className="text-5xl font-bold tracking-tight text-brand-600">RealtyAI</h1>
        </div>
        <p className="mt-4 text-lg text-gray-600">AI Operating System for Real Estate Agents</p>
        <div className="mt-8 p-6 bg-white rounded-lg shadow-sm border border-gray-200 text-left">
          <p className="text-sm text-gray-500 font-medium">Good morning, Sarah</p>
          <div className="mt-3 space-y-1 text-sm text-gray-700">
            <p>You have:</p>
            <p>• 3 new leads</p>
            <p>• 2 follow-ups due</p>
            <p>• 1 listing expiring soon</p>
            <p>• 5 unread client messages</p>
          </div>
        </div>
        <Link
          href="/dashboard"
          className="mt-6 inline-flex items-center gap-2 rounded-lg bg-brand-600 px-6 py-3 text-sm font-medium text-white shadow-sm transition-colors hover:bg-brand-700"
        >
          Go to Dashboard
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
          </svg>
        </Link>
      </div>
    </main>
  );
}
