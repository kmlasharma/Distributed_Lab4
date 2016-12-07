from flask import Flask, jsonify
from flask import abort
from flask import make_response
import requests
import os
import sys
from OpenSSL import SSL
import json
import base64
import shutil
from shutil import copyfile
import datetime
from datetime import datetime

context = SSL.Context(SSL.SSLv23_METHOD)
cer = os.path.join(os.path.dirname(__file__), './resources/CLIENT/udara.com.crt')
key = os.path.join(os.path.dirname(__file__), './resources/CLIENT/udara.com.key')

CLIENT_CACHE_PATH = "./CLIENT_CACHE/"
LOCAL_STORAGE = "./LOCAL_STORAGE/"
commands_list = ["read", "req write", "write", "upload"]
fileServerAddresses = ['https://0.0.0.0:5050/Server/NewFile', 'https://0.0.0.0:5060/Server/NewFile']
directoryServerAddress = "https://0.0.0.0:5010/DirectoryServer/CheckTimestamps"
fileID = 0

clientapp = Flask(__name__)


@clientapp.route('/DISTRIBUTED_LAB4')
def index():
    return 'Flask is running!'

def getLastModified(path):
	return str(datetime.fromtimestamp(os.path.getmtime(path)))

def uploadFile(cmd):
	filenameToUpload = cmd[1]
	for filename in os.listdir(CLIENT_CACHE_PATH):
		if filename == filenameToUpload:
			print ("Error! File already exists. Please select 'Write'.")
			return 

	#cache file
	copyfile(LOCAL_STORAGE + filenameToUpload, CLIENT_CACHE_PATH + filenameToUpload)
	print ("Cached file %s" % filenameToUpload)

	#send file to main file server
	modTime = getLastModified(CLIENT_CACHE_PATH + filenameToUpload)
	url = fileServerAddresses[0]
	headers = {'content-type': 'application/json'}
	files = {
		'file' : (filenameToUpload, open(LOCAL_STORAGE + filenameToUpload, 'rb'))
		}
	data = {'title' : filenameToUpload, 'id' : fileID, 'last-modified' : modTime}
	response = requests.post(url, files=files, data=data, verify=False)
	print (response.content)

	


def retrieveReadFile(cmd):
	filenameToRead = cmd[1]
	modTime = getLastModified(CLIENT_CACHE_PATH + filenameToRead)
	#send this mod time to dir ser and see if cache's copy is outdated

	checkOutdated = {
		'filename' : filenameToRead,
		'last_modified' : modTime
	}
	response = requests.get(directoryServerAddress, json=checkOutdated, verify=False)

	content = response.content
	responseDict = json.loads(content.decode())
	print (responseDict)
	toUpdate = responseDict["upToDate"]
	if toUpdate == True: #cache copy is up to date, so can transfer info from cache to user's local storage
		copyfile(CLIENT_CACHE_PATH + filenameToRead, LOCAL_STORAGE + filenameToRead)
		print ("Transferred cached file %s" % filenameToRead)
	#else: # request server holding the file from dir ser, then download file from file server

if __name__ == '__main__':
	if not os.path.isdir(CLIENT_CACHE_PATH):
		os.mkdir(CLIENT_CACHE_PATH)
	cmd = input("Commands: " + str(commands_list) + "\n")
	cmd = cmd.split(" ")
	if (commands_list[3] in cmd):
		uploadFile(cmd)
	elif (commands_list[0] in cmd):
		retrieveReadFile(cmd)
		print ("HIII")


	context = (cer, key)
	clientapp.run( host='0.0.0.0', port=5000, debug = True, ssl_context=context)