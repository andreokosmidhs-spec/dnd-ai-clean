import React from "react";
import { Crown } from "lucide-react";
import { Badge } from "../ui/badge";

const WizardHeader = ({ steps, currentStepIndex = 0 }) => {
  const safeCurrentIndex = Math.min(
    Math.max(currentStepIndex, 0),
    Math.max(steps.length - 1, 0)
  );

  return (
    <div className="bg-black/70 border-b border-slate-800 px-6 py-5">
      <div className="flex flex-col items-center text-center space-y-3">
        <div className="flex items-center justify-center gap-2">
          <Crown className="h-7 w-7 text-amber-400" />
          <h2 className="text-2xl md:text-3xl font-bold text-amber-400">
            Character Creation
          </h2>
          <Crown className="h-7 w-7 text-amber-400" />
        </div>
        <div className="flex flex-wrap justify-center gap-2">
          {steps.map((step, idx) => {
            const isActive = idx === safeCurrentIndex;
            return (
              <Badge
                key={step.id}
                variant={isActive ? "default" : "outline"}
                className={
                  isActive
                    ? "bg-amber-600 text-black shadow-md"
                    : "border-amber-600/50 text-amber-300"
                }
              >
                {step.label}
              </Badge>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default WizardHeader;
