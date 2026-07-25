import routePlanning from "@/assets/route-planning.svg";

export function EmptyState() {
  return (
    <div className="empty-map" aria-label="Route planning preview">
      <img src={routePlanning} alt="" />
      <p>Your route and planned rests will appear here.</p>
    </div>
  );
}
