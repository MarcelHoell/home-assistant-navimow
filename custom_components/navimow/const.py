"""Constants for the Segway Navimow integration."""

DOMAIN = "navimow"

# OAuth Configuration
CLIENT_ID = "homeassistant"
CLIENT_SECRET = "57056e15-722e-42be-bbaa-b0cbfb208a52"
TOKEN_URL = "https://navimow-fra.ninebot.com/openapi/oauth/getAccessToken"
AUTH_BASE_URL = "https://navimow-h5-fra.willand.com/smartHome/login"


def is_online(device_status: dict | None) -> bool:
    """Whether the mower is reachable. Empty status means the API told us nothing."""
    if not device_status:
        return False
    if not device_status.get("online", True):
        return False
    return str(device_status.get("vehicleState", "")).lower() != "offline"