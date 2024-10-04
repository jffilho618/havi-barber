from pymongo import MongoClient

# Conectar ao MongoDB
client = MongoClient("mongodb+srv://jffilho618:AzrNtnNxi2dmKzkd@havibarber.6ui8c.mongodb.net/?retryWrites=true&w=majority&appName=havibarber")  # Ajuste a URL conforme necessário
db = client['nome_do_banco']
usuarios_collection = db['usuários']

# Adicionar um novo usuário
usuario_exemplo = {
    "usuario": "havi_barber",
    "senha": ("havi123"),
}

usuarios_collection.insert_one(usuario_exemplo)
print("Usuário adicionado com sucesso!")
