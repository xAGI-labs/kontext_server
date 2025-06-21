# MLP

## Overview

You are an expert in building Full stack applications using FastAPI.
You are expert in building APIs using fastapi.
initialize a fast api app and do the tasks

## Task

1. read through the entire repository
2. we're going to simply create a api server in next js that is going to work with replicate, these 3 inputs are going to work like this:
    
    1. [localhost:3000/img/](http://localhost:3000/img/cats)<img-prompt> → img response 
    this api endpoint will take a prompt and generate a image response basically, the url doesnt have to be strictly that but the functionality is that 

    [localhost:3000/img/](http://localhost:3000/img/cats)<img-prompt>/ <editing-prompt>
    this api endpoint will take image prompt and an editing prompt and generate an image response with the image doing that pose or whatever is edited

    [localhost:3000/img/](http://localhost:3000/img/cats)<img-url>/ <editing-prompt>
    this api endpoint will take a image url and an editing prompt and return an image response ith the image doing that pose or whatever is edited


4. For replicate: use this npm install replicate

    https://replicate.com/black-forest-labs/flux-kontext-pro/api follow this url to do this

5. I've already passed REPLICATE_API_TOKEN in the .env so use it accordingly