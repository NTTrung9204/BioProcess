from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_pyfile('config.py')
    
    # Register blueprints
    from app.controllers.customer_controller import customer_bp
    from app.controllers.raman_controller import raman_bp
    
    app.register_blueprint(customer_bp)
    app.register_blueprint(raman_bp)
    
    return app 