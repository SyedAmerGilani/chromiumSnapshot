#!/usr/bin/python3

import urllib.request
import subprocess
from os.path import exists,join,normpath
import os
import stat
import configparser
import logging
from io import BytesIO
from zipfile import ZipFile
import platform

class chromiumSnapshot:

    zipFileTable = {'Win':'chrome-win32.zip', 'Linux':'chrome-linux.zip', 'Linux_x64':'chrome-linux.zip'}
    executableTable = {'Win':'chrome-win32\chrome.exe', 'Linux':'chrome-linux/chrome', 'Linux_x64':'chrome-linux/chrome'}

    def __init__(self,name):
        #logging.basicConfig(level=logging.DEBUG)
        self.detectPlatform()
        self.readINI(name)
        self.getLatestRevision()
        self.getLatest()
        self.run()
        self.writeINI(name)


    def readINI(self,name):
        self.oldLatest = 0
        configParser = configparser.ConfigParser()
        if exists(name):
            configParser.read(name)
        else:
            configParser.add_section('general')
        config = configParser['general']
        self.oldLatest = int(config.get('latest',0))
        self.baseUrl = config.get('baseUrl', 'https://storage.googleapis.com/chromium-browser-continuous')
        self.outputDirectory = config.get('outputDirectory','output')
        print("Old Revision: " + str(self.oldLatest))

    def writeINI(self,name):
        configParser = configparser.ConfigParser()
        configParser.add_section('general')
        configParser.set('general', 'latest', str(self.latest))
        configParser.set('general', 'baseUrl', self.baseUrl)
        configParser.set('general', 'outputDirectory', self.outputDirectory)
        with open(name, 'w') as configfile:
            configParser.write(configfile)

    def detectPlatform(self):
        detectedPlatform = platform.system()
        if detectedPlatform == 'Windows':
            self.platform = 'Win'
        elif detectedPlatform == 'Linux':
            if platform.architecture()[0] == '64bit':
                self.platform = 'Linux_x64'
            else:
                self.platform = 'Linux'
        else:
            print("this platform is not supported")
            exit()
        print("detected platform: " + self.platform)

    def getLatestRevision(self):
        latestfile = urllib.request.urlopen(self.baseUrl + '/' + self.platform + '/LAST_CHANGE')
        self.latest = int(latestfile.read().decode('utf-8'))
        print("Latest Revision: " + str(self.latest))

        
    def getLatest(self):
        if not os.path.exists(self.outputDirectory):
            os.makedirs(self.outputDirectory)
        if (self.oldLatest < self.latest) or (not os.path.exists(join(self.outputDirectory, self.executableTable[self.platform]))):
            print("newer revision available\nDownloading...")
            url = urllib.request.urlopen(self.baseUrl + '/' + self.platform + '/' + str(self.latest) + '/' + self.zipFileTable[self.platform])
            zipfile = ZipFile(BytesIO(url.read()))
            print("extracting...")
            zipfile.extractall(self.outputDirectory)

    def run(self):
        print("executing...")
        command = join(self.outputDirectory, self.executableTable[self.platform])
        os.chmod(command, os.stat(command).st_mode | stat.S_IXUSR)
        if self.platform in ['Linux', 'Linux_x64']:
            sandboxPath= join(self.outputDirectory, self.executableTable[self.platform] + "_sandbox")
            os.chmod(sandboxPath, os.stat(sandboxPath).st_mode | stat.S_IXUSR)
            process = subprocess.Popen(command, env=dict(os.environ, CHROME_DEVEL_SANDBOX=sandboxPath))
        else:
            process = subprocess.Popen(command)

if __name__ == "__main__":
    cSnapshot = chromiumSnapshot("chromiumSnapshot.ini")
