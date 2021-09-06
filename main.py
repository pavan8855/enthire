from cdktf import App, TerraformOutput, TerraformStack, Token
from constructs import Construct

from imports.aws import (AwsProvider, DataAwsCallerIdentity, EksNodeGroup,
                         IamPolicy, IamRole, IamRolePolicyAttachment)
from imports.eks import Eks
from imports.helm import HelmProvider, Release

from imports.vpc import Vpc


class MyStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)

        # define resources here
        AwsProvider(self, 'Aws', region='us-west-2')
               
        iamrole = IamRole(self, "iamRole",
                name="node_role",
                assume_role_policy= '{ "Version": "2012-10-17", "Statement": [{ "Action": "sts:AssumeRole", "Effect": "Allow", "Sid":"", "Principal": { "Service": "ec2.amazonaws.com" } }] }'
        )
        
        iampollicy1 =  IamRolePolicyAttachment(self, "iamRPA1", policy_arn="arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
                                               role=iamrole.name
                                 )
        iampollicy2 = IamRolePolicyAttachment(self, "iamRPA2", policy_arn="arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
                                               role=iamrole.name
                                 )
        iampollicy3 = IamRolePolicyAttachment(self, "iamRPA3", policy_arn="arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
                                               role=iamrole.name
                                 )        
        
        my_vpc= Vpc(self, 'MyVpc',
            name='my-vpc',
            cidr='10.0.0.0/16',
            azs=['us-west-2a', 'us-west-2b', 'us-west-2c'],
            private_subnets=['10.0.1.0/24', '10.0.2.0/24', '10.0.3.0/24'],
            public_subnets=['10.0.101.0/24', '10.0.102.0/24', '10.0.103.0/24'],
            enable_nat_gateway=True,
            enable_dns_hostnames=True,
            single_nat_gateway=True                      
        )
        
        my_eks= Eks(self, 'MyEks',
            cluster_name='my-eks',
            subnets=Token().as_list(my_vpc.public_subnets_output),
            vpc_id=Token().as_string(my_vpc.vpc_id_output),
            manage_aws_auth=False,
            cluster_version='1.21',
            write_kubeconfig= False,
            cluster_endpoint_public_access=True,
            node_groups=([{
                "desired_capacity": 3,
                "iam_role_arn": iamrole.arn,
                "instance_types": ["t2.micro"],
                "max_capacity": 3,
                "min_capacity": 1,
                "subnets": Token().as_list(my_vpc.public_subnets_output),
                "public_ip": True,
                "depends_on":[iampollicy1, iampollicy2, iampollicy3]
            }])
            )
        
        HelmProvider(self,'Helm',
                     kubernetes=[{
                            "host": my_eks.cluster_endpoint_output,
                            "insecure": True,
                            "exec":[{
                                "apiVersion": "client.authentication.k8s.io/v1alpha1",
                                "args": ["--region", "us-west-2", "eks", "get-token", "--cluster-name", my_eks.cluster_name],
                                "command": "aws"
                            }]
                         }]
            )
        kdh = Release(self, 'kubernetes-dashboard',
                      name= "my-dashboard",
                      chart="../../../kubernetes-dashboard",
                      namespace= "default"
                    )      
        
        TerraformOutput(self, 'cluster_endpoint',
            value=my_eks.cluster_endpoint_output
        )

        TerraformOutput(self, 'create_user_arn',
            value=DataAwsCallerIdentity(self, 'current').arn
        )

app = App()
MyStack(app, "enthire")

app.synth()
