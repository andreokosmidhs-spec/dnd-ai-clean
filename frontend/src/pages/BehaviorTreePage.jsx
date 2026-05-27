/**
 * BehaviorTreePage.jsx
 * Standalone route page for the Behavior Tree Editor.
 * Route: /behavior-trees
 */
import React from "react";
import { useNavigate } from "react-router-dom";
import BehaviorTreeEditor from "../components/BehaviorTreeEditor";

export default function BehaviorTreePage() {
  const navigate = useNavigate();
  return (
    <BehaviorTreeEditor onBack={() => navigate(-1)} />
  );
}
