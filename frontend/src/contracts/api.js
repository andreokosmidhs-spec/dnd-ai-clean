/**
 * API Contracts - TypeScript interfaces for backend communication
 * 
 * All API responses follow the normalized envelope:
 * - Success: {success: true, data: T, error: null}
 * - Error: {success: false, data: null, error: {type, message, details}}
 */

// ============================================================================
// Generic API Response Types
// ============================================================================

export interface ApiError {
  type: string;
  message: string;
  details?: Record<string, any>;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: ApiError | null;
}

// ============================================================================
// Domain Entity Types
// ============================================================================

export interface CharacterStats {
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
}

export interface CharacterState {
  name: string;
  race: string;
  class: string;
  background: string;
  goal?: string;
  level: number;
  hp: number;
  max_hp: number;
  ac: number;
  abilities: {
    str: number;
    dex: number;
    con: number;
    int: number;
    wis: number;
    cha: number;
  };
  proficiencies: string[];
  languages: string[];
  inventory: any[];
  features: string[];
  conditions: string[];
  reputation: Record<string, any>;
  current_xp?: number;
  xp_to_next?: number;
  proficiency_bonus?: number;
  attack_bonus?: number;
  injury_count?: number;
}

export interface WorldBlueprint {
  world_core: {
    name: string;
    tone: string;
    central_conflict?: string;
  };
  starting_town?: {
    name: string;
    summary: string;
    population?: number;
  };
  regions?: any[];
  factions?: any[];
  threats?: any[];
}

export interface WorldState {
  location?: string;
  current_location?: string;
  time_of_day?: string;
  weather?: string;
  active_npcs?: any[];
  faction_states?: Record<string, any>;
  quest_flags?: Record<string, any>;
}

export interface Campaign {
  campaign_id: string;
  world_name: string;
  world_blueprint: WorldBlueprint;
  intro?: string;
  created_at: string;
  updated_at: string;
}

export interface Character {
  character_id: string;
  campaign_id: string;
  character_state: CharacterState;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// API Request Types
// ============================================================================

export interface WorldBlueprintRequest {
  world_name: string;
  tone: string;
  starting_region_hint: string;
  campaign_id?: string;
}

export interface CharacterCreateRequest {
  campaign_id: string;
  character: Partial<CharacterState> & {
    stats?: CharacterStats;
    hitPoints?: number;
    aspiration?: {
      goal?: string;
    };
    racial_traits?: any[];
  };
}

export interface ActionRequest {
  campaign_id: string;
  character_id: string;
  action: string;
  check_result?: number;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface WorldBlueprintResponse {
  campaign_id: string;
  world_blueprint: WorldBlueprint;
  world_state: WorldState;
}

export interface CharacterCreateResponse {
  character_id: string;
  character_state: CharacterState;
  intro_markdown?: string;
  starting_location?: string;
}

export interface CampaignLatestResponse {
  campaign_id: string;
  world_blueprint: WorldBlueprint;
  intro: string;
  character: CharacterState;
  character_id: string;
  world_state: WorldState;
}

export interface ActionResponse {
  narration: string;
  options: string[];
  check_request?: {
    ability: string;
    dc: number;
  };
  world_state_update?: Partial<WorldState>;
  player_updates?: {
    xp_gained?: number;
    xp_reason?: string;
    level_up_events?: any[];
  };
  combat_started?: boolean;
}

// ============================================================================
// Typed API Response Wrappers
// ============================================================================

export type WorldBlueprintApiResponse = ApiResponse<WorldBlueprintResponse>;
export type CharacterCreateApiResponse = ApiResponse<CharacterCreateResponse>;
export type CampaignLatestApiResponse = ApiResponse<CampaignLatestResponse>;
export type ActionApiResponse = ApiResponse<ActionResponse>;
