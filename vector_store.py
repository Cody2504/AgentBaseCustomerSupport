from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict, Any
import json
import os
from langsmith import traceable
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = 'models/embedding-001'
DB_PATH = './.chroma_db'
FAQ_FILE_PATH= './cake_FAQ.json'
INVENTORY_FILE_PATH = './cake_inventory.json'

class Product:
    def __init__(self, name: str, id: str, description: str, type: str, price: float, quantity: int):
        self.name = name
        self.id = id
        self.description = description
        self.type = type
        self.price = price
        self.quantity = quantity

class QuestionAnswerPairs:
    def __init__(self, question: str, answer: str):
        self.question = question
        self.answer = answer

class CakeShopVectorStore:
    def __init__(self):
        # Initialize Google Generative AI Embeddings
        self.embedding_function = GoogleGenerativeAIEmbeddings(
            google_api_key=API_KEY,
            model=MODEL_NAME
        )

        # Create or get Chroma collections
        self.faq_collection = Chroma(
            collection_name="FAQ",
            embedding_function=self.embedding_function,
            persist_directory=DB_PATH
        )
        self.inventory_collection = Chroma(
            collection_name="Inventory",
            embedding_function=self.embedding_function,
            persist_directory=DB_PATH
        )
        
        # Load data if collections are empty
        if len(self.faq_collection.get()['ids']) == 0:
            self._load_faq_collection(FAQ_FILE_PATH)

        if len(self.inventory_collection.get()['ids']) == 0:
            self._load_inventory_collection(INVENTORY_FILE_PATH)
            
    def _load_faq_collection(self, faq_file_path: str):
        with open(faq_file_path, 'r') as f:
            faqs = json.load(f)

        # Prepare data for Langchain Chroma
        texts = []
        metadatas = []
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=30)

        # Add questions and split answers as separate documents
        for faq in faqs:
            # Add question as a single chunk
            texts.append(faq['question'])
            metadatas.append({"type": "question", "question": faq['question'], "answer": faq['answer']})

            # Split answer into chunks
            answer_chunks = text_splitter.split_text(faq['answer'])
            for chunk in answer_chunks:
                texts.append(chunk)
                metadatas.append({"type": "answer_chunk", "question": faq['question'], "answer": chunk})

        # Add documents to collection
        self.faq_collection.add_texts(
            texts=texts,
            metadatas=metadatas
        )

    def _load_inventory_collection(self, inventory_file_path: str):
        with open(inventory_file_path, 'r') as f:
            inventories = json.load(f)

        # Prepare data for Langchain Chroma
        texts = []
        metadatas = []
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=30)

        for inventory in inventories:
            # Split description into chunks
            desc_chunks = text_splitter.split_text(inventory['description'])
            for chunk in desc_chunks:
                texts.append(chunk)
                meta = inventory.copy()
                meta['description'] = chunk
                metadatas.append(meta)

        # Add documents to collection
        self.inventory_collection.add_texts(
            texts=texts,
            metadatas=metadatas
        )
    @traceable
    def query_faqs(self, query: str) -> Dict[str, Any]:
        """Query FAQ collection and return relevant results."""
        return self.faq_collection.similarity_search_with_relevance_scores(
            query=query,
            k=5
        )
    @traceable
    def query_inventories(self, query: str) -> Dict[str, Any]:
        """Query inventory collection and return relevant results."""
        return self.inventory_collection.similarity_search_with_relevance_scores(
            query=query,
            k=5
        )
