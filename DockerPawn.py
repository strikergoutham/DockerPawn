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

if args.host is None:
    parser.print_help()
    exit()

port = "2375"
host = args.host
if args.port is not None:
    port = args.port

endpoint = "http://"+host+":"+port+"/"

#lowlevel API Client
client = docker.APIClient(endpoint)


headers = {
        'Accept': 'application/json'
}


def listImages():
    ImagesEndpoint = endpoint +'images/json'
    response = requests.request(method='GET', url=ImagesEndpoint, headers=headers)
    JsonResponse = json.loads(response.text)
    print("\n\n.................Available Docker Images on the remote host...................\n\n")
    if len(JsonResponse) > 0:
        if "RepoTags" in JsonResponse[0]:
            for i in range(0, len(JsonResponse)):
                print("Image ID: ", JsonResponse[i]["Id"])
                print("Image Repository Tags: ", JsonResponse[i]["RepoTags"])
                print("Image Label: ", JsonResponse[i]["Labels"])
                print("Image Size: ", JsonResponse[i]["Size"])
                print("<--------------------------------------------------------------->\n")


if __name__ == "__main__":
    try:
        DockerInfo = client.version()
    except (requests.exceptions.ConnectionError):
        print("unable to connect to docker endpoint!")
        exit()


    listImages()



















