from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, abort
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, Balanca, RegistroDiario, User
from io import BytesIO
from openpyxl import Workbook
from datetime import datetime, date

routes_bp = Blueprint('routes', __name__)

# --- Autenticação ---

@routes_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('routes.index'))
        else:
            flash("Usuário ou senha inválidos.", "danger")

    return render_template("login.html", title="Login")

@routes_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sessão encerrada.", "info")
    return redirect(url_for('routes.login'))

# --- Gestão de Usuários (Apenas Admin) ---

@routes_bp.route("/usuarios", methods=["GET", "POST"])
@login_required
def usuarios():
    if not current_user.is_admin:
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for('routes.index'))

    if request.method == "POST":
        novo_user = request.form.get('username')
        nova_senha = request.form.get('password')
        eh_admin = True if request.form.get('is_admin') else False

        if User.query.filter_by(username=novo_user).first():
            flash("Usuário já existe.", "warning")
        else:
            u = User(username=novo_user, is_admin=eh_admin)
            u.set_password(nova_senha)
            db.session.add(u)
            db.session.commit()
            flash(f"Usuário {novo_user} criado com sucesso!", "success")
        return redirect(url_for('routes.usuarios'))

    todos_usuarios = User.query.all()
    return render_template("usuarios.html", usuarios=todos_usuarios, title="Gerenciar Usuários")

@routes_bp.route("/excluir_usuario/<int:user_id>", methods=["POST"])
@login_required
def excluir_usuario(user_id):
    if not current_user.is_admin:
        abort(403)
    
    user_to_delete = User.query.get_or_404(user_id)
    if user_to_delete.id == current_user.id:
        flash("Você não pode excluir a si mesmo.", "warning")
    else:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash("Usuário removido.", "success")
    return redirect(url_for('routes.usuarios'))

# --- Rotas Principais ---

@routes_bp.route("/")
@login_required
def index():
    balancas = Balanca.query.all()
    return render_template("index.html", title="Dashboard", balancas=balancas)

@routes_bp.route("/cadastrar", methods=["GET", "POST"])
@login_required
def cadastrar():
    # Apenas admin cadastra novas balanças? Se sim, descomente a linha abaixo:
    # if not current_user.is_admin: abort(403)
    
    if request.method == "POST":
        dados = request.form
        existente = Balanca.query.filter_by(identificacao=dados['identificacao']).first()
        if existente:
            flash("Erro: Identificação já existe.", "danger")
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
        flash("Balança cadastrada!", "success")
        return redirect(url_for("routes.index"))
    return render_template("cadastro_balanca.html", title="Nova Balança")

@routes_bp.route("/verificar/<int:id>", methods=["GET", "POST"])
@login_required
def verificar(id):
    balanca = Balanca.query.get_or_404(id)
    if request.method == "POST":
        resultado = float(request.form['resultado_obtido'])
        responsavel = request.form['responsavel']
        
        # LÓGICA DE DATA:
        # Se for admin e enviou data, usa ela. Senão, usa hoje.
        if current_user.is_admin and request.form.get('data'):
            data = datetime.strptime(request.form['data'], "%Y-%m-%d").date()
        else:
            data = date.today()

        novo_registro = RegistroDiario(
            data=data,
            resultado_obtido=resultado,
            responsavel=responsavel,
            balanca_id=balanca.id
        )
        db.session.add(novo_registro)
        db.session.commit()
        flash("Verificação salva!", "success")
        return redirect(url_for('routes.index'))
    return render_template("verificacao.html", balanca=balanca, now=date.today().strftime('%Y-%m-%d'))

@routes_bp.route("/historico/<int:id>")
@login_required
def historico(id):
    balanca = Balanca.query.get_or_404(id)
    registros = RegistroDiario.query.filter_by(balanca_id=id).order_by(RegistroDiario.data.desc()).all()
    return render_template("historico.html", balanca=balanca, registros=registros)

@routes_bp.route("/exportar_excel/<int:id>")
@login_required
def exportar_excel(id):
    balanca = Balanca.query.get_or_404(id)
    registros = RegistroDiario.query.filter_by(balanca_id=id).order_by(RegistroDiario.data.asc()).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Historico"
    ws.append(["Data", "Padrão", "Obtido", "Diferença", "Status", "Responsável"])

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
    filename = f"Historico_{balanca.identificacao}.xlsx"
    return send_file(output, download_name=filename, as_attachment=True, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@routes_bp.route("/excluir_registro/<int:id>/<int:balanca_id>", methods=["POST"])
@login_required
def excluir_registro(id, balanca_id):
    # Proteção no Back-end: Apenas Admin pode excluir
    if not current_user.is_admin:
        flash("Apenas administradores podem excluir registros.", "danger")
        return redirect(url_for("routes.historico", id=balanca_id))
        
    registro = RegistroDiario.query.get_or_404(id)
    db.session.delete(registro)
    db.session.commit()
    flash("Registro excluído.", "success")
    return redirect(url_for("routes.historico", id=balanca_id))