#!/usr/bin/env python3

import os
import aws_cdk as cdk

from pipeline.infra_stack import PipelineStack
from ecs_fargate.infra_stack import ECSStack
from vpc_base.infra_stack import VPCStack

class GravitonSpotWorkshop(cdk.App):

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.stack_name = "GravitonSpotWorkshop"
            self.pipeline_module = PipelineStack(self, self.stack_name + "-pipeline")

if __name__ == '__main__':
    app = GravitonSpotWorkshop()
    app.synth()
