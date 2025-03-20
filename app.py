from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Load environment variables
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
os.environ["LANGCHAIN_API_KEY"] = groq_api_key

# Function to check if the current question is related to the history
def is_related_to_history(question, history):
    if not history:
        return False
    
    # Extract keywords from the question (simple tokenization)
    question_words = set(re.split(r'\W+', question.lower()))
    
    # Extract keywords from the history
    history_text = " ".join([msg['content'] for msg in history]).lower()
    history_words = set(re.split(r'\W+', history_text))
    
    # Check for overlap in keywords (excluding common stop words)
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'to', 'in', 'of', 'for', 'and', 'or', 'but'}
    question_keywords = question_words - stop_words
    history_keywords = history_words - stop_words
    
    # Consider the question related if there's at least one keyword overlap
    return bool(question_keywords & history_keywords)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    question = data.get('question')
    temperature = data.get('temperature', 0.3)
    max_tokens = data.get('max_tokens', 50)
    history = data.get('history', [])  # Session history sent from frontend

    if not question:
        return jsonify({'error': 'No question provided'}), 400

    # Use history only if the question is related to previous messages
    if is_related_to_history(question, history):
        history_text = "\n".join([msg['content'] for msg in history])
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You're an AI assistant that maintains conversation context only for related topics."),
            ("user", f"{history_text}\nUser: {question}")
        ])
    else:
        # If the question is unrelated, ignore the history
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You're an AI assistant that answers questions without prior context unless explicitly related."),
            ("user", f"User: {question}")
        ])
    
    # Use only the mixtral-8x7b-32768 model
    llm = ChatGroq(model="mixtral-8x7b-32768")
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser
    answer = chain.invoke({"question": question})

    # Update history for the current session (not persisted)
    new_history = history + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer}
    ]

    return jsonify({
        'response': answer,
        'history': new_history  # Return updated history for the current session
    })

@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    # Since history is not persisted, this endpoint just confirms the action
    return jsonify({'message': 'Chat history cleared (session-only)'})

@app.route('/api/history', methods=['GET'])
def get_history():
    # Since history is not persisted, return an empty history
    return jsonify({'history': []})

if __name__ == '__main__':
    app.run(debug=True, port=5000)