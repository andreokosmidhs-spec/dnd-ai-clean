import React from "react";

const IdentityStep = ({ identity, onChange, onNext }) => {

  const handleGenderExpression = (e) => {
    onChange({ genderExpression: Number(e.target.value) });
  };

  const canContinue = identity.name.trim().length > 0;

  return (
    <div className="p-4">
      {/* Name input */}
      <div className="mb-4">
        <label className="block text-white text-sm">Name</label>
        <input
          type="text"
          value={identity.name}
          onChange={(e) => onChange({ name: e.target.value })}
          className="w-full p-2 rounded bg-gray-800 text-white"
        />
      </div>

      {/* Sex selector */}
      <div className="mb-4">
        <label className="block text-white text-sm">Sex</label>
        <select
          value={identity.sex}
          onChange={(e) => onChange({ sex: e.target.value })}
          className="p-2 rounded bg-gray-800 text-white"
        >
          <option value="male">Male</option>
          <option value="female">Female</option>
          <option value="unspecified">Unspecified</option>
        </select>
      </div>

      {/* Gender Expression Slider */}
      <div className="mb-4">
        <label className="block text-white text-sm">
          Gender Expression ({identity.genderExpression})
        </label>
        <input
          type="range"
          min="0"
          max="100"
          value={identity.genderExpression}
          onChange={handleGenderExpression}
          className="w-full"
        />
      </div>

      {/* Next button */}
      <div className="text-right">
        <button
          disabled={!canContinue}
          onClick={onNext}
          className={
            "px-4 py-2 rounded text-sm font-semibold " +
            (canContinue
              ? "bg-amber-500 hover:bg-amber-600 text-black"
              : "bg-gray-700 cursor-not-allowed text-gray-500")
          }
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default IdentityStep;
