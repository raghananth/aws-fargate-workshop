#!/usr/bin/env python3

import aws_cdk as cdk
from constructs import Construct
import aws_cdk.aws_ecr as ecr
import aws_cdk.aws_iam as iam
import aws_cdk.aws_codecommit as codecommit
import aws_cdk.aws_codepipeline as codepipeline
import aws_cdk.aws_codebuild as codebuild
import aws_cdk.aws_codepipeline_actions as codepipeline_actions
import os


class PipelineStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        name = "graviton2-spot-workshop"
 
        # Repo for Application
        codecommit_repo = codecommit.Repository(
            scope=self,
            id=f"{name}-app-repo",
            repository_name=f"{name}",
            description=f"Application code repository"
        )

        # Create ECR repository
        container_repository = ecr.Repository(
            scope=self,
            id=f"{name}-container",
            repository_name=f"{name}"
        )

        buildspec_x86 = codebuild.BuildSpec.from_source_filename("infra/config/x86-buildspec.yml")
        docker_build_x86 = codebuild.PipelineProject(
            scope=self,
            id=f"DockerBuild_x86",
            environment=dict(
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                privileged=True),
            environment_variables={
                'REPO_ECR': codebuild.BuildEnvironmentVariable(
                    value=container_repository.repository_uri),
            },
            build_spec=buildspec_x86
        )
        container_repository.grant_pull_push(docker_build_x86)

        buildspec_arm64 = codebuild.BuildSpec.from_source_filename("infra/config/arm64-buildspec.yml")
        docker_build_arm64 = codebuild.PipelineProject(
            scope=self,
            id=f"DockerBuild_ARM64",
            environment=dict(
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_ARM,
                privileged=True),
            environment_variables={
                'REPO_ECR': codebuild.BuildEnvironmentVariable(
                    value=container_repository.repository_uri),
            },
            build_spec=buildspec_arm64
        )
        container_repository.grant_pull_push(docker_build_arm64)

        buildspec_manifest = codebuild.BuildSpec.from_source_filename("infra/config/manifest-buildspec.yml")
        manifest_build = codebuild.PipelineProject(
            scope=self,
            id=f"ManifestBuild",
            environment=dict(
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                privileged=True),
            environment_variables={
                'REPO_ECR': codebuild.BuildEnvironmentVariable(
                    value=container_repository.repository_uri),
            },
            build_spec=buildspec_manifest
        )
        container_repository.grant_pull_push(manifest_build)

        pipeline = codepipeline.Pipeline(
            scope=self,
            id=f"{name}-container--pipeline",
            pipeline_name=f"{name}"
        )

        source_output = codepipeline.Artifact()
        docker_output_x86 = codepipeline.Artifact("x86_BuildOutput")
        docker_output_arm64 = codepipeline.Artifact("ARM64_BuildOutput")

        source_action = codepipeline_actions.CodeCommitSourceAction(
            action_name="CodeCommit_Source",
            repository=codecommit_repo,
            output=source_output,
            branch="main"
        )

        pipeline.add_stage(
            stage_name="Source",
            actions=[source_action]
        )

        # Stages in CodePipeline
        pipeline.add_stage(
            stage_name="DockerBuild",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name=f"DockerBuild_x86",
                    project=docker_build_x86,
                    input=source_output,
                    outputs=[docker_output_x86]),
                codepipeline_actions.CodeBuildAction(
                    action_name=f"DockerBuild_ARM64",
                    project=docker_build_arm64,
                    input=source_output,
                    outputs=[docker_output_arm64])
            ]
        )

        manifest_output = codepipeline.Artifact("ManifestOutput")
        pipeline.add_stage(
            stage_name="Manifest",
            actions=[
                codepipeline_actions.CodeBuildAction(
                action_name="Manifest",
                project=manifest_build,
                input=source_output,
                outputs=[manifest_output])
            ]
        )

        # Outputs
        cdk.CfnOutput(
            scope=self,
            id="application_repository",
            value=codecommit_repo.repository_clone_url_http
        )
