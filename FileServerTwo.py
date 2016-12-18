from flask import Flask, jsonify
from flask import abort
from flask import make_response
from flask import request
from flask import Response
import requests
import os
import sys
from OpenSSL import SSL
import sqlite3
import argparse
from flask import send_file

context = SSL.Context(SSL.SSLv23_METHOD)
cer = os.path.join(os.path.dirname(__file__), './resources/MASTER_FILE_SERVER/udara.com.crt')
key = os.path.join(os.path.dirname(__file__), './resources/MASTER_FILE_SERVER/udara.com.key')
fileServerAddressesForRep = {1: 'https://0.0.0.0:5050/Server/Replicate'}
directoryServerAddress = "https://0.0.0.0:5010/DirectoryServer"
fileserver = Flask(__name__)
FILE_FOLDER = "./FILE_SERVER_FOLDER_%s/"



@fileserver.route('/Server')
def index():
    return 'File Server is running!'

@fileserver.route('/Server/NewFile', methods=["POST"])
def uploadNewFileFromClient():
	if not request.files:
		return make_response(jsonify({'error': 'Not found'}), 404)
	else:
		newFile = request.files["file"]
		filename = request.form['title']
		fileID = request.form['id']
		hashedFile = request.form['hash']
		print (hashedFile)
		path = FILE_FOLDER + filename
		newFile.save(path)
		print ("Successfully saved %s on server %s" % (filename, server_id))
		makeReplicate(newFile, filename, fileID, hashedFile)
		return "Successfully saved master copy onto server %s" % server_id, 201

@fileserver.route('/Server/UpdateFile', methods=["POST"])
def updateFileFromClient():
	if not request.files:
		return make_response(jsonify({'error': 'Not found'}), 404)
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
		return "Successfully saved master copy onto server %s" % server_id, 201

#send the file to other server for replication
def updateReplicate(fileToReplicate, filename, fileID, hashedFile):
	url = fileServerAddressesForRep[1]
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
	url = fileServerAddressesForRep[2]
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

	

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='File Server requires an ID')
	parser.add_argument("-id", help="id of file server")
	args = parser.parse_args()

	if (args.id):
		global server_id
		server_id = args.id
	FILE_FOLDER = FILE_FOLDER % server_id
	if not os.path.isdir(FILE_FOLDER):
		os.mkdir(FILE_FOLDER)

	context = (cer, key)
	fileserver.run( host='0.0.0.0', port=5060, debug = False/True, ssl_context=context)