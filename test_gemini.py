#!/usr/bin/env python3
"""
Simple test script to verify Google Gemini API is working
"""
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv('backend/.env')

def test_gemini_api():
    """Test basic Gemini API functionality"""
    api_key = os.getenv("GOOGLE_API_KEY")
    print(f"API key present: {bool(api_key)}")
    print(f"API key length: {len(api_key) if api_key else 0}")
    
    if not api_key:
        print("❌ No GOOGLE_API_KEY found!")
        return
    
    try:
        # Test with simple model
        print("🧪 Testing Gemini API with simple request...")
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.1,
            google_api_key=api_key,
        )
        
        # Simple test prompt
        prompt = ChatPromptTemplate.from_messages([
            ("human", "Return exactly this JSON: {{\"test\": \"success\", \"status\": \"working\"}}")
        ])
        
        chain = prompt | llm
        result = chain.invoke({"input": "test"})
        
        print(f"✅ API Response received!")
        print(f"Response content: {repr(result.content)}")
        print(f"Response length: {len(result.content)}")
        
        # Try to parse as JSON
        import json
        try:
            parsed = json.loads(result.content)
            print(f"✅ Valid JSON response: {parsed}")
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}")
            print(f"Raw response: {result.content}")
            
    except Exception as e:
        print(f"❌ API call failed: {e}")
        print(f"Exception type: {type(e).__name__}")

if __name__ == "__main__":
    test_gemini_api()