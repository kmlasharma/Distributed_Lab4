Distributed File Server
===================


This distributed file server is written in python3, using the Flask framework. The distributed servers communicate via HTTPs requests and responses, using jSON.

----------


Design
-------------

There are three main servers in the system:
- Directory Server
- File Server
- Client Proxy


#### Directory Server
The Directory Server is essentially the dynamic controller of the system - it keeps track of live file servers in the system and what files they contain, selects appropriate servers for storage of new files, contains details on each file server and how to contact them. The directory server must be run first. 

####  File Server
File Servers can be dynamically allocated to the system, with the user selecting a different port and ID in order to run each file server. They are the essential storage unit of the system; their responsibilities include the storage of new files, updating existing files, creating replicates within the system, and communicating with the client to return files.

#### Client Proxy
The Client Proxy is the 'man in the middle' between the user and the system, handling all user requests such as, log in, uploading files, downloading files and writing to files. Client Proxies can also be dynamically added to the system, each running on a different user-selected port and ID. The Client Proxy translates the user requests into HTTP requests to both the Directory Server and File Server.



Features
-------------------

#### Security
Security is guaranteed by the system using HTTPs. Each server communicates via HTTPs and TCP handshakes, with OpenSSL self signed certs and keys. During the running of the system, the user may see some warning with the regards to the certs, which is due to the fact that they are unsigned by a CA.

#### Replication
Each file is hosted on two servers, a master server and a replicate server. Upon uploading a file for the first time, the directory server will return a URL corresponding to a file server available to take the file. Once a file has been posted to the file server, the fileserver will dynamically select another live file server onto which, the file will be replicated. The Directory Server is notified of all locations of the file, in order to handle future requests to read/write etc. Whenever a file is edited, both the master server and the replication server will update their copies.
> **Note:** The master file server and replication file server are dynamically chosen at every file upload. They are different for each file.


#### Caching
All caching in the system is performed at the client side. All files uploaded to the file servers are also kept in a cache by the client. Should a client request a certain file for read/write, the client can check 1) if they file exists in their cache and 2) is this file up to date. In order to check that a file is up to date with the file servers' copy, the directory server can compare the hashes of the client's copy and the file servers' copy. If they are different, the Client assumes the file servers' copy is the up to date one, and will subsequently request it for download. All subsequent editions to a file will be relayed to the file servers' copy. 

#### Locking
In order to write to a file in the system, the user must first request a file in **write mode**. If the file is currently unlocked, the client will allocate the lock to the user and only then, can the user perform write updates. Write locks are relinquished once the user has successfully written to the file, and it's edition is known by the directory server and file servers. Should other clients want to write to the file as well, they must wait until the lock is relinquished.

#### Directory Service

The directory service is implemented by the directory server, responsible for mapping the file names of files currently in the system onto file identifiers of the various file servers. If a client proxy needs to download a file from the system, they must first contact the directory server to retrieve the location (ie the URL of the file server) of the file. Should a Client require the the location due to a write request, the master file server URL for that file will be returned. Otherwise, for operations such as read, the replicate server URL will be returned. 

#### Transactions
Once a write request has been transmitted by the client proxy to the master file server hosting the specific file, it is the master file server's responsibility to update the replicate of the file, and to notify the directory server of the new file. The replicate server will simply redownload the new file from the master server, while the directory server will receive a new hash of the updated file.

----------

Running & Dependencies
-------------

#### External Dependencies

The following are required:
- Python3 
- Flask
```sh
$ pip3 install Flask
```

- Python3 Requests
```sh
$ pip3 install Requests
```


#### Running

In order to run the system, the Directory Server must be run first. This is because as File Servers become live, they will immediately attempt to notify the directory server of their existence. Similarly, once a user is logged into the Client, the Client will attempt to contact the directory server and pull down a list of files that currently exist in the system. The following is an example of how to run the system, with 2 Clients and 2 live File Servers.
```sh
$ python3 DirectoryServer.py
$ python3 FileServer.py -id 1 -port 5060
$ python3 FileServer.py -id 2 -port 5070
$ python3 ClientProxy.py -id 1 -port 5000
$ python3 ClientProxy.py -id 2 -port 5010
```

**Note:** 
- All files for Client Proxy interractions (ie where the Client Proxy will read files from/save files to) must be placed into the 'Local Storage' Folder. Paths to files outside of the system will not be accepted. 
- Upon the log in prompt, enter any username and any password and you will be added into the system. 
- In order to communicate with the system, enter the number corresponding to your request between 1 and 4 (the options will be displayed) followed by the name of your file which should exist either in your local storage folder or in the system itself. (ie when uploading, the filename should not exist already in the system, or when reading, the filename should exist within the system).