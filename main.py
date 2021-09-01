from json import JSONEncoder

from cdktf import App, TerraformOutput, TerraformStack, Token
from constructs import Construct

from imports.aws import (AwsProvider, DataAwsCallerIdentity, EksNodeGroup,
                         IamPolicy, IamRole, IamRolePolicyAttachment,
                         SecurityGroup)
from imports.eks import Eks
from imports.vpc import Vpc
from main import IamRole

# import imports.aws


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
            subnets=Token().as_list(my_vpc.private_subnets_output),
            vpc_id=Token().as_string(my_vpc.vpc_id_output),
            manage_aws_auth=False,
            cluster_version='1.17'            
        )        
        
        node_group= EksNodeGroup(self, 'MyNodes',
            node_group_name="my-node-group",
            cluster_name='my-eks',
            instance_types=["t2.micro"],
            subnet_ids=Token().as_list(my_vpc.private_subnets_output),
            scaling_config= [{
               "desiredSize": 1, 
               "maxSize": 1, 
               "minSize": 1
            }], 
            node_role_arn=iamrole.arn, 
            depends_on = [
            iampollicy1,
            iampollicy2,
            iampollicy3
            ]
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
