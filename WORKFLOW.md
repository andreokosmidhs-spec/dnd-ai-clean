# Development Workflow (Codex · GitHub · Emergent)

Στόχος: σταθερό, επαναλήψιμο workflow ανάμεσα σε **Codex**, **GitHub** και **Emergent**, χωρίς να σπάει το build.

---

## 1. Ποιος κάνει τι

- **GitHub (`main`)**  
  Είναι ΠΑΝΤΑ το *single source of truth*. Όλες οι αλλαγές περνάνε από PR.

- **Codex**  
  Αυτόματος dev agent που:
  - γράφει/αλλάζει κώδικα,
  - ανοίγει branches & PRs,
  - τρέχει `npm run build` στο repo.

- **Emergent**  
  ΜΟΝΟ για:
  - sync του κώδικα (pull από `origin/main`),
  - build / preview.  
  ΌΧΙ για μόνιμες αλλαγές κώδικα ή commits.

---

## 2. Όταν θέλω μια αλλαγή

1. **Ορίζω μικρό task** (μία συγκεκριμένη αλλαγή / bugfix).
2. **Ανοίγω Codex task** και του δίνω:
   - Περιγραφή του τι θέλω.
   - Όνομα branch π.χ. `codex/<short-description>`.
   - Ποια αρχεία επιτρέπεται να αλλάξει.

   Παράδειγμα:

   ```text
   Task: Fix JSX structure in ReviewStep.jsx so build passes.

   Branch: codex/fix-jsx-structure-in-reviewstep

   Files you may edit:
   - frontend/src/components/CharacterCreationV2/ReviewStep.jsx

   Do NOT touch any backend files.
   Run npm run build in the repo before you say the task is done.
