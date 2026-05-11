# Test Credentials

No authentication / login is required by this D&D app — all endpoints are
campaign-scoped via path params.

## Existing test data
- Campaign ID: `29feef57-a81d-4799-a988-88d644406acc`
- Character ID: `69fc667f579c1db376ac58db`
- The campaign has active storylines and an existing knowledge deck for
  end-to-end testing of DM feedback, lessons, reactions, and storyline
  resolution flows.

## API keys
- `EMERGENT_LLM_KEY` (in `backend/.env`) powers all OpenAI / Gemini calls
  used by the DM, storyline judge, pitch grader, NPC sheet generator, and
  the new DM Lesson distiller.
- TTS (OpenAI TTS) requires a separate `OPENAI_API_KEY` — currently absent.
