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

context = SSL.Context(SSL.SSLv23_METHOD)
cer = os.path.join(os.path.dirname(__file__), './resources/CLIENT/udara.com.crt')
key = os.path.join(os.path.dirname(__file__), './resources/CLIENT/udara.com.key')

CLIENT_CACHE_PATH = "./CLIENT_CACHE/"
LOCAL_STORAGE = "./LOCAL_STORAGE/"
commands_dict = {"1" : "read", "2" : "req write", "3" : "write", "4": "upload"}
fileServerAddresses = {'1' : 'https://0.0.0.0:5050/Server/', '2' : 'https://0.0.0.0:5060/Server/'}
directoryServerAddress = "https://0.0.0.0:5010/DirectoryServer/"
DB_NAME_USERS = "Users.db"
DB_NAME_LOCKS = "Locks.db"
fileID = 0
loggedIn = []
clientapp = Flask(__name__)


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
	# modTime = getLastModified(CLIENT_CACHE_PATH + filenameToUpload)
	hashedFile = hashlib.md5(open(CLIENT_CACHE_PATH + filenameToUpload,'rb').read()).hexdigest()
	url = fileServerAddresses['1']
	headers = {'content-type': 'application/json'}
	files = {
		'file' : (filenameToUpload, open(LOCAL_STORAGE + filenameToUpload, 'rb'))
		}
	data = {'title' : filenameToUpload, 'id' : fileID, 'hash' : hashedFile}
	response = requests.post(url + "NewFile", files=files, data=data, verify=False)
	print (response.content)

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
			print ("YAY! YOUVE LOCKED FILE ALREADY!")
		else:
			print ("This file is already locked by a different user (%s). You cannot write to it." % user_name)
	else: #ie not in lock service
		print ("Please use 'req write' function to request a lock on the file")


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
		print ("This file is already locked by a different user (%s). Please try again later." % user_name)
	else: #ie not in lock service, so put in lock and give them file.
		params = (filename, username)
		sql_command = "INSERT INTO locks VALUES (?, ?)"
		insertIntoDB(DB_NAME_LOCKS, params, sql_command)

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
			print ("The db: %s" % resultPassword)
			print ("The user's: %s" % hashedPassword)
	else:
		print ("The user does not exist in DB. Signing up user...")
		hashedPassword = hashlib.md5(password.encode('utf-8')).hexdigest()
		params = (username, hashedPassword)
		sql_command = "INSERT INTO users VALUES (?, ?)"
		insertIntoDB(DB_NAME_USERS, params, sql_command)
		loggedIn.append(username)
		print ("User %s signed up and logged in." % username)




def retrieveReadFile(cmd):
	if (checkLoggedIn(cmd[2]) == False):
		print ("Unable to carry out read task. User is not logged in.")
		return
	filenameToRead = cmd[1]
	if(os.path.isfile(CLIENT_CACHE_PATH + filenameToRead)):
		print ("File exists in client's cache.")
		hashedFile = hashlib.md5(open(CLIENT_CACHE_PATH + filenameToRead,'rb').read()).hexdigest()
		checkOutdated = {
			'filename' : filenameToRead,
			'hash' : hashedFile
		}
		response = requests.get(directoryServerAddress + "CheckHash", json=checkOutdated, verify=False)

		content = response.content
		responseDict = json.loads(content.decode())
		print (responseDict)
		toUpdate = responseDict["upToDate"]
	else:
		print ("File does not exist in client cache.")
		toUpdate = False

	if toUpdate == True: #cache copy is up to date, so can transfer info from cache to user's local storage
		copyfile(CLIENT_CACHE_PATH + filenameToRead, LOCAL_STORAGE + filenameToRead)
		print ("Transferred cached file %s" % filenameToRead)
	else: # request server holding the file from dir ser, then download file from file server (note when the cache's copy is out of date we assume the master file server and replicate file server is up to date)
		#TODO write response to a file, transfer to client cache and transfer to local storage.
		data = {'filename' : filenameToRead}
		response = requests.get(directoryServerAddress + "GetServerID", json=data, verify=False)
		print (response)
		content = response.content
		responseDict = json.loads(content.decode())
		print (responseDict)
		serverIdToQuery = responseDict["ID"]
		url = fileServerAddresses[serverIdToQuery]
		response = requests.get(url + "retrieveFile", json=data, verify=False)
		print (response.content)


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



if __name__ == '__main__':
	if not os.path.isdir(CLIENT_CACHE_PATH):
		os.mkdir(CLIENT_CACHE_PATH)
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
	clientapp.run( host='0.0.0.0', port=5000, debug = True, ssl_context=context)