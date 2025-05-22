import os
from groq import Groq
import logging

class GroqService:
    def __init__(self, api_key=None):
        """Initialize Groq client with API key from environment variable or passed directly."""
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "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")
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"  # Default model
        logging.info("GroqService initialized")

    async def generate_response(self, message_text, chat_history=None):
        """Generate a response to a message using Groq API."""
        try:
            messages = []
            
            # Add chat history if provided
            if chat_history:
                for msg in chat_history:
                    if msg.get("role") and msg.get("content"):
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
            
            # Add the current message
            messages.append({
                "role": "user",
                "content": message_text
            })
            
            # Make the API call
            completion = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            logging.error(f"Error generating response from Groq: {str(e)}")
            return "Sorry, I couldn't generate a response at this time." 