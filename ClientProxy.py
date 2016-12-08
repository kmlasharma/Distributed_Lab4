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
import hashlib

context = SSL.Context(SSL.SSLv23_METHOD)
cer = os.path.join(os.path.dirname(__file__), './resources/CLIENT/udara.com.crt')
key = os.path.join(os.path.dirname(__file__), './resources/CLIENT/udara.com.key')

CLIENT_CACHE_PATH = "./CLIENT_CACHE/"
LOCAL_STORAGE = "./LOCAL_STORAGE/"
commands_list = ["read", "req write", "write", "upload"]
fileServerAddresses = {'1' : 'https://0.0.0.0:5050/Server/', '2' : 'https://0.0.0.0:5060/Server/'}
directoryServerAddress = "https://0.0.0.0:5010/DirectoryServer/"
fileID = 0

clientapp = Flask(__name__)


@clientapp.route('/DISTRIBUTED_LAB4')
def index():
    return 'Flask is running!'

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
	# modTime = getLastModified(CLIENT_CACHE_PATH + filenameToUpload)
	hashedFile = hashlib.md5(open(CLIENT_CACHE_PATH + filenameToUpload,'rb').read()).hexdigest()
	url = fileServerAddresses['1']
	headers = {'content-type': 'application/json'}
	files = {
		'file' : (filenameToUpload, open(LOCAL_STORAGE + filenameToUpload, 'rb'))
		}
	data = {'title' : filenameToUpload, 'id' : fileID, 'hash' : hashedFile}
	response = requests.post(url + "NewFile", files=files, data=data, verify=False)
	print (response.content)

# def writeToFile(cmd):
# 	#make sure the client has authority to cache


def retrieveReadFile(cmd):
	filenameToRead = cmd[1]

	hashedFile = hashlib.md5(open(CLIENT_CACHE_PATH + filenameToRead,'rb').read()).hexdigest()
	checkOutdated = {
		'filename' : filenameToRead,
		'hash' : hashedFile
	}
	response = requests.get(directoryServerAddress + "CheckHash", json=checkOutdated, verify=False)

	content = response.content
	responseDict = json.loads(content.decode())
	print (responseDict)
	toUpdate = responseDict["upToDate"]
	if toUpdate == True: #cache copy is up to date, so can transfer info from cache to user's local storage
		copyfile(CLIENT_CACHE_PATH + filenameToRead, LOCAL_STORAGE + filenameToRead)
		print ("Transferred cached file %s" % filenameToRead)
	else: # request server holding the file from dir ser, then download file from file server (note when the cache's copy is out of date we assume the master file server and replicate file server is up to date)
		#TODO
		data = {'filename' : filenameToRead}
		response = requests.get(directoryServerAddress + "GetServerID", json=data, verify=False)
		print (response)
		content = response.content
		responseDict = json.loads(content.decode())
		print (responseDict)
		serverIdToQuery = responseDict["ID"]
		url = fileServerAddresses[serverIdToQuery]
		response = requests.get(url + "retrieveFile", json=data, verify=False)
		print (response.content)





if __name__ == '__main__':
	if not os.path.isdir(CLIENT_CACHE_PATH):
		os.mkdir(CLIENT_CACHE_PATH)
	cmd = input("Commands: " + str(commands_list) + "\n")
	cmd = cmd.split(" ")
	if (commands_list[3] in cmd):
		uploadFile(cmd)
		print ("Client wants to upload")
	elif (commands_list[0] in cmd):
		retrieveReadFile(cmd)
		print ("Client wants to read")
	elif (commands_list[2] in cmd):
		writeToFile(cmd)
		print ("Client wants to write")


	context = (cer, key)
	clientapp.run( host='0.0.0.0', port=5000, debug = True, ssl_context=context)