# Some of this is AI so I can skip the long research into the SOAP API for CUCM
# to find all of the required fields.  Some of this is my own code to flush out
# some logic.

import urllib3
import asyncio
import datetime
import requests

def githubImport(user, repo, module):
    data = {}
    url = 'https://raw.githubusercontent.com/{}/{}/master/{}.py'.format(
        user,
        repo,
        module
    )

    r = requests.get(url).text
    exec(r, data)

githubImport('casnix', 'CucmAXL', 'CucmAXL')

# Suppress SSL warnings (use proper certs in production)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Configuration ─────────────────────────────────────────────────────────────

CUCM_HOST     = "192.168.1.10"          # Your CUCM publisher IP or hostname
CUCM_VERSION  = "14.0"                  # AXL schema version (match your CUCM)
AXL_USERNAME  = "axladmin"
AXL_PASSWORD  = "yourpassword"

WSDL_PATH     = f"schema/AXLAPI.wsdl"   # Download from CUCM: /plugins/axlsqltoolkit.zip
AXL_URL       = f"https://{CUCM_HOST}:8443/axl/"

# ── Phone / Line Settings ─────────────────────────────────────────────────────

PHONE_CONFIG = {
    "name":          "SEP001122334455",   # Must match MAC: SEP + MAC (uppercase, no colons)
    "description":   "John Doe - Desk",
    "product":       "Cisco 8861",        # Product model name (exactly as in CUCM)
    "model":         "Cisco 8861",
    "class":         "Phone",
    "protocol":      "SIP",
    "protocolSide":  "User",
    "devicePoolName":         "Default",
    "locationName":           "Hub_None",
    "commonPhoneConfigName":  "Standard Common Phone Profile",
    "phoneTemplateName":      "Standard 8861 SIP",
    "useTrustedRelayPoint":   "Default",
    "builtInBridgeStatus":    "Default",
    "packetCaptureMode":      "None",
    "certificateOperation":   "No Pending Operation",
    "deviceMobilityMode":     "Default",
}

LINE_CONFIG = {
    "pattern":          "1001",          # Extension / DN
    "routePartitionName": "Internal_PT", # Partition (or None for <None>)
    "description":      "John Doe",
    "alertingName":     "John Doe",
    "asciiAlertingName": "John Doe",
    "voiceMailProfileName": "NoVoiceMail",
    "shareLineAppearanceCssName": None,
}

LINE_APPEARANCE = {                      # How the line appears on the phone button
    "index":         1,
    "label":         "John Doe",
    "display":       "John Doe",
    "displayAscii":  "John Doe",
    "e164Mask":      None,
    "maxNumCalls":   2,
    "busyTrigger":   1,
}




# ── Helper: Add or Get DN ─────────────────────────────────────────────────────

def add_line(service):
    """Add a Directory Number (DN/extension). Skips if it already exists."""
    try:
        result = service.addLine(line={
            "pattern":              LINE_CONFIG["pattern"],
            "routePartitionName":   LINE_CONFIG["routePartitionName"],
            "description":          LINE_CONFIG["description"],
            "alertingName":         LINE_CONFIG["alertingName"],
            "asciiAlertingName":    LINE_CONFIG["asciiAlertingName"],
            "voiceMailProfileName": LINE_CONFIG["voiceMailProfileName"],
        })
        print(f"[✓] Added DN: {LINE_CONFIG['pattern']}")
        return result
    except Exception as e:
        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
            print(f"[~] DN {LINE_CONFIG['pattern']} already exists — will reuse it.")
        else:
            raise


# ── Helper: Add Phone ─────────────────────────────────────────────────────────

def add_phone(service):
    """Add a phone and associate the line in one call."""

    lines_payload = {
        "line": [
            {
                "index":          LINE_APPEARANCE["index"],
                "label":          LINE_APPEARANCE["label"],
                "display":        LINE_APPEARANCE["display"],
                "displayAscii":   LINE_APPEARANCE["displayAscii"],
                "e164Mask":       LINE_APPEARANCE["e164Mask"],
                "maxNumCalls":    LINE_APPEARANCE["maxNumCalls"],
                "busyTrigger":    LINE_APPEARANCE["busyTrigger"],
                "dirn": {
                    "pattern":            LINE_CONFIG["pattern"],
                    "routePartitionName": LINE_CONFIG["routePartitionName"],
                },
            }
        ]
    }

    phone_payload = {**PHONE_CONFIG, "lines": lines_payload}

    result = service.addPhone(phone=phone_payload)
    print(f"[✓] Added phone: {PHONE_CONFIG['name']}")
    print(f"    UUID: {result['return']}")
    return result


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Connecting to CUCM AXL API...")
    service, history = get_axl_client()

    # Step 1: Ensure the DN exists
    add_line(service)

    # Step 2: Add the phone with the line assigned
    add_phone(service)

    print("\nDone! The phone has been added and the extension assigned.")


if __name__ == "__main__":
    main()