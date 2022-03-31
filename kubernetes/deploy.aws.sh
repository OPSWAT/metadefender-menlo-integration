#!/bin/bash
CWD=$(cd "$(dirname "${BASH_SOURCE[0]}")/" && pwd)

# Requirements:
# kubectl
# eksctl
# aws cli

## Env variables:
# VERSION, AWS_ACCOUNT, AWS_REGION, AWS_DEFAULT_PROFILE, EKS_CLUSTER, EKS_NAMESPACE, EKS_SERVICE, DOMAIN
## Env variables

CMD=$1
if [[ "$CMD" = '' ]]; then
  echo "Available commands:"
  echo ""
  echo "create_cluster"
  echo "delete_cluster"
  echo "view_resources"
  echo "create_namespace"
  echo "build_image"
  echo "create_certificate"
  echo "apply_deployment"
  echo "apply_service"
  echo "apply_ingress"
fi

# Create your Amazon EKS cluster and nodes
function create_cluster() {
  eksctl create cluster --name $EKS_CLUSTER --region ${AWS_REGION}
}

# Delete your cluster and nodes
function delete_cluster() {
  eksctl delete cluster --name $EKS_CLUSTER --region ${AWS_REGION}
}

function configure_cluster() {
  eksctl utils write-kubeconfig --cluster=$EKS_CLUSTER --region ${AWS_REGION}
}

# View Kubernetes resources
function view_resources() {
  echo "All resources"
  kubectl get all -n $EKS_NAMESPACE

  echo "Nodes"
  kubectl get nodes -o wide

  echo -e "\nPods"
  kubectl get pods --all-namespaces -o wide

  echo "Service Details"
  kubectl -n $EKS_NAMESPACE describe service $EKS_SERVICE
}

function create_namespace() {
  kubectl create namespace $EKS_NAMESPACE
}

function build_image() {
  cd $CWD/../
  docker build -t 108895011981.dkr.ecr.${AWS_REGION}.amazonaws.com/mdcl-menlo:$VERSION .
}

function create_ecr_repo() {
  aws ecr create-repository --repository-name metadefender-menlo --region ${AWS_REGION}
}

function ecr_login() {
  aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com
}

function push_image() {
  docker push 108895011981.dkr.ecr.${AWS_REGION}.amazonaws.com/mdcl-menlo:$VERSION
}

function apply_deployment() {
  kubectl -n $EKS_NAMESPACE apply -f deployment.yaml
}

function apply_service() {
  kubectl -n $EKS_NAMESPACE apply -f service.yaml
}

function apply_ingress() {
  kubectl -n $EKS_NAMESPACE apply -f ingress.yaml
}

# execute commands
$CMD ${@:2}
