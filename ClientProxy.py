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
import sqlite3
import argparse


context = SSL.Context(SSL.SSLv23_METHOD)
cer = os.path.join(os.path.dirname(__file__), './resources/CLIENT/udara.com.crt')
key = os.path.join(os.path.dirname(__file__), './resources/CLIENT/udara.com.key')

CLIENT_CACHE_PATH = "./CLIENT_CACHE_%s/"
LOCAL_STORAGE = "./LOCAL_STORAGE/"
commands_dict = {"1" : "Read a File", "2" : "Request Write Access to a File", "3" : "Write to a File", "4": "Upload a new File"}
fileServerAddresses = {}
directoryServerAddress = "https://0.0.0.0:5050/DirectoryServer/"
DB_NAME_USERS = "Users.db"
DB_NAME_LOCKS = "Locks.db"
loggedIn = []
clientapp = Flask(__name__)
filenameToHash = {}
fileID = 0

@clientapp.route('/DISTRIBUTED_LAB4')
def index():
    return 'Flask is running!'

def uploadFile(cmd): #num filename username
	if (checkLoggedIn(cmd[2]) == False):
		print ("Unable to carry out upload task. User is not logged in.")
		return
	filenameToUpload = cmd[1]
	for filename in os.listdir(CLIENT_CACHE_PATH):
		if filename == filenameToUpload:
			print ("Error! File already exists. Please select 'Write'.")
			return 

	#cache file
	copyfile(LOCAL_STORAGE + filenameToUpload, CLIENT_CACHE_PATH + filenameToUpload)
	print ("Cached file %s" % filenameToUpload)

	#send file to main file server
	hashedFile = hashlib.md5(open(CLIENT_CACHE_PATH + filenameToUpload,'rb').read()).hexdigest()
	#get the address of a fileserver that is available for uploading
	url = directoryServerAddress + "requestAServer"
	response = requests.get(url, verify=False)
	content = response.content
	responseDict = json.loads(content.decode())
	print (responseDict)
	serverID = responseDict["server_id"]
	serverURL = responseDict["base_url"]
	if (not serverID in fileServerAddresses):
		fileServerAddresses[serverID] = serverURL

	headers = {'content-type': 'application/json'}
	files = {
		'file' : (filenameToUpload, open(LOCAL_STORAGE + filenameToUpload, 'rb'))
		}
	data = {'title' : filenameToUpload, 'id' : fileID, 'hash' : hashedFile}
	response = requests.post(serverURL + "/NewFile", files=files, data=data, verify=False)
	if (response.code == 201):
		print (response.content)
		filenameToHash[filenameToUpload] = hashedFile
	else: 
		print (response.content)
		print ("This file could not be saved.")

#here the only way to write to a file is that a user has already got a lock on it from req write
def writeToFile(cmd): #num filename username
	if (checkLoggedIn(cmd[2]) == False):
		print ("Unable to carry out upload task. User is not logged in.")
		return
	filename = cmd[1]
	username = cmd[2]
	#check if file exists in lock db
	file_name = queryDB(DB_NAME_LOCKS, "SELECT filename FROM locks WHERE filename=?", filename)
	print(file_name)
	if (file_name): #exists in db
		user_name = queryDB(DB_NAME_LOCKS, "SELECT username FROM locks WHERE filename=?", filename)
		if (user_name == username): #correct person is requesting to use their lock capabilities to write
			print ("You have a pending lock on this file - only YOU can write to it.")
			#post new written file to file servers which will update dir ser
			print ("Caching file...")
			copyfile(LOCAL_STORAGE + filename, CLIENT_CACHE_PATH + filename)
			hashedFile = hashlib.md5(open(CLIENT_CACHE_PATH + filename,'rb').read()).hexdigest()
			# get the master id holding this file
			masterFileServerID = getServerID(filename, True)
			if (masterFileServerID not in fileServerAddresses): #send a request to get it
				url = directoryServerAddress + "requestAServer"
				dataDict = {'server_id': masterFileServerID, 'selectThis' : True}
				response = requests.get(url, json=dataDict, verify=False)
				content = response.content
				responseDict = json.loads(content.decode())
				print (responseDict)
				url = responseDict["base_url"]
				fileServerAddresses[masterFileServerID] = url
			else:	
				url = fileServerAddresses[masterFileServerID]

			files = {
				'file' : (filename, open(CLIENT_CACHE_PATH + filename, 'rb'))
				}
			data = {'title' : filename, 'id' : fileID, 'hash' : hashedFile}
			print ("Informing master file server of an updated File")
			response = requests.post(url + "/UpdateFile", files=files, data=data, verify=False)
			print (response.content)
			#relinquish lock on file
			deleteLock(filename)
		else:
			print ("This file is already locked by a different user (%s). You cannot write to it." % user_name)
	else: #ie not in lock service
		print ("Please use 'req write' function to request a lock on the file")


