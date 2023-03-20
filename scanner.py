import requests as req
from model.extensions import Scanner
from subprocess import Popen
from sys import executable
from zipfile import ZipFile


class RawDataScanner(Scanner):
    def __init__(self, url, name):
        self.scanner_url = url
        self.scanner_name = name
    
    def scan(self, data, filepath):
        file_extension = filepath.split(".")[-1]
        params = { "ext": file_extension }
        res = req.post(f"{self.scanner_url}/scan/data", params=params, data=data)

        if res.status_code != 200:
            print("Err: " + str(res.status_code))
            print("Err: " + str(res.text))
        
        ret_value = res.json()['detected']
        return ret_value


class DownloadScanner(Scanner):
    def __init__(self, url, download_url, local_port, name):
        self.scanner_url = url
        self.download_url = download_url
        self.local_port = local_port
        self.scanner_name = name
    
    def scan(self, data, filepath):
        """
        Starts a local server at port @local_port, and sends the @download_url to the avred server.
        The avred server then requests the file to scan from the @download_url.
        avred: file uploaded -> scanner: create server & send url to avred-server -> avred-server: get url, download file, and scan it
        """
        folder, filename = filepath.rsplit("\\", 1)
        # if it's an .lnk file, pack it into a .zip before downloading (cannot download .lnk)
        if filename.split(".")[-1] == "lnk":
            zip_filepath = filepath + ".zip"
            with ZipFile(zip_filepath, "w") as zip_f:
                zip_f.write(filepath, filename)
            filename = filename + ".zip" # serve the .zip file 

        server = Popen([executable, "-m", "http.server", str(self.local_port), "-d", folder])
        
        params = { "url": f"{self.download_url}/{filename}" }
        res = req.get(f"{self.scanner_url}/scan/down", params=params)

        if res.status_code != 200:
            print("Err: " + str(res.status_code))
            print("Err: " + str(res.text))
            raise Exception(res.text)

        ret_value = res.json()['detected']
        server.terminate()
        return ret_value
