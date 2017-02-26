# Helper functions that we only have to write once to make life easier
from flask import jsonify

def response(data={}):
    # Sends 200 success response
    response = jsonify(data)
    response.status_code = 200
    return response
