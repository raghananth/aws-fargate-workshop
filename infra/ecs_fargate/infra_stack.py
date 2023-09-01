import aws_cdk as cdk
from constructs import Construct
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_iam as iam
import aws_cdk.aws_elasticloadbalancingv2 as elbv2
import aws_cdk.aws_ssm as ssm
import os


class ECSFargateStack(cdk.Stack):

    def __init__(self, scope: Construct, id: str, vpc, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        cluster = ecs.Cluster(
            self, 'ECSFargate',
            vpc=vpc,
            container_insights=True
        )

        serviceDefinitions = [
                { "name" : "grav","cpu_architecture": ecs.CpuArchitecture.ARM64, "arch" : "arm64", "capacity_provider": "FARGATE" },
                { "name" : "x86","cpu_architecture": ecs.CpuArchitecture.X86_64, "arch" : "x86", "capacity_provider": "FARGATE" }
            ]
        for service in serviceDefinitions:
            self.createService(vpc,cluster,service)

    def createService(self, vpc,cluster, serviceDef):

        container_uri = ssm.StringParameter.value_for_string_parameter(self ,"graviton2-spot-workshop-uri")
        
        port_mapping =  ecs.PortMapping(
            container_port=8080,
            protocol=ecs.Protocol.TCP
        )

        policyStatement = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["logs:CreateLogStream",
                     "logs:PutLogEvent",
                     "ecr:BatchGetImage",
                     "ecr:GetDownloadUrlForLayer",
                     "ecr:GetAuthorizationToken"
                     ],
            resources=["*"]
        )

        # Create task definition
        task_definition = ecs.FargateTaskDefinition(self, f"{serviceDef['name']}-Task",
            runtime_platform=ecs.RuntimePlatform(
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
                cpu_architecture=serviceDef['cpu_architecture']
            )
        )

        task_definition.add_to_execution_role_policy(policyStatement)        

        container = task_definition.add_container(
            f"web-{serviceDef['name']}",
            image=ecs.ContainerImage.from_registry(f"{container_uri}"),
            memory_limit_mib=512
        )        

        container.add_port_mappings(port_mapping)


        # Create Service
        service = ecs.FargateService(
            self, f"{serviceDef['name']}-Service",
            cluster=cluster,
            task_definition=task_definition,
            capacity_provider_strategies=[ecs.CapacityProviderStrategy(
                                            capacity_provider=serviceDef['capacity_provider'],
                                            weight=1
                                            )
            ]
        )

        # Create ALB
        lb = elbv2.ApplicationLoadBalancer(
            self, f"{serviceDef['name']}_LB",
            vpc=vpc,
            internet_facing=True
        )

        listener = lb.add_listener(
            "PublicListener",
            port=80,
            open=True
        )

        # Attach ALB to ECS Service
        listener.add_targets(
            "ECS",
            port=80,
            targets=[service]
        )

        cdk.CfnOutput(
            self, f"{serviceDef['name']}-LoadBalancerDNS",
            value=lb.load_balancer_dns_name
        )
