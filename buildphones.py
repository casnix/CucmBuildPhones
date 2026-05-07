# buildphones.py
# Copyright Matt Rienzo (C) 2026
# Builds several phones in Cisco Unified Communications Manager (CUCM) based
# on a CSV.
#
# This version grabs CucmAXL from github; you can download that library direct
# and import it locally if needed.

import csv
import sys
import urllib3
import argparse
import requests
import namespace
import traceback

from pprint import pprint

##########################################
### Module versioning for my convention###
##########################################
class _MODULE__buildphones():
    _Version = "0.1.0-beta"
    _VersionNum = "0.1.0.1"
    _VersionTuple = (0, 1, 0, 1)
    _CopyrightHeader = """

    Copyright Matt Rienzo (C) 2026
    Builds several phones in Cisco Unified Communications Manager (CUCM) based
    on a CSV.

    MIT License

    """

    @classmethod
    def Version(cls) -> str:
        return cls._Version
    
    @classmethod
    def VersionNum(cls) -> str:
        return cls._VersionNum
    
    @classmethod
    def VersionTuple(cls) -> tuple[int, int, int, int]:
        return cls._VersionTuple
    
    @classmethod
    def Copyright(cls) -> str:
        return cls._CopyrightHeader
    

###############################################################################
### Dynamic Github imports and checks methods blocks                        ###
###############################################################################
### For not locally installed modules.                                      ###
###                                                                         ###
### THIS CAN INTRODUCE CODE/VARIABLE INSTABILITY IF MULTIPLE MODULES USE    ###
### THE SAME NAMED GLOBAL VARIABLES, METHODS, ETC.                          ###
###                                                                         ###
### THIS IS A SECURITY RISK AND IS UNSAFE.                                  ###
### PLEASE ONLY DO THIS IF YOU TRUST THE REMOTE REPO.                       ###
### THIS IS INCLUDED FOR DEMO PURPOSES; I RECOMMEND ADDING THE IMPORTED     ###
### MODULES DIRECTLY ON YOUR LOCAL FILESYSTEM.                              ###
###############################################################################
# Reserve the class names to be imported
_MODULE__CucmAXL = classmethod
CucmAXL = classmethod

# Import from github
def githubImport(
        user: str,
        repo: str, 
        module: str, 
        tag: str = "master",
        printOut: bool = False
        ) -> None:
    """
    Dynamicaly import a module from a remote github repo.  THIS CAN INTRODUCE
    CODE/VARIABLE INSTABILITY IF MULTIPLE MODULES USE THE SAME NAMED GLOBAL
    VARIABLES, METHODS, ETC.

    THIS IS A SECURITY RISK AND IS UNSAFE. 
    PLEASE ONLY DO THIS IF YOU TRUST THE REMOTE REPO.
    THIS IS INCLUDED FOR DEMO PURPOSES; I RECOMMEND ADDING THE IMPORTED MODULES
    DIRECTLY ON YOUR LOCAL FILESYSTEM.
    """
    data = {}
    url: str = 'https://raw.githubusercontent.com/{}/{}/{}/{}.py'.format(
        user,
        repo,
        tag,
        module
    )

    print(
        f"[githubImport] Attempting to grab {module} for import from {url}"
    ) if printOut else next

    try:
        r = requests.get(url).text
        # print(r)  # For dubug purposes
        exec(r, globals())
    except Exception as e:
        print(
            f"[githubimport] Failed to grab {module} from {url}."
        ) if printOut else next
        print(
            f"[githubImport] Reason: {type(e).__name__}: {e}"
        ) if printOut else next

        raise

def moduleFailVerCheck(
        moduleName: str, 
        minimumVersion: tuple[int, int, int, int],
        hardFail: bool = True,
        printOut: bool = True
    ) -> bool:
    """ 
    Check if a github imported module is above or equal to the minimum version
    specified in the arguments.  To prevent printing the result to the console,
    set `printOut` to false.  To do a soft check and continue execution of the 
    script despite failing the version check, set `hardFail` to false.

    The version variable expects a tuple in format of
    (MAJOR, MINOR, PATCH, RELEASE)

    Function will kill the script on a hard fail, return True on soft fail, and
    return False if it passes.
    """
    mangled = "_MODULE__"+moduleName
    modVersion: tuple[int, int, int, int] = globals()[mangled].VersionTuple()

    # magic will be set to:
    # 0 - pass
    # 1 - fail, hard check
    # 2 - fail, soft check
    magic = 0

    magic = 1 if modVersion < minimumVersion and hardFail else magic
    magic = 2 if modVersion < minimumVersion and not hardFail else magic

    print(
        f"{moduleName} is below required version. Minimum version is " + 
        f"{minimumVersion}, but found {modVersion}"
    ) if magic > 0 and printOut else next

    returnCode = False
    sys.exit(1) if magic == 1 else next
    returnCode = True if magic == 2 else False

    return returnCode

