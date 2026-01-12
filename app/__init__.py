from flask import Flask
from flask_login import LoginManager
from .models import db, User

def create_app():
    app = Flask(__name__)
    # Altere esta chave para algo seguro em produção
    app.config['SECRET_KEY'] = 'chave_secreta_projeto_balanca' 
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///balancas.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Configuração do Login
    login_manager = LoginManager()
    login_manager.login_view = 'routes.login'
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes import routes_bp
    app.register_blueprint(routes_bp)

    return app