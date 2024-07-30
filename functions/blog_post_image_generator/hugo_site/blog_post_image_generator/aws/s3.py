import os


def upload(image_temp_directory, images_bucket_name, s3_client, image_info):
    local_path = os.path.join(image_temp_directory, image_info)
    s3_client.upload_file(
        local_path,
        images_bucket_name,
        image_info,
        ExtraArgs={"ContentType": "image/png"},
    )
