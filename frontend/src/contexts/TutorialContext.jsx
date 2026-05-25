import React, { createContext, useContext, useState, useCallback } from "react";

const STORAGE_KEY = "dnd_tutorial_dismissed";

const TutorialContext = createContext(null);

export function TutorialProvider({ children }) {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);

  const openTutorial = useCallback((fromStep = 0) => {
    setStep(fromStep);
    setOpen(true);
  }, []);

  const closeTutorial = useCallback((permanent = false) => {
    setOpen(false);
    if (permanent) localStorage.setItem(STORAGE_KEY, "1");
  }, []);

  const hasSeenTutorial = () => !!localStorage.getItem(STORAGE_KEY);

  return (
    <TutorialContext.Provider value={{ open, step, setStep, openTutorial, closeTutorial, hasSeenTutorial }}>
      {children}
    </TutorialContext.Provider>
  );
}

export function useTutorial() {
  return useContext(TutorialContext);
}
