# MetaDefender - Menlo Security Middleware

## Development

### Repositories

Please use the `origin` repository for internal development, syncronize only the main and develop branches between `origin` and `github` repos.

- origin: Internal remote repository  
`origin git@bitbucket.org:metascan/mdcl-menlo-middleware.git`

- github: Public remote repository  
`github git@github.com:OPSWAT/metadefender-menlo-integration.git`

### Repo setup

```bash
git clone git@bitbucket.org:metascan/mdcl-menlo-middleware.git

cd mdcl-menlo-middleware

git remote add github git@github.com:OPSWAT/metadefender-menlo-integration.git

git flow init
# [gitflow "branch"]
# 	master = main
# 	develop = develop
# [gitflow "prefix"]
# 	feature = feature/
# 	bugfix = bugfix/
# 	release = release/
# 	hotfix = hotfix/
# 	support = support/
# 	versiontag =
```

Use [git-flow workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow) for development

## Documentation

* [Integration Guide](docs/Menlo%20-%20MetaDefender%20Integration%20Guide.pdf)
* [Menlo Security File Sanitization API](docs/Menlo%20Sanitization%20API.html)

## Middleware documentation
Make sure you have `python3.5` or above installed. 
This Middleware leverages python's async mechanism introduced in `python3.5`

Before you run it, install all dependencies: 
`pip install -r requirements.txt`

To run the app: 
`python3 -m metadefender_menlo`

Middleware should be configured using the [config](config.yml) file:
```
service: metadefender                       # MetaDefender Core service is the only current integration allowed
api: 
  type: core                                # mandatory, should be either `core` or `cloud`
  params:
    apikey: null                            # optional for MetaDefender Core (in case is configured to request it), but `mandatory for MetaDefender Cloud`
  url: 
    core: https://localhost:8008            # MetaDefender Core URL - can be HTTP or HTTPS (certificate validation is disabled)
    cloud: https://api.metadefender.com/v4  # MetaDefender Cloud URL - this doesn't need to be updated, will be consumed when api type is `cloud`
server: 
  port: 3000
  host: "0.0.0.0"
  api_version: /api/v1
https:
  load_local: false                         # enable https by using locally stored certs
  crt: /tmp/certs/server.crt                # location of the public key
  key: /tmp/certs/server.key                # location of the private key
logging:
  enabled: true                             # enable or disable logging. 
  level: INFO                               # select from (NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL) (see https://docs.python.org/3/library/logging.html#levels)
  logfile: /var/log/md-menlo/app.log        # absolute path to the logfile. If path doesn't exist will be created (make sure the user has the right permissions)
  interval: 24                              # the interval (in hours) for log rotation
  backup_count: 30                          # for how many intervals should the logs be kept (e.g. 30 logs for 24h each -> 30 days logs)
  ```

Menlo requires all communication to be done over https, so either deploy an reverse proxy (nginx) in front of it to handle SSL or use the configuration `https` in the `config.yml`. 
You can add self-signed X509 certs, but have to be signed by a (custom) Certificate Authority. The rootCA public key will be required to be uploaded to Menlo Security Web Policy configuration. 

The location can be altered also by modifiying `metadefender_menlo/__main__.py` at lines 22-23. 

## AWS Cloud deployment

To change the environemnt, update `.env` file.
```bash
# Use `local` for local development.
# Use `dev` for testing the deployment on https://menlo-dev.metadefender.com
# Use `prod` for deploying a new version to prod env: https://menlo.metadefender.com
MENLO_ENV=<env>
```

Follow the next steps after the env is set.
```bash
# 1. Go to the kubernetes folder
cd kubernetes

# 2. Build a new image version. 
# set different <version> for each deployment, 
# you can append a letter to the current version number while testing. e.g. 1.1.0-c
./deploy.aws.sh build_image 1.1.0-c

# 3.a Login to AWS ECR. Once in a while if your session expires
./deploy.aws.sh ecr_login

# 3. Push image to remote
./deploy.aws.sh push_image 1.1.0-c

# 4. Deploy the new image to the dev cluster
./deploy.aws.sh apply_deployment

# Check the new deployment on 
https://menlo-dev.metadefender.com
```

## Bitbucket automated deployment

Some Bitbucket pipelines have been configured in order for everybody to easily build and deploy the Menlo middleware to any environment from the same place (Bitbucket pipelines that trigger cloud agents), thus eliminating potential deviations in the build/deploy script or others (OS, software etc.). Plus, this way all builds/deploys can be tracked.

There are 3 pipelines:

- **branches: develop** - automatically triggered to build/deploy to dev when there is a merge to develop
- **branches: main** - automatically triggered to build/deploy to prod when there is a merge to main
- **custom: manual** - manually triggered pipeline to deploy to dev from any branch other than develop/main

All of the environment variables used in the scripts can be viewed and configured in Bitbucket->Repository Settings->Deployments OR Repository variables

For local deployments, use the gitignored `.env` file which will be sourced in the script.

## Kubernetes deployment
First, you’re required to build a container. There’s a `Dockerfile` in the repo, that you can use to build the container and push it to your registry. Once you have it, you will have to modify deployment.yaml and specify your own container image. 

Also, check the `deploy.sh` script. It was built specifically for Google Cloud to leverage GKE (Google Kubernetes Engine). But it can be easily adapted to run in any Kubernetes supported environment. 

For AWS deployment please check `deploy.aws.sh`.

The GCP specific part is building the cluster and (if needed) the static IP. 

Modify the deploy script to use your own cluster and certificates as needed. If you don’t require self-signed certs, you can remove the entire portion with openssl and jump directly to adding your certificates as Kubernetes secrets. 

