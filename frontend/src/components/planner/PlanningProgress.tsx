import { domAnimation, LazyMotion, m } from "motion/react";

const STAGES = [
  "Locating the truck route",
  "Calculating duty limits",
  "Building daily logs",
] as const;

export function PlanningProgress({ stage }: { stage: number }) {
  return (
    <LazyMotion features={domAnimation} strict>
      <div className="planning-progress" role="status" aria-live="polite">
        <m.div
          key={stage}
          initial={{ opacity: 0, filter: "blur(6px)", y: 4 }}
          animate={{ opacity: 1, filter: "blur(0)", y: 0 }}
          transition={{ duration: 0.2 }}
        >
          <span>{String(stage + 1).padStart(2, "0")} / 03</span>
          <strong>{STAGES[stage]}</strong>
        </m.div>
      </div>
    </LazyMotion>
  );
}