####################################################################
### Module tuple block                                           ###
####################################################################
# Formatted this way with the tuple expansion for the purpose of ###
# readability in the case of multiple remote imports.            ###
####################################################################
IMPORT_CucmAXL = ('casnix', 'CucmAXL', 'CucmAXL', 'master')

####################################
### Module minimum version block ###
####################################
VERSION_CucmAXL = (0, 1, 0, 0)

#########################
### Import call block ###
#########################
try:
    githubImport(*IMPORT_CucmAXL)

except:
    sys.exit(1)


##################################
### Module version check block ###
##################################
moduleFailVerCheck("CucmAXL", VERSION_CucmAXL)

# Suppress SSL warnings (use proper certs in production)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def addPhones(ccm: CucmAXL, phones: list, debug: bool) -> None:
    """
    Iterate through `phones` and add a phone per each to CUCM.
    """
    def printOut(thisPhone: dict) -> None:
        print("[D] addPhones() -- current value of dict: thisPhone:")
        pprint(thisPhone)

    for thisPhone in phones:
        try:
            printOut(thisPhone) if debug else next
            ccm.addPhone(phone={**thisPhone})
        except Exception as e:
            if "duplicate value" in str(e).lower():
                print(
                    f"[~] Phone {thisPhone["name"]} already exists, skipping."
                )
                next
            else:
                raise
    
def addLines(ccm: CucmAXL, lines: list, debug: bool) -> None:
    """
    Iterate through `lines` and add a line per each to CUCM.
    """

    def printOut(thisLine: dict) -> None:
        print("[D] addLines() -- current value of dict: thisLine:")
        pprint(thisLine)

    failures = 0 # For future failure tolerance count
    for thisLine in lines:
        try:
            printOut(thisLine) if debug else next
            ccm.addLine(line = {**thisLine})
        except Exception as e:
            if (
                "already exists" in str(e).lower()
                or "duplicate" in str(e).lower()
                or "A DN exists"
            ):
                print(
                    f"[~] DN {thisLine['pattern']} already exists, "+
                      "will reuse it"
                )
            else:
                raise

def serializeCSV(data: list, debug: bool = False) -> tuple[list, list]:
    """
    Separate the source table into two arrays of lists.
    The first array will have data relevant to the addPhone method referenced
     by the CucmAXL object in the main logic.
    The secod array will have data relevant to the addLine method referenced
     by the CucmAXL object in the main logic.
    """
    _deviceConfig = []
    _lineConfig = []
    _lineAppearance: dict
    for enum in enumerate(data):
        index = enum[0]
        print(
            f"[D] serializeCSV() - Current indice is {index}\n"
            f"[D] serializeCSV() - Current enum is {enum}"
        ) if debug else next

        print(
            f"[D] serializeCSV() - Setting _lineConfig[{index}]"
        ) if debug else next
        _lineConfig.append({
            "pattern": data[index]["linePattern"],
            "routePartitionName": data[index]["routePartition"],
            "description": data[index]["description"],
            "alertingName": data[index]["alertingName"],
            "asciiAlertingName": data[index]["asciiAlertingName"],
            "voiceMailProfileName": data[index]["vmProfile"],
            "shareLineAppearanceCssName": data[index]["callingSearchSpace"],
            "usage": "Device"
        })
        print(
            f"[D] serializeCSV() - Dump of _lineConfig[{index}]:"
        ) if debug else next
        pprint(_lineConfig[index]) if debug else next

        print(
            f"[D] serializeCSV() - Setting _lineAppearance"
        ) if debug else next
        _lineAppearance = {
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
        }
        print(
            f"[D] serializeCSV() - Dump of _lineAppearance:"
        ) if debug else next
        pprint(_lineAppearance) if debug else next

        print(
            f"[D] serializeCSV() - Setting _deviceConfig[{index}]"
        ) if debug else next
        _deviceConfig.append({
            "name": data[index]["devName"],
            "description": data[index]["desc"],
            "product": data[index]["devType"],
            "class": data[index]["devClass"],
            "protocol": data[index]["protocol"],
            "protocolSide": data[index]["protocolSide"],
            "devicePoolName": data[index]["devPool"],
            "locationName": data[index]["loc"],
            "commonPhoneConfigName": data[index]["commonConfig"],
            "phoneTemplateName": data[index]["phoneTemplate"],
            "useTrustedRelayPoint": data[index]["useRelay"],
            "builtInBridgeStatus": data[index]["bridgeStatus"],
            "packetCaptureMode": data[index]["packetCap"],
            "certificateOperation": data[index]["certOp"],
            "deviceMobilityMode": data[index]["devMobility"],
            "securityProfileName": data[index]["securityProfile"],
            "sipProfileName": data[index]["sipProfile"],
            "callingSearchSpaceName": data[index]["callingSearchSpace"],
            "lines": {
                "line": [{**_lineAppearance}]
            }
        })
        print(
            f"[D] serializeCSV() - Dump of _deviceConfig[{index}]:"
        ) if debug else next
        pprint(_deviceConfig[index]) if debug else next

    return (_deviceConfig, _lineConfig)

