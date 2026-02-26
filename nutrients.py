import os
import json
import google.generativeai as genai
from google.generativeai import TaskType
from langchain_community.document_loaders import DirectoryLoader, PDFMinerLoader, TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("AIzaSyCgRNgd04AllhAdKTdbDFNlG-ollnwsTTI"))

# Define your knowledge base folder path - you'll manually add files here
NUTRITION_KB_PATH = "./assets/nutrition_kb"
VECTOR_STORE_PATH = "./assets/nutrition_kb/vector_store.index"

# Define nutrition values list
nutrition_values_list = [
    "Calories", 
    "FatContent", 
    "SaturatedFatContent", 
    "CholesterolContent", 
    "SodiumContent", 
    "CarbohydrateContent", 
    "FiberContent", 
    "SugarContent", 
    "ProteinContent"
]

async def get_nutrition_recommendation(disease, user_language="English"):
    """Generate personalized nutrition values based on disease using knowledge base"""
    
    # Initialize the vector store from the knowledge base folder
    vector_store = await initialize_vector_store(NUTRITION_KB_PATH)
    
    # Search for relevant context from knowledge base
    context = []
    if vector_store:
        results = await vector_store.similarity_search(f"nutrition for {disease}", k=3)
        context = [doc.page_content for doc in results]
    
    # Join context information
    context_text = "\n\n".join(context) if context else "No specific context available."
    
    # Create prompt for Gemini
    prompt = f"""
    You are a nutrition expert specializing in medical nutrition therapy.
    
    CONTEXT INFORMATION FROM KNOWLEDGE BASE:
    {context_text}
    
    Based on the above context and your knowledge, generate personalized nutrition values for someone with {disease}.
    
    Provide ONLY a JSON object with the following nutrition values:
    {nutrition_values_list}
    
    The output should be ONLY a valid JSON object with numeric values for each nutrient and include a brief
    "description" explaining why these values are appropriate for {disease}.
    
    For example:
    {{
        "Calories": 1800,
        "FatContent": 55,
        "SaturatedFatContent": 16,
        "CholesterolContent": 200,
        "SodiumContent": 1500,
        "CarbohydrateContent": 200,
        "FiberContent": 35,
        "SugarContent": 25,
        "ProteinContent": 60,
        "description": "This diet is tailored for {disease} by [explanation]"
    }}
    
    Response should be in {user_language}.
    """
    
    # Generate response with Gemini
    generation_config = {
        "max_output_tokens": 1024,
        "temperature": 0.2,
        "top_p": 0.95,
        "top_k": 5,
    }
    
    model = genai.GenerativeModel(
        model_name="gemini-2.5-pro",
        generation_config=generation_config
    )
    
    response = model.generate_content(prompt)
    response_text = response.text
    
    # Parse the JSON response
    try:
        # Clean up response if it contains markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        nutrition_data = json.loads(response_text)
        return nutrition_data
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Raw response: {response_text}")
        # Fallback response
        return {
            "error": "Failed to generate valid nutrition recommendations",
            "raw_response": response_text
        }

async def initialize_vector_store(kb_path):
    """Initialize vector store from knowledge base directory"""
    try:
        # Check if vector store already exists
        if os.path.exists(VECTOR_STORE_PATH):
            print("Loading existing vector store...")
            embedding_model = GoogleGenerativeAIEmbeddings(
                model="embedding-001",
                task_type=TaskType.RETRIEVAL_DOCUMENT,
                title="Nutrition Knowledge",
                api_key=os.getenv("GOOGLE_API_KEY")
            )
            return FAISS.load_local(VECTOR_STORE_PATH, embedding_model)
        
        # Check if knowledge base directory exists and has files
        if not os.path.exists(kb_path):
            print(f"Knowledge base path {kb_path} does not exist. Creating it...")
            os.makedirs(kb_path, exist_ok=True)
            return None
            
        # Check if there are any files in the directory
        files = [f for f in os.listdir(kb_path) if os.path.isfile(os.path.join(kb_path, f))]
        if not files:
            print(f"No files found in knowledge base directory {kb_path}")
            return None
            
        print(f"Found {len(files)} files in knowledge base. Building vector store...")
        
        # Load documents from knowledge base
        loader = DirectoryLoader(
            kb_path,
            {
                ".pdf": (lambda path: PDFLoader(path)),
            }
        )
        
        docs = await loader.load()
        print(f"Loaded {len(docs)} documents")
        
        if not docs:
            print("No documents were loaded from knowledge base")
            return None
            
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        splits = text_splitter.split_documents(docs)
        
        # Create embeddings and vector store
        embedding_model = GoogleGenerativeAIEmbeddings(
            model="embedding-001",
            task_type=TaskType.RETRIEVAL_DOCUMENT,
            title="Nutrition Knowledge",
            api_key=os.getenv("IDHAR TYPE KAR DENA")
        )
        
        vector_store = FAISS.from_documents(splits, embedding_model)
        vector_store.save_local(VECTOR_STORE_PATH)
        print(f"Created and saved vector store with {len(splits)} chunks")
        
        return vector_store
        
    except Exception as e:
        print(f"Error initializing vector store: {e}")
        return None

# Example API endpoint
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class DiseaseRequest(BaseModel):
    disease: str
    language: str = "English"

@app.post("/nutrition-recommendation")
async def nutrition_recommendation_endpoint(request: DiseaseRequest):
    try:
        result = await get_nutrition_recommendation(request.disease, request.language)
        return {"nutrition_recommendation": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# For testing directly
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Create the knowledge base directory if it doesn't exist
        os.makedirs(NUTRITION_KB_PATH, exist_ok=True)
        print(f"Knowledge base directory: {NUTRITION_KB_PATH}")
        print(f"Add your PDF, TXT, and CSV files to this directory manually.")
        
        # Test with a disease
        test_disease = "diabetes"
        print(f"\nTesting nutrition recommendation for {test_disease}:")
        result = await get_nutrition_recommendation(test_disease)
        print(json.dumps(result, indent=2))
    
    asyncio.run(test())
