# imports:
from flask import Flask
from flasgger import Swagger
from mongodb_connection_holder import MongoConnectionHolder
from routes import init_routes
import os

# set app and swagger:
app = Flask(__name__)
Swagger(app)

# init DB Connection:
MongoConnectionHolder.init()

# Import Routes:
init_routes(app)

# run everything:
if __name__ == "__main__":
    port = os.environ.get("PORT", 8088)
    app.run(port=port, debug=True)

    