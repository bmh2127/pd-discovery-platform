import google.generativeai as genai
import os
from dotenv import load_dotenv

# Test Google AI SDK
load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Fixed: Use current model name
model = genai.GenerativeModel('gemini-1.5-flash')  # Changed from 'gemini-pro'

response = model.generate_content("What are the key motor symptoms of Parkinson's disease?")
print("Gemini response:", response.text)