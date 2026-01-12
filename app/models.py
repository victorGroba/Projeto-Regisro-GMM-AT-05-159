from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Balanca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    identificacao = db.Column(db.String(20), nullable=False, unique=True)
    modelo = db.Column(db.String(50), nullable=False)
    numero_serie = db.Column(db.String(50), nullable=False)
    validade_calibracao = db.Column(db.String(10), nullable=False)
    criterio_aceitacao = db.Column(db.String(20), nullable=False)
    padrao = db.Column(db.String(50), nullable=False)
    valor_convencional = db.Column(db.Float, nullable=False)
    numero_certificado = db.Column(db.String(50), nullable=False)
    fabricante = db.Column(db.String(50), nullable=False)
    validade_padrao = db.Column(db.String(10), nullable=False)

    registros = db.relationship('RegistroDiario', backref='balanca', lazy=True)

class RegistroDiario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, default=datetime.utcnow)
    resultado_obtido = db.Column(db.Float, nullable=False)
    responsavel = db.Column(db.String(100), nullable=False)
    balanca_id = db.Column(db.Integer, db.ForeignKey('balanca.id'), nullable=False)

    @property
    def diferenca(self):
        return round(abs(self.resultado_obtido - self.balanca.valor_convencional), 4)

    @property
    def status(self):
        # Remove caracteres especiais para conversão
        criterio_limpo = self.balanca.criterio_aceitacao.replace("±", "").replace(",", ".")
        try:
            criterio = float(criterio_limpo)
        except ValueError:
            criterio = 0.05 # Valor padrão em caso de erro
            
        return "Conforme" if self.diferenca <= criterio else "Não Conforme"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)