# buildphones.py
# Copyright Matt Rienzo (C) 2026
# Builds several phones in Cisco Unified Communications Manager (CUCM) based
# on a CSV.
#
# This version grabs CucmAXL from github; you can download that library direct
# and import it locally if needed.

import csv
import asyncio
import urllib3
import argparse
import datetime
import requests
import Namespace

# Import from github
def githubImport(user: str, repo: str, module: str):
    """
    Dynamicaly import a module from a remote github repo.

    THIS IS A SECURITY RISK AND IS UNSAFE. 
    PLEASE ONLY DO THIS IF YOU TRUST THE REMOTE REPO.
    THIS IS INCLUDED FOR DEMO PURPOSES; I RECOMMEND ADDING THE IMPORTED MODULES
    DIRECTLY ON YOUR LOCAL FILESYSTEM.
    """
    data = {}
    url: str = 'https://raw.githubusercontent.com/{}/{}/master/{}.py'.format(
        user,
        repo,
        module
    )

    print(f"[githubImport] Attempting to grab {module} for import from {url}")

    try:
        r = requests.get(url).text
        exec(r, data)
    except Exception as e:
        print(f"[githubimport] Failed to grab {module} from {url}.")
        print(f"[githubImport] Reason: {type(e).__name__}: {e}")

githubImport('casnix', 'CucmAXL', 'CucmAXL')

# Typehint classes imported from github
CucmAXL = classmethod

# Suppress SSL warnings (use proper certs in production)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def addPhones(ccm: CucmAXL, phones: list) -> None:
    """
    Iterate through `phones` and add a phone per each to CUCM.
    """
    for thisPhone in phones:
        ccm.addPhone(phone={**thisPhone})

def addLines(ccm: CucmAXL, lines: list) -> None:
    """
    Iterate through `lines` and add a line per each to CUCM.
    """
    for thisLine in lines:
        try:
            ccm.addLine(line = {**thisLine})
        except Exception as e:
            if (
                "already exists" in str(e).lower() \
                    or "duplicate" in str(e).lower()
            ):
                print(
                    f"[~] DN {thisLine['pattern']} already exists, "+
                      "will reuse it"
                )
            else:
                raise

def renderCSV(data: list) -> tuple[list, list]:
    """
    Separate the source table into two arrays of lists.
    The first array will have data relevant to the addPhone method referenced
     by the CucmAXL object in the main logic.
    The secod array will have data relevant to the addLine method referenced
     by the CucmAXL object in the main logic.
    """
    data.pop(0) # Remove table header

    _deviceConfig = []
    _lineConfig = []
    _lineAppearance = []
    for index in enumerate(data):
        _lineConfig.append({
            "pattern": data[index]["linePattern"],
            "routePartitionName": data[index]["routePartition"],
            "description": data[index]["description"],
            "alertingName": data[index]["alertingName"],
            "asciiAlertingName": data[index]["asciiAlertingName"],
            "voiceMailProfileName": data[index]["vmProfile"],
            "shareLineAppearanceCssName": data[index]["callingSearchSpace"]
        })

        _lineAppearance.append({
            "index": int(data[index]["index"]),
            "label": data[index]["label"],
            "display": data[index]["display"],
            "displayAscii": data[index]["displayAscii"],
            "e164Mask": data[index]["e164Mask"],
            "maxNumCalls": int(data[index]["maxNumCalls"]),
            "busyTrigger": int(data[index]["busyTrigger"]),
            "dirn": {
                "pattern": _lineConfig[index]["pattern"],
                "routePartitionName": _lineConfig[index]["routePartitionName"]
            }
        })

        _deviceConfig.append({
            "name": data[index]["devName"],
            "description": data[index]["desc"],
            "product": data[index]["devType"],
            "model": data[index]["devModel"],
            "class": data[index]["devClass"],
            "protocol": data[index]["protocol"],
            "protocolSide": data[index]["protocolSide"],
            "devicePoolName": data[index]["devicePool"],
            "locationName": data[index]["loc"],
            "commonPhoneConfigName": data[index]["commonConfig"],
            "phoneTemplateName": data[index]["phoneTemplate"],
            "useTrustedRelayPoint": data[index]["useRelay"],
            "builtInBridgeStatus": data[index]["bridgeStatus"],
            "packetCaptureMode": data[index]["packetCap"],
            "certificateOperation": data[index]["certOp"],
            "deviceMobilityMode": data[index]["devMobility"],
            "lines": {
                "line": [{**_lineAppearance}]
            }
        })

    return (_deviceConfig, _lineConfig)

def parseARGV() -> Namespace:
    """
    Glean CSV source from command line arguments.
    """
    parser = argparse.ArgumentParser()
    sourceArgs = ('-c', '--csv-file')
    sourceArgsOpts = {
        "help": 'Source CSV file to read phone and line table from.',
        "type": str,
        "default": "source.csv",
        "dest": 'sourceFile'
    }
    
    serverArgs = ('-t', '--server')
    serverArgsOpts = {
        "help": "Target CCM server",
        "type": str,
        "dest": 'ccmServer',
        "required": True
    }
    
    wsdlArgs = ('-x', '--wsdl-source')
    wsdlArgsOpts = {
        "help": 'Path to the WSDL file defining the API',
        "type": str,
        "default": "AXLAPI.wsdl",
        "dest": 'wsdlSource',
        "required": True
    }
    
    passwordArgs = ('-p', '--password')
    passwordArgsOpts = {
        "help": "Password for standard AXL user",
        "type": str,
        "dest": 'axlPassword',
        "required": True
    }

    userArgs = ('-u', '--user')
    userArgsOpts = {
        "help": "Username for standard AXL user",
        "type": str,
        "dest": 'axlUser',
        "required": True
    }

    parser.add_argument(*sourceArgs, **sourceArgsOpts)
    parser.add_argument(*serverArgs, **serverArgsOpts)
    parser.add_argument(*wsdlArgs, **wsdlArgsOpts)
    parser.add_argument(*passwordArgs, **passwordArgsOpts)
    parser.add_argument(*userArgs, **userArgsOpts)

    return parser.parse_args()

def main() -> None:
    """
    Application logic steps:
        1) Parse command line arguments
        2) Parse CSV into arrays of dicts
        3) Open a client to the CUCM server and build the phones
    """
    argv: Namespace = parseARGV()
    with open(argv.sourceFile, newline='') as f:
        reader = csv.DictReader(f)
        sourceData = list(reader)

    phoneConfigs: list[dict[str, str | list]]
    lineConfigs: list[dict[str, str]]
    (phoneConfigs, lineConfigs) = renderCSV(sourceData)

    axlClientProfile = (
        argv.wsdlSource,
        argv.axlUser,
        argv.axlPassword,
        argv.ccmServer
    )

    CUCM = CucmAXL(*axlClientProfile)

    addLines(CUCM, lineConfigs)
    addPhones(CUCM, phoneConfigs)

if __name__ == "__main__":
    main()
