import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from dotenv import load_dotenv


load_dotenv('../.env')

app = Flask(__name__, static_folder='static_hls', static_url_path='/hls')
CORS(app, resources={
    r"/api/*": {"origins": "http://localhost:3000"},
    r"/hls/*": {"origins": "http://localhost:3000"}
})


# configure MongoDB URI via env var MONGO_URI


# MongoDB connection setup with error handling
mongo_uri = "mongodb+srv://ak_db_user:akdbuser1234@cluster0.pdhavjz.mongodb.net/rtsp_app?retryWrites=true&w=majority&appName=Cluster0"
app.config["MONGO_URI"] = mongo_uri

try:
    mongo = PyMongo(app)
    # Test the connection
    mongo.db.command('ping')
    print("MongoDB connection successful!")
except Exception as e:
    print(f"MongoDB connection error: {e}")
    # Create a fallback in-memory database for development
    class MockDB:
        def __init__(self):
            self.overlays = MockCollection("overlays")
            self.settings = MockCollection("settings")
    
    class MockCollection:
        def __init__(self, name):
            self.name = name
            self.data = []
            self.counter = 1
        
        def insert_one(self, document):
            document['_id'] = self.counter
            self.counter += 1
            self.data.append(document)
            class Result:
                def __init__(self, id):
                    self.inserted_id = id
            return Result(document['_id'])
        
        def find(self):
            return self.data.copy()
        
        def find_one(self, query=None):
            if not query:
                return self.data[0] if self.data else None
            for doc in self.data:
                if '_id' in query and doc['_id'] == query['_id']:
                    return doc.copy()
            return None
        
        def update_one(self, query, update):
            for i, doc in enumerate(self.data):
                if '_id' in query and doc['_id'] == query['_id']:
                    for k, v in update.get('$set', {}).items():
                        self.data[i][k] = v
                    return
        def delete_one(self, query):
            for i, doc in enumerate(self.data):
                if '_id' in query and doc['_id'] == query['_id']:
                    del self.data[i]
                    return
        
        def replace_one(self, query, document, upsert=False):
            for i, doc in enumerate(self.data):
                if not query or (doc.get('_id') == query.get('_id', None)):
                    self.data[i] = document
                    return
            if upsert:
                document['_id'] = self.counter
                self.counter += 1
                self.data.append(document)
        
        def command(self, cmd):
            return {"ok": 1.0}
    
    class MockMongo:
        def __init__(self):
            self.db = MockDB()
    print("Using mock in-memory database")
    mongo = MockMongo()


# Collections
overlays = mongo.db.overlays
settings = mongo.db.settings


# Health
@app.route('/api/health')
def health():
    return jsonify({"ok": True})


# CRUD for overlays
@app.route('/api/overlays', methods=['POST'])
def create_overlay():
    data = request.json or {}
    # basic validation
    allowed = {'name','type','content','x','y','width','height','zIndex','visible'}
    filtered = {k: data[k] for k in data if k in allowed}
    res = overlays.insert_one(filtered)
    return jsonify({"id": str(res.inserted_id)}), 201


@app.route('/api/overlays', methods=['GET'])
def list_overlays():
    docs = list(overlays.find())
    out = []
    for d in docs:
        d['id'] = str(d['_id'])
        d.pop('_id')
        out.append(d)
    return jsonify(out)


@app.route('/api/overlays/<id>', methods=['GET'])
def get_overlay(id):
    try:
        doc = overlays.find_one({"_id": ObjectId(id)})
    except Exception:
        return jsonify({"error":"invalid id"}), 400
    if not doc:
        return jsonify({"error": "Not found"}), 404
    doc['id'] = str(doc['_id']); doc.pop('_id')
    return jsonify(doc)


@app.route('/api/overlays/<id>', methods=['PUT'])
def update_overlay(id):
    data = request.json or {}
    try:
        overlays.update_one({"_id": ObjectId(id)}, {'$set': data})
    except Exception:
        return jsonify({"error":"invalid id or update failed"}), 400
    return jsonify({"ok": True})


@app.route('/api/overlays/<id>', methods=['DELETE'])
def delete_overlay(id):
    try:
        overlays.delete_one({"_id": ObjectId(id)})
    except Exception:
        return jsonify({"error":"invalid id"}), 400
    return jsonify({"ok": True})


# Settings: e.g., store rtsp_url or other global settings
@app.route('/api/settings', methods=['GET'])
def get_settings():
    s = settings.find_one({}) or {}
    if '_id' in s: s.pop('_id')
    return jsonify(s)


@app.route('/api/settings', methods=['POST','PUT'])
def save_settings():
    data = request.json or {}
    settings.replace_one({}, data, upsert=True)
    return jsonify({"ok": True})


if __name__ == '__main__':
    # host and port can be configured via env
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port, debug=True)