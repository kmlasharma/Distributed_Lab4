from flask import Flask, jsonify
from flask import abort
from flask import make_response
from flask import request
import os
import sys
from OpenSSL import SSL
import sqlite3

DB_REPLICATES_NAME = "replicates.db"
DB_MASTER_NAME = "master.db"
context = SSL.Context(SSL.SSLv23_METHOD)
cer = os.path.join(os.path.dirname(__file__), './resources/DIRECTORY_SERVER/udara.com.crt')
key = os.path.join(os.path.dirname(__file__), './resources/DIRECTORY_SERVER/udara.com.key')

dirserverapp = Flask(__name__)


@dirserverapp.route('/DirectoryServer')
def index():
    return 'DirectoryServer is running!'

@dirserverapp.route('/DirectoryServer/NewFiles', methods=['POST'])
def addToDB():
	if not request.json:
		abort(400)
	else:
		newFilesDict = request.json
		connectionReplicates = sqlite3.connect(DB_REPLICATES_NAME)
		cursorReplicates = connectionReplicates.cursor()

		connectionMaster = sqlite3.connect(DB_MASTER_NAME)
		cursorMaster = connectionMaster.cursor()

		for fileinfo in newFilesDict:
			master = fileinfo['master']
			server_id = fileinfo['id']
			filename = fileinfo['title']
			if (master == True):
				modTime = fileinfo['last-modified']
				params = (server_id, filename, modTime)
				print (params)
				sql_command = "INSERT INTO master VALUES (?, ?, ?)"
				cursorMaster.execute(sql_command, params)
				connectionMaster.commit()
			else:
				params = (server_id, filename)
				sql_command = "INSERT INTO replicates VALUES (?, ?)"
				cursorReplicates.execute(sql_command, params)
				connectionReplicates.commit()


		print ("Master")
		cursorMaster.execute("SELECT * FROM master;")
		result = cursorMaster.fetchall()
		for r in result:
			print(r)

		print ("Replicates")
		cursorReplicates.execute("SELECT * FROM replicates;")
		result = cursorReplicates.fetchall()
		for r in result:
			print(r)

		return "Successfully saved to database!", 201
	
def initDB():
	filenameReplicates = "%s" % DB_REPLICATES_NAME
	filenameMaster = "%s" % DB_MASTER_NAME
	if (not os.path.isfile(filenameReplicates)): #if db doesn't exist
		connection = sqlite3.connect("replicates.db")
		cursor = connection.cursor()
		sql_command = """CREATE TABLE replicates ( server_id VARCHAR(100) PRIMARY KEY, filename VARCHAR(30));"""
		cursor.execute(sql_command)
		connection.commit()
	
	if (not os.path.isfile(filenameMaster)):
		connectionMaster = sqlite3.connect("master.db")
		cursorMaster = connectionMaster.cursor()
		sql_command = """CREATE TABLE master ( server_id VARCHAR(100) , filename VARCHAR(30) PRIMARY KEY, last_modified VARCHAR (30));"""
		cursorMaster.execute(sql_command)
		connectionMaster.commit()

if __name__ == '__main__':
	initDB()

	context = (cer, key)
	dirserverapp.run( host='0.0.0.0', port=5010, debug = True, ssl_context=context)