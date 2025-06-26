import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

def get_followers(username):
    """Scrape followers from public Instagram profile"""
    url = f"https://www.instagram.com/{username}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        if response.status_code == 404:
            return None, "Account not found or is private"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', type='application/ld+json')
        
        if not script_tag:
            return None, "Could not extract follower data. Instagram may have changed their structure."
        
        try:
            profile_data = json.loads(script_tag.string)
        except json.JSONDecodeError:
            return None, "Failed to parse profile data."
        
        # Extract followers from the interactionStatistic
        followers = set()
        for stat in profile_data.get('mainEntityOfPage', {}).get('interactionStatistic', []):
            if 'followers' in stat.get('name', '').lower():
                # The identifier might be a URL, we take the last part as the username
                user_url = stat.get('identifier', '')
                if user_url:
                    # Extract username from URL
                    user = user_url.rstrip('/').split('/')[-1]
                    followers.add(user)
                break
        
        return followers, None
    except requests.exceptions.RequestException as e:
        return None, f"Network error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

def save_session_data(session_id, followers):
    """Save followers data for a session"""
    session_file = f"data/{session_id}.json"
    with open(session_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "followers": list(followers)
        }, f)

def load_session_data(session_id):
    """Load followers data from session"""
    session_file = f"data/{session_id}.json"
    if os.path.exists(session_file):
        with open(session_file, 'r') as f:
            data = json.load(f)
            return set(data['followers'])
    return None

@app.route('/', methods=['GET'])
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/track', methods=['POST'])
def track():
    """Handle tracking request"""
    username = request.form.get('username').strip()
    if not username:
        return jsonify({"error": "Please enter a username"}), 400
    
    # Check for existing session
    session_id = session.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
    
    # Get current followers
    current_followers, error = get_followers(username)
    if error:
        return jsonify({"error": error}), 400
    
    # Load previous followers from session
    previous_followers = load_session_data(session_id)
    
    # Save current as new previous
    save_session_data(session_id, current_followers)
    
    # Compare
    if previous_followers is None:
        # First run, no comparison
        return jsonify({
            "message": "Baseline saved. Run again later to see changes.",
            "current_count": len(current_followers)
        })
    
    new_followers = list(current_followers - previous_followers)
    unfollowers = list(previous_followers - current_followers)
    
    # Save result files for download
    new_file = f"data/{session_id}_new.txt"
    unfollowers_file = f"data/{session_id}_unfollowers.txt"
    
    with open(new_file, 'w') as f:
        f.write("\n".join(new_followers))
    
    with open(unfollowers_file, 'w') as f:
        f.write("\n".join(unfollowers))
    
    return jsonify({
        "new_count": len(new_followers),
        "unfollowers_count": len(unfollowers),
        "session_id": session_id,
        "new_followers": new_followers[:5],  # Show first 5
        "unfollowers": unfollowers[:5]       # Show first 5
    })

@app.route('/download/<type>/<session_id>')
def download(type, session_id):
    """Download result files"""
    valid_types = ['new', 'unfollowers']
    if type not in valid_types:
        return "Invalid file type", 400
    
    filename = f"data/{session_id}_{type}.txt"
    if not os.path.exists(filename):
        return "File not found", 404
    
    return send_file(
        filename,
        as_attachment=True,
        download_name=f"{type}_{session_id[:8]}.txt"
    )

if __name__ == '__main__':
    app.run(debug=True)
