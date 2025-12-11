export const buildCharacterPayload = (state) => {
  return {
    identity: {
      name: state.identity?.name || "",
      sex: state.identity?.sex || "",
      age: state.identity?.age ?? null,
      appearanceExpression: state.identity?.appearanceExpression ?? 50,
    },
    race: {
      key: state.race?.key || "",
      variantKey: state.race?.variantKey || "",
    },
    class: {
      key: state.class?.key || "",
      subclassKey: state.class?.subclassKey || "",
      level: state.class?.level ?? 1,
      skillProficiencies: state.class?.skillProficiencies || [],
    },
    abilityScores: {
      method: state.abilityScores?.method || "standard_array",
      str: state.abilityScores?.str ?? null,
      dex: state.abilityScores?.dex ?? null,
      con: state.abilityScores?.con ?? null,
      int: state.abilityScores?.int ?? null,
      wis: state.abilityScores?.wis ?? null,
      cha: state.abilityScores?.cha ?? null,
    },
    background: {
      key: state.background?.key || "",
      variantKey: state.background?.variantKey || "",
    },
    appearance: {
      ageCategory: state.appearance?.ageCategory || "",
      heightCm: state.appearance?.heightCm ?? null,
      build: state.appearance?.build || "",
      skinTone: state.appearance?.skinTone || "",
      hairColor: state.appearance?.hairColor || "",
      eyeColor: state.appearance?.eyeColor || "",
      notableFeatures: state.appearance?.notableFeatures || [],
    },
    review: state.review || {},
  };
};
