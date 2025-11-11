from flask import jsonify

def health():
    return jsonify({"status": "ok", "service": "FitCheck Insights API"}), 200
