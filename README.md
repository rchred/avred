# avred

Antivirus reducer. 

Avred is being used to identify which parts of a file are identified
by a Antivirus, and tries to show as much possible information and context about each match. 

This includes: 
* Section names of matches
* Decompilation if match contains code
* Verification of matches

It is mainly used to make it easier for RedTeamers to obfuscate their tools. 


## Background

Most antivirus engines rely on strings or other bytes sequences to recognize malware.
This project helps to automatically recover these signatures (matches).

The difference to similar projects is: 
* Knowledge of internal file structures. 
  * Can extract vbaProject.bin and modify it 
  * Knows about PE sections and scan each one individually
  * Knows .NET streams
* Supports any Antivirus (thanks to AMSI server via HTTP)
* Shows detailed information about each match (disassembly etc.)
* Verifies the matches


## Supported files:

* PE (EXE) files, r2 disassembly
* PE .NET files, dncil disassembly
* Word files, pcodedmp disassembly


## Example


## Screenshots


## Install 

Requires: python 3.8 (and radare2 in PATH for PE / exe files)

```
pip3 install -r requirements.txt
```

If you get the error `ImportError: failed to find libmagic. Check your installation` try: 
```
pip3 install python-magic-bin==0.4.14
```

### radare2 Setup
- follow [instructions](https://github.com/radareorg/radare2#installation) for Windows, or download exe from [releases](https://github.com/radareorg/radare2/releases) and add to PATH

### python-magic Bug
- on Windows 10 Pro with Python 3.10.4: magic package has bugs (freezes, crashes, TP_NUM_C_BUFS too small: 50), use python-magic-bin

## Setup

First, we need a windows instance with an antivirus. We use [avred-server](https://github.com/dobin/avred-server) as interface to this antivirus.

On VM `1.1.1.1:9001`:
* Deploy a avred-server onto a VM with the AV you want to test
* Configured the `config.json` on the avred-server directory
* Start server: `./avred-server.py`
* Test it: http://1.1.1.1:9001/test

Second, once you have this, you can setup avred.
* checkout avred 
* Configure your servers in `config.json` (eg `1.1.1.1:9001`)
* Scan file with: `./avred.py --file mimikatz.exe --server amsi`


## How to use

For the webapp: 
```sh
$ python3 app.py --listenip 127.0.0.1 --listenport 8080
```

Manually: 
```sh
$ python3 avred.py --server amsi --file malware/evil.exe
```

## File and Directory structure

I am team NO-DB. Only files.

File nomenclature: 
* `file.exe`: The file you want to scan
* `file.exe.log`: All log output of the scanning (with `--logtofile`)
* `file.exe.matches`: JSON dump of all matches
* `file.exe.outcome`: Pickled Outcome data structure with all further information

For the webapp, files are uploaded to `app/uploads`. 


## References

Similar to: 
* https://github.com/matterpreter/DefenderCheck
* https://github.com/rasta-mouse/ThreatCheck
* https://github.com/RythmStick/AMSITrigger

Based on: 
* https://github.com/scrt/avdebugger


## Issues when scanning and options

### EXE PE

*If all sections get detected*, use `--isolate`. Instead of nulling a section and see if
the AV stops identifying it, the option will do the opposite: null other sections, and see
if the AV still detects it. 

*If there are a lot of matches in `.text`*, use `--ignoreText` to skip analyzing this section.
The findings in the other sections are usually good enough. 