def deleteLock(filename):
	connection = sqlite3.connect(DB_NAME_LOCKS)
	cursor = connection.cursor()
	params = (filename,)
	cursor.execute("DELETE FROM locks WHERE filename=?", params)
	connection.commit()


def requestWriteAccess(cmd): #num filename username
	if (checkLoggedIn(cmd[2]) == False):
		print ("Unable to carry out request to write; User is not logged in.")
		return
	filename = cmd[1]
	username = cmd[2]
	file_name = queryDB(DB_NAME_LOCKS, "SELECT filename FROM locks WHERE filename=?", filename)
	print(file_name)
	if (file_name): #exists in db
		user_name = queryDB(DB_NAME_LOCKS, "SELECT username FROM locks WHERE filename=?", filename)
		if (user_name != username):
			print ("This file is already locked by a different user (%s). Please try again later." % user_name)
		else:
			print ("You have already locked this file.")
	else: #ie not in lock server, so put in lock and give them file (check cache)
		params = (filename, username)
		sql_command = "INSERT INTO locks VALUES (?, ?)"
		insertIntoDB(DB_NAME_LOCKS, params, sql_command)
		#check if in cache
		if os.path.isfile(CLIENT_CACHE_PATH+filename):
			print ("File exists in cache. Checking if it is up to date...")
			hashedFile = filenameToHash[filename]
			#check if up to date
			upToDate = checkIfUpToDate(hashedFile, filename)
			if upToDate == True: #cache copy is up to date, so can transfer info from cache to user's local storage
				copyfile(LOCAL_STORAGE + filename, CLIENT_CACHE_PATH + filename)
				print ("Transferred cached file with write access: %s" % filename)
			else: # request server holding the file from dir ser, then download file from file server (note when the cache's copy is out of date we assume the master file server and replicate file server is up to date)
				serverID = getServerID(filename, True)
				getFileFromFileServer(serverID, filename)
		else: # request server id from dir ser
			serverID = getServerID(filename, True)
			getFileFromFileServer(serverID, filename)

def getServerID(filename, masterNeededValue):
	data = {'filename' : filename, 'masterNeeded' : masterNeededValue}
	response = requests.get(directoryServerAddress + "GetServerID", json=data, verify=False)
	print (response)
	content = response.content
	responseDict = json.loads(content.decode())
	print (responseDict)
	serverIdToQuery = responseDict["ID"]
	return serverIdToQuery

def getFileFromFileServer(serverID, filename):
	data = {'filename' : filename}
	if (serverID not in fileServerAddresses): #send a request to get it
		url = directoryServerAddress + "requestAServer"
		dataDict = {'server_id': serverID, 'selectThis' : True}
		response = requests.get(url, json=dataDict, verify=False)
		content = response.content
		responseDict = json.loads(content.decode())
		print (responseDict)
		url = responseDict["base_url"]
		fileServerAddresses[serverID] = url
	else:	
		url = fileServerAddresses[serverID]
	response = requests.get(url + "/retrieveFile", json=data, verify=False)
	print ("Writing file to client cache...")
	f = open(CLIENT_CACHE_PATH + filename, 'wb')
	f.write(response.content)
	f.close()
	#update file in local storage
	print ("Transferring file to local storage...")
	copyfile(LOCAL_STORAGE + filename, CLIENT_CACHE_PATH + filename)
	print ("Storing hash of file...")
	hashedFile = hashlib.md5(open(CLIENT_CACHE_PATH + filename,'rb').read()).hexdigest()


def checkIfUpToDate(hashedFile, filename):
	checkOutdated = {
			'filename' : filename,
			'hash' : hashedFile
		}
	response = requests.get(directoryServerAddress + "CheckHash", json=checkOutdated, verify=False)
	content = response.content
	responseDict = json.loads(content.decode())
	print (responseDict)
	upToDate = responseDict["upToDate"]
	return upToDate


def retrieveReadFile(cmd):
	if (checkLoggedIn(cmd[2]) == False):
		print ("Unable to carry out read task. User is not logged in.")
		return
	filenameToRead = cmd[1]
	if(os.path.isfile(CLIENT_CACHE_PATH + filenameToRead)):
		print ("File exists in client's cache.")
		hashedFile = hashlib.md5(open(CLIENT_CACHE_PATH + filenameToRead,'rb').read()).hexdigest()
		upToDate = checkIfUpToDate(hashedFile, filenameToRead)
	else:
		print ("File does not exist in client cache.")
		upToDate = False

	if upToDate == True: #cache copy is up to date, so can transfer info from cache to user's local storage
		copyfile(CLIENT_CACHE_PATH + filenameToRead, LOCAL_STORAGE + filenameToRead)
		print ("Transferred cached file %s" % filenameToRead)
	else: # request server holding the file from dir ser, then download file from file server (note when the cache's copy is out of date we assume the master file server and replicate file server is up to date)
		serverID = getServerID(filenameToRead, False)
		getFileFromFileServer(serverID, filenameToRead)



