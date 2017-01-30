from flask import Flask, jsonify
from flask import abort
from flask import make_response
from flask import request
import os
import sys
from OpenSSL import SSL
import sqlite3

FILE_DIRECTORY_DB_NAME = "fileDirectory.db"
FILE_SERVERS_DB_NAME = "fileServers.db"
context = SSL.Context(SSL.SSLv23_METHOD)
cer = os.path.join(os.path.dirname(__file__), './resources/DIRECTORY_SERVER/udara.com.crt')
key = os.path.join(os.path.dirname(__file__), './resources/DIRECTORY_SERVER/udara.com.key')

dirserverapp = Flask(__name__)


@dirserverapp.route('/DirectoryServer/pullDownFilenames', methods=['GET'])
def pullDownFilenames():
	conn = sqlite3.connect(FILE_DIRECTORY_DB_NAME)
	cursor = conn.cursor()
	cursor.execute("SELECT filename FROM fileDirectory;")
	result = cursor.fetchall()
	print (result)
	if (not result):
		return "No files currently in DB.", 202
	else:
		listOfFilenames = []
		for eachTuple in result:
			listOfFilenames.append(eachTuple[0])
		return make_response(jsonify(listOfFilenames), 200)

@dirserverapp.route('/DirectoryServer/newFileServerNotification', methods=['POST'])
def enterNewFileServer():
	print (request.json)
	if not request.json:
		abort(400)
	else:
		conn = sqlite3.connect(FILE_SERVERS_DB_NAME)
		cursor = conn.cursor()
		infoDict = request.json
		serverid = infoDict['id']
		cursor.execute("SELECT server_id FROM listOfFileServers WHERE server_id=?", (serverid,))
		result = cursor.fetchall()
		if not result:
			print ("This entry does not already exist. Entering...")
			serverurl = infoDict['base_url']
			params = (serverid, serverurl)
			sql_command = "INSERT INTO listOfFileServers VALUES (?, ?)"
			cursor.execute(sql_command, params)
			conn.commit()

			print ("listOfFileServers")
			printDB("listOfFileServers", FILE_SERVERS_DB_NAME)
			return "Successfully saved to file server database!", 200
		else:
			print ("This entry already exists. Aborting..")
			print (result)
			abort(400)

#two ways to request a server, 1) request any; you dont care which and 2) request a specific one by their id and get url back
@dirserverapp.route('/DirectoryServer/requestAServer', methods=['GET'])
def requestAServer():
	print (request.json)
	if not request.json: #random file server requested
		connection = sqlite3.connect(FILE_SERVERS_DB_NAME)
		cursor = connection.cursor()
		cursor.execute("SELECT * FROM listOfFileServers ORDER BY RANDOM() LIMIT 1")
		result = cursor.fetchall()
		print (result)
		dictResponse = jsonify({'server_id': result[0][0], 'base_url': result[0][1]})
		print (dictResponse)
		return make_response(dictResponse, 200)
	else: #specific file server requested
		infoDict = request.json
		connection = sqlite3.connect(FILE_SERVERS_DB_NAME)
		cursor = connection.cursor()
		fileServerId = infoDict['server_id']
		getThisServer = infoDict['selectThis']
		if (getThisServer == True): #server wants back the url for this specific id
			cursor.execute("SELECT base_url FROM listOfFileServers WHERE server_id=?", (fileServerId,))
			result = cursor.fetchall()
			dictResponse = jsonify({'base_url': result[0][0]})
			print (dictResponse)
			return make_response(dictResponse, 200)
		else: #server does not want back the url for this id
			cursor.execute("SELECT server_id, base_url FROM listOfFileServers WHERE server_id!=? ORDER BY RANDOM() LIMIT 1", (fileServerId,))
			result = cursor.fetchall()
			print (result)
			dictResponse = jsonify({'server_id' : result[0][0], 'base_url': result[0][1]})
			print (dictResponse)
			return make_response(dictResponse, 200)


