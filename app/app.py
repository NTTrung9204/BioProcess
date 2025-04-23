from datetime import timedelta
import gc
from flask import Flask
import os
import threading
import time
from flask_socketio import SocketIO
# from flask_cors import CORS

from app.config import HostConfig, PathConfig
from app.repositories import init_timescale_database
from app.services import produce_data, consume_kafka, initialize_customer_db, initialize_project_db
from app.controllers.raman_controller import register_socket_handlers as register_raman_socket_handlers
from app.controllers.optimization_controller import register_socket_handlers as register_optimization_socket_handlers
from app.controllers import (
    auth_bp, customer_bp, raman_bp, project_bp, optimization_bp,
    api_bp, upload_bp, query_bp, producer_bp, operator_bp, reactor_bp,
    feed_bp, feed_composition_bp, catalyst_bp, catalyst_composition_bp,
    test_campaign_bp
)


# Create the Flask app
def create_app():
    app = Flask(__name__)
    # CORS(app)
    app.config["SECRET_KEY"] = "secret!"
    app.permanent_session_lifetime = timedelta(days=7)
    
    # Register Jinja filters
    @app.template_filter('datetime')
    def format_datetime(value, format='%Y-%m-%d %H:%M'):
        """Format a datetime object to string format"""
        if value is None:
            return ""
        return value.strftime(format)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(raman_bp)
    app.register_blueprint(project_bp)
    app.register_blueprint(optimization_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(query_bp)
    app.register_blueprint(producer_bp)
    app.register_blueprint(operator_bp)
    app.register_blueprint(reactor_bp)
    app.register_blueprint(feed_bp)
    app.register_blueprint(feed_composition_bp)
    app.register_blueprint(catalyst_bp)
    app.register_blueprint(catalyst_composition_bp)
    app.register_blueprint(test_campaign_bp)

    return app

# Initialize Flask and Socket.IO
app = create_app()
socketio = SocketIO(app, cors_allowed_origins="*")

# Register socket handlers
register_raman_socket_handlers(socketio)
register_optimization_socket_handlers(socketio)

# Ensure upload directory exists
os.makedirs(PathConfig.UPLOAD_FOLDER, exist_ok=True)

# This is only for direct execution of app.py, which is not recommended
# Use run.py as the main entry point instead
if __name__ == "__main__":
    print("⚠️ Warning: Running app.py directly is not recommended.")
    print("⚠️ Please use run.py as the main entry point.")
    print("🔄 Continuing with startup sequence...")
    
    time.sleep(2)  # Give some time for services to start

    time.sleep(2)  # Wait for database initialization to complete

    # Start background threads for data production and consumption
    threading.Thread(target=produce_data, daemon=True).start()
    threading.Thread(target=consume_kafka, daemon=True).start()

    # Start the Flask application with Socket.IO
    socketio.run(
        app, 
        host="0.0.0.0", 
        port=int(HostConfig.HOST_PORT), 
        debug=True, 
        use_reloader=False,
        allow_unsafe_werkzeug=True
    ) 