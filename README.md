# Image Generation API

A FastAPI-based image generation and editing service using Replicate's Flux Kontext Pro model.

## Setup

1. Make sure you have Python 3.7+ installed
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Make sure your `.env` file contains your Replicate API token:
   ```
   REPLICATE_API_TOKEN=your_token_here
   ```
   (The application will automatically load this from the .env file)

## Running the Server

### Option 1: Direct Python Execution

```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 2: Docker Deployment (Recommended)

#### Using Docker Compose (Easiest)
```bash
# Build and start the container
docker-compose up --build

# Run in detached mode
docker-compose up -d --build

# Stop the container
docker-compose down
```

#### Using Docker directly
```bash
# Build the image
docker build -t image-generation-api .

# Run the container
docker run -p 8000:8000 --env-file .env image-generation-api
```

The server will start on `http://localhost:8000`

## API Endpoints

### 1. Generate Image from Prompt
**GET** `/img/{img_prompt}`

Generates an image from a text prompt.

**Example:**
```
GET http://localhost:8000/img/a%20beautiful%20sunset%20over%20mountains
```

### 2. Generate and Edit Image
**GET** `/img/{img_prompt}/{editing_prompt}`

First generates an image from the initial prompt, then edits it with the editing prompt.

**Example:**
```
GET http://localhost:8000/img/a%20cat%20sitting/make%20it%20wearing%20a%20hat
```

### 3. Edit Image from URL
**GET** `/edit/{img_url}/{editing_prompt}`

Takes an existing image URL and applies an editing prompt to it.

**Example:**
```
GET http://localhost:8000/edit/https%3A//example.com/image.jpg/add%20sunglasses
```

## Response Format

All endpoints return the generated/edited image directly as a WebP image file with the appropriate `image/webp` content type.

## API Documentation

Once the server is running, you can access:
- Interactive API docs: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`

## Notes

- All images are generated in 1:1 aspect ratio as WebP format
- URL encoding is required for prompts and image URLs containing special characters
- The service uses Replicate's Flux Kontext Pro model for high-quality image generation and editing
