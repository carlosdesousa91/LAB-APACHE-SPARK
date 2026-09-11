# Lab Elasticsearch + Kibana

Laboratório introdutório de **Elasticsearch** e **Kibana** com Docker.
Sobe um nó único (single-node), sem autenticação — ideal para estudo local.

---

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) instalado
- [Docker Compose](https://docs.docker.com/compose/)
- Permissão para usar o Docker (no Linux: usuário no grupo `docker`)

```bash
docker --version
docker compose version
```

---

## Estrutura

```text
ELASTICSEARCH/
├── docker-compose.yml
└── README.md
```

---

## Passo 1 — Subir Elasticsearch e Kibana

```bash
cd ELASTICSEARCH
docker compose up -d
```

Na primeira vez, o Docker baixa as imagens (pode demorar).

Verifique o status:

```bash
docker compose ps
```

Você deve ver:

| Container       | Status  |
|-----------------|---------|
| `elasticsearch` | healthy / running |
| `kibana`        | running |

Aguarde o Elasticsearch ficar **healthy** (cerca de 30–60 segundos). O Kibana sobe em seguida.

---

## Passo 2 — Abrir as interfaces

| Serviço       | URL                   |
|---------------|-----------------------|
| Elasticsearch | http://localhost:9200 |
| Kibana        | http://localhost:5601 |

No Kibana, explore o menu lateral (ex.: **Dev Tools** para rodar consultas).

---

## Passo 3 — Testar a API do Elasticsearch

```bash
curl http://localhost:9200
```

**Resultado esperado:** um JSON com `cluster_name`, `version` e `"tagline" : "You Know, for Search"`.

Outros testes rápidos:

```bash
# Saúde do cluster
curl http://localhost:9200/_cluster/health?pretty

# Informações do nó
curl http://localhost:9200/_cat/nodes?v
```

---

## Passo 4 — Criar um documento de teste

```bash
curl -X POST "http://localhost:9200/alunos/_doc/1?pretty" \
  -H "Content-Type: application/json" \
  -d '{"nome":"Ana","curso":"Big Data","idade":25}'
```

Buscar o documento:

```bash
curl "http://localhost:9200/alunos/_doc/1?pretty"
```

Listar índices:

```bash
curl "http://localhost:9200/_cat/indices?v"
```

No Kibana (**Dev Tools**), você pode rodar o equivalente:

```http
GET alunos/_doc/1
```

---

## Parar os serviços

```bash
docker compose down
```

Para apagar também os dados salvos no volume:

```bash
docker compose down -v
```

---

## Problemas comuns

**Container não fica healthy**
- Veja os logs: `docker compose logs -f elasticsearch`
- Em máquinas com pouca RAM, o Elasticsearch pode falhar; tente aumentar a memória disponível do Docker.

**Kibana não abre / fica carregando**
- Aguarde mais alguns segundos após o Elasticsearch ficar healthy.
- Veja os logs: `docker compose logs -f kibana`

**Porta 9200 ou 5601 em uso**
- Pare o outro serviço ou altere o mapeamento em `docker-compose.yml`.

**permission denied no Docker (Linux)**
```bash
sudo usermod -aG docker $USER
```
Depois saia e entre novamente na sessão.
