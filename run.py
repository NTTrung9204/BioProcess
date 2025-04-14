from app.app import app, socketio
from app.repositories import init_timescale_database
from app.services import produce_data, consume_kafka, initialize_customer_db, initialize_project_db
import threading
import time
import os
from app.config import HostConfig

if __name__ == "__main__":
    print("🚀 Starting application in Docker environment...")
    time.sleep(2)  # Give some time for services to start

    # Initialize database tables
    print("📊 Initializing databases...")
    init_timescale_database()
    initialize_customer_db()
    initialize_project_db()

    time.sleep(2)  # Wait for database initialization to complete

    # Start background threads for data production and consumption
    print("🔄 Starting background services...")
    threading.Thread(target=produce_data, daemon=True).start()
    threading.Thread(target=consume_kafka, daemon=True).start()
    
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Starting web server on port {port}...")
    
    # Start the Flask application with Socket.IO
    socketio.run(
        app, 
        host="0.0.0.0", 
        port=port, 
        debug=True, 
        use_reloader=False,
        allow_unsafe_werkzeug=True
    ) 