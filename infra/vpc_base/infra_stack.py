import aws_cdk as cdk
import aws_cdk.aws_ec2 as ec2


class VPCStack(cdk.Stack):

    def __init__(self, scope: cdk.Stack, id=str, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.vpc = ec2.Vpc(
            self, "WorkshopVPC",
            max_azs=2,
            cidr='10.0.0.0/24',
            enable_dns_support=True,
            enable_dns_hostnames=True,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                subnet_type=ec2.SubnetType.PUBLIC,
                name="Public",
                cidr_mask=26
                ),
                ec2.SubnetConfiguration(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                name="Private",
                cidr_mask=26
               )
               ],
               nat_gateways=1,
               )