Check `deployment.yaml` and place the real `apikey` (if you plan to use MetaDefender Cloud), or just remove that environment variable entirely if it is not going to be used. You can also set the apikey in the config file, if you prefer to have it hardcoded in the container image, instead of passing it as an environment variable. 

```
containers:
- name: "metadefender-menlo-integration"     
  image: "<<middleware-container>>"         # Build your own container using the Dockerfile provided in the repository
  env:
  - name: "apikey"
    value: "<<MetaDefender-Cloud-apikey>>"  # Set your private apikey if you will integrate with MetaDefender Cloud
```


## MetaDefender Core - Menlo Security Integration Guide

### About This Guide
This document describes the integration of Menlo Security with MetaDefender Core and Cloud, using the current middleware


### Integration Overview

Menlo Security has the ability to call an external API (called Sanitization API), which allows to offload the file analysis to MetaDefender and retrieve the sanitized file once is available. 

The Sanitization API specification includes: 
* `Submit metadata` - not implemented in this Middleware to maintain a stateless system
* `Check Existing Report` - SHA256 lookup 
* `File Submission` 
* `Analysis Report` - Menlo will keep polling this endpoint until the status is completed
* `Retrieve Sanitized file`

#### Installation Prerequisites

The middleware is using `python3` and requires minimum python3.5 to run. 
A list of all libraries are included in [requirements.txt](requirements.txt)

The application can run on the same VM as MetaDefender Core or a separate system. 
Can also run in a Docker container, a [Dockerfile](Dockerfile) is made available. 

#### Integration Steps


##### Step 1: Deploy Integration Middleware

First, clone this repository: 
`git clone https://github.com/georgeprichici/metadefender-menlo-integration.git`

Second, install all dependencies: 
`pip install -r requirements.txt`

##### Step 2: Configure Middleware
Middleware should be configured using the [config](config.yml) file. 
Make sure you place the certs in the right folder (`certs`) and under the right name, since Menlo requires all communication to be done over https. 

```
service: metadefender
api: 
  type: cloud
  params:
    apikey: null
  url: 
    core: https://1.2.3.4:8008
    cloud: https://api.metadefender.com/v4    
server: 
  port: 3000
  host: "0.0.0.0"
  api_version: /api/v1
https:
  load_local: false
  crt: /tmp/certs/server.crt
  key: /tmp/certs/server.key
logging:
  enabled: true
  level: INFO
  logfile: /var/log/md-menlo/app.log
  interval: 24
  backup_count: 30
  ```
See the [Middleware Documentation](#Middleware-documentation) for details. 

##### Step 3: Configure Menlo Integration

1. Login to Menlo Admin console (`https://admin.menlosecurity.com`)
2. Go to Web Policy > Content Inspection
3. Edit `Menlo File REST API` 
4. Add the following details: 
    - Plugin Name: `MetaDefender Core`
    - Plugin Description: `MetaDefender Core API Integration`
    - Base URL: The url of the middleware (e.g. `https://1.2.3.4:3000`)
      - :warning: **HTTPS** is required!
    - Certificate: the certificate (X.509) used for the Middleware 
        - This will be used for certificate validation        
    - Type of transfers: 
      - Enable Downloads if MetaDefender is used to scan and sanitize downloaded files
      - Enable Uploads if MetaDefender will be used to also redact uploaded files
    - Authorization Header: 
      - For MetaDefender Core: you can put any dummy data, since this header will be ignored on the Middleware side
      - For MetaDefender Cloud: 
        - you can choose to input here the apikey instead in the config file 
        - if so, you'll need to enable the functionality 
          - uncomment the prepare function in api.handlers.base_handler.py
        - The main benefit is the ability to switch keys in Menlo admin console, maybe use different keys for different departments/groups. 
    - Hash Check: leave it unchecked, to force a file analysis and sanitization on every file download
    - Metadata Check: leave it unchecked since is not supported in this integration
    - Allow File Replacement: Enable this functionality if you plan to use MetaDefender to sanitize the downloaded files or redact uploaded files

##### Step 4: Test

1. Navigate to `https://safe.menlosecurity.com`
2. Search for a PDF
3. Try to download the PDF
4. You should see the File Download request in the Admin Console (Logs > Web Logs)
5. Click on the table entry and you'll see the analyis details on the right side. 


### Logging guide

```
SERVICE > TYPE > DETAILS

SERVICE
    - MenloPlugin
    - MetaDefenderCloud

TYPE:
    - Request
    - Response
    - Iternal

DETAILS: 
    - <JSON Object>
    - <Order>

Exapmple:
    MenloPlugin > Request > {method: GET, endpoint: "/api/v1/file/bzIyMDYyNDl6ekt5TElTZVMxNmllVHR2TWE"}
    MetadeDefenderCloud > Request > {https://api.metadefender.com/v4/file/converted/bzIyMDYyNDl6ekt5TElTZVMxNmllVHR2TWE | {'apikey': '4da78a411dd24a44d839e16fa2be7c1f', 'x-forwarded-for': '81.196.34.198', 'x-real-ip': '81.196.34.198'}}
    MetadeDefenderCloud > Response > {status_500}
    MeloPlugin > Internal > "Error from md cloud"
    MenloPlugin > Response > {500 response: sanitized file (binary data)}
```


## Extras
* [Postman collection](api/Menlo%20Security%20-%20Sanitization%20Public%20API.postman_collection.json)
* [OpenAPI 3.0 Spec File](api/menlo-sanitization-openapi.yaml)
