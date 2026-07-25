import { Printer } from "lucide-react";

import { Button } from "@/components/ui/button";

export function PrintToolbar() {
  return (
    <div className="print-toolbar">
      <div>
        <p className="eyebrow">Daily records</p>
        <h2>Review every day, then print or save as PDF.</h2>
      </div>
      <Button type="button" onClick={() => window.print()}>
        <Printer aria-hidden="true" size={16} />
        Print / Save PDF
      </Button>
    </div>
  );
}
