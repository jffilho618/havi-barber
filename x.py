from pymongo import MongoClient

# Conectar ao MongoDB
client = MongoClient('mongodb://localhost:27017/')  # Ajuste a URL conforme necessário
db = client['nome_do_banco']
usuarios_collection = db['usuários']

# Adicionar um novo usuário
usuario_exemplo = {
    "usuario": "usuario_exemplo",
    "senha": ("senha_exemplo")
}

usuarios_collection.insert_one(usuario_exemplo)
print("Usuário adicionado com sucesso!")
