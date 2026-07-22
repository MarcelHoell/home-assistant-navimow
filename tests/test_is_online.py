"""Run: python tests/test_is_online.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "navimow"))
from const import is_online  # noqa: E402

assert is_online({"vehicleState": "isDocked"}) is True
assert is_online({"vehicleState": "isRunning", "online": True}) is True
assert is_online({"vehicleState": "offline"}) is False
assert is_online({"vehicleState": "Offline"}) is False  # Segway sends both cases
assert is_online({"vehicleState": "isDocked", "online": False}) is False
assert is_online({}) is False  # device missing from the API payload
assert is_online(None) is False

print("ok")
