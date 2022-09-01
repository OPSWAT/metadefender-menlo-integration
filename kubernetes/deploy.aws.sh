#!/bin/bash
CWD=$(cd "$(dirname "${BASH_SOURCE[0]}")/" && pwd)

# Requirements:
# kubectl
# eksctl
# aws cli

## Env variables:
# VERSION,MENLO_ENV, AWS_ACCOUNT, AWS_REGION, AWS_DEFAULT_PROFILE, EKS_CLUSTER, EKS_NAMESPACE, EKS_SERVICE, DOMAIN
## Env variables

CMD=$1
if [[ "$CMD" = '' ]]; then
  echo "Available commands:"
  echo ""
  echo "view_resources"
  echo "create_namespace"
  echo "build_image"
  echo "ecr_login"
  echo "push_image"
  echo "apply_deployment"
  echo "apply_service"
  echo "apply_ingress"
  echo "apply_hpa"
fi

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
  docker build -t ${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/mdcl-menlo:${MENLO_ENV}-$VERSION .
}

function ecr_login() {
  aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com
}

function push_image() {
  docker push ${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/mdcl-menlo:${MENLO_ENV}-$VERSION
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

function apply_hpa() {
  kubectl -n $EKS_NAMESPACE apply -f hpa.yaml
}

# execute commands
$CMD ${@:2}
