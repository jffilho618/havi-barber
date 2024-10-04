from flask import Flask, jsonify, request, send_from_directory, render_template, redirect, url_for, session, flash
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__, static_url_path='', static_folder='.', template_folder='.')

app.secret_key = 'bomba'  # Substitua por uma chave secreta única



# Conexão com o MongoDB
client = MongoClient("mongodb+srv://jffilho618:Yn9CWR3vSEePyfvX@havibarber.6ui8c.mongodb.net/?retryWrites=true&w=majority&appName=havibarber")
db = client['nome_do_banco']  # Substitua pelo nome do seu banco de dados
agendamentos_collection = db['agendamentos']
usuarios_collection = db['usuários']  # Coleção para armazenar usuários/barbeiros

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']

        # Procura o usuário no banco de dados
        user = usuarios_collection.find_one({"usuario": usuario})

        if user and user['senha'] == senha:  # Verifica a senha diretamente
            session['usuario'] = usuario
            return redirect(url_for('dono'))  # Redireciona para a página do barbeiro
        else:
            flash('Credenciais inválidas. Tente novamente.')

    return render_template('login.html')  # Página de login

# Logout
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('usuario', None)
    return redirect(url_for('index'))  # Redireciona para a página inicial


# Proteção da rota para barbeiro
def login_required(f):
    def wrap_login_required(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap_login_required.__name__ = f.__name__  # Isso mantém o nome da função original
    return wrap_login_required

# Página do cliente (index.html)
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')  # Página inicial do cliente

# Página do barbeiro (dono.html) - protegida
@app.route('/dono')
@login_required
def dono():
    return render_template('dono.html')  # Página de gerenciamento dos agendamentos

from datetime import datetime

@app.route('/agendamentos', methods=['POST'])
def create_agendamento():
    data = request.json
    horario = data.get("horario")
    data_agendamento = data.get("data")

    # Verifica se o horário já passou
    agendamento_data_hora = datetime.strptime(f"{data_agendamento} {horario}", "%Y-%m-%d %H:%M")
    agora = datetime.now()

    if agendamento_data_hora < agora:
        return jsonify({"error": "Não é possível agendar para um horário no passado."}), 400

    # Verifica se o horário já está reservado
    agendamento_existente = agendamentos_collection.find_one({
        "data": data_agendamento,
        "horario": horario
    })

    if agendamento_existente:
        return jsonify({"error": "Horário já reservado."}), 409  # Conflito

    result = agendamentos_collection.insert_one(data)
    data['_id'] = str(result.inserted_id)

    return jsonify(data), 201


# API para obter todos os agendamentos (somente barbeiro)
@app.route('/agendamentos', methods=['GET'])
@login_required
def get_agendamentos():
    agendamentos = agendamentos_collection.find()
    lista_agendamentos = []

    for agendamento in agendamentos:
        lista_agendamentos.append({
            "_id": str(agendamento["_id"]),
            "nome": agendamento["nome"],
            "telefone": agendamento["telefone"],
            "data": agendamento["data"],
            "horario": agendamento["horario"],
            "servico": agendamento["servico"],
            "preco": agendamento["preco"]
        })

    return jsonify(lista_agendamentos)

# API para buscar agendamentos por telefone (acessível pelo cliente)
@app.route('/agendamentos/telefone', methods=['POST'])
def get_agendamentos_por_telefone():
    telefone = request.json.get('telefone')
    hoje = datetime.now().strftime('%Y-%m-%d')

    agendamentos = agendamentos_collection.find({
        "telefone": telefone,
        "data": {"$gte": hoje}
    })

    lista_agendamentos = []

    for agendamento in agendamentos:
        lista_agendamentos.append({
            "_id": str(agendamento["_id"]),
            "nome": agendamento["nome"],
            "telefone": agendamento["telefone"],
            "data": agendamento["data"],
            "horario": agendamento["horario"],
            "servico": agendamento["servico"],
            "preco": agendamento["preco"]
        })

    if not lista_agendamentos:
        return jsonify({"message": "Nenhum agendamento futuro encontrado para este telefone."}), 404

    return jsonify(lista_agendamentos), 200

# API para remover agendamento (somente barbeiro)
@app.route('/agendamentos/<id>', methods=['DELETE'])
def remover_agendamento(id):
    agendamento = agendamentos_collection.find_one({"_id": ObjectId(id)})

    if not agendamento:
        return jsonify({"error": "Agendamento não encontrado"}), 404

    result = agendamentos_collection.delete_one({"_id": ObjectId(id)})

    if result.deleted_count > 0:
        return jsonify({"message": "Agendamento removido com sucesso"}), 200
    else:
        return jsonify({"error": "Erro ao remover agendamento"}), 500

# API para obter horários disponíveis (acessível pelo cliente)
@app.route('/horarios_disponiveis', methods=['GET'])
def get_horarios_disponiveis():
    try:
        data = request.args.get('data')
        if not data or len(data) != 10 or data[4] != '-' or data[7] != '-':
            return jsonify({'error': 'Data inválida. Use o formato YYYY-MM-DD.'}), 400

        horarios_agendados = agendamentos_collection.find({"data": data})
        horarios_reservados = [agendamento["horario"] for agendamento in horarios_agendados]

        todos_horarios = [
            "09:00", "09:40", "10:20", "11:00", "13:00", "13:40",
            "14:20", "15:00", "15:40", "16:20", "17:00", "17:40",
            "18:20", "19:00"
        ]

        horarios_disponiveis = [horario for horario in todos_horarios if horario not in horarios_reservados]

        return jsonify(horarios_disponiveis)

    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor.'}), 500



if __name__ == "__main__":
    app.run(debug=True)
