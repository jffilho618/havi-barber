from flask import Flask, jsonify, request, send_from_directory
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson import ObjectId

app = Flask(__name__, static_url_path='', static_folder='.')

# Conexão com o MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["havi_barber"]

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def send_static(path):
    return send_from_directory('.', path)

@app.route('/agendamentos', methods=['POST'])
def create_agendamento():
    data = request.json

    # Verifica se o horário já está reszervado
    horario = data.get("horario")
    data_agendamento = data.get("data")

    agendamento_existente = db.agendamentos.find_one({
        "data": data_agendamento,
        "horario": horario
    })

    if agendamento_existente:
        return jsonify({"error": "Horário já reservado."}), 409  # Conflito

    # Se não houver conflito, insere o novo agendamento
    result = db.agendamentos.insert_one(data)

    # Convertendo o ObjectId em string
    data['_id'] = str(result.inserted_id)

    return jsonify(data), 201

@app.route('/agendamentos', methods=['GET'])
def get_agendamentos():
    agendamentos = db.agendamentos.find()
    lista_agendamentos = []

    for agendamento in agendamentos:
        lista_agendamentos.append({
            "_id": str(agendamento["_id"]),  # Convertendo ObjectId para string
            "nome": agendamento["nome"],
            "telefone": agendamento["telefone"],
            "data": agendamento["data"],
            "horario": agendamento["horario"],
            "servico": agendamento["servico"],
            "preco": agendamento["preco"]
        })

    return jsonify(lista_agendamentos)

# Nova rota para obter os agendamentos de um usuário com base no telefone e data futura
from flask import jsonify, request
from datetime import datetime
from pymongo import MongoClient

# Conexão com MongoDB (exemplo)
client = MongoClient('mongodb://localhost:27017/')
db = client['nome_do_banco']  # Substitua pelo nome do seu banco de dados

from datetime import datetime

@app.route('/agendamentos/telefone', methods=['POST'])
def get_agendamentos_por_telefone():
    telefone = request.json.get('telefone')

    if not telefone:
        return jsonify({"error": "Telefone não fornecido."}), 400

    # Obtém a data atual no formato 'YYYY-MM-DD'
    hoje = datetime.now().strftime('%Y-%m-%d')

    # Usando a comparação de strings no MongoDB para a data
    agendamentos = db.agendamentos.find({
        "telefone": telefone,
        "data": {"$gte": hoje}  # Compara como string
    })

    lista_agendamentos = []

    for agendamento in agendamentos:
        lista_agendamentos.append({
            "_id": str(agendamento["_id"]),
            "nome": agendamento["nome"],
            "telefone": agendamento["telefone"],
            "data": agendamento["data"],  # Já está formatada corretamente
            "horario": agendamento["horario"],
            "servico": agendamento["servico"],
            "preco": agendamento["preco"]
        })

    if not lista_agendamentos:
        return jsonify({"message": "Nenhum agendamento futuro encontrado para este telefone."}), 404

    return jsonify(lista_agendamentos), 200

# Modificação para impedir cancelamento a menos de 1 hora do horário agendado
@app.route('/agendamentos/<id>', methods=['DELETE'])
def remover_agendamento(id):
    agendamento = db.agendamentos.find_one({"_id": ObjectId(id)})

    if not agendamento:
        return jsonify({"error": "Agendamento não encontrado"}), 404

    # Remove o agendamento
    result = db.agendamentos.delete_one({"_id": ObjectId(id)})

    if result.deleted_count > 0:
        return jsonify({"message": "Agendamento removido com sucesso"}), 200
    else:
        return jsonify({"error": "Erro ao remover agendamento"}), 500



if __name__ == "__main__":
    app.run(debug=True)
