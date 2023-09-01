#!/usr/bin/env python3

import os
import aws_cdk as cdk

from pipeline.infra_stack import PipelineStack
from ecs_fargate.infra_stack import ECSFargateStack
from vpc_base.infra_stack import VPCStack

class GravitonSpotWorkshop(cdk.App):

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.stack_name = "GravitonSpotWorkshop"
            self.base_module = VPCStack(self, self.stack_name + "-vpc")
            self.pipeline_module = PipelineStack(self, self.stack_name + "-pipeline")
            self.ecs_fargate_module = ECSFargateStack(self, self.stack_name + "-ecs-fargate",self.base_module.vpc)

if __name__ == '__main__':
    app = GravitonSpotWorkshop()
    app.synth()
