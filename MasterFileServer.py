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


@masterfileserver.route('/MasterFileServer')
def index():
    return 'MasterFileServer is running!'

@masterfileserver.route('/MasterFileServer/NewFile', methods=["POST"])
def addFile():
	if not request.json:
		return make_response(jsonify({'error': 'Not found'}), 404)
	else:
		return request.json['file']
	

if __name__ == '__main__':
	context = (cer, key)
	masterfileserver.run( host='0.0.0.0', port=5050, debug = False/True, ssl_context=context)