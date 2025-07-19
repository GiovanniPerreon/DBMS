"""
Keep-alive web server to prevent Replit from sleeping
This ensures 24/7 uptime for the Discord bot
"""

from flask import Flask
import threading
import time

app = Flask(__name__)

@app.route('/')
def home():
    """Health check endpoint"""
    return '''
    <html>
        <head>
            <title>Discord Bot - Online</title>
            <meta http-equiv="refresh" content="30">
        </head>
        <body>
            <h1>🤖 Discord Bot is Running!</h1>
            <p>Status: <span style="color: green;">Online</span></p>
            <p>This page refreshes every 30 seconds to keep the bot alive.</p>
            <p>Last updated: <span id="time"></span></p>
            <script>
                document.getElementById('time').innerText = new Date().toLocaleString();
            </script>
        </body>
    </html>
    '''

@app.route('/status')
def status():
    """JSON status endpoint"""
    return {
        "status": "online",
        "timestamp": time.time(),
        "message": "Discord bot is running"
    }

def keep_alive():
    """Start the Flask server to keep the bot alive"""
    app.run(host='0.0.0.0', port=5000, debug=False)