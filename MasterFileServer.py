from flask import Flask, jsonify
from flask import abort
from flask import make_response
from flask import request
import os
import sys
from OpenSSL import SSL
import sqlite3

context = SSL.Context(SSL.SSLv23_METHOD)
cer = os.path.join(os.path.dirname(__file__), './resources/MASTER_FILE_SERVER/udara.com.crt')
key = os.path.join(os.path.dirname(__file__), './resources/MASTER_FILE_SERVER/udara.com.key')

masterfileserver = Flask(__name__)
FILE_FOLDER = "./FILE_SERVER_FOLDER/"


@masterfileserver.route('/MasterFileServer')
def index():
    return 'MasterFileServer is running!'

@masterfileserver.route('/MasterFileServer/NewFile', methods=["POST"])
def addFile():
	if not request.files:
		return make_response(jsonify({'error': 'Not found'}), 404)
	else:
		# return request.json['file']
		# filename = request.json['title']
		# fileBytes = request.json['file']
		# print (fileBytes)
		# print (type(fileBytes))
		# with open(filename,'wb') as f:
		# 	f.write(fileBytes.encode())
		newFile = request.files["file"]
		filename = request.form['title']
		path = FILE_FOLDER + filename
		newFile.save(path)
		


	

if __name__ == '__main__':
	if not os.path.isdir(FILE_FOLDER):
		os.mkdir(FILE_FOLDER)

	context = (cer, key)
	masterfileserver.run( host='0.0.0.0', port=5050, debug = False/True, ssl_context=context)