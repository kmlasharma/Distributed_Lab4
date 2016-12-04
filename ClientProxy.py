from flask import Flask, jsonify
from flask import abort
from flask import make_response
import requests
import os
import sys
from OpenSSL import SSL
import json
import base64


context = SSL.Context(SSL.SSLv23_METHOD)
cer = os.path.join(os.path.dirname(__file__), './resources/CLIENT/udara.com.crt')
key = os.path.join(os.path.dirname(__file__), './resources/CLIENT/udara.com.key')

CLIENT_CACHE_PATH = "./CLIENT_CACHE/"
LOCAL_STORAGE = "./LOCAL_STORAGE/"
commands_list = ["req read", "req write", "write", "upload"]
fileServerAddresses = ['https://0.0.0.0:5050/Server/NewFile', 'https://0.0.0.0:5060/Server/NewFile']
fileID = 0

clientapp = Flask(__name__)

tasks = [
    {
        'id': 1,
        'title': u'Buy groceries',
        'description': u'Milk, Cheese, Pizza, Fruit, Tylenol', 
        'done': False
    },
    {
        'id': 2,
        'title': u'Learn Python',
        'description': u'Need to find a good Python tutorial on the web', 
        'done': False
    }
]

@clientapp.route('/DISTRIBUTED_LAB4')
def index():
    return 'Flask is running!'

@clientapp.route('/data')
def names():
    data = {"names": ["John", "Jacob", "Julie", "Jennifer"]}
    return jsonify(data)

def uploadFile(cmd):
	cmdarr = cmd.split(" ")
	filenameToUpload = cmdarr[1]
	for filename in os.listdir(CLIENT_CACHE_PATH):
		if filename == filenameToUpload:
			print ("Error! File exists!")
			return 

	#send file to main file server

	url = fileServerAddresses[0]
	headers = {'content-type': 'application/json'}
	files = {
		'file' : (filenameToUpload, open(LOCAL_STORAGE + filenameToUpload, 'rb'))
		}
	data = {'title' : filenameToUpload, 'id' : fileID}
	response = requests.post(url, files=files, data=data, verify=False)
	print (response.content)




if __name__ == '__main__':
	if not os.path.isdir(CLIENT_CACHE_PATH):
		os.mkdir(CLIENT_CACHE_PATH)
	cmd = input("Commands: " + str(commands_list) + "\n")
	print (cmd)
	if (commands_list[3] in cmd):
		uploadFile(cmd)


	context = (cer, key)
	clientapp.run( host='0.0.0.0', port=5000, debug = True, ssl_context=context)