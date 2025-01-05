//separating out client side code and code we're running on the server. 
//this is code we're running on server 

"use server";

//here well call internal api 
//bc this is running on server no one can see headers so only thing that changed is adding that one header 
//now we have t do some refactoring 


export async function generateImage(text: string) {
    try {
      const response = await fetch('http://localhost:3000/api/generate-image', {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-SECRET": process.env.API_SECRET || "",
        },
        body: JSON.stringify({ text }),
      });
  
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
  
      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Server Error:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Failed to generate image",
      };
    }
  }
  