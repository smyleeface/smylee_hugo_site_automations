import base64
from datetime import datetime
import json
import os


def generate_image(title, description, filename, bedrock_client, image_temp_directory, model_type, number_of_images=1):
    prompt = f'Use a combination of technology, scenic, and animal imagery where the title and description are:\n\n"{title}"\n"{description}"\n\n.'
    negative_prompt = "avoid using typography or text"
    if model_type == "stability_ai":
        bedrock_image_names = run_stability_ai(
            prompt, negative_prompt, bedrock_client, filename, image_temp_directory, number_of_images
        )
    else:
        bedrock_image_names = run_titan_image_generator(
            prompt, negative_prompt, bedrock_client, filename, image_temp_directory, number_of_images
        )
    return bedrock_image_names


def invoke_model(bedrock_client, input_text, model_name):
    try:
        bedrock_response = bedrock_client.invoke_model(
            body=json.dumps(input_text).encode("utf-8"),
            contentType="application/json",
            accept="application/json",
            modelId=model_name,
        )
        response_body = json.loads(bedrock_response["body"].read().decode("utf-8"))
        return response_body
    except Exception as e:
        print(e)
        raise e


def save_image(image_data, idx, image_temp_directory, filename, timestamp):
    base_filename = os.path.basename(filename).replace(".md", "")
    base_pathname = os.path.dirname(filename).replace("content/post/", "images/")
    os.makedirs(f"{image_temp_directory}/{base_pathname}", exist_ok=True)
    image_filename = f"{base_pathname}/{base_filename}_image_{idx}_{timestamp}.png"
    with open(f"{image_temp_directory}/{image_filename}", "wb") as image_file:
        image_file.write(base64.b64decode(image_data))
    return image_filename


def run_stability_ai(
    prompt,
    negative_prompt,
    bedrock_client,
    filename,
    image_temp_directory,
    number_of_images=1,
):
    input_text = {
        "text_prompts": [
            {"text": prompt, "weight": 1, "negativeText": negative_prompt}
        ],
        "cfgScale": 8,
        "seed": 0,
        "steps": 50,
        "quality": "standard",
        "width": 512,
        "height": 512,
        "numberOfImages": number_of_images,
    }
    model_name = "stability.stable-diffusion-xl-v1"
    response_body = invoke_model(bedrock_client, input_text, model_name)
    images = response_body["artifacts"]
    # Save images locally
    filenames = []
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    for idx, image_data in enumerate(images):
        filenames.append(
            save_image(image_data.get("base64"), idx, image_temp_directory, filename, timestamp)
        )
    return filenames


def run_titan_image_generator(
    prompt,
    negative_prompt,
    bedrock_client,
    filename,
    image_temp_directory,
    number_of_images=1,
):
    input_text = {
        "textToImageParams": {"text": prompt, "negativeText": negative_prompt},
        "taskType": "TEXT_IMAGE",
        "imageGenerationConfig": {
            "cfgScale": 8,
            "seed": 0,
            "quality": "standard",
            "width": 1024,
            "height": 1024,
            "numberOfImages": number_of_images,
        },
    }
    model_name = "amazon.titan-image-generator-v1"
    response_body = invoke_model(bedrock_client, input_text, model_name)
    images = response_body["images"]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    # Save images locally
    filenames = []
    for idx, image_data in enumerate(images):
        filenames.append(save_image(image_data, idx, image_temp_directory, filename, timestamp))
    return filenames
