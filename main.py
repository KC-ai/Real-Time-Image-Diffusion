

#code to set up modal and how to connect that to nextjs app, and how to do cold starts and optimizations from there 

#setting up modal is the main part of this project 

#possible to set up odal in next js app but advisable to create it in separate folder or repo bc if you change back end for modal, you dont want to redeploy next js app 

#to start off we need to import a bunch of libraries 
#libraries installed locally but also within modal containers 

#TODO: LOOK AT BEST PRACTICES FOR GOING THROUGH AND LOOKING AT DOCS, AND TRY WITH MODAL DOCS 

#modal endpoints is fastapi server under the hood 

import modal 
import io 
from fastapi import Response, HTTPException, Query, Request 
from datetime import datetime, timezone
import requests
import os

#most of code was taken from Building a Stable Diffusion + LoRA image generation pipeline on Modal
#requests since requests to our enpoints and access to env vars as well with os 

#first download image gen model 

#we're going to use this model: https://huggingface.co/stabilityai/sdxl-turbo

#define function called downlaod model 

def download_model():
    from diffusers import AutoPipelineForText2Image
    import torch 

    pipe = AutoPipelineForText2Image.from_pretrained("stabilityai/sdxl-turbo", torch_dtype=torch.float16, variant="fp16")
    #we use the 16 bit precision - highest bit is 32, if you want your generation to be faster go lower but quality is worse
    #TODO: WHAT IS PRECISION? 
    #from here just set up your modal image. its like docker container env 
    #we need to set the os of our image
    #modal spinning up docker container that runs on linux and uses debian os 
    #installing certain libraries inside the container itself, since locally its hella heavy so within the image we're installing them 
    #image is docker container 

image = (
    modal.Image.debian_slim()
    .pip_install("fastapi[standard]", "transformers", "accelerate", "diffusers", "requests")
    .run_function(download_model))

#now we need to set up our modal app 

app = modal.App("sd-demo1", image=image)

#we need to set up a class and set up deocrator 

#pass in a secrets parameter here
@app.cls(
    image = image, 
    gpu="A10G", #prolly best value here for the GPU and our purposes. If you experience high load, modal lets you distribute it across multiple GPUs
    container_idle_timeout=300,   #need to specify container idle timeout - keep it on for 5 mins after last use, hitting endpoint every 5 minutes 
    secrets=[modal.Secret.from_name("custom-secret")]

)

class Model:
    #define function to load weights of our model here 

    #2 decorators, so function thats called when docker container is building and packaging your shit up 

    @modal.build()
    @modal.enter()
    #TODO: LOOK INTO THEIR DOCS 

    #we're loading weights instead of dwnldng it since we alr dwnld image b4 hand 
    def load_weights(self):
        from diffusers import AutoPipelineForText2Image
        import torch 

        self.pipe = AutoPipelineForText2Image.from_pretrained("stabilityai/sdxl-turbo", torch_dtype=torch.float16, variant="fp16")

        #we specify model again and pipe this to CUDA since we tell modal to make sure this runs on GPU
        #NVIDIA's biggest moat is CUDA. Their CUDA kernels are sw stack and theyre better by far
        #TODO: LOOK INTO HOW TO WRITE CUDA KERNELS 
        self.pipe.to("cuda")

        #this is within our docker container, so its already accesisble there 
        self.API_KEY = os.environ["API_KEY"]

    #create modal endpoint - query endpoint from nextjs app

    @modal.web_endpoint()
    #we have https type request param and the prompt has a query param as well (this is like search and sort on HF)
    def generate(self, request: Request, prompt: str = Query(..., description="The prompt for image generation")):

        #if the api key sent in the request headers doesnt match the api key we set ourselves, we raise an error
        api_key = request.headers.get("X-API-Key")
        if api_key != self.API_KEY:
            raise HTTPException(
                status_code=401,
                detail="Unauthorized"

            )








        #our image is going to be pipe function that takes in prompt - img user wants gen, and number of inference steps (the more the quality higher latency)
        image = self.pipe(prompt, num_inference_steps=1, guidance_scale=0.0).images[0] #higher guidance the more it confines to the prompt but 0.0 disables it 
        #we get list of images and get the first but we want to laod it into memory to load fast

        #create buffer since more efficient that saving to disk 

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        
        #we just return image from buffer 
        #we should have some verification on our backend to make sure the media/datatype we're getting is an image
        return Response(content = buffer.getvalue(), media_type="image/jpeg")
    

    #another api endpoint named health 
    @modal.web_endpoint()
    def health(self):
        """Lightweight endpoint for keeping the container warm"""
        return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
    
    #by doing this our container doesn't spin down - it's always active. preventing cold start
    #this endpoint isnt doing a calculation, its just keeping a container warm - diff than gen an img which reqs GPUs
    
#modal deploy your_modal_file.py provides a URL you can use in your Next.js app API calls.








#this is our url: https://kc-ai--sd-demo1-model-generate.modal.run/
#once we have our url we need to authenticate since now we hv $$ thats wasted if someone uses it 
#to secure API we need to ensure no one can touch API we use api key 
# if someone got access to url can burn all our credits 
# for api key within modal, theres a secrets place where we can put in environment variable etc.
#  Hit custom and create a new secret and using python library secret, just create a new one and put it in
#

# import secrets

# # Generate a random URL-safe string with approximately 22 characters (16 bytes)
# random_urlsafe = secrets.token_urlsafe(16)
# print(random_urlsafe)

#any sensitive key you would access by adding to the decorator


#after authentication, lets work on the cold start part. 
#one thing to note is bc modal is serverless service, code is running in docker containers. so needs to spin up and spin down 
#by default, modal container spins down after 60 sec of inactivity 
#so put another param in decorator where you put default number for timeout/ spin down. 
#this is an issue since gpu has to cold start up again if no one uses it for a while - hella slow 

#another param named keep_warm, with containers always running but this bills you so its tough w limited budget 

#thus a solution is a cron job (job running periodically) that pings your api periodically - every couple mins or every hour so it nvr spins dwn

#lets do cron job every 5 mins 
@app.function(
    schedule=modal.Cron("*/5 * * * *"),
    secrets=[modal.Secret.from_name("custom-secret")]
)
def keep_warm():
    generate_url = "https://kc-ai--sd-demo1-model-generate.modal.run"
    health_url = "https://kc-ai--sd-demo1-model-health.modal.run"

    # # First check health endpoint (no API key needed)
    health_response = requests.get(health_url)
    print(f"Health check at: {health_response.json()['timestamp']}")

    # Then make a test request to generate endpoint with API key
    headers = {"X-API-Key": os.environ["API_KEY"]}
    generate_response = requests.get(generate_url, headers=headers)
    print(f"Generate endpoint tested successfully at: {datetime.now(timezone.utc).isoformat()}")

#next we create another api endpoint using the modal web endpoint 