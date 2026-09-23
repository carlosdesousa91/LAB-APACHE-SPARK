"""
Deny List — exemplo simples de Spark + Elasticsearch

O que este app faz:
1. Lê logs do índice logs-firewall
2. Extrai o src_ip de um log no formato KV (chave=valor)
3. Se o IP estiver na deny list, gera um alerta
4. Grava o incidente no índice incidentes e no arquivo danylist.csv

O app fica em execução até você pressionar Ctrl+C.
Novos logs no Elastic aparecem no próximo ciclo.

Como executar:
  spark-submit deny_list.py
"""

from pyspark.sql import SparkSession
import time
from datetime import datetime

# ============================================================
# CONFIGURAÇÃO — altere para o seu ambiente
# ============================================================
ES_HOST = "localhost"
ES_PORT = "9200"
ES_USER = "elastic"       # deixe "" se o Elastic não pedir senha
ES_PASSWORD = "changeme"

INDEX_LOGS = "logs-firewall"
INDEX_INCIDENTES = "incidentes"
ARQUIVO_CSV = "danylist.csv"
INTERVALO_SEGUNDOS = 10

# IPs que devem gerar alerta
DENY_LIST = [
    "203.0.113.10",
    "198.51.100.25",
    "192.0.2.50",
]
# ============================================================

spark = (
    SparkSession.builder
    .appName("DenyList")
    .config("spark.jars.packages", "org.elasticsearch:elasticsearch-spark-30_2.12:8.15.3")
    .config("es.nodes", ES_HOST)
    .config("es.port", ES_PORT)
    .config("es.nodes.wan.only", "true")
    .config("es.net.http.auth.user", ES_USER)
    .config("es.net.http.auth.pass", ES_PASSWORD)
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")


def pega_campo(mensagem, campo):
    """Lê um valor de um log KV. Ex: src_ip=1.2.3.4 -> 1.2.3.4"""
    for parte in mensagem.split():
        if parte.startswith(campo + "="):
            return parte.split("=", 1)[1]
    return ""


# cria o CSV com cabeçalho na primeira execução
try:
    with open(ARQUIVO_CSV, "x") as f:
        f.write("timestamp,src_ip,dest_ip,action,message\n")
except FileExistsError:
    pass

print("=" * 50)
print("Deny List iniciado")
print("Lendo:", INDEX_LOGS)
print("IPs na lista:", ", ".join(DENY_LIST))
print("Ctrl+C para parar")
print("=" * 50)

# guarda logs já alertados para não repetir o mesmo alarme
ja_visto = set()

try:
    while True:
        try:
            logs = (
                spark.read.format("es")
                .option("es.resource", INDEX_LOGS)
                .load()
                .collect()
            )
        except Exception:
            print("Aguardando dados no índice", INDEX_LOGS, "...")
            time.sleep(INTERVALO_SEGUNDOS)
            continue

        novos = 0
        for log in logs:
            mensagem = log["message"]
            src_ip = pega_campo(mensagem, "src_ip")

            if src_ip in DENY_LIST and mensagem not in ja_visto:
                ja_visto.add(mensagem)
                novos += 1

                dest_ip = pega_campo(mensagem, "dest_ip")
                action = pega_campo(mensagem, "action")
                agora = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

                print("\n[ALERTA] IP da deny list encontrado:", src_ip)
                print("         log:", mensagem)

                with open(ARQUIVO_CSV, "a") as f:
                    f.write(f"{agora},{src_ip},{dest_ip},{action},{mensagem}\n")

                incidente = spark.createDataFrame(
                    [(agora, src_ip, dest_ip, action, mensagem)],
                    ["@timestamp", "src_ip", "dest_ip", "action", "message"],
                )
                (
                    incidente.write.format("es")
                    .option("es.resource", INDEX_INCIDENTES)
                    .mode("append")
                    .save()
                )

        if novos == 0:
            agora = datetime.now().strftime("%H:%M:%S")
            print(f"[{agora}] sem novos matches")

        time.sleep(INTERVALO_SEGUNDOS)

except KeyboardInterrupt:
    print("\nDeny List encerrado pelo usuário.")
    spark.stop()
