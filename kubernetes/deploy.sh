#!/bin/bash
DOMAIN="$1"
USE_STATIC_IP=0
start=$SECONDS
# echo "[STEP 0]: Create the cluster"
# gcloud container clusters create metadefender-menlo-cluster

echo "Selected kube context: $(kubectl config current-context)"

if [ -z $DOMAIN]; then
    echo "No domain provided"
    echo "Reserve static IP"
    DOMAIN=$(gcloud compute addresses create metadefender-menlo-static-ip --global --ip-version IPV4 --format="value(address)")    
    USE_STATIC_IP=1
fi
echo "[STEP 1]: Use domain/ip: $DOMAIN" 

echo "[STEP 3]: Create self-signed cert"
echo "[STEP 3a]: Create non-password rootCA key"
openssl genrsa -out rootCA.key 4096

echo "[STEP 3b]: Create and self sign the Root Certificate (rootCA.crt will be used also in Menlo Web Policy config)"
openssl req -x509 -new -nodes -key rootCA.key -sha256 -days 1024 -subj "/C=US/ST=CA/O=Corporation, Inc./CN=$DOMAIN" -out rootCA.crt

echo "[STEP 3c]: Create non-password server key"
openssl genrsa -out tls.key 2048

echo "[STEP 3d]: Create signing request"
cat > csr_details.txt <<-EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
req_extensions = req_ext
distinguished_name = dn

[ dn ]
C=US
ST=California
L=San Francisco
O=Product
OU=Product
emailAddress=noreply@corporation.com
CN=$DOMAIN 

[ req_ext ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1=$DOMAIN
EOF

openssl req -new -sha256 -nodes -key tls.key -out server.csr -config <( cat csr_details.txt )

#echo "Signing request content:" 
#echo $(openssl req -in server.csr -noout -text)
echo "Set MENLO_ENV"
export MENLO_ENV="$1"

echo "[STEP 3e]: Create signed cert"
openssl x509 -req -in server.csr -CA rootCA.crt -CAkey rootCA.key -CAcreateserial -out tls.crt -days 365 -sha256

echo "Generated server cert:"
#echo $(openssl x509 -in server.crt -noout -text)

echo "[STEP 4]: Create the Kube secret"
kubectl create secret tls metadefender-menlo-secret-tls --cert ./tls.crt --key ./tls.key

echo "[STEP 1]: Create the deployment"
kubectl apply -f deployment.yaml

echo "[STEP 2]: Create the service"
kubectl apply -f service.yaml

if ["$USE_STATIC_IP" -eq "0"]; then
    echo "[STEP 4]: Create Ingress"
    kubectl apply -f ingress.yaml
else 
    echo "[STEP 4]: Create Ingress with StaticIP"
    kubectl apply -f ingress-static-ip.yaml
fi
end=$SECONDS

echo "MetaDefender - Menlo Security middleware deployed."
echo "Total time $((end-start)) sec."
echo "Service running at https://$DOMAIN"