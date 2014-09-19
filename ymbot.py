#!/usr/bin/env python

#Script to upload assets to YESMAIL.
#Author: Sri Doddapaneni
#License: Do what you wish. No Liability.

import requests
import os
import zipfile
import time
import sys
import os
from git import *
import base64
import json

from contextlib import closing
from zipfile import ZipFile, ZIP_DEFLATED
import os
import sh


def getAuthHeaders():
    execdir = application_path = os.path.dirname(__file__)
    filepath = execdir + '/http_auth_token'
    if not  os.path.isfile(filepath):
        print 'http_auth_token file not found'
        return False

    f = open(filepath)
    data = f.read()
    try:
        authheaders = json.loads(data)
    except ValueError:
        print "http_auth_token has invalid JSON."
        return False
    if not 'Authorization' in authheaders.keys():
        print 'Auth Headers not found. Should be like {"Authorization": "Basic authstring"}'
        return False

    return authheaders



def zipdir(basedir, archivename):
    assert os.path.isdir(basedir)
    with closing(ZipFile(archivename, "w", ZIP_DEFLATED)) as z:
        for root, dirs, files in os.walk(basedir):
            files = [f for f in files if not f[0] == '.']
            dirs[:] = [d for d in dirs if not d[0] == '.']
            #NOTE: ignore empty directories
            for fn in files:
                if fn == '.gitignore':
                    continue
                absfn = os.path.join(root, fn)
                zfn = absfn[len(basedir)+len(os.sep):] #XXX: relative path
                z.write(absfn, zfn)

def gitMakeFirstCommit(dirt):
    with open(dirt + "/.gitignore", "w") as gitignore:
        gitignore.write(".git\n.gitignore")
        gitignore.close()
    print "Git: Init " + dirt
    repo = Repo.init(dirt)
    index = repo.index
    print "Git: Adding files"
    index.add(['*'])
    print "Git: Commiting"
    index.commit("first commit")

def makeAutoCommit(dirt):
    gitX = sh.git.bake(_cwd=dirt)
    gitX("add", "-u" , ".")
    print "Git: verifying repo state"
    repo = Repo(dirt)
    index = repo.index
    if repo.untracked_files:
        index.add(repo.untracked_files)
    if repo.is_dirty():
        index.commit("Auto Commit")
        return True
    else:
        return False

def getDir(directory):
    dirt = os.getcwd()
    if directory != ".":
        dirt = dirt + '/' + directory
    return dirt


def uploadAssetsToYesMail(mmid, filename):
    with open(filename, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
        data = {"assetName": "content.zip", "assetBase64Data" : encoded_string}
        jsonData = json.dumps(data)
        headers = {'content-type': 'application/json'}
        headers.update(getAuthHeaders())
        url = "https://services.yesmail.com/enterprise/masters/" + str(mmid) + "/assets"

        # data = {"eventType": "AAS_PORTAL_START", "data": {"uid": "hfe3hf45huf33545", "aid": "1", "vid": "1"}}
        # params = {'sessionKey': '9ebbd0b25760557393a43064a92bae539d962103', 'format': 'xml', 'platformId': 1}

        r = requests.post(url, params={}, data=jsonData, headers=headers)
        if r.status_code == 202:
            print "PUSH OK"
            print "Fetching Status"
            data = json.loads(r.text)
            time.sleep(3)
            getLog(data['statusNoWaitURI'])
        else:
            print "PUSH FAILED"
            print r.text
        image_file.close()
    if os.path.isfile(filename):
        os.remove(filename)

def getLog(url):
    r = requests.get(url, params={}, headers=getAuthHeaders())
    print r.text

def push(directory, mmid, force):
    dirt = getDir(directory)
    if makeAutoCommit(dirt) or force:
        print "Pushing Changes to YesMail"
        assetFileName = "/tmp/" + str(time.time()) + ".zip"
        zipdir(dirt, assetFileName)
        print "Uploading to YesMail for mmid %", mmid
        uploadAssetsToYesMail(mmid, assetFileName)
        print "Done!"
    else:
        print "Repo is clean. No push required"


def fetchAsset(mmid, assetUrl, dirt):
    print "Fetching asset " + assetUrl
    headers = {'content-type': 'application/json', 'Accept': 'application/json'}
    headers.update(getAuthHeaders())
    r = requests.get(assetUrl, headers=headers)
    data = json.loads(r.text)
    if not os.path.exists(dirt):
        os.makedirs(dirt)
    filename = data['assetName']
    if 'html' in filename:
        filename = filename.replace('html', str(mmid) + '.html')
    if 'text' in filename:
        filename = filename.replace('text', str(mmid) + '.txt')
    filedata = base64.b64decode(data['assetBase64Data'])
    with open(dirt + '/' + filename, "wb") as f:
        f.write(filedata)


def fetch(mmid, directory):
    if directory == '.':
        directory = str(mmid)
    dirt = getDir(directory)
    print "Cloning to :" + dirt
    url = "https://services.yesmail.com/enterprise/masters/" + str(mmid) + "/assets"
    headers = {'content-type': 'application/json', 'Accept': 'application/json'}
    headers.update(getAuthHeaders())
    print "Fetching " + str(mmid)
    r = requests.get(url, headers=headers)
    data = json.loads(r.text)
    assets = data['assets']
    if r.status_code == 200:
        print "FETCH OK"
        print "Asset Count: " + str(len(assets))
        for assetUrl in assets:
            fetchAsset(mmid, assetUrl, dirt)
    print "Adding Git for version control"
    gitMakeFirstCommit(dirt)
    print "Done"

def checkRemoteStatus():
    # pull text and html files
    # complain if they are not the same as local copies
    pass


if __name__ == '__main__':
    args = sys.argv[1:]

    if len(args) >= 3:
        if args[0] == 'push' and len(args) >= 3:
            if len(args) == 4 and args[3] == '--force':
                force = True
            else:
                force = False
            # directory, mmid
            push(args[1], args[2], force)

        elif args[0] == 'fetch' and len(args) == 3:
            fetch(args[1], args[2])
    else:
        print """ymbot supports:
                push: ymbot push local_dir MMID [--force]
                fetch: ymbot fetch MMID local_dir
                """
