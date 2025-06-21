from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, HTMLResponse
from fastapi.staticfiles import StaticFiles
import replicate
import os
import requests
from typing import Optional
import base64
from io import BytesIO
from pydantic import BaseModel

class AnimationRequest(BaseModel):
    image_url: str
    frames: Optional[int] = 8

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

app = FastAPI(title="Kontext Sprite Generator", description="Professional AI sprite generation using FLUX Kontext Pro")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

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

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the landing page"""
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Landing page not found</h1><p>Please make sure templates/index.html exists</p>")

@app.get("/health")
async def health():
    return {"message": "Kontext Sprite Generator API is running"}

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
                "input_image": f"data:image/png;base64,{base_image_b64}",
                "num_outputs": 1,
                "aspect_ratio": "match_input_image",
                "output_format": "png",
                "output_quality": 80,
                "safety_tolerance": 2
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
                "input_image": f"data:image/png;base64,{image_b64}",
                "num_outputs": 1,
                "aspect_ratio": "match_input_image",
                "output_format": "png",
                "output_quality": 80,
                "safety_tolerance": 2
            }
        )
        
        # Get edited image bytes
        image_bytes = get_image_from_replicate_output(output)
        
        return Response(content=image_bytes, media_type="image/png")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image editing failed: {str(e)}")

@app.get("/spritegen/{description}")
async def generate_sprite(description: str):
    """
    Generate a video game sprite based on description
    """
    try:
        # Optimize prompt for sprite generation
        sprite_prompt = f"pixel art sprite, {description}, 8-bit style, retro video game character, clean pixel art, transparent background, game sprite sheet style, detailed pixelated design"
        
        output = replicate_client.run(
            "black-forest-labs/flux-kontext-pro",
            input={
                "prompt": sprite_prompt,
                "num_outputs": 1,
                "aspect_ratio": "1:1",
                "output_format": "png",
                "output_quality": 100,
                "safety_tolerance": 2
            }
        )
        
        image_bytes = get_image_from_replicate_output(output)
        
        return Response(content=image_bytes, media_type="image/png")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sprite generation failed: {str(e)}")

@app.get("/spritegen-multi/{description}")
async def generate_multiple_sprites(description: str):
    """
    Generate 6 different video game sprite poses of the same character using iterative editing for consistency
    """
    try:
        sprites = []
        count = 6  # Fixed count of 6 sprites
        
        # Step 1: Generate base sprite
        base_sprite_prompt = f"pixel art sprite, {description}, 8-bit style, retro video game character, clean pixel art, transparent background, game sprite sheet style, detailed pixelated design"
        
        base_output = replicate_client.run(
            "black-forest-labs/flux-kontext-pro",
            input={
                "prompt": base_sprite_prompt,
                "num_outputs": 1,
                "aspect_ratio": "1:1",
                "output_format": "png",
                "output_quality": 100,
                "safety_tolerance": 2
            }
        )
        
        # Get base sprite
        base_image_url = base_output[0] if isinstance(base_output, list) else base_output
        base_image_b64 = download_image_as_base64(base_image_url)
        
        # Add base sprite to results
        sprites.append({
            "index": 1,
            "variation": "idle",
            "image_data": base_image_b64,
            "image_url": base_image_url
        })
        
        # Step 2: Generate 5 variations using iterative editing
        variation_prompts = [
            f"Make the {description} face left direction while maintaining identical character design and pixel art style",
            f"Make the {description} face right direction while maintaining identical character design and pixel art style", 
            f"Change the {description} to a jumping pose while keeping the exact same character appearance and pixel art style",
            f"Make the {description} in a crouching pose while maintaining identical character design and pixel art style",
            f"Give the {description} an attacking pose while preserving the same character identity and pixel art style"
        ]
        
        for i in range(1, count):
            try:
                # Use the base image as input for editing
                variation_prompt = variation_prompts[i-1]
                print(variation_prompt)
                variation_names = ["left_facing", "right_facing", "jumping", "crouching", "attacking"]
                
                edited_output = replicate_client.run(
                    "black-forest-labs/flux-kontext-pro",
                    input={
                        "prompt": variation_prompt,
                        "input_image": f"data:image/png;base64,{base_image_b64}",
                        "num_outputs": 1,
                        "aspect_ratio": "match_input_image",
                        "output_format": "png",
                        "output_quality": 100,
                        "safety_tolerance": 2
                    }
                )
                
                # Get edited sprite
                edited_image_url = edited_output[0] if isinstance(edited_output, list) else edited_output
                edited_image_b64 = download_image_as_base64(edited_image_url)
                
                sprites.append({
                    "index": i + 1,
                    "variation": variation_names[i-1],
                    "image_data": edited_image_b64,
                    "image_url": edited_image_url
                })
                
            except Exception as e:
                sprites.append({
                    "index": i + 1,
                    "variation": variation_names[i-1] if i-1 < len(variation_names) else f"pose_{i}",
                    "error": f"Failed to generate variation {i}: {str(e)}"
                })
        
        return {
            "description": description,
            "total_sprites": count,
            "sprites_generated": len([s for s in sprites if "error" not in s]),
            "method": "iterative_editing_for_consistency",
            "variations": ["idle", "left_facing", "right_facing", "jumping", "crouching", "attacking"],
            "sprites": sprites
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multiple sprite generation failed: {str(e)}")

@app.post("/animate/{animation_type}")
async def generate_animation_sprites(animation_type: str, request: AnimationRequest):
    """
    Generate animation sprites from an existing character image for specific animation types
    Animation types: walk, run, jump, attack, idle, death, cast, defend
    """
    try:
        print(f"Received request for animation_type: {animation_type}")
        print(f"Request data: {request}")
        
        # Validate animation type
        valid_animations = ["walk", "run", "jump", "attack", "idle", "death", "cast", "defend"]
        if animation_type.lower() not in valid_animations:
            raise HTTPException(status_code=400, detail=f"Invalid animation type. Must be one of: {valid_animations}")
        
        # Validate frames count
        if request.frames < 2 or request.frames > 8:
            raise HTTPException(status_code=400, detail="Frames must be between 2 and 8")
        
        sprites = []
        
        print(f"Downloading base image from: {request.image_url}")
        # Download base image
        base_image_b64 = download_image_as_base64(request.image_url)
        print("Base image downloaded successfully")
        
        # Add original image as first frame
        sprites.append({
            "frame": 1,
            "animation_type": animation_type,
            "image_data": base_image_b64,
            "image_url": request.image_url
        })
        
        # Define animation-specific prompts
        animation_prompts = {
            "walk": [
                "Change to walking animation frame 2 - left foot forward while keeping the same character and pixel art style",
                "Change to walking animation frame 3 - right foot forward while keeping the same character and pixel art style", 
                "Change to walking animation frame 4 - mid-stride pose while keeping the same character and pixel art style"
            ],
            "run": [
                "Change to running animation frame 2 - fast running pose with arms pumping while keeping the same character and pixel art style",
                "Change to running animation frame 3 - full sprint with body leaning forward while keeping the same character and pixel art style",
                "Change to running animation frame 4 - running with opposite leg forward while keeping the same character and pixel art style"
            ],
            "jump": [
                "Change to jumping animation frame 2 - crouching before jump while keeping the same character and pixel art style",
                "Change to jumping animation frame 3 - mid-air jump pose while keeping the same character and pixel art style",
                "Change to jumping animation frame 4 - landing pose while keeping the same character and pixel art style"
            ],
            "attack": [
                "Change to attack animation frame 2 - wind-up attack pose while keeping the same character and pixel art style",
                "Change to attack animation frame 3 - mid-attack strike while keeping the same character and pixel art style",
                "Change to attack animation frame 4 - follow-through attack pose while keeping the same character and pixel art style"
            ],
            "idle": [
                "Change to idle animation frame 2 - slight breathing movement while keeping the same character and pixel art style",
                "Change to idle animation frame 3 - subtle pose variation while keeping the same character and pixel art style",
                "Change to idle animation frame 4 - return to neutral stance while keeping the same character and pixel art style"
            ],
            "death": [
                "Change to death animation frame 2 - staggering backward while keeping the same character and pixel art style",
                "Change to death animation frame 3 - falling down while keeping the same character and pixel art style",
                "Change to death animation frame 4 - lying on ground while keeping the same character and pixel art style"
            ],
            "cast": [
                "Change to casting animation frame 2 - raising hands to cast spell while keeping the same character and pixel art style",
                "Change to casting animation frame 3 - channeling magic energy while keeping the same character and pixel art style",
                "Change to casting animation frame 4 - releasing spell while keeping the same character and pixel art style"
            ],
            "defend": [
                "Change to defend animation frame 2 - raising shield/guard while keeping the same character and pixel art style",
                "Change to defend animation frame 3 - full defensive stance while keeping the same character and pixel art style",
                "Change to defend animation frame 4 - blocking impact while keeping the same character and pixel art style"
            ]
        }
        
        # Generate animation frames
        selected_prompts = animation_prompts[animation_type.lower()][:request.frames-1]
        
        for i, prompt in enumerate(selected_prompts):
            try:
                edited_output = replicate_client.run(
                    "black-forest-labs/flux-kontext-pro",
                    input={
                        "prompt": prompt,
                        "input_image": f"data:image/png;base64,{base_image_b64}",
                        "num_outputs": 1,
                        "aspect_ratio": "match_input_image",
                        "output_format": "png",
                        "output_quality": 100,
                        "safety_tolerance": 2
                    }
                )
                
                # Get edited sprite
                edited_image_url = edited_output[0] if isinstance(edited_output, list) else edited_output
                edited_image_b64 = download_image_as_base64(edited_image_url)
                
                sprites.append({
                    "frame": i + 2,
                    "animation_type": animation_type,
                    "image_data": edited_image_b64,
                    "image_url": edited_image_url
                })
                
            except Exception as e:
                sprites.append({
                    "frame": i + 2,
                    "animation_type": animation_type,
                    "error": f"Failed to generate frame {i + 2}: {str(e)}"
                })
        
        return {
            "animation_type": animation_type,
            "total_frames": request.frames,
            "frames_generated": len([s for s in sprites if "error" not in s]),
            "method": "iterative_editing_animation",
            "original_image": request.image_url,
            "sprites": sprites
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in animate endpoint: {error_details}")
        raise HTTPException(status_code=500, detail=f"Animation sprite generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
