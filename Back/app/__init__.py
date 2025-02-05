from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS 

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Initialiser SQLAlchemy
    db.init_app(app)

    # Configurer CORS avant d'enregistrer les routes
    CORS(app)

    # Importer et enregistrer les routes
    from .routes import main
    app.register_blueprint(main)
    # Créer les tables si elles n'existent pas
    with app.app_context():
        db.create_all()

    return app
