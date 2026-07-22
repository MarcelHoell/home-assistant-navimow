"""Constants for the Segway Navimow integration."""

DOMAIN = "navimow"

# OAuth Configuration
CLIENT_ID = "homeassistant"
CLIENT_SECRET = "57056e15-722e-42be-bbaa-b0cbfb208a52"
TOKEN_URL = "https://navimow-fra.ninebot.com/openapi/oauth/getAccessToken"
AUTH_BASE_URL = "https://navimow-h5-fra.willand.com/smartHome/login"


# Raw vehicleState values that mean "the mower is not powered on".
#
# "isIdel" is Segway's typo for idle, but measured against a live account it is
# what the API reports for a switched-off mower, appearing within one or two
# 30s polls. It was never once observed while the mower was demonstrably on
# (~4h of logs across three sessions). The correctly spelled "isIdle" has never
# been seen at all and is deliberately not listed — if Segway ever fixes the
# typo, this set needs revisiting.
#
# Cutting power to the charging station is invisible to the API and does not
# show up here.
OFFLINE_RAW_STATES = {"offline", "isidel"}


def is_online(device_status: dict | None) -> bool:
    """Whether the mower is powered on. Empty status means it dropped out of the payload."""
    if not device_status:
        return False
    if not device_status.get("online", True):  # never seen in the wild, kept as a guard
        return False
    return str(device_status.get("vehicleState", "")).lower() not in OFFLINE_RAW_STATES