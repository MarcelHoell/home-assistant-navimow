"""Self-checks that run without Home Assistant installed.

Run: python3 tests/test_navimow.py
"""
import ast
import sys
from pathlib import Path

COMPONENT = Path(__file__).resolve().parents[1] / "custom_components" / "navimow"
sys.path.insert(0, str(COMPONENT))

from const import is_online  # noqa: E402

# --- reachability ----------------------------------------------------------
assert is_online({"vehicleState": "isDocked"}) is True
assert is_online({"vehicleState": "isRunning", "online": True}) is True
assert is_online({"vehicleState": "offline"}) is False
assert is_online({"vehicleState": "Offline"}) is False  # Segway sends both cases
assert is_online({"vehicleState": "isDocked", "online": False}) is False
assert is_online({}) is False  # device missing from the API payload
assert is_online(None) is False


# --- state tables stay in sync --------------------------------------------
# lawn_mower.py imports Home Assistant, so read the dicts out of the source
# instead of importing the module.
def _dict_literal(name: str) -> dict:
    tree = ast.parse((COMPONENT / "lawn_mower.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and node.targets[0].id == name:
            keys = [ast.literal_eval(k) for k in node.value.keys]
            values = [
                v.attr if isinstance(v, ast.Attribute) else ast.literal_eval(v)
                for v in node.value.values
            ]
            return dict(zip(keys, values))
    raise AssertionError(f"{name} not found in lawn_mower.py")


raw_to_canonical = _dict_literal("RAW_STATE_TO_CANONICAL")
canonical_to_activity = _dict_literal("CANONICAL_TO_ACTIVITY")

unmapped = {
    canonical
    for canonical in raw_to_canonical.values()
    if canonical != "unknown" and canonical not in canonical_to_activity
}
assert not unmapped, f"canonical states without a LawnMowerActivity: {sorted(unmapped)}"

# Every error-ish raw state the sensor knows must also be an error for the mower
error_states = next(
    ast.literal_eval(node.value)
    for node in ast.parse((COMPONENT / "sensor.py").read_text()).body
    if isinstance(node, ast.Assign) and node.targets[0].id == "_ERROR_RAW_STATES"
)
for raw in error_states:
    assert raw_to_canonical.get(raw) == "error", f"{raw!r} is an error in sensor.py only"

print("ok")