def printVersion() -> None:
    """
    Print version, copyright, and required CucmAXL module minimum version.
    """

    print(f"Script buildphones.py version {_MODULE__buildphones.Version()}")
    print(_MODULE__buildphones.Copyright())
    print(f"Uses the CucmAXL module, version {_MODULE__CucmAXL.Version()}")
    print("CucmAXL is imported from github.com/casnix/CucmAXL")

    sys.exit(0)

def handleInclusiveArgs(parser: namespace) -> None:
    """
    Verify command line arguments that require companion options are all there
    """
    print(
        f"[D] handleInclusiveArgs() - parser.sourceFile = {parser.sourceFile}\n"
        f"[D] handleInclusiveArgs() - parser.ccmServer = {parser.ccmServer}\n"
        f"[D] handleInclusiveArgs() - parser.axlPassword = {parser.axlPassword}\n"
        f"[D] handleInclusiveArgs() - parser.axlUser = {parser.axlUser}\n"
        f"[D] handleInclusiveArgs() - parser.wsdlSource = {parser.wsdlSource}\n"
    ) if parser.debug else next

    withSourceFile: bool = parser.sourceFile and (
        not parser.ccmServer
        or not parser.axlPassword 
        or not parser.axlUser 
        or not parser.wsdlSource
    )
    print(
        f"[D] handleInclusiveArgs() - withSourceFile = {withSourceFile}"
    ) if parser.debug else next

    withCCMServer: bool = parser.ccmServer and (
        not parser.axlPassword 
        or not parser.axlUser 
        or not parser.wsdlSource
    )
    print(
        f"[D] handleInclusiveArgs() - withCCMServer = {withCCMServer}"
    ) if parser.debug else next


    withAXLPassword: bool = parser.axlPassword and (
        not parser.ccmServer 
        or not parser.axlUser 
        or not parser.wsdlSource
    )
    print(
        f"[D] handleInclusiveArgs() - withAXLPassword = {withAXLPassword}"
    ) if parser.debug else next


    withAXLUser: bool = parser.axlUser and (
        not parser.axlPassword 
        or not parser.ccmServer 
        or not parser.wsdlSource
    )
    print(
        f"[D] handleInclusiveArgs() - withAXLUser = {withAXLUser}"
    ) if parser.debug else next


    withWSDLSource: bool = parser.wsdlSource and (
        not parser.axlPassword 
        or not parser.axlUser 
        or not parser.ccmServer
    )
    print(
        f"[D] handleInclusiveArgs() - withWSDLSource = {withWSDLSource}"
    ) if parser.debug else next


    if (
        withSourceFile
        or withCCMServer
        or withAXLPassword
        or withAXLUser
        or withWSDLSource
        ):
        print(
            "Options error!\n"
            "These options must be used together: -t & -x & -p & -u\n"
            "This is true also if -c is used.\n"
            "For more information, use --help\n"
        )
        sys.exit(2)
    
    return

