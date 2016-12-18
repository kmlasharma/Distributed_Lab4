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

@dirserverapp.route('/DirectoryServer/CheckHash', methods=['GET'])
def checkTimeStamp():
	if not request.json:
		abort(400)
	else:
		checkDict = request.json
		file_name = checkDict['filename']
		hashedString = checkDict['hash']
		connection = sqlite3.connect(DB_NAME)
		cursor = connection.cursor()

		print ("fileDirectory")
		cursor.execute("SELECT * FROM fileDirectory;")
		result = cursor.fetchall()
		for r in result:
			print(r)
		cursor.execute("SELECT hash FROM fileDirectory WHERE filename=?", (file_name,))
		result = cursor.fetchall()
		if result is None:
			print ("ITS NONE!!!!!!!")
		else:
			print ("ITS NOT NONE!!!!!!!")
			for r in result:
				print(r[0])
		print (hashedString)
		if r[0] == hashedString:
			return make_response(jsonify({'upToDate': True}), 200)
		else:
			return make_response(jsonify({'upToDate': False}), 200)

@dirserverapp.route('/DirectoryServer/GetServerID', methods=['GET'])
def getServerID():
	if not request.json:
		abort(400)
	else:
		dataDict = request.json
		filename = dataDict['filename']
		master = dataDict['masterNeeded']
		connection = sqlite3.connect(DB_NAME)
		cursor = connection.cursor()
		if master == True:
			cursor.execute("SELECT master_server_id FROM fileDirectory WHERE filename=?", (filename,))
		else:
			cursor.execute("SELECT replicate_server_id FROM fileDirectory WHERE filename=?", (filename,))
		result = cursor.fetchall()
		replicate_server_id = result[0][0]
		print (result)
		print (replicate_server_id)
		print ("Return replicate id of : %s" % replicate_server_id)
		return make_response(jsonify({'ID': replicate_server_id}), 200)

@dirserverapp.route('/DirectoryServer/UpdateFile', methods=['POST'])
def updateDB():
	if not request.json:
		abort(400)
	else:
		newFilesDict = request.json
		conn = sqlite3.connect(DB_NAME)
		cursor = conn.cursor()

		hashedFile = newFilesDict['hash']
		title = newFilesDict['title']
		params = (hashedFile, title)
		sql_command = "UPDATE fileDirectory SET hash = ? WHERE filename = ?;"
		cursor.execute(sql_command, params)
		conn.commit()

		print ("fileDirectory")
		printDB()

		return "Successfully updated the database!", 201
		

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
		hashedFile = newFilesDict['hash']
		replicate_id = newFilesDict['replicate_id']

		params = (master_id, title, hashedFile, replicate_id)
		sql_command = "INSERT INTO fileDirectory VALUES (?, ?, ?, ?)"
		cursor.execute(sql_command, params)
		conn.commit()

		print ("fileDirectory")
		printDB()

		return "Successfully saved to database!", 201
	
def printDB():
	connection = sqlite3.connect(DB_NAME)
	cursor = connection.cursor()
	cursor.execute("SELECT * FROM fileDirectory;")
	result = cursor.fetchall()
	print ("===")
	for r in result:
		print (r)
	print ("===")


def initDB():
	filenameMaster = "%s" % DB_NAME
	if (not os.path.isfile(filenameMaster)):
		connectionMaster = sqlite3.connect("fileDirectory.db")
		cursorMaster = connectionMaster.cursor()
		sql_command = """CREATE TABLE fileDirectory ( master_server_id VARCHAR(100) , filename VARCHAR(30) PRIMARY KEY, hash VARCHAR (200), replicate_server_id VARCHAR(100));"""
		cursorMaster.execute(sql_command)
		connectionMaster.commit()
	else: #read from what is already in db
		printDB()
if __name__ == '__main__':
	initDB()

	context = (cer, key)
	dirserverapp.run( host='0.0.0.0', port=5010, debug = True, ssl_context=context)