def insertIntoDB(dbName, params, query):
	connection = sqlite3.connect(dbName)
	cursor = connection.cursor()
	cursor.execute(query, params)
	connection.commit()


def queryDB(dbName, query, param):
	connection = sqlite3.connect(dbName)
	cursor = connection.cursor()
	cursor.execute(query, (param,))
	results = cursor.fetchall()
	if results:
		return results[0][0]
	else:
		return results


def checkLoggedIn(username):
	print (loggedIn)
	print (username)
	if username in loggedIn:
		return True
	else:
		return False

def handleUser(username, password):
	user_name = queryDB(DB_NAME_USERS, "SELECT username FROM users WHERE username=?", username)
	connection = sqlite3.connect(DB_NAME_USERS)
	cursor = connection.cursor()

	print (user_name)
	if (user_name == username):
		print ("The user exists")
		hashedPassword = hashlib.md5(password.encode('utf-8')).hexdigest()
		resultPassword = queryDB(DB_NAME_USERS, "SELECT password FROM users WHERE username=?", username)
		if (resultPassword == hashedPassword):
			print ("The user provided correct credentials")
			loggedIn.append(user_name)
		else:
			print ("The user provided the wrong password")
			print ("The db password: %s" % resultPassword)
			print ("The user's: %s" % hashedPassword)
	else:
		print ("The user does not exist in DB. Signing up user...")
		hashedPassword = hashlib.md5(password.encode('utf-8')).hexdigest()
		params = (username, hashedPassword)
		sql_command = "INSERT INTO users VALUES (?, ?)"
		insertIntoDB(DB_NAME_USERS, params, sql_command)
		loggedIn.append(username)
		print ("User %s signed up and logged in." % username)



def initDB():
	#create user account db
	if (not os.path.isfile(DB_NAME_USERS)):
		connectionMaster = sqlite3.connect(DB_NAME_USERS)
		cursorMaster = connectionMaster.cursor()
		sql_command = """CREATE TABLE users (username VARCHAR(40) PRIMARY KEY, password VARCHAR(100));"""
		cursorMaster.execute(sql_command)
		connectionMaster.commit()
	else: #read from what is already in db
		connection = sqlite3.connect(DB_NAME_USERS)
		cursor = connection.cursor()
		cursor.execute("SELECT * FROM users;")
		result = cursor.fetchall()
		print ("=USER ACCOUNTS=")
		for r in result:
			print (r)
		print ("===")

	#create lock db
	if (not os.path.isfile(DB_NAME_LOCKS)):
		connectionMaster = sqlite3.connect(DB_NAME_LOCKS)
		cursorMaster = connectionMaster.cursor()
		sql_command = """CREATE TABLE locks (filename VARCHAR(40) PRIMARY KEY, username VARCHAR(100));"""
		cursorMaster.execute(sql_command)
		connectionMaster.commit()
	else: #read from what is already in db
		connection = sqlite3.connect(DB_NAME_LOCKS)
		cursor = connection.cursor()
		cursor.execute("SELECT * FROM locks;")
		result = cursor.fetchall()
		print ("=CURRENT LOCKS=")
		for r in result:
			print (r)
		print ("===")

def initCacheAndReadings():
	
	if not os.path.isdir(CLIENT_CACHE_PATH):
		os.mkdir(CLIENT_CACHE_PATH)
	else: #read from it and initialise hashes
		for filename in os.listdir(CLIENT_CACHE_PATH):
			hashedFile = hashlib.md5(open(CLIENT_CACHE_PATH + filename,'rb').read()).hexdigest()
			filenameToHash[filename] = hashedFile
		print (filenameToHash)




if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Client Proxy Server requires an ID (1-100) and a port number (5000 - 5040)')
	parser.add_argument("-id", help="id of file server")
	parser.add_argument("-port", help="id of file server")
	args = parser.parse_args()

	if (args.id):
		global client_id
		client_id = args.id
	if (args.port):
		global port_num
		port_num = args.port
	CLIENT_CACHE_PATH = CLIENT_CACHE_PATH % (client_id)
	initCacheAndReadings()
	initDB()
	print ("== LOG IN ==")
	loginName = input("User Name: ")
	password = input("Password: ")
	handleUser(loginName, password)
	while 1:
		print ("number filename username")
		cmd = input("Commands: " + str(commands_dict) + "\n")
		cmd = cmd.split(" ")
		if (cmd[0] == "1"):
			print ("Client wants to read")
			retrieveReadFile(cmd)
		elif (cmd[0] == "2"):
			print ("Client wants to request write access")
			requestWriteAccess(cmd)
		elif (cmd[0] == "3"):
			print ("Client wants to write to a file")
			writeToFile(cmd)
		elif (cmd[0] == "4"):
			print ("Client wants to upload")
			uploadFile(cmd)


	context = (cer, key)
	clientapp.run( host='0.0.0.0', port=port_num, debug = True, ssl_context=context)