#!/usr/bin/env python3
"""
Quick test to verify MODE_LIMITS are correctly imported and accessible
"""
import sys
sys.path.insert(0, '/app/backend')

from routers.dungeon_forge import MODE_LIMITS

print("=" * 60)
print("MODE_LIMITS Configuration Test")
print("=" * 60)

expected_modes = ["intro", "exploration", "social", "combat", "downtime", "travel", "rest"]

print("\nVerifying MODE_LIMITS dictionary:")
print(f"✓ MODE_LIMITS exists: {MODE_LIMITS is not None}")
print(f"✓ MODE_LIMITS is dict: {isinstance(MODE_LIMITS, dict)}")
print(f"✓ Number of modes: {len(MODE_LIMITS)}")

print("\nMode configurations:")
for mode in expected_modes:
    if mode in MODE_LIMITS:
        limits = MODE_LIMITS[mode]
        print(f"  ✓ {mode:12s} - min: {limits['min']:2d}, max: {limits['max']:2d}")
    else:
        print(f"  ✗ {mode:12s} - MISSING!")

print("\nv6.1 Compliance Check:")
v61_spec = {
    "intro": {"min": 12, "max": 16},
    "exploration": {"min": 6, "max": 10},
    "social": {"min": 6, "max": 10},
    "combat": {"min": 4, "max": 8},
    "downtime": {"min": 4, "max": 8},
}

all_match = True
for mode, expected in v61_spec.items():
    actual = MODE_LIMITS.get(mode, {})
    matches = actual == expected
    all_match = all_match and matches
    status = "✓" if matches else "✗"
    print(f"  {status} {mode:12s} - {'MATCH' if matches else 'MISMATCH'}")

print("\n" + "=" * 60)
if all_match:
    print("✅ SUCCESS: All MODE_LIMITS match v6.1 specification")
else:
    print("❌ FAILURE: Some MODE_LIMITS don't match v6.1 specification")
print("=" * 60)
