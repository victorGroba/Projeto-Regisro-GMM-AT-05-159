from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from .models import db, Balanca, RegistroDiario
from io import BytesIO
from openpyxl import Workbook
from datetime import datetime, date

routes_bp = Blueprint('routes', __name__)

@routes_bp.route("/")
def index():
    balancas = Balanca.query.all()
    return render_template("index.html", title="Balanças", balancas=balancas)

@routes_bp.route("/cadastrar", methods=["GET", "POST"])
def cadastrar():
    if request.method == "POST":
        dados = request.form
        existente = Balanca.query.filter_by(identificacao=dados['identificacao']).first()
        if existente:
            flash("Erro: já existe uma balança com essa identificação.", "danger")
            return redirect(url_for("routes.cadastrar"))

        nova = Balanca(
            identificacao=dados['identificacao'],
            modelo=dados['modelo'],
            numero_serie=dados['numero_serie'],
            validade_calibracao=dados['validade_calibracao'],
            criterio_aceitacao=dados['criterio_aceitacao'],
            padrao=dados['padrao'],
            valor_convencional=float(dados['valor_convencional']),
            numero_certificado=dados['numero_certificado'],
            fabricante=dados['fabricante'],
            validade_padrao=dados['validade_padrao']
        )
        db.session.add(nova)
        db.session.commit()
        flash("Balança cadastrada com sucesso!", "success")
        return redirect(url_for("routes.index"))
    return render_template("cadastro_balanca.html", title="Cadastro de Balança")

@routes_bp.route("/verificar/<int:id>", methods=["GET", "POST"])
def verificar(id):
    balanca = Balanca.query.get_or_404(id)
    if request.method == "POST":
        resultado = float(request.form['resultado_obtido'])
        responsavel = request.form['responsavel']
        data = datetime.strptime(request.form['data'], "%Y-%m-%d").date()

        novo_registro = RegistroDiario(
            data=data,
            resultado_obtido=resultado,
            responsavel=responsavel,
            balanca_id=balanca.id
        )
        db.session.add(novo_registro)
        db.session.commit()
        flash(f"Verificação registrada com sucesso!", "success")
        return redirect(url_for('routes.index'))
    return render_template("verificacao.html", balanca=balanca, now=date.today().strftime('%Y-%m-%d'))

@routes_bp.route("/historico/<int:id>")
def historico(id):
    balanca = Balanca.query.get_or_404(id)
    registros = RegistroDiario.query.filter_by(balanca_id=id).order_by(RegistroDiario.data.desc()).all()
    return render_template("historico.html", balanca=balanca, registros=registros)

@routes_bp.route("/exportar_excel/<int:id>")
def exportar_excel(id):
    balanca = Balanca.query.get_or_404(id)
    registros = RegistroDiario.query.filter_by(balanca_id=id).order_by(RegistroDiario.data.asc()).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Histórico de Verificações"

    ws.append([
        "Data",
        "Valor Convencional do Padrão",
        "Resultado Obtido",
        "Diferença",
        "Status",
        "Responsável"
    ])

    for r in registros:
        ws.append([
            r.data.strftime("%d/%m/%Y"),
            balanca.valor_convencional,
            r.resultado_obtido,
            round(r.diferenca, 4),
            r.status,
            r.responsavel
        ])

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    filename = f"historico_{balanca.identificacao}.xlsx"
    return send_file(output, download_name=filename, as_attachment=True, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@routes_bp.route("/excluir_registro/<int:id>/<int:balanca_id>", methods=["POST"])
def excluir_registro(id, balanca_id):
    registro = RegistroDiario.query.get_or_404(id)
    db.session.delete(registro)
    db.session.commit()
    flash("Registro excluído com sucesso.", "success")
    return redirect(url_for("routes.historico", id=balanca_id, admin=1))
