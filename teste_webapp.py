import requests
import json

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzTlQpsLZxemQN0WwNJOHiLaTPsWouD8YkFK9NN17oXTHGTrQzyndlML_CPP8rl7W34zA/exec"  # URL do seu Apps Script Web App

pedido = {
    "requisitante": "Raul",
    "projeto": "Projeto X",
    "itens": "Item 1, Item 2",
    "quantidade": "10",
    "observacoes": "Sem observações",
    "dataPrevista": "2025-09-15"
}

response = requests.post(
    WEBAPP_URL,
    headers={"Content-Type": "application/json"},
    data=json.dumps(pedido)
)

print(response.text)