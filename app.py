from flask import Flask, jsonify, request, send_from_directory
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

app = Flask(__name__, static_url_path='', static_folder='.')

# Conexão com o MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['nome_do_banco']
agendamentos_collection = db['agendamentos']  # Defina a coleção

@app.route('/')
def index():
    return send_from_directory('.', 'dono.html')

@app.route('/<path:path>')
def send_static(path):
    return send_from_directory('.', path)

@app.route('/agendamentos', methods=['POST'])
def create_agendamento():
    data = request.json

    # Verifica se o horário já está reservado
    horario = data.get("horario")
    data_agendamento = data.get("data")

    agendamento_existente = agendamentos_collection.find_one({
        "data": data_agendamento,
        "horario": horario
    })

    if agendamento_existente:
        return jsonify({"error": "Horário já reservado."}), 409  # Conflito

    # Se não houver conflito, insere o novo agendamento
    result = agendamentos_collection.insert_one(data)

    # Convertendo o ObjectId em string
    data['_id'] = str(result.inserted_id)

    return jsonify(data), 201

@app.route('/agendamentos', methods=['GET'])
def get_agendamentos():
    agendamentos = agendamentos_collection.find()
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

@app.route('/agendamentos/telefone', methods=['POST'])
def get_agendamentos_por_telefone():
    telefone = request.json.get('telefone')

    if not telefone:
        return jsonify({"error": "Telefone não fornecido."}), 400

    # Obtém a data atual no formato 'YYYY-MM-DD'
    hoje = datetime.now().strftime('%Y-%m-%d')

    # Usando a comparação de strings no MongoDB para a data
    agendamentos = agendamentos_collection.find({
        "telefone": telefone,
        "data": {"$gte": hoje}  # Compara como string
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

@app.route('/agendamentos/<id>', methods=['DELETE'])
def remover_agendamento(id):
    agendamento = agendamentos_collection.find_one({"_id": ObjectId(id)})

    if not agendamento:
        return jsonify({"error": "Agendamento não encontrado"}), 404

    # Remove o agendamento
    result = agendamentos_collection.delete_one({"_id": ObjectId(id)})

    if result.deleted_count > 0:
        return jsonify({"message": "Agendamento removido com sucesso"}), 200
    else:
        return jsonify({"error": "Erro ao remover agendamento"}), 500

@app.route('/horarios_disponiveis', methods=['GET'])
def get_horarios_disponiveis():
    try:
        data = request.args.get('data')
        print('Data recebida:', data)

        # Verifique se a data está em um formato válido
        if not data or len(data) != 10 or data[4] != '-' or data[7] != '-':
            return jsonify({'error': 'Data inválida. Use o formato YYYY-MM-DD.'}), 400

        # Obtenha todos os horários já agendados para a data
        horarios_agendados = agendamentos_collection.find({"data": data})
        horarios_reservados = [agendamento["horario"] for agendamento in horarios_agendados]

        # Defina todos os horários possíveis
        todos_horarios = [
            "09:00", "09:40", "10:20", "11:00", "13:00", "13:40",
            "14:20", "15:00", "15:40", "16:20", "17:00", "17:40",
            "18:20", "19:00"
        ]

        # Filtre os horários disponíveis
        horarios_disponiveis = [horario for horario in todos_horarios if horario not in horarios_reservados]

        return jsonify(horarios_disponiveis)

    except Exception as e:
        print('Erro ao processar a solicitação:', str(e))
        return jsonify({'error': 'Erro interno do servidor.'}), 500

if __name__ == "__main__":
    app.run(debug=True)
