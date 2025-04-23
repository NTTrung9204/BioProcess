from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_pyfile('config.py')
    
    # Register blueprints
    from app.controllers.customer_controller import customer_bp
    from app.controllers.raman_controller import raman_bp
    from app.controllers.operator_controller import operator_bp
    from app.controllers.reactor_controller import reactor_bp
    from app.controllers.feed_controller import feed_bp
    from app.controllers.catalyst_controller import catalyst_bp
    from app.controllers.catalyst_composition_controller import catalyst_composition_bp
    from app.controllers.test_campaign_controller import test_campaign_bp
    
    app.register_blueprint(customer_bp)
    app.register_blueprint(raman_bp)
    app.register_blueprint(operator_bp)
    app.register_blueprint(reactor_bp)
    app.register_blueprint(feed_bp)
    app.register_blueprint(catalyst_bp)
    app.register_blueprint(catalyst_composition_bp)
    app.register_blueprint(test_campaign_bp)
    
    return app 