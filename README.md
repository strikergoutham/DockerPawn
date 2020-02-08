# DockerPawn
Script Name : Docker Pawn(non TLS REST endpoints)

Author : Goutham Madhwaraj K B ( @barriersec.com)


Description :

This tool can be used to exploit docker REST API end points which are available without TLS and which are exposed publicly.
UnAuth Exposed endpoints = root level access on the host system.

This Script Does the following :

>> Gathers Remote Host and docker daemon Information
>> uses existing alpine base image if available / pulls a new alpine image from the docker registry.
>> deploys a container with root file system mounted onto container at /rootFS
>> adds an entry with credentials "pawned/pawned" to the /etc/passwd wth root privileges .
>> cleans up the operations.

usage :
pre requisites :

>> works on python 3
>> pip3 install docker
>> pip3 install requests

>> usage :

pythonPawn.py -ip "victim host IP" [optional port. Default (2375)]
