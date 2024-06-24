import os
import sys

from troposphere import ImportValue, Parameter, Template, Ref, Output, Export

from function_blog_post_image_generator import FunctionBlogPostImageGenerator


if __name__ == "__main__":
    template_file = sys.argv[1]
    rando_hash = sys.argv[2]

    main_template = Template()

    application_prefix = "HugoBots"
    application_prefix_lowercase = application_prefix.lower()

    # parameters
    primary_kms_arn = os.getenv("KMS_KEY_ID_ARN")
    github_app_private_key_ssm_path = Parameter(
        "GHAppPrivateKeySSMPath",
        Type="String",
        Description="KMS Encrypted GitHub App Private Key SSM Parameter Path",
        Default="/SmyleeDevWorkflows/GitHubApp/PrivateKey",
    )

    cdn_bucket_name = os.getenv("CDN_BUCKET_NAME")

    # primary s3 bucket for uploading artifacts
    s3_bucket_for_artifacts_param_name = "BucketForUploadsUsWest2"
    s3_buckets_for_artifacts_import = ImportValue("S3::BucketForUploadsUsWest2-Name")
    s3_bucket_for_artifacts = Parameter(
        s3_bucket_for_artifacts_param_name, Type="String"
    )

    # Blog Post Image Generator
    blog_post_image_generator_s3_zip_path_param_name = "BlogPostImageGeneratorS3ZipPath"
    blog_post_image_generator_s3_zip_path = Parameter(
        blog_post_image_generator_s3_zip_path_param_name, Type="String"
    )
    blog_post_image_generator_function = FunctionBlogPostImageGenerator(
        application_prefix,
        s3_bucket_for_artifacts_param_name,
        blog_post_image_generator_s3_zip_path_param_name,
        "/SmyleeDevWorkflows",
        primary_kms_arn,
        cdn_bucket_name,
    )
    main_template = blog_post_image_generator_function.add_resource(main_template)
    main_template.add_output(
        Output(
            application_prefix + "ImageGeneratorTopic",
            Export=Export(f"S3::{application_prefix}-SNSImageGeneratorTopic"),
            Description="SNS Topic to trigger the blog post image generator function",
            Value=Ref(main_template.resources["ImageGeneratorTopic"]),
        )
    )

    # add parameters to template
    main_template.add_parameter(s3_bucket_for_artifacts)
    main_template.add_parameter(blog_post_image_generator_s3_zip_path)

    with open(os.path.join(os.path.dirname(__file__), template_file), "w") as cf_file:
        cf_file.write(main_template.to_yaml())

    print(main_template.to_yaml())
