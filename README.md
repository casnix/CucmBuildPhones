# CucmBuildPhones
Batch jobber to build a bunch of lines and phones in CUCM with a CSV file to model the configs.


## Caveats
As of the latest version, the script will pull the CucmAXL library from https://raw.github.com/casnix/stable/CucmAXL.py!
This is not typically done, and may not pass scrunity of your security team.  If this is the case, grab that file and place it into the same directory as `buildphones.py`.  Comment out the blocks relating to github imports and module version checks.  Add
`from CucmAXL import CucmAXL` to the top of the script.  *It is planned to add a CLI argument to force this behavior instead of 
the live pull from github.  The live pull is for lightweight install with the ability to automatically load improvements to the
library.*


## Versions
Current version 0.1.1 -- Use this. 

Version 0.1.0-beta -- working, is the same as v0.1.1 (stable) but with some minor differences in the code base.

Version 0.1.0-alpha -- may not work, is probably broken.  


## Command usage:
```
usage: buildphones.py [-h] [-c SOURCEFILE] [-t CCMSERVER] [-x WSDLSOURCE] [-P AXLPASSWORD] [-U AXLUSER] [-v] [-d] [-V] [-p PORT] [-a SERVICEPATH]

options:
  -h, --help            show this help message and exit
  -c, --csv-file SOURCEFILE
                        Source CSV file to read phone and line table from.
  -t, --server CCMSERVER
                        Target CCM server
  -x, --wsdl-source WSDLSOURCE
                        Path to the WSDL file defining the API
  -P, --password AXLPASSWORD
                        Password for standard AXL user
  -U, --user AXLUSER    Username for standard AXL user
  -v, --version         Print version
  -d, --debug           Turn on debug console logs to STDOUT
  -V, --verbose         Turn on verbose output
  -p, --port PORT       Specify port for AXL service on server (default 8443)
  -a, --service-path SERVICEPATH
                        Specify the path to the AXL service on server (default /axl/)
```

## CSV file
write up inbound

## Roadmap
+ Next: Make github imports default, but provide conditional import of local library with the `--local-lib` option.
+ Second: Auto-insert "https://" to target server URI if not present, or alternately do "http://" if `--no-ssl` is passed.
+ Third: Set a custom URI protocol with `--uri-protocol`
+ Fourth: Add an override column to CSV to update existing lines or phones if they already exist.  Force this on the entire list if the `--force-update` option is passed.
+ Fifth: Write unit tests.
