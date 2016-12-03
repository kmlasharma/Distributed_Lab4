from flask import Flask, jsonify
from flask import abort
from flask import make_response
import requests
import os
import sys
from OpenSSL import SSL
import json

context = SSL.Context(SSL.SSLv23_METHOD)
cer = os.path.join(os.path.dirname(__file__), './resources/CLIENT/udara.com.crt')
key = os.path.join(os.path.dirname(__file__), './resources/CLIENT/udara.com.key')

CLIENT_CACHE_PATH = "./CLIENT_CACHE/"
LOCAL_STORAGE = "./LOCAL_STORAGE/"
commands_list = ["req read", "req write", "write", "upload"]
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

	url = 'https://0.0.0.0:5050/MasterFileServer/NewFile'
	with open(LOCAL_STORAGE + filenameToUpload, "rb") as fileOpen:
		f = fileOpen.read()
	headers = {'content-type': 'application/json'}
	print ("BBBBB")
	payload = {'title' : filenameToUpload, 'id' : str(fileID), 'file': f.decode('utf-8')}
	print (json.dumps(payload))
	response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)
	print (response.content.decode('utf-8'))



if __name__ == '__main__':
	if not os.path.isdir(CLIENT_CACHE_PATH):
		os.mkdir(CLIENT_CACHE_PATH)

	cmd = input("Commands: " + str(commands_list) + "\n")
	print (cmd)
	if (commands_list[3] in cmd):
		uploadFile(cmd)


	context = (cer, key)
	clientapp.run( host='0.0.0.0', port=5000, debug = True, ssl_context=context)