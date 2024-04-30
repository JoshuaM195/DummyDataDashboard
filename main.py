from flask import Flask, redirect, render_template, request, url_for
from pymongo import MongoClient
import random
from bson import ObjectId

client = MongoClient('mongodb://localhost:27017/')
db = client['FlightData']
collection = db['Dummy']

app = Flask(__name__)



@app.route('/')
def index():
    # Fetching document count from the collection
    doc_count = collection.count_documents({})
    return f"Documents in collection: {doc_count}"

@app.route('/add')
def add_document():
    # Example: Adding a document
    new_document = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "interests": ["aviation", "travel"]
    }
    collection.insert_one(new_document)
    return "Document added!"

@app.route('/view')
def view_documents():
    # Example: Fetching all documents
    documents = collection.find()
    print(documents)
    return render_template('doc.html', documents=documents)


def generate_random_color():
    return "%06x" % random.randint(0, 0xFFFFFF)

@app.route('/reviews')
def reviews():
    # Fetch all user reviews and assuming user_name is part of the review document
    user_reviews = collection.find({"type": "user_review"})
    reviews_list = []
    for review in user_reviews:
        # Ensure to fetch user_name if it's stored separately or within the same document
        user_data = collection.find_one({"user_id": review["user_id"], "user_name": {"$exists": True}})
        if user_data:
            review['user_name'] = user_data.get('user_name', 'No name available')
            
        geo_data = collection.find_one({"type": "geolocation", "destination_id": review["destination_id"]})
        if geo_data:
            review['country'] = geo_data.get('country', 'Unknown country')
        
        
        review['color'] = generate_random_color()  # Assign a random color for each review
        reviews_list.append(review)

    return render_template('reviews.html', reviews=reviews_list)

@app.route('/add_review', methods=['POST'])
def add_review():
    user_name = request.form['user_name']
    country = request.form['country']
    comment = request.form['comment']
    rating = request.form['rating']

    # Find the highest current user ID
    latest_user = collection.find_one({"type": "user"}, sort=[("user_id", -1)])
    new_user_id = (latest_user['user_id'] + 1) if latest_user else 21
    
    latest_destination = collection.find_one(
    {"type": "geolocation"},
    sort=[("destination_id", -1)]
    )

    # Check what the database returned
    if latest_destination:
        new_destination_id = latest_destination['destination_id'] + 1
        print("New Destination ID:", new_destination_id)
    else:
        new_destination_id = 21  # Default starting ID
        print("Using default Destination ID:", new_destination_id)
    
    # Check if user already exists, if not, create new user
    user = collection.find_one({"user_name": user_name, "type": "user"})
    if not user:
        collection.insert_one({
            "user_id": new_user_id,
            "user_name": user_name,
            "type": "user"
        })
    else:
        new_user_id = user['user_id']  # Use existing user ID if user already exists

    # Insert new destination
    collection.insert_one({
        "destination_id": new_destination_id,
        "country": country,
        "type": "geolocation"
    })

    # Insert new user review
    collection.insert_one({
        "user_id": new_user_id,
        "destination_id": new_destination_id,
        "text": comment,
        "rating": rating,
        "type": "user_review"
    })
    return redirect(url_for('reviews'))  # Redirect back to the reviews page


if __name__ == "__main__":
    app.run(port=8000, debug=True)
