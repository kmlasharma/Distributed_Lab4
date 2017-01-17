from flask import Flask, jsonify
from flask import abort
from flask import make_response
from flask import request
from flask import send_file
from flask import Response
import requests
import os
import sys
from OpenSSL import SSL
import sqlite3
import argparse
import json

context = SSL.Context(SSL.SSLv23_METHOD)
cer = os.path.join(os.path.dirname(__file__), './resources/MASTER_FILE_SERVER/udara.com.crt')
key = os.path.join(os.path.dirname(__file__), './resources/MASTER_FILE_SERVER/udara.com.key')
fileServerAddresses = {}
directoryServerAddress = "https://0.0.0.0:5050/DirectoryServer"
fileserver = Flask(__name__)
FILE_FOLDER = "./FILE_SERVER_FOLDER_%s/"


@fileserver.route('/Server')
def index():
    return 'File Server is running!'

@fileserver.route('/Server/NewFile', methods=["POST"])
def uploadNewFileFromClient():
	if not request.files:
		abort(400)
	else:
		newFile = request.files["file"]
		filename = request.form['title']
		if (not checkIfFileExists(filename)):
			fileID = request.form['id']
			hashedFile = request.form['hash']
			print (hashedFile)
			path = FILE_FOLDER + filename
			newFile.save(path)
			print ("Successfully saved %s on server %s" % (filename, server_id))
			makeReplicate(newFile, filename, fileID, hashedFile)
			return "Successfully saved master copy onto server %s" % server_id, 200
		else:
			return "This file already exists", 304

def checkIfFileExists(fname):
	if (os.path.isfile(FILE_FOLDER + fname)):
		return True
	else:
		return False


@fileserver.route('/Server/UpdateFile', methods=["POST"])
def updateFileFromClient():
	if not request.files:
		abort(400)
	else:
		newFile = request.files["file"]
		filename = request.form['title']
		fileID = request.form['id']
		hashedFile = request.form['hash']
		print (hashedFile)
		path = FILE_FOLDER + filename
		newFile.save(path)
		print ("Successfully updated %s on server %s" % (filename, server_id))
		updateReplicate(newFile, filename, fileID, hashedFile)
		return "Successfully saved master copy onto server %s" % server_id, 200

#send the file to other server for replication
def updateReplicate(fileToReplicate, filename, fileID, hashedFile):
	url = directoryServerAddress + "/GetServerID"
	dataDict = {'filename' : filename, 'masterNeeded' : False}
	response = requests.get(url, json=dataDict, verify=False)
	print (response)
	content = response.content
	responseDict = json.loads(content.decode())
	print (responseDict)
	serverIdToQuery = responseDict["ID"]
	if serverIdToQuery not in fileServerAddresses:
		url = directoryServerAddress + "/requestAServer"
		dataDict = {'server_id': serverIdToQuery, 'selectThis' : True}
		response = requests.get(url, json=dataDict, verify=False)
		content = response.content
		responseDict = json.loads(content.decode())
		url = responseDict["base_url"]
		fileServerAddresses[serverIdToQuery] = url
	else:
		url = fileServerAddresses[serverIdToQuery]

	headers = {'content-type': 'application/json'}
	files = {
		'file' : (filename, open(FILE_FOLDER + filename, 'rb'))
		}
	data = {'title' : filename, 'id' : fileID}
	response = requests.post(url + "/Replicate", files=files, data=data, verify=False)
	if (response.status_code == 201): # 
		content = response.content
		responseDict = json.loads(content.decode())
		print (responseDict)
		replicateID = responseDict["Server_ID"]
		
		updateDB =  {
		        'title': filename,
		        'hash' : hashedFile,
		    }

		response = requests.post(directoryServerAddress + "/UpdateFile", json=updateDB, verify=False)
		print (response)


@fileserver.route('/Server/Replicate', methods=["POST"])
def acceptReplicate():
	if not request.files:
		return make_response(jsonify({'error': 'No file included'}), 400)
	else:
		newFile = request.files["file"]
		filename = request.form['title']
		path = FILE_FOLDER + filename
		newFile.save(path)
		print ("Successfully saved %s" % filename)
		return jsonify({"Server_ID" : server_id, "Message" : "Successfully saved replicate onto server"}), 201

#send the file to other server for replication
def makeReplicate(fileToReplicate, filename, fileID, hashedFile):
	url = directoryServerAddress + "/requestAServer"
	dataDict = {"server_id" : server_id, "selectThis" : False}
	response = requests.get(url, json=dataDict, verify=False)
	content = response.content
	responseDict = json.loads(content.decode())
	print (responseDict)
	serverID = responseDict["server_id"]
	serverURL = responseDict["base_url"]
	if (not serverID in fileServerAddresses):
		fileServerAddresses[serverID] = serverURL


	url = serverURL + "/Replicate"
	headers = {'content-type': 'application/json'}
	files = {
		'file' : (filename, open(FILE_FOLDER + filename, 'rb'))
		}
	data = {'title' : filename, 'id' : fileID}
	response = requests.post(url, files=files, data=data, verify=False)
	if (response.status_code == 201): # 
		content = response.content
		responseDict = json.loads(content.decode())
		print (responseDict)
		replicateID = responseDict["Server_ID"]
		
		fileSaved =  {
		        'master_id': server_id,
		        'title': filename,
		        'hash' : hashedFile,
		        'replicate_id' : replicateID
		    }

		response = requests.post(directoryServerAddress + "/NewFiles", json=fileSaved, verify=False)
		print (response)
		


@fileserver.route('/Server/retrieveFile', methods=['GET'])
def retrieveFile():
	if not request.json:
		abort(400)
	else:
		dataDict = request.json
		filename = dataDict['filename']
		for eachFilename in os.listdir(FILE_FOLDER):
			print ("Found in dir " + eachFilename)
			print ("Looking for " + filename)
			if eachFilename == filename:
				openFile = open(FILE_FOLDER + filename, 'r')
				break
		if (openFile != None):
			return (send_file(FILE_FOLDER + filename))
		else:
			return jsonify({"Error" : "Error! File not found at this server!"}), 404

def notifyDirSer():
	url = directoryServerAddress + "/newFileServerNotification"
	data = {'id' : server_id, 'base_url' : 'https://0.0.0.0:%s/Server' % (port_num)}
	response = requests.post(url, json=data, verify=False)
	if (response.status_code == 201): # 
		print ("This file server %s is registered with the directory server." % server_id)
	else:
		print ("Error occured trying to register file server %s with the directory server." % server_id)
	print (response)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='File Server requires an ID (1-100) and a port number (5060 onwards)')
	parser.add_argument("-id", help="id of file server")
	parser.add_argument("-port", help="id of file server")
	args = parser.parse_args()

	if (args.id):
		global server_id
		server_id = args.id
	if (args.port):
		global port_num
		port_num = args.port
	FILE_FOLDER = FILE_FOLDER % server_id
	if not os.path.isdir(FILE_FOLDER):
		os.mkdir(FILE_FOLDER)
	context = (cer, key)
	notifyDirSer()
	fileserver.run( host='0.0.0.0', port=port_num, debug = False/True, ssl_context=context)
	