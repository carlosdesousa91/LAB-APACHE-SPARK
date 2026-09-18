import requests

# URL da API de destino
url = 'http://host.docker.internal:9200/dados-spark/_doc'
# http://localhost:9200/dados-spark/_doc

# Dados que você deseja enviar
dados = {
    'nome': 'João Silva',
    'email': 'joao@email.com',
    'idade': 30
}

# Realiza a requisição POST enviando os dados em JSON
resposta = requests.post(url, json=dados)

# Verifica se a requisição foi bem-sucedida
if resposta.status_code == 201:  # 201 geralmente significa 'Criado com sucesso'
    print('Dados enviados com sucesso!')
    print('Resposta da API:', resposta.json())
else:
    print(f'Erro ao enviar dados. Código de status: {resposta.status_code}')
    print('Detalhes:', resposta.text)