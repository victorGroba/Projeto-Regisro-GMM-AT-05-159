from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
        criterio = float(self.balanca.criterio_aceitacao.replace("±", "").replace(",", "."))
        return "Conforme" if self.diferenca <= criterio else "Não Conforme"
