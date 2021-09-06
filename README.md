# enthire
EKS using terraform-cdk and kubernetes-dashboard helm chart.
AWS, Helm providers are used
kubernetes-dashboard helm chart is included in the repo.(Modified helm chart to enable metric server installation and readonly service account creation).

##steps to execute
1. pipenv install
2. cdktf synth
3. cdktf deploy

##Login to dashboard
1. open url https://34.219.242.77:30144/
2. get tokens from admin for login

## future work
1. implement tls
2. modify helm chart to add service accounts
3. add inbound rules for allowing traffic
4. Iam roles for cluster access control
5. use of worker groups instead of node groups
