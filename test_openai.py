
import os
from dotenv import load_dotenv
from openai import OpenAI

# Step 1: Load the .env file
load_dotenv()

# Step 2: Verify the API key exists
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OpenAI API key not found!")

# Step 3: Create the OpenAI client
client = OpenAI(timeout=30.0, max_retries=1)

# Step 4: Ask a simple biology question
print("Sending request to OpenAI...", flush=True)

response = client.responses.create(
    model="gpt-5-mini",
    instructions=(
        "You are a biomedical research assistant. "
        "Explain biological concepts clearly. "
        "Do not invent scientific citations."
    ),
    input="Explain what the PKD1 gene does in 2 simple sentences.",
    max_output_tokens=300
)

# Step 5: Display the response
print("\nLLM Response:")
print(response.output_text)
