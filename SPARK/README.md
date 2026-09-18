# Lab Apache Spark

Laboratório introdutório de **Apache Spark** com Docker.
O cluster sobe com 1 Master e 3 Workers.

---

## Pré-requisitos

Antes de começar, confirme que você tem:

- [Docker](https://docs.docker.com/get-docker/) instalado
- [Docker Compose](https://docs.docker.com/compose/) (já vem no Docker Desktop / Docker Engine recente)
- Permissão para usar o Docker (no Linux: usuário no grupo `docker`)

Para verificar:

```bash
docker --version
docker compose version
```

Se aparecer `permission denied` no Linux, peça ao professor/admin para te adicionar ao grupo:

```bash
sudo usermod -aG docker $USER
```

Depois, saia e entre novamente na sessão (ou reinicie o computador).

---

## Estrutura do projeto

```text
SPARK/
├── docker-compose.yml   # Sobe o cluster Spark
├── Dockerfile           # Imagem Spark + biblioteca requests
├── apps/                # Scripts Python (PySpark)
│   ├── hello_spark.py
│   ├── word_count.py
│   └── enviar_elastic.py
├── data/                # Arquivos de dados de exemplo
│   └── palavras.txt
└── README.md
```

---

## Passo 1 — Subir o cluster

No terminal, entre na pasta do projeto e execute:

```bash
cd SPARK
docker compose up -d --build
```

Na primeira vez, o Docker baixa as imagens e instala o `requests` (pode demorar alguns minutos). Use `--build` de novo se alterar o `Dockerfile`.

Verifique se os containers estão rodando:

```bash
docker compose ps
```

Você deve ver:

| Container         | Status  |
|-------------------|---------|
| `spark-master`    | running |
| `spark-worker-1`  | running |
| `spark-worker-2`  | running |
| `spark-worker-3`  | running |

---

## Passo 2 — Abrir a interface web

Com o cluster no ar, abra no navegador:

| Serviço   | URL                         |
|-----------|-----------------------------|
| Master UI | http://localhost:8080       |
| Worker 1  | http://localhost:8081       |
| Worker 2  | http://localhost:8082       |
| Worker 3  | http://localhost:8083       |

Na tela do Master (`8080`), confirme que aparecem **3 workers** conectados.

---

## Passo 3 — Primeiro teste (Hello Spark)

Rode o script que cria um DataFrame simples:

```bash
docker compose exec spark-master \
  /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  /opt/spark-apps/hello_spark.py
```

**Resultado esperado:** uma tabela com nomes/idades, o total de linhas e a versão do Spark.

---

## Passo 4 — Segundo teste (Word Count)

Rode a contagem de palavras no arquivo `data/palavras.txt`:

```bash
docker compose exec spark-master \
  /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  /opt/spark-apps/word_count.py
```

**Resultado esperado:** lista de palavras ordenada pela frequência (ex.: `spark`, `dados`, etc.).

---

## Passo 5 — Enviar dados mockados para o Elasticsearch

O script `enviar_elastic.py` cria um DataFrame com eventos fictícios e envia o lote para a API REST do Elasticsearch (`_bulk`).

**Pré-requisito:** o lab Elasticsearch precisa estar no ar (pasta `ELASTICSEARCH/`). O Spark acessa a API pela porta `9200` do host (`host.docker.internal`).

```bash
# Em outro terminal, na pasta ELASTICSEARCH:
docker compose up -d
```

Rode o job:

```bash
docker compose exec spark-master \
  /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  /opt/spark-apps/enviar_elastic.py
```

**Resultado esperado:** tabela com 5 eventos mockados e a mensagem de que foram enviados para o índice `spark-eventos`.

Para conferir no Elasticsearch:

```bash
curl "http://localhost:9200/spark-eventos/_search?pretty"
```

No Kibana (**Dev Tools**):

```http
GET spark-eventos/_search
```

---

## Parar o cluster

Quando terminar o lab:

```bash
docker compose down
```

Para remover também os volumes/dados criados pelos containers (se houver):

```bash
docker compose down -v
```

---

## Problemas comuns

**Containers não sobem**
- Confirme que o Docker está em execução.
- Veja os logs: `docker compose logs`

**Workers não aparecem no Master / job sem recursos**
- Aguarde 10–20 segundos após o `up`.
- Recarregue a página http://localhost:8080 e confirme **3 workers** Alive.
- Se o Master estiver em mais de uma rede Docker, ele pode escutar no IP errado e os workers não registram. O Master deve ficar só em `spark-net`.
- Recrie o cluster: `docker compose down && docker compose up -d`

**Porta já em uso (8080, 8081, 8082, 8083 ou 7077)**
- Pare o outro serviço que estiver usando a porta, ou altere o mapeamento em `docker-compose.yml`.

**Job falha ao ler arquivo**
- Confirme que `data/palavras.txt` existe na pasta do projeto.
- As pastas `apps/` e `data/` são montadas dentro dos containers automaticamente.

**Falha ao conectar no Elasticsearch**
- Suba o lab em `ELASTICSEARCH/` (`docker compose up -d`) e aguarde o container ficar healthy.
- Teste no host: `curl http://localhost:9200`

---

## Próximos passos (opcional)

1. Edite `apps/hello_spark.py` e rode de novo.
2. Altere `data/palavras.txt` e repita o Word Count.
3. Troque os dados mockados em `apps/enviar_elastic.py` e envie de novo para o Elasticsearch.
4. Crie um novo script em `apps/` e envie com `spark-submit` da mesma forma.
