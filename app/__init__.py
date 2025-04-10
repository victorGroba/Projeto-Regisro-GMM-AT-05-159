from flask import Flask
from .models import db
from .routes import routes_bp

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'sua_chave_secreta'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///balancas.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)  # <- Aqui você associa o db à app

    app.register_blueprint(routes_bp)

    return app
