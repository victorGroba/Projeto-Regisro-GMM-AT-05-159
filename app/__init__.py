from flask import Flask
from flask_login import LoginManager
from .models import db, User
import os # <--- Não esqueça de importar o OS

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'
    
    # --- CORREÇÃO AQUI ---
    # Usamos 4 barras (////) para indicar um caminho absoluto no Linux/Docker
    # Isso garante que ele pegue o arquivo dentro da pasta instance onde seus dados estão salvos
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////app/instance/balancas.db' 
    # ---------------------

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'routes.login'
    login_manager.login_message = "Faça login para acessar."
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes import routes_bp
    app.register_blueprint(routes_bp)
    
    # Garante que as tabelas existam (cria se não houver)
    with app.app_context():
        db.create_all()

    return app