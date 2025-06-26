# app.py
from flask import Flask, render_template, request, jsonify, send_file, session
import instaloader
import os
import json
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'

# Create data directories if not exists
os.makedirs('sessions', exist_ok=True)
os.makedirs('data', exist_ok=True)

def get_followers_list(username, password, target_account):
    """Fetch followers from Instagram"""
    L = instaloader.Instaloader()
    session_file = f"sessions/{username}_session"
    
    try:
        if os.path.exists(session_file):
            L.load_session_from_file(username, session_file)
        else:
            L.login(username, password)
            L.save_session_to_file(session_file)
    except Exception as e:
        raise Exception(f"Login failed: {str(e)}")
    
    try:
        profile = instaloader.Profile.from_username(L.context, target_account)
        return set(follower.username for follower in profile.get_followers())
    except Exception as e:
        raise Exception(f"Couldn't fetch followers: {str(e)}")

@app.route('/', methods=['GET'])
def index():
    """Main page with clean UI"""
    return render_template('index.html')

@app.route('/track', methods=['POST'])
def track_followers():
    """Process tracking request"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    target_account = data.get('target_account')
    
    if not all([username, password, target_account]):
        return jsonify({"error": "All fields are required"}), 400
    
    try:
        # Get current followers
        current_followers = get_followers_list(username, password, target_account)
        
        # Generate unique ID for this session
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        
        # Prepare data storage
        data_dir = f"data/{session_id}"
        os.makedirs(data_dir, exist_ok=True)
        
        # Check for previous data
        previous_file = f"{data_dir}/previous.json"
        previous_followers = set()
        
        if os.path.exists(previous_file):
            with open(previous_file, 'r') as f:
                previous_data = json.load(f)
                previous_followers = set(previous_data.get('followers', []))
        
        # Calculate changes
        new_followers = list(current_followers - previous_followers)
        unfollowers = list(previous_followers - current_followers)
        
        # Save current data for next comparison
        with open(previous_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "followers": list(current_followers)
            }, f)
        
        # Save results for download
        with open(f"{data_dir}/new_followers.txt", 'w') as f:
            f.write("\n".join(new_followers))
        
        with open(f"{data_dir}/unfollowers.txt", 'w') as f:
            f.write("\n".join(unfollowers))
        
        return jsonify({
            "new_count": len(new_followers),
            "unfollowers_count": len(unfollowers),
            "session_id": session_id
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<file_type>/<session_id>')
def download_file(file_type, session_id):
    """Download result files"""
    valid_types = ['new_followers', 'unfollowers']
    if file_type not in valid_types:
        return "Invalid file type", 400
    
    try:
        return send_file(
            f"data/{session_id}/{file_type}.txt",
            as_attachment=True,
            download_name=f"{file_type}_{session_id[:8]}.txt"
        )
    except FileNotFoundError:
        return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True)
