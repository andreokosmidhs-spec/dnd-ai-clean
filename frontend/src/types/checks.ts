/**
 * TypeScript types for the DC (Difficulty Class) check system
 * Mirrors backend models from /app/backend/models/check_models.py
 */

export type DifficultyBand = 
  | 'trivial'
  | 'easy'
  | 'moderate'
  | 'hard'
  | 'very_hard'
  | 'nearly_impossible';

export type AdvantageState = 'normal' | 'advantage' | 'disadvantage';

export type CheckOutcome =
  | 'critical_success'
  | 'clear_success'
  | 'marginal_success'
  | 'marginal_failure'
  | 'clear_failure'
  | 'critical_failure';

export interface CheckRequest {
  ability: string;
  skill: string | null;
  dc: number;
  dc_band: DifficultyBand;
  advantage_state: AdvantageState;
  reason: string;
  action_context: string;
  opposed_check?: boolean;
  group_check?: boolean;
  dc_reasoning?: string;
}

export interface PlayerRoll {
  d20_roll: number;
  modifier: number;
  total: number;
  advantage_state: AdvantageState;
  advantage_rolls: number[] | null;
  ability_modifier: number;
  proficiency_bonus: number;
  other_bonuses: number;
}

export interface CheckResolution {
  success: boolean;
  outcome: CheckOutcome;
  margin: number;
  check_request: CheckRequest;
  player_roll: PlayerRoll;
  outcome_tier: 'critical' | 'clear' | 'marginal';
  suggested_narration_style: string;
}

export interface Character {
  name: string;
  race: string;
  class: string;
  level: number;
  stats: {
    strength: number;
    dexterity: number;
    constitution: number;
    intelligence: number;
    wisdom: number;
    charisma: number;
  };
  skills?: string[];
  hp?: number;
  max_hp?: number;
}
