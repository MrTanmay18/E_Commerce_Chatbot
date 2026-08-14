import pandas as pd
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from groq import Groq
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Path to FAQ CSV file
faqs_path = Path(__file__).parent / "resources/faq_data.csv"

# Initialize ChromaDB and Groq clients
chroma_client = chromadb.Client()
collection_name_faq = "faqs"
Groq_client = Groq()

# Embedding model used for semantic similarity search
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/all-MiniLM-L6-V2"
)


def ingest_faq_data(path):
    # Create FAQ collection if it doesn't already exist
    collection = chroma_client.get_or_create_collection(
        name=collection_name_faq,
        embedding_function=ef
    )
    # Avoid ingesting data again if collection already has documents
    if collection.count() == 0:
        print("Ingesting FAQ data into ChromaDB...")

        df = pd.read_csv(path)

        # Questions are stored as documents
        docs = df["question"].tolist()

        # Answers are stored as metadata
        metadata = [
            {"answer": ans}
            for ans in df["answer"].tolist()
        ]
        # Create unique IDs for each FAQ
        ids = [f"id_{i}" for i in range(len(docs))]

        collection.add(
            documents=docs,
            metadatas=metadata,
            ids=ids
        )
        print(
            f"FAQ data successfully ingested into "
            f"Chroma collection: {collection_name_faq}"
        )
    else:
        print(
            f"Collection '{collection_name_faq}' "
            f"already contains data"
        )


def get_relevant_qa(query):
    # Retrieve the FAQ collection
    collection = chroma_client.get_collection(
        name=collection_name_faq,
        embedding_function=ef
    )
    # Find the 2 most similar FAQ questions
    result = collection.query(
        query_texts=[query],
        n_results=2
    )

    return result


def faq_chain(query):
    # Retrieve relevant FAQs
    result = get_relevant_qa(query)

    # Extract answers to use as context
    context = ''.join([r.get('answer') for r in result['metadatas'][0]])

    # Generate final answer using LLM
    answer = generate_answer(query, context)
    return answer


def generate_answer(query, context):
    # Prompt LLM to answer only using retrieved context
    prompt = f'''Given the following context and question, generate answer based on this context only.
        If the answer is not found in the context, kindly state "I don't know". Don't try to make up an answer.

        QUESTION: {query}

        CONTEXT: {context}
        '''

    # Send request to Groq LLM
    completion = Groq_client.chat.completions.create(
        model=os.environ['GROQ_MODEL'],
        messages=[
            {
                'role': 'user',
                'content': prompt
            }
        ],
    )
    return completion.choices[0].message.content


if __name__ == "__main__":
    # Load FAQ data into ChromaDB
    ingest_faq_data(faqs_path)
    # Test user query
    query = "Do you take cash as payment option?"

    # result = get_relevant_qa(query)
    # print(result)

    # Run complete RAG pipeline
    answer = faq_chain(query)
    print(answer)
