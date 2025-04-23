from app.app import app, socketio
from app.repositories import init_timescale_database
from app.services import (
    produce_data, consume_kafka, 
    initialize_customer_db, initialize_project_db, 
    initialize_operator_db, initialize_reactor_db, 
    initialize_feed_db, initialize_catalyst_db,
    initialize_feed_composition_db, initialize_catalyst_composition_db,
    initialize_test_campaign_db
)
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
    initialize_operator_db()
    initialize_reactor_db()
    initialize_feed_db()
    initialize_catalyst_db()
    initialize_feed_composition_db()
    initialize_catalyst_composition_db()
    initialize_test_campaign_db()

    

    time.sleep(2)  # Wait for database initialization to complete

    print("🔄 Starting background services...")
    # threading.Thread(target=produce_data, daemon=True).start()
    threading.Thread(target=consume_kafka, daemon=True).start()
    
    port = int(HostConfig.HOST_PORT)
    print(f"🌐 Starting web server on port {port}...")
    
    socketio.run(
        app, 
        host="0.0.0.0", 
        port=port, 
        debug=True, 
        use_reloader=False,
        allow_unsafe_werkzeug=True
    ) 