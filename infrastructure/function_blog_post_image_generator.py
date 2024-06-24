from awacs.aws import Action, Allow, PolicyDocument, Principal, Statement
from troposphere import Sub, Template, GetAtt, Ref
import troposphere.awslambda as awslambda
import troposphere.iam as iam
from troposphere.iam import Policy
import troposphere.sns as sns


class FunctionBlogPostImageGenerator:

    def __init__(
        self,
        app_prefix,
        application_s3_param,
        application_zip_param,
        app_parameter_store_path,
        primary_kms_arn,
        cdn_bucket_name,
    ):
        self._app_name = "ImageGenerator"
        self._app_prefix = app_prefix
        self._application_s3_param = application_s3_param
        self._application_zip_param = application_zip_param
        self._app_parameter_store_path = app_parameter_store_path
        self._primary_kms_arn = primary_kms_arn
        self._cdn_bucket_name = cdn_bucket_name

    def get_function_sns_topic_resource(
        self, subscriptions: [sns.Subscription]
    ) -> sns.Topic:
        return sns.Topic(
            self._app_name + "Topic",
            TopicName=self._app_prefix + "-" + self._app_name,
            Subscription=subscriptions,
        )

    def get_function_definition(self, function_role) -> awslambda.Function:
        return awslambda.Function(
            self._app_name,
            Handler="hugo_site.blog_post_image_generator.handler.lambda_handler",
            Role=GetAtt(function_role, "Arn"),
            FunctionName=self._app_prefix + "-" + self._app_name,
            Runtime="python3.11",
            Timeout=300,
            Code=awslambda.Code(
                S3Bucket=Ref(self._application_s3_param),
                S3Key=Ref(self._application_zip_param),
            ),
            Environment=awslambda.Environment(
                Variables={
                    "IMAGE_TEMP_DIR": "/tmp",
                    "WEBSITE_CDN_IMAGES_BUCKET": self._cdn_bucket_name,
                },
            ),
        )

    def add_resource(self, current_template: Template) -> Template:
        function_role = self.get_function_role_and_policy()
        function_definition = self.get_function_definition(function_role)
        topic_subscription = [self.add_topic_subscription(function_definition)]
        sns_topic_resource = self.get_function_sns_topic_resource(topic_subscription)
        function_event_invoke_config = self.get_function_event_invoke_config(
            function_definition
        )
        awslambda_permission = self.get_lambda_trigger_permissions(
            function_definition, sns_topic_resource
        )

        current_template.add_resource(function_role)
        current_template.add_resource(function_definition)
        current_template.add_resource(sns_topic_resource)
        current_template.add_resource(function_event_invoke_config)
        current_template.add_resource(awslambda_permission)

        return current_template

    def add_topic_subscription(self, lambda_function) -> sns.Subscription:
        return sns.Subscription(
            Protocol="lambda", Endpoint=GetAtt(lambda_function, "Arn")
        )

    def get_lambda_trigger_permissions(
        self, function_definition, topic_definition
    ) -> awslambda.Permission:
        return awslambda.Permission(
            self._app_name + "SnsLambdaPermission",
            Action="lambda:InvokeFunction",
            FunctionName=Ref(function_definition),
            Principal="sns.amazonaws.com",
            SourceArn=Ref(topic_definition),
        )

    def get_function_event_invoke_config(
        self, function_definition: awslambda.Function
    ) -> awslambda.EventInvokeConfig:
        return awslambda.EventInvokeConfig(
            self._app_name + "EventInvokeConfig",
            FunctionName=Ref(function_definition),
            MaximumRetryAttempts=0,
            Qualifier="$LATEST",
        )

    def get_function_role_and_policy(self) -> iam.Role:
        allow_write_to_log_statement = Statement(
            Effect=Allow,
            Action=[
                Action("logs", "CreateLogGroup"),
                Action("logs", "CreateLogStream"),
                Action("logs", "PutLogEvents"),
            ],
            Resource=["*"],
        )

        allow_get_parameter_statement = Statement(
            Effect=Allow,
            Action=[
                Action("ssm", "GetParameter*"),
            ],
            Resource=[
                Sub(
                    "arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter${AppParameterStorePath}/*",
                    AppParameterStorePath=self._app_parameter_store_path,
                )
            ],
        )

        allow_kms_decrypt = Statement(
            Effect=Allow,
            Action=[
                Action("kms", "Decrypt"),
            ],
            Resource=[self._primary_kms_arn],
        )

        allow_write_to_s3_bucket = Statement(
            Effect=Allow,
            Action=[
                Action("s3", "PutObject"),
                Action("s3", "ListAllMyBuckets"),
            ],
            Resource=[
                Sub(
                    "arn:aws:s3:::${CdnBucketName}/*",
                    CdnBucketName=self._cdn_bucket_name,
                ),
                Sub(
                    "arn:aws:s3:::${CdnBucketName}",
                    CdnBucketName=self._cdn_bucket_name,
                ),
            ],
        )

        allow_bedrock_access = Statement(
            Effect=Allow,
            Action=[Action("bedrock", "InvokeModel")],
            Resource=[
                "arn:aws:bedrock:us-west-2::foundation-model/stability.stable-diffusion-xl-v1",
                "arn:aws:bedrock:us-west-2::foundation-model/amazon.titan-image-generator-v1",
            ],
        )

        policy_document = PolicyDocument(
            Version="2012-10-17",
            Id="LambdaExecutionPolicy",
            Statement=[
                allow_write_to_log_statement,
                allow_get_parameter_statement,
                allow_kms_decrypt,
                allow_write_to_s3_bucket,
                allow_bedrock_access,
            ],
        )

        # trust relationship for lambda
        assume_role_statement = Statement(
            Effect=Allow,
            Principal=Principal(
                "Service", ["lambda.amazonaws.com", "ssm.amazonaws.com"]
            ),
            Action=[Action("sts", "AssumeRole")],
        )

        assume_role_policy_document = PolicyDocument(
            Version="2012-10-17",
            Id="AssumeRolePolicy",
            Statement=[assume_role_statement],
        )

        function_execution_role = iam.Role(
            self._app_name + "FunctionRole",
            AssumeRolePolicyDocument=assume_role_policy_document,
            Policies=[
                Policy(
                    PolicyName="LambdaAllowResources", PolicyDocument=policy_document
                )
            ],
        )

        return function_execution_role