@dirserverapp.route('/DirectoryServer/CheckHash', methods=['GET'])
def checkTimeStamp():
	if not request.json:
		abort(400)
	else:
		checkDict = request.json
		file_name = checkDict['filename']
		hashedString = checkDict['hash']
		connection = sqlite3.connect(FILE_DIRECTORY_DB_NAME)
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
		connection = sqlite3.connect(FILE_DIRECTORY_DB_NAME)
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
		conn = sqlite3.connect(FILE_DIRECTORY_DB_NAME)
		cursor = conn.cursor()

		hashedFile = newFilesDict['hash']
		title = newFilesDict['title']
		params = (hashedFile, title)
		sql_command = "UPDATE fileDirectory SET hash = ? WHERE filename = ?;"
		cursor.execute(sql_command, params)
		conn.commit()

		print ("fileDirectory")
		printDB("fileDirectory", FILE_DIRECTORY_DB_NAME)

		return "Successfully updated the database!", 200
		

@dirserverapp.route('/DirectoryServer/NewFiles', methods=['POST'])
def addToDB():
	if not request.json:
		abort(400)
	else:
		newFilesDict = request.json
		conn = sqlite3.connect(FILE_DIRECTORY_DB_NAME)
		cursor = conn.cursor()

		title = newFilesDict['title']
		cursor.execute("SELECT master_server_id FROM fileDirectory WHERE filename=?", (title,))
		result = cursor.fetchall()
		print (result)
		if (not result):
			fileserverid_retrieved = None
		else:
			fileserverid_retrieved = result[0][0]
			
		print (fileserverid_retrieved)
		if (fileserverid_retrieved is None): #if filename is null, doesnt exist, so insert it
			master_id = newFilesDict['master_id']
			hashedFile = newFilesDict['hash']
			replicate_id = newFilesDict['replicate_id']
			params = (master_id, title, hashedFile, replicate_id)
			sql_command = "INSERT INTO fileDirectory VALUES (?, ?, ?, ?)"
			cursor.execute(sql_command, params)
			conn.commit()
			print ("fileDirectory:")
			printDB("fileDirectory", FILE_DIRECTORY_DB_NAME)
			return "Successfully saved to database!", 200
		else:
			return ("This file %s exists on server %s" % (title, fileserverid_retrieved)), 304
	
def printDB(nameOfDB, DB_NAME):
	connection = sqlite3.connect(DB_NAME)
	cursor = connection.cursor()
	query = "SELECT * FROM {}".format(nameOfDB)
	cursor.execute(query)
	result = cursor.fetchall()
	print ("===")
	for r in result:
		print (r)
	print ("===")


def initDB():
	filenameMaster = "%s" % FILE_DIRECTORY_DB_NAME
	if (not os.path.isfile(filenameMaster)):
		print ("Creating DB %s as it does not exist." % filenameMaster)
		connectionMaster = sqlite3.connect(filenameMaster)
		cursorMaster = connectionMaster.cursor()
		sql_command = """CREATE TABLE fileDirectory ( master_server_id VARCHAR(100) , filename VARCHAR(30) PRIMARY KEY, hash VARCHAR (200), replicate_server_id VARCHAR(100));"""
		cursorMaster.execute(sql_command)
		connectionMaster.commit()
	else: #read from what is already in db
		print ("DB %s already exits:" % filenameMaster)
		printDB("fileDirectory", FILE_DIRECTORY_DB_NAME)

	filenameFileSers = "%s" % FILE_SERVERS_DB_NAME
	if (not os.path.isfile(filenameFileSers)):
		print ("Creating DB %s as it does not exist" % filenameFileSers)
		connectionMaster = sqlite3.connect(filenameFileSers)
		cursorMaster = connectionMaster.cursor()
		sql_command = """CREATE TABLE listOfFileServers ( server_id VARCHAR(100) PRIMARY KEY, base_url VARCHAR(200));"""
		cursorMaster.execute(sql_command)
		connectionMaster.commit()
	else: #drop the contents (assuming when dir server was last dropped, all file servers were dropped.)
		print ("Dropping DB %s as it already exists" % filenameFileSers)
		connection = sqlite3.connect(FILE_SERVERS_DB_NAME)
		cursor = connection.cursor()
		cursor.execute("""DROP TABLE listOfFileServers""")
		print ("Creating DB %s as it was dropped." % filenameFileSers)
		sql_command = """CREATE TABLE listOfFileServers ( server_id VARCHAR(100) PRIMARY KEY, base_url VARCHAR(200));"""
		cursor.execute(sql_command)
		connection.commit()
		

if __name__ == '__main__':
	initDB()

	context = (cer, key)
	dirserverapp.run( host='0.0.0.0', port=5050, debug = False, ssl_context=context)