import pymongo 
import requests
from flask import Flask, jsonify,request

# Helper function to make MongoDB documents JSON serializable
def serialize_doc(doc):
    doc['_id'] = str(doc['_id'])  # Convert ObjectId to string
    return doc

client = pymongo.MongoClient('mongodb+srv://triet:1@cluster0.cjzmm.mongodb.net/')
db = client.sample_mflix
collection = db.news

hf_token = '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'
embedding_url = 'https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2'

def generate_embedding(text: str) -> list[float]:
    response = requests.post(
        embedding_url, 
        headers={'Authorization': f'Bearer {hf_token}'}, 
        json={'inputs': text})
    if response.status_code != 200:
        raise ValueError(f"Request failed with status code {response.status_code}: {response.text}")
    return response.json()

# for doc in collection.find({'plain_text':{"$exists": True}}):
#     doc['plot_embedding_hf'] = generate_embedding(doc['plain_text'])
#     collection.replace_one({'_id': doc['_id']}, doc)


query = 'abcd'

results = collection.aggregate([
    {"$vectorSearch":{
        "queryVector": generate_embedding(query),
        "path":"plot_embedding_hf",
        "numCandidates": 100,
        "limit": 10,
        "index":"PlotSemanticSearch"
    }}
])

# for doc in results:
#     print(f'{doc["title"]} \n - {doc["plain_text"]} \n')

app = Flask(__name__)

# Define a route
@app.route('/')
def home():
    return "Hello, World!"

# Define a JSON endpoint
@app.route('/api/data')
def get_data():
    # Run the aggregation inside the route to get a fresh cursor each time
    query = request.args.get('search')
    print(query)
    results = collection.aggregate([
        {"$vectorSearch": {
            "queryVector": generate_embedding(query),
            "path": "plot_embedding_hf",
            "numCandidates": 100,
            "limit": 10,
            "index": "PlotSemanticSearch"
        }}
    ])
    
    # Convert results to a list and serialize documents
    results_list = [serialize_doc(doc) for doc in results]
    return jsonify(results_list)

# Run the server
if __name__ == '__main__':
    app.run(port=8000)