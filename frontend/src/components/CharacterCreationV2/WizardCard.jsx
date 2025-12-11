import React from "react";
import WizardHeader from "./WizardHeader";

const WizardCard = ({
  stepTitle,
  stepNumber,
  totalSteps,
  children,
  onBack,
  onNext,
  backDisabled = false,
  nextDisabled = false,
  nextLabel = "Next",
  steps = [],
  onSelectStep,
}) => {
  const totalStepsCount = totalSteps ?? steps.length;
  const safeStepNumber = Math.min(Math.max(stepNumber ?? 1, 1), totalStepsCount || 1);
  const currentStepIndex = safeStepNumber - 1;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 shadow-2xl backdrop-blur">
        <WizardHeader
          steps={steps}
          currentStepIndex={currentStepIndex}
          onSelectStep={onSelectStep}
        />

        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400">
              Step {safeStepNumber} / {totalStepsCount}
            </p>
            <h2 className="text-2xl font-bold text-amber-400">{stepTitle}</h2>
          </div>
        </div>

        <div className="px-6 py-5 space-y-4">
          <div>{children}</div>
        </div>

        <div className="flex items-center justify-between border-t border-slate-800 px-6 py-4">
          <button
            type="button"
            onClick={onBack}
            disabled={backDisabled}
            className={`px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${
              backDisabled
                ? "border-slate-800 bg-slate-800/60 text-slate-600 cursor-not-allowed"
                : "border-slate-700 text-slate-200 hover:bg-slate-800"
            }`}
          >
            Back
          </button>
          <button
            type="button"
            onClick={onNext}
            disabled={nextDisabled}
            className={`px-5 py-2 rounded-lg text-sm font-semibold transition-colors ${
              nextDisabled
                ? "bg-slate-700 text-slate-400 cursor-not-allowed"
                : "bg-amber-500 text-black hover:bg-amber-400"
            }`}
          >
            {nextLabel}
          </button>
        </div>
      </div>
    </div>
  );
};

export default WizardCard;
