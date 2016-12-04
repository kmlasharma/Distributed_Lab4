from flask import Flask, jsonify
from flask import abort
from flask import make_response
from flask import request
import os
import sys
from OpenSSL import SSL
import sqlite3

DB_NAME = "replicates.db"
context = SSL.Context(SSL.SSLv23_METHOD)
cer = os.path.join(os.path.dirname(__file__), './resources/DIRECTORY_SERVER/udara.com.crt')
key = os.path.join(os.path.dirname(__file__), './resources/DIRECTORY_SERVER/udara.com.key')

dirserverapp = Flask(__name__)


@dirserverapp.route('/DirectoryServer')
def index():
    return 'DirectoryServer is running!'

@dirserverapp.route('/DirectoryServer/NewReplicate' methods=['POST'])
def addToDB():
	if not request.json:
		abort(400)
	print request.json
	
def initDB():
	if (not os.path.isfile('./%s') % DB_NAME): #if db doesn't exist
		connection = sqlite3.connect("replicates.db")
		cursor = connection.cursor()
		sql_command = """CREATE TABLE replicates ( server_id INTEGER(100) PRIMARY KEY, filename VARCHAR(30), server_ip VARCHAR(20), direction CHAR(1));"""
		cursor.execute(sql_command)
		connection.commit()
	else:
		connection = sqlite3.connect("replicates.db")
		cursor = connection.cursor()

if __name__ == '__main__':
	initDB()

	context = (cer, key)
	dirserverapp.run( host='0.0.0.0', port=5010, debug = True, ssl_context=context)