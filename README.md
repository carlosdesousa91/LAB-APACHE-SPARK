# Labs — Spark, Elasticsearch e OpenSearch

Repositório com laboratórios introdutórios usando Docker Compose.

| Pasta | Conteúdo |
|-------|----------|
| [`SPARK/`](SPARK/) | Cluster Apache Spark (Master + Workers) |
| [`ELASTICSEARCH/`](ELASTICSEARCH/) | Elasticsearch + Kibana |
| [`OPENSEARCH/`](OPENSEARCH/) | OpenSearch + OpenSearch Dashboards |

O Spark envia dados à API do Elasticsearch em `http://localhost:9200` (`host.docker.internal` a partir dos containers).

O OpenSearch escuta em `http://localhost:9201` e o Dashboards em `http://localhost:5602`, para não disputar as portas do Elasticsearch e do Kibana.

Entre na pasta do lab desejado e siga o `README.md` correspondente.
