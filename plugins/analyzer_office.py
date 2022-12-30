
import copy
import logging
from re import I
import olefile

from reducer import Reducer
from utils import *
from model.model import Match
import pcodedmp.pcodedmp as pcodedmp
from plugins.file_office import FileOffice, VbaAddressConverter
from pcodedmp.disasm import DisasmEntry
from intervaltree import Interval, IntervalTree


def analyzeFileWord(fileOffice: FileOffice, scanner, analyzerOptions={}):
    makroData = fileOffice.data

    reducer = Reducer(fileOffice, scanner)
    matchesIntervalTree = reducer.scan(0, len(makroData))
    return matchesIntervalTree


def convertResults(ole, results) -> IntervalTree:
    ac = VbaAddressConverter(ole)
    it = IntervalTree()

    for result in results: 
        ite: DisasmEntry
        for ite in result:
            physBegin = ac.physicalAddressFor(ite.data.modulename, ite.begin)
            physEnd = ac.physicalAddressFor(ite.data.modulename, ite.end)
            ite.data.begin = physBegin
            ite.data.end = physEnd
            it.add(Interval(physBegin, physEnd, ite.data))
      
    return it


def augmentFileWord(fileOffice: FileOffice, matchesIntervalTree):
    matches = []

    # dump makros as disassembled code
    results = pcodedmp.processFile(fileOffice.filepath)

    # the output of pcodedmp is wrong. Convert results to real physical addresses.
    # use the extracted vbaProject.bin from fileOffice.data
    oleFile = olefile.OleFileIO(fileOffice.data)
    results = convertResults(oleFile, results)

    # correlate the matches with the dumped code
    idx = 0
    for m in matchesIntervalTree:
        data = fileOffice.data[m.begin:m.end]
        dataHexdump = hexdump.hexdump(data, result='return')
        sectionName = 'word/vbaProject.bin'
        detail = ''

        itemSet = results.at(m.begin)
        if len(itemSet) > 0:
            item = next(iter(itemSet))
            detail = "{} {} {}: ".format(item.data.lineNr, item.data.begin, item.data.end) + "\n" + item.data.text
        
        match = Match(idx, m.begin, m.end-m.begin)
        match.setData(data)
        match.setDataHexdump(dataHexdump)
        match.setInfo(sectionName)
        match.setDetail(detail)

        matches.append(match)
        idx += 1

    return matches