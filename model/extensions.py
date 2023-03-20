from abc import ABC, abstractmethod
from utils import patchData, FillType
from dataclasses import dataclass
import os


@dataclass
class Scanner(ABC):
    """Interface to the AV scanner"""
    scanner_url: str = ""
    scanner_name: str = ""

    @abstractmethod
    def scan(self, data, filename):
        pass


class PluginFileFormat():
    """Interface for file format plugins"""
    def __init__(self):
        self.filepath = None
        self.filename = None
        self.fileData = b""  # The content of the file
        self.data = b""      # The data we work on
        

    def parseFile(self) -> bool:
        self.data = self.fileData  # Default: File is Data


    def getData(self):
        return self.data


    def getFileWithNewData(self, data):
        return data  # Default: Data is the File. No need to modify.


    def loadFromFile(self, filepath: str) -> bool:
        self.filepath = filepath
        self.filename = os.path.basename(filepath)

        with open(self.filepath, "rb") as f:
            self.fileData = f.read()

        return self.parseFile()


    def hidePart(self, base: int, size: int, fillType: FillType=FillType.null):
        self.data = patchData(self.data, base, size, fillType)

        