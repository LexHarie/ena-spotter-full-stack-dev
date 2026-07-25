import routePlanning from "@/assets/route-planning.svg";

export function App() {
  return (
    <main className="min-h-screen bg-paper text-ink">
      <header className="flex items-center justify-between border-b border-line px-6 py-4">
        <a className="font-satoshi text-sm tracking-tight" href="/">
          <span className="mr-2 inline-block size-3 rounded-route bg-amber" />
          ROUTELOG
        </a>
        <p className="font-erode text-sm text-muted">
          FMCSA-aware trip planning
        </p>
      </header>
      <section className="opening-grid">
        <div className="opening-copy">
          <p className="eyebrow">Plan your run</p>
          <h1>A clear road ahead.</h1>
          <p>
            Build a truck route, place required stops, and generate a daily duty
            log for every day of the trip.
          </p>
        </div>
        <div className="empty-map" aria-label="Route planning preview">
          <img src={routePlanning} alt="" />
          <p>Your route and planned rests will appear here.</p>
        </div>
      </section>
    </main>
  );
}
