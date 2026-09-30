# Lab OpenSearch + Dashboards

Laboratório introdutório de **OpenSearch** e **OpenSearch Dashboards** com Docker.
Sobe um nó único (single-node), sem autenticação — ideal para estudo local.

As portas no host são diferentes das do lab Elasticsearch, para os dois stacks poderem ficar no ar ao mesmo tempo.

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
OPENSEARCH/
├── docker-compose.yml
└── README.md
```

---

## Passo 1 — Subir OpenSearch e Dashboards

```bash
cd OPENSEARCH
docker compose up -d
```

Na primeira vez, o Docker baixa as imagens (pode demorar).

Verifique o status:

```bash
docker compose ps
```

Você deve ver:

| Container               | Status            |
|-------------------------|-------------------|
| `opensearch`            | healthy / running |
| `opensearch-dashboards` | running           |

Aguarde o OpenSearch ficar **healthy** (cerca de 30–60 segundos). O Dashboards sobe em seguida.

---

## Passo 2 — Abrir as interfaces

| Serviço               | URL                   |
|-----------------------|-----------------------|
| OpenSearch            | http://localhost:9201 |
| OpenSearch Dashboards | http://localhost:5602 |

No Dashboards, explore o menu lateral (ex.: **Dev Tools** para rodar consultas).

---

## Passo 3 — Testar a API do OpenSearch

```bash
curl http://localhost:9201
```

**Resultado esperado:** um JSON com `cluster_name`, `version` e `"tagline" : "The OpenSearch Project: https://opensearch.org/"`.

Outros testes rápidos:

```bash
# Saúde do cluster
curl http://localhost:9201/_cluster/health?pretty

# Informações do nó
curl http://localhost:9201/_cat/nodes?v
```

---

## Passo 4 — Criar um documento de teste

```bash
curl -X POST "http://localhost:9201/alunos/_doc/1?pretty" \
  -H "Content-Type: application/json" \
  -d '{"nome":"Ana","curso":"Big Data","idade":25}'
```

Buscar o documento:

```bash
curl "http://localhost:9201/alunos/_doc/1?pretty"
```

Listar índices:

```bash
curl "http://localhost:9201/_cat/indices?v"
```

No Dashboards (**Dev Tools**), você pode rodar o equivalente:

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
- Veja os logs: `docker compose logs -f opensearch`
- Em máquinas com pouca RAM, o OpenSearch pode falhar; tente aumentar a memória disponível do Docker.
- No Linux, se o nó não sobe por `max virtual memory areas`, ajuste: `sudo sysctl -w vm.max_map_count=262144`

**Dashboards não abre / fica carregando**
- Aguarde mais alguns segundos após o OpenSearch ficar healthy.
- Veja os logs: `docker compose logs -f opensearch-dashboards`

**Porta 9201, 9600 ou 5602 em uso**
- Pare o outro serviço ou altere o mapeamento em `docker-compose.yml`.

**permission denied no Docker (Linux)**
```bash
sudo usermod -aG docker $USER
```
Depois saia e entre novamente na sessão.
