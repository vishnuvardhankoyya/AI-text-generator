"""
Install the Google AI Python SDK

$ pip install google-generativeai

See the getting started guide for more information:
https://ai.google.dev/gemini-api/docs/get-started/python
"""

import os
from gradio_client import Client

# Set environment variable (do this in your shell or script setup)
# export HF_ACCESS_TOKEN='your-access-token'

# Fetch the access token from environment variable
access_token ="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"

# Replace with your actual username and Space name on Hugging Face
repo_id = "vishnukoyya/chatbot"

# Initialize the client with the repo_id and authentication token
client = Client(repo_id, hf_token=access_token)

# Send a request to the Gradio app
 # Ensure this matches your Gradio app's endpoint
result = client.predict(
		message="Hello!!",
		system_message="You are a friendly Chatbot.",
		max_tokens=512,
		temperature=0.7,
		top_p=0.95,
		api_name="/chat"
)
print(result)