from flask import Flask, render_template, request, jsonify
import subprocess
import os

app = Flask(__name__)

def launch_in_terminal(script_path, env_vars):
    # Construct the environment export and python command
    env_str = ' '.join([f'export {k}="{v}";' for k, v in env_vars.items() if v])
    
    # Get absolute path for the script to be safe
    abs_script_path = os.path.abspath(script_path)
    abs_cwd = os.path.abspath(os.path.dirname(__file__))
    
    command = f'cd {abs_cwd}; {env_str} python {abs_script_path}'
    
    # Escape for AppleScript string literal
    escaped_command = command.replace('\\', '\\\\').replace('"', '\\"')
    
    # Use osascript to open a new Terminal window and run the command
    apple_script = f'''
    tell application "Terminal"
        activate
        do script "{escaped_command}"
    end tell
    '''
    try:
        subprocess.run(['osascript', '-e', apple_script], check=True)
        return True, "Script launched in Terminal successfully!"
    except Exception as e:
        return False, str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/run', methods=['POST'])
def run_script():
    data = request.json
    script = data.get('script')
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"status": "error", "message": "Username and password are required."}), 400
        
    env_vars = {
        "POSHMARK_USERNAME": username,
        "POSHMARK_PASSWORD": password
    }
    
    script_map = {
        "closet": "actions/closet_reshare.py",
        "feed": "actions/feed_reshare.py",
        "follow": "actions/follow_users.py",
        "insights": "insights/top_liked_brand_listings.py"
    }
    
    if script not in script_map:
        return jsonify({"status": "error", "message": "Invalid script selected."}), 400
        
    success, msg = launch_in_terminal(script_map[script], env_vars)
    
    if success:
        return jsonify({"status": "success", "message": msg})
    else:
        return jsonify({"status": "error", "message": f"Failed to launch: {msg}"}), 500

@app.route('/api/insights/latest', methods=['GET'])
def latest_insights():
    insights_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'insights.json')
    if not os.path.exists(insights_file):
        return jsonify({"status": "error", "message": "No insights available yet. Run the Insights script first."}), 404
        
    import json
    try:
        with open(insights_file, 'r') as f:
            data = json.load(f)
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Could not read insights: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
