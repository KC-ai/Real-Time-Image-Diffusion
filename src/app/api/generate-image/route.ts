import { NextResponse } from "next/server";
import { put } from "@vercel/blob"

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { text } = body;

    //done new 
    const apiSecret = request.headers.get("X-API-Secret");
    if (apiSecret !== process.env.API_SECRET) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // TODO: Call your Image Generation API here
    // For now, we'll just echo back the text

      ////////////
    //Never call external api on client side
    //first you need to get the prompt the user sent
    console.log(text)

    const url = new URL("https://kc-ai--sd-demo1-model-generate.modal.run/")
    //security rzns this is btr 

    url.searchParams.set("prompt", text)

    console.log("Requesting URL", url.toString())

    //we create fetch request to this url 
    const response = await fetch(url.toString(), {
      method: "GET", 
      headers: {
        //sending our X-API-Key through backend here 
        "X-API-Key": process.env.API_KEY || "", 
        Accept: "image/jpeg",
      },
    });

    //need some basic error handling 

    if (!response.ok){
      const errorText = await response.text();
      console.error("API Response:", errorText);
      throw new Error(
        `HTTP error! status: ${response.status}, message: ${errorText}`

      );
    }

    //asynchronous, so need to await the response 
    const imageBuffer = await response.arrayBuffer();

    //maybe could name img after the prompt, this is naive approach tho cuz could use malicious code etc
    //so have random user id or something, which is why we use crypto
    const filename = `${crypto.randomUUID()}.jpg`

    const blob = await put(filename, imageBuffer, {
      access: "public", 
      contentType: "image/jpeg",
    } )

    //code similar with any other storage 

    //return our imageurl to display it on the frontend

    return NextResponse.json({
      success: true, 
      imageUrl: blob.url,
    });

    //need to store the prompt and image url in a databse here 
    //once we do that, thats the entire back end 

    //regardless you should be storing the file path you get on vercel and put that in our db 



    /////////////








    return NextResponse.json({
      success: true,
      message: `Received: ${text}`,
    });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Failed to process request" },
      { status: 500 }
    );
  }
}