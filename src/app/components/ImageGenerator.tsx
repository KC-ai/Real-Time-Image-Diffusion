//this is all the client side code, with no fetch requests 
//only line thats diff is instead of fetch req, calling generateImage function from server actions 
"use client";

import { url } from "inspector";
import { useState } from "react";

interface ImageGeneratorProps {
  generateImage: (text: string) => Promise<{ success: boolean; imageUrl?: string; error?: string }>;
}

export default function ImageGenerator({ generateImage }: ImageGeneratorProps) {
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setImageUrl(null);

    try {
      const result = await generateImage(inputText);

      if (!result.success) {
        throw new Error(result.error || "Failed to generate image");
      }

      if (result.imageUrl) {
        const img = new Image();
        const url = result.imageUrl
        img.onload = () => {
            setImageUrl(url);
        };
        img.src = url;
        // img.src = result.imageUrl;

      } else {
        throw new Error("No image URL received");
      }
      setInputText("");
    } catch (error) {
      console.error("Error:", error);
      setError(error instanceof Error ? error.message : "Failed to generate image");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-between p-8">
      <main className="flex-1 flex flex-col items-center gap-8">
        {error && (
          <div className="w-full max-w-2xl p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
            {error}
          </div>
        )}
        {imageUrl && (
          <div className="w-full max-w-2xl rounded-lg overflow-hidden shadow-lg">
            <img src={imageUrl} alt="Generated artwork" className="w-full h-auto" />
          </div>
        )}
        {isLoading && (
          <div className="w-full max-w-2xl flex items-center justify-center">
            <div className="w-12 h-12 border-4 border-gray-300 border-t-black rounded-full animate-spin"></div>
          </div>
        )}
      </main>
      <footer className="w-full max-w-3xl mx-auto">
        <form onSubmit={handleSubmit} className="w-full">
          <div className="flex gap-2">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              className="flex-1 p-3 rounded-lg bg-black/[.05] dark:bg-white/[.06] border focus:outline-none focus:ring-2"
              placeholder="Describe the image you want to generate..."
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !inputText.trim()}
              className="px-6 py-3 rounded-lg bg-foreground hover:bg-gray-600 transition disabled:opacity-50"
            >
              {isLoading ? "Generating..." : "Generate"}
            </button>
          </div>
        </form>
      </footer>
    </div>
  );
}
