import React from "react";
import { Crown } from "lucide-react";
import { Badge } from "../ui/badge";

const WizardHeader = ({ steps, currentStepIndex = 0, onSelectStep }) => {
  const safeCurrentIndex = Math.min(
    Math.max(currentStepIndex, 0),
    Math.max(steps.length - 1, 0)
  );

  return (
    <div className="bg-black/70 border-b border-slate-800 px-6 py-5">
      <div className="flex flex-col items-center text-center space-y-3">
        <div className="flex items-center justify-center gap-2">
          <Crown className="h-7 w-7 text-amber-400" />
          <h2 className="text-2xl md:text-3xl font-bold text-amber-400">Character Creation</h2>
          <Crown className="h-7 w-7 text-amber-400" />
        </div>
        <div className="flex flex-wrap justify-center gap-2">
          {steps.map((step, idx) => {
            const isActive = idx === safeCurrentIndex;
            const isComplete = Boolean(step.isComplete);
            const isLocked = step.isLocked && !isActive && !isComplete;
            const state = isComplete ? "complete" : isActive ? "active" : "upcoming";
            const clickable = onSelectStep && (isComplete || isActive) && !isLocked;
            const handleClick = () => {
              if (clickable) onSelectStep(idx);
            };
            return (
              <button
                key={step.id}
                type="button"
                onClick={handleClick}
                disabled={!clickable}
                className={`focus:outline-none ${clickable ? "" : "cursor-default"}`}
              >
                <Badge
                  variant={isActive ? "default" : "outline"}
                  className={`${
                    state === "active"
                      ? "bg-amber-600 text-black shadow-md"
                      : state === "complete"
                        ? "border-amber-500/70 bg-amber-500/10 text-amber-200"
                        : "border-slate-700 text-slate-300"
                  } flex items-center gap-2 rounded-full px-3 py-1`}
                >
                  <span
                    className={`flex h-6 w-6 items-center justify-center rounded-full border ${
                      state === "active"
                        ? "border-amber-200 bg-amber-100/80 text-amber-800"
                        : state === "complete"
                          ? "border-amber-500 bg-amber-500/20 text-amber-200"
                          : "border-slate-600 bg-slate-800 text-slate-300"
                    }`}
                  >
                    {isComplete ? "✓" : idx + 1}
                  </span>
                  <span className="font-semibold">{step.label}</span>
                </Badge>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default WizardHeader;
