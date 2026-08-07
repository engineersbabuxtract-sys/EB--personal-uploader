# app.py - Flask web server for Koyeb
from flask import Flask, jsonify, request
import os
import sys
import subprocess
import logging

app = Flask(__name__)

@app.route("/")
def hello():
    """Root endpoint"""
    return jsonify({
        "status": "running",
        "bot": "Engineers Babu Uploader",
        "version": "2.0.0",
        "environment": "Koyeb",
        "port": os.environ.get("PORT", "8080")
    })

@app.route("/health")
def health():
    """Health check endpoint for Koyeb"""
    try:
        # Check if bot process is running
        result = subprocess.run(
            ["pgrep", "-f", "python3 main.py"],
            capture_output=True,
            text=True,
            timeout=5
        )
        is_running = bool(result.stdout.strip())
        
        return jsonify({
            "status": "healthy" if is_running else "unhealthy",
            "bot_running": is_running,
            "pid": result.stdout.strip() or "None"
        }), 200 if is_running else 503
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route("/ping")
def ping():
    """Simple ping endpoint"""
    return "pong", 200

@app.route("/info")
def info():
    """Get bot info"""
    return jsonify({
        "name": "Engineers Babu Uploader",
        "python_version": sys.version,
        "environment": os.environ.get("KOYEB_APP_NAME", "unknown"),
        "region": os.environ.get("KOYEB_REGION", "unknown")
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