def parseARGV() -> namespace:
    """
    Glean CSV source from command line arguments.
    """
    parser = argparse.ArgumentParser()
    sourceArgs = ('-c', '--csv-file')
    sourceArgsOpts = {
        "help": 'Source CSV file to read phone and line table from.',
        "type": str,
        "dest": 'sourceFile'
    }
    
    serverArgs = ('-t', '--server')
    serverArgsOpts = {
        "help": "Target CCM server",
        "type": str,
        "dest": 'ccmServer',
    }
    
    wsdlArgs = ('-x', '--wsdl-source')
    wsdlArgsOpts = {
        "help": 'Path to the WSDL file defining the API',
        "type": str,
        "dest": 'wsdlSource',
    }
    
    passwordArgs = ('-P', '--password')
    passwordArgsOpts = {
        "help": "Password for standard AXL user",
        "type": str,
        "dest": 'axlPassword',
    }

    userArgs = ('-U', '--user')
    userArgsOpts = {
        "help": "Username for standard AXL user",
        "type": str,
        "dest": 'axlUser',
    }

    versionArgs = ('-v', '--version')
    versionArgsOpts = {
        "help": "Print version",
        "dest": "printVersion",
        "action": "store_true"
    }

    debugArgs = ('-d', '--debug')
    debugArgsOpts = {
        "help": "Turn on debug console logs to STDOUT",
        "dest": "debug",
        "action": "store_true"
    }

    verboseArgs = ('-V', '--verbose')
    verboseArgsOpts = {
        "help": "Turn on verbose output",
        "dest": "verbose",
        "action": "store_true"
    }

    portArgs = ('-p', '--port')
    portArgsOpts = {
        "help": "Specify port for AXL service on server (default 8443)",
        "dest": "port",
        "default": "8443"
    }

    axlPathArgs = ('-a', '--service-path')
    axlPathOpts = {
        "help": "Specify the path to the AXL service on server" +
         " (default /axl/)",
        "dest": "servicePath",
        "default": "/axl/"
    }

    parser.add_argument(*sourceArgs, **sourceArgsOpts)
    parser.add_argument(*serverArgs, **serverArgsOpts)
    parser.add_argument(*wsdlArgs, **wsdlArgsOpts)
    parser.add_argument(*passwordArgs, **passwordArgsOpts)
    parser.add_argument(*userArgs, **userArgsOpts)
    parser.add_argument(*versionArgs, **versionArgsOpts)
    parser.add_argument(*debugArgs, **debugArgsOpts)
    parser.add_argument(*verboseArgs, **verboseArgsOpts)
    parser.add_argument(*portArgs, **portArgsOpts)
    parser.add_argument(*axlPathArgs, **axlPathOpts)

    return parser.parse_args(args=None if sys.argv[1:] else ['--help'])

def main() -> None:
    """
    Application logic steps:
        1) Parse command line arguments
        2) Parse CSV into arrays of dicts
        3) Open a client to the CUCM server and build the phones
    """
    argv: namespace = parseARGV()
    handleInclusiveArgs(argv)
    printVersion() if argv.printVersion else next
    argv.verbose = True if argv.debug else argv.verbose

    print("[+] Reading CSV source.") if argv.verbose else next
    try:
        with open(argv.sourceFile, newline='') as f:
            reader = csv.DictReader(f)
            sourceData = list(reader)
            print(
                "[D] main() - After CSV source read"
            ) if argv.debug else next
            print(
                "[D] main() - Dump of list[dict] sourceData:"
            ) if argv.debug else next
            pprint(sourceData) if argv.debug else next
    except Exception as e:
        print(f"[x] Failed to open {argv.sourceFile}.")
        print(f"[~] Exception: {str(e)}")
        traceback.print_exc()
        sys.exit(2)

    phoneConfigs: list[dict[str, str | list]]
    lineConfigs: list[dict[str, str]]

    try:
        print("[+] Serializing CSV data...") if argv.verbose else next
        (phoneConfigs, lineConfigs) = serializeCSV(sourceData, argv.debug)
        print("[D] main() - After serializeCSV call") if argv.debug else next
        print(
            "[D] main() - Dump of list[dict] phoneConfigs:"
        ) if argv.debug else next

        pprint(phoneConfigs) if argv.debug else next
        
        print(
            "[D] main() - Dump of list[dict] lineConfigs"
        ) if argv.debug else next

        pprint(lineConfigs) if argv.debug else next
    except Exception as e:
        print("[x] Failed to serialize CSV data.")
        print(f"[~] Exception: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
    
    targetCCMServer = f"{argv.ccmServer}:{argv.port}{argv.servicePath}"
    axlClientProfile = (
        argv.wsdlSource,
        argv.axlUser,
        argv.axlPassword,
        targetCCMServer
    )

    print("[D] main() - axlClientProfile -> (") if argv.debug else next
    print("[D] \twsdlSource,") if argv.debug else next
    print("[D] \taxlUser,") if argv.debug else next
    print("[D] \taxlPassword,") if argv.debug else next
    print("[D] \tccmServer") if argv.debug else next
    print("[D] )") if argv.debug else next
    print()
    print("[D] main() - Dump of list axlClientProfile:") if argv.debug else next
    pprint(axlClientProfile) if argv.debug else next

    try:
        print(
            f"[+] Connecting to CallManager server {argv.ccmServer}..."
        ) if argv.verbose else next

        CUCM = CucmAXL(*axlClientProfile)
    except Exception as e:
        print(f"[x] Failed to connect to CallManager server {argv.ccmServer}")
        print(f"[~] Exception: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

    try:
        print("[+] Adding lines...") if argv.verbose else next
        addLines(CUCM, lineConfigs, argv.debug)
    except Exception as e:
        print(f"[x] Failed to add lines")
        print(f"[~] Exception: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
    
    try:
        print("[+] Adding phones...") if argv.verbose else next
        addPhones(CUCM, phoneConfigs, argv.debug)
    except Exception as e:
        print(f"[x] Failed to add phones")
        print(f"[~] Exception: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

    print("[+] Done.")
    sys.exit(0)

if __name__ == "__main__":
    main()
