from flask import Flask, jsonify
from flask import abort
from flask import make_response
from flask import request
import os
import sys
from OpenSSL import SSL
import sqlite3

DB_NAME = "fileDirectory.db"
context = SSL.Context(SSL.SSLv23_METHOD)
cer = os.path.join(os.path.dirname(__file__), './resources/DIRECTORY_SERVER/udara.com.crt')
key = os.path.join(os.path.dirname(__file__), './resources/DIRECTORY_SERVER/udara.com.key')

dirserverapp = Flask(__name__)


@dirserverapp.route('/DirectoryServer')
def index():
    return 'DirectoryServer is running!'

@dirserverapp.route('/DirectoryServer/CheckTimestamps', methods=['GET'])
def checkTimeStamp():
	if not request.json:
		abort(400)
	else:
		checkDict = request.json
		file_name = checkDict['filename']
		modTime = checkDict['last_modified']
		connection = sqlite3.connect(DB_NAME)
		cursor = connection.cursor()

		print ("fileDirectory")
		cursor.execute("SELECT * FROM fileDirectory;")
		result = cursor.fetchall()
		for r in result:
			print(r)
		cursor.execute("SELECT last_modified FROM fileDirectory WHERE filename=?", (file_name,))
		result = cursor.fetchall()
		if result is None:
			print ("ITS NONE!!!!!!!")
		else:
			print ("ITS NOT NONE!!!!!!!")
			for r in result:
				print(r[0])
		print (modTime)
		if r[0] == modTime:
			return make_response(jsonify({'upToDate': True}), 200)
		else:
			return make_response(jsonify({'upToDate': False}), 200)


		

@dirserverapp.route('/DirectoryServer/NewFiles', methods=['POST'])
def addToDB():
	if not request.json:
		abort(400)
	else:
		newFilesDict = request.json
		conn = sqlite3.connect(DB_NAME)
		cursor = conn.cursor()

		master_id = newFilesDict['master_id']
		title = newFilesDict['title']
		modTime = newFilesDict['last_modified']
		replicate_id = newFilesDict['replicate_id']

		params = (master_id, title, modTime, replicate_id)
		sql_command = "INSERT INTO fileDirectory VALUES (?, ?, ?, ?)"
		cursor.execute(sql_command, params)
		conn.commit()

		print ("fileDirectory")
		cursor.execute("SELECT * FROM fileDirectory;")
		result = cursor.fetchall()
		for r in result:
			print(r)

		return "Successfully saved to database!", 201
	
def initDB():
	filenameMaster = "%s" % DB_NAME
	if (not os.path.isfile(filenameMaster)):
		connectionMaster = sqlite3.connect("fileDirectory.db")
		cursorMaster = connectionMaster.cursor()
		sql_command = """CREATE TABLE fileDirectory ( master_server_id VARCHAR(100) , filename VARCHAR(30) PRIMARY KEY, last_modified VARCHAR (30), replicate_server_id VARCHAR(100));"""
		cursorMaster.execute(sql_command)
		connectionMaster.commit()

if __name__ == '__main__':
	initDB()

	context = (cer, key)
	dirserverapp.run( host='0.0.0.0', port=5010, debug = True, ssl_context=context)