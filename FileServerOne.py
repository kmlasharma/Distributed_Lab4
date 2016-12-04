from flask import Flask, jsonify
from flask import abort
from flask import make_response
from flask import request
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
fileServerAddressesForRep = {2 : 'https://0.0.0.0:5060/Server/Replicate'}
directoryServerAddress = "https://0.0.0.0:5010/DirectoryServer/NewFiles"
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
		path = FILE_FOLDER + filename
		newFile.save(path)
		print ("Successfully saved %s" % filename)
		makeReplicate(newFile, filename, fileID)
		return "Successfully saved master copy onto server %s" % server_id, 201

@fileserver.route('/Server/Replicate', methods=["POST"])
def acceptReplicate():
	if not request.files:
		return make_response(jsonify({'error': 'No file included'}), 404)
	else:
		newFile = request.files["file"]
		filename = request.form['title']
		path = FILE_FOLDER + filename
		newFile.save(path)
		print ("Successfully saved %s" % filename)
		return jsonify({"Server_ID" : server_id, "Message" : "Successfully saved replicate onto server"}), 201

#send the file to other server for replication
def makeReplicate(fileToReplicate, filename, fileID):
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
		
		fileSaved = [
		    {
		        'id': server_id,
		        'title': filename,
		        'master' : True
		    },
		    {
		        'id': replicateID,
		        'title': filename,
		        'master' : False
		    }
		]

		response = requests.post(directoryServerAddress, json=fileSaved, verify=False)
		print (response)



		

	

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
	fileserver.run( host='0.0.0.0', port=5050, debug = False/True, ssl_context=context)