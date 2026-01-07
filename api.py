from flask import Flask
from src.clients.clob import ClobAPIClient
from src.api.clob import register_clob_routes


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Initialize CLOB client
    clob_client = ClobAPIClient()
    
    # Register CLOB routes
    register_clob_routes(app, clob_client)
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health():
        return {"status": "healthy"}, 200
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)
