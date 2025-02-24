
import logging
from copy import deepcopy
from utils import *
import r2pipe
from ansi2html import Ansi2HTMLConverter
import json
from reducer import Reducer
from model.model import Match, FileInfo, UiDisasmLine
from model.extensions import Scanner
from plugins.file_pe import FilePe
from intervaltree import Interval, IntervalTree
from typing import List


def analyzeFileExe(filePe: FilePe, scanner: Scanner, analyzerOptions={}) -> IntervalTree:
    # Scans a PE file given with filePe with Scanner scanner. 
    # Returns all matches.
    isolate = analyzerOptions.get("isolate", False)
    remove = analyzerOptions.get("remove", False)
    ignoreText = analyzerOptions.get("ignoreText", False)

    matchesIntervalTree = investigate(filePe, scanner, isolate, remove, ignoreText)
    return matchesIntervalTree


# Fix for https://github.com/radareorg/radare2-r2pipe/issues/146
def cmdcmd(r, cmd):
    first = r.cmd(cmd)
    return first if len(first) > 0 else r.cmd("")

def augmentFilePe(filePe: FilePe, matches: List[Match]) -> str:
    # Augment the matches with R2 decompilation and section information.
    # Returns a FileInfo object with detailed file information too.

    conv = Ansi2HTMLConverter()
    r2 = r2pipe.open(filePe.filepath)
    r2.cmd("e scr.color=2") # enable terminal color output
    r2.cmd("aaa")

    baddr = cmdcmd(r2, "e bin.baddr")
    baseAddr = int(baddr, 16)

    MORE = 16
    for match in matches:
        data = filePe.data[match.start():match.end()]
        dataHexdump = hexdmp(data, offset=match.start())
        detail = []

        section = filePe.findSectionFor(match.fileOffset)
        sectionName = '<unknown>'
        if section is not None:
            sectionName = section.name

        if section is None: 
            logging.warn("No section found for offset {}".format(match.fileOffset))
            filePe.printSections()
        elif section.name == ".text":
            # offset from .text segment (in file)
            offset = match.start() - section.addr
            # base=0x400000 + .text=0x1000 + offset=0x123
            addrDisasm = baseAddr + section.virtaddr + offset - MORE
            sizeDisasm = match.size + MORE + MORE

            
            # r2: Print Dissabled (by bytes)
            asm = cmdcmd(r2, "pDJ {} @{}".format(sizeDisasm, addrDisasm))
            asm = json.loads(asm)
            for a in asm:
                relOffset = a['offset'] - baseAddr - section.virtaddr
                isPart = False
                if relOffset >= offset and relOffset < offset+match.size:
                    isPart = True
                
                text = a['text']
                textHtml = conv.convert(text, full=False)
            
                disasmLine = UiDisasmLine(
                    relOffset + section.addr, 
                    a['offset'],
                    isPart,
                    text, 
                    textHtml
                )
                detail.append(disasmLine)

        match.setData(data)
        match.setDataHexdump(dataHexdump)
        match.setSectionInfo(sectionName)
        match.setDisasmLines(detail)

    return ""


def investigate(filePe, scanner, isolate=False, remove=False, ignoreText=False) -> List[Match]:
    if remove:
        logging.info("Remove: Ressources, Versioninfo")
        filePe.hideSection("Ressources")
        filePe.hideSection("VersionInfo")

    # identify which sections get detected
    detected_sections = []
    if isolate:
        logging.info("Section Detection: Isolating sections (zero all others)")
        detected_sections = findDetectedSectionsIsolate(filePe, scanner)
    else:
        logging.info("Section Detection: Zero section (leave all others intact)")
        detected_sections = findDetectedSections(filePe, scanner)
    logging.info(f"{len(detected_sections)} section(s) trigger the antivirus independantly")
    for section in detected_sections:
        logging.info(f"  section: {section.name}")

    reducer = Reducer(filePe, scanner)
    matches = []
    if len(detected_sections) == 0 or len(detected_sections) > 3:
        logging.info("Section analysis failed. Fall back to non-section-aware reducer")
        match = reducer.scan(0, len(filePe.data))
        matches += match
    else:
        # analyze each detected section
        for section in detected_sections:
            # reducing .text may not work well
            if ignoreText and section.name == '.text':
                continue

            logging.info(f"Launching bytes analysis on section {section.name}")

            match = reducer.scan(section.addr, section.addr+section.size)
            matches += match

    return sorted(matches)


def findDetectedSectionsIsolate(filePe, scanner):
    # isolate individual sections, and see which one gets detected
    detected_sections = []

    for section in filePe.sections:
        filePeCopy = deepcopy(filePe)

        filePeCopy.hideAllSectionsExcept(section.name)
        status = scanner.scan(filePeCopy.data, filePeCopy.filename)

        if status:
            detected_sections += [section]

        logging.info(f"Hide all except: {section.name} -> Detected: {status}")

    return detected_sections


def findDetectedSections(filePe, scanner):
    # remove stuff until it does not get detected anymore
    detected_sections = []

    for section in filePe.sections:
        filePeCopy = deepcopy(filePe)
        filePeCopy.hideSection(section.name)

        status = scanner.scan(filePeCopy.data, filePeCopy.filename)
        if not status:
            detected_sections += [section]

        logging.info(f"Hide: {section.name} -> Detected: {status}")

    return detected_sections

