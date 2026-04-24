import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6">
      <h1 className="text-6xl font-bold tracking-tight">VITAL</h1>
      <p className="mt-4 text-gray-400 max-w-xl text-center">
        Invisible guardian for warehouse workers. WiFi sensing + computer vision +
        environmental intelligence — detecting medical events in under 2 seconds.
      </p>
      <div className="mt-10 flex gap-4">
        <Link
          href="/dashboard"
          className="px-6 py-3 rounded-xl bg-white text-black font-semibold hover:bg-gray-200"
        >
          Supervisor dashboard
        </Link>
        <Link
          href="/worker"
          className="px-6 py-3 rounded-xl border border-gray-700 hover:border-gray-500"
        >
          Worker app
        </Link>
      </div>
    </main>
  );
}
