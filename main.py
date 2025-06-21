from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
import replicate
import os
import requests
from typing import Optional
import base64
from io import BytesIO

def load_env():
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    except FileNotFoundError:
        pass

load_env()

app = FastAPI(title="Image Generation API", description="API for image generation and editing using Replicate")

replicate_client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))

def download_image_as_base64(url: str) -> str:
    """Download image from URL and convert to base64"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return base64.b64encode(response.content).decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download image: {str(e)}")

def get_image_from_replicate_output(output) -> bytes:
    """Get image bytes from Replicate output"""
    try:
        if isinstance(output, list) and len(output) > 0:
            image_url = output[0]
        else:
            image_url = output
        
        response = requests.get(image_url)
        response.raise_for_status()
        return response.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get image from Replicate: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Image Generation API is running"}

@app.get("/img/{img_prompt}")
async def generate_image(img_prompt: str):
    """
    Generate an image from a text prompt
    """
    try:
        output = replicate_client.run(
            "black-forest-labs/flux-kontext-pro",
            input={
                "prompt": img_prompt,
                "num_outputs": 1,
                "aspect_ratio": "1:1",
                "output_format": "png",
                "output_quality": 80
            }
        )
        
        image_bytes = get_image_from_replicate_output(output)
        
        return Response(content=image_bytes, media_type="image/png")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

@app.get("/img/{img_prompt}/{editing_prompt}")
async def generate_and_edit_image(img_prompt: str, editing_prompt: str):
    """
    Generate an image from a prompt and then edit it with another prompt
    """
    try:
        base_output = replicate_client.run(
            "black-forest-labs/flux-kontext-pro",
            input={
                "prompt": img_prompt,
                "num_outputs": 1,
                "aspect_ratio": "1:1",
                "output_format": "png",
                "output_quality": 80
            }
        )
        
        # Get the base image URL
        if isinstance(base_output, list) and len(base_output) > 0:
            base_image_url = base_output[0]
        else:
            base_image_url = base_output
        
        # Convert base image to base64 for editing
        base_image_b64 = download_image_as_base64(base_image_url)
        
        # Edit the image with the editing prompt
        edited_output = replicate_client.run(
            "black-forest-labs/flux-kontext-pro",
            input={
                "prompt": editing_prompt,
                "image": f"data:image/png;base64,{base_image_b64}",
                "num_outputs": 1,
                "aspect_ratio": "1:1",
                "output_format": "png",
                "output_quality": 80
            }
        )
        
        # Get edited image bytes
        image_bytes = get_image_from_replicate_output(edited_output)
        
        return Response(content=image_bytes, media_type="image/png")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation and editing failed: {str(e)}")

@app.get("/edit/{img_url:path}/{editing_prompt}")
async def edit_image_from_url(img_url: str, editing_prompt: str):
    """
    Edit an existing image from URL with an editing prompt
    """
    try:
        # Download and convert image to base64
        image_b64 = download_image_as_base64(img_url)
        
        # Edit the image with the editing prompt
        output = replicate_client.run(
            "black-forest-labs/flux-kontext-pro",
            input={
                "prompt": editing_prompt,
                "image": f"data:image/png;base64,{image_b64}",
                "num_outputs": 1,
                "aspect_ratio": "1:1",
                "output_format": "png",
                "output_quality": 80
            }
        )
        
        # Get edited image bytes
        image_bytes = get_image_from_replicate_output(output)
        
        return Response(content=image_bytes, media_type="image/png")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image editing failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
