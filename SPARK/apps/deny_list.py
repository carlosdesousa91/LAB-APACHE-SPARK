"""
Deny List — exemplo simples de Spark + Elasticsearch

O Spark lê logs do índice logs-firewall, compara o IP com uma deny list
e grava os matches no índice incidentes e no arquivo danylist.csv.

O app fica em execução até Ctrl+C.
Novos logs no Elastic entram no próximo ciclo.

Como executar (na pasta SPARK):
  docker compose exec spark-master \\
    /opt/spark/bin/spark-submit \\
    --master spark://spark-master:7077 \\
    /opt/spark-apps/deny_list.py
"""

from datetime import datetime, timezone
import json
import time
import urllib.request

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# ============================================================
# CONFIGURAÇÃO — altere para o seu ambiente
# ============================================================
# De dentro do container Spark use host.docker.internal (não localhost)
ES_HOST = "host.docker.internal"
ES_PORT = "9200"
ES_USER = ""          # lab sem senha — deixe vazio
ES_PASSWORD = ""

INDEX_LOGS = "logs-firewall"
INDEX_INCIDENTES = "incidentes"
ARQUIVO_CSV = "/opt/spark-apps/danylist.csv"
INTERVALO_SEGUNDOS = 10

DENY_LIST = [
    "203.0.113.10",
    "198.51.100.25",
    "192.0.2.50",
]
# ============================================================

ES_URL = f"http://{ES_HOST}:{ES_PORT}"


def agora_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def pega_campo(mensagem, campo):
    """Lê um valor de um log KV. Ex: src_ip=1.2.3.4 -> 1.2.3.4"""
    for parte in str(mensagem).split():
        if parte.startswith(campo + "="):
            return parte.split("=", 1)[1]
    return ""


def chamar_elastic(caminho, metodo="GET", corpo=None):
    url = f"{ES_URL}{caminho}"
    headers = {"Content-Type": "application/json"}
    data = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(url, data=data, method=metodo, headers=headers)
    if ES_USER:
        senha = f"{ES_USER}:{ES_PASSWORD}".encode()
        import base64
        req.add_header("Authorization", "Basic " + base64.b64encode(senha).decode())
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ler_logs():
    resposta = chamar_elastic(f"/{INDEX_LOGS}/_search?size=1000")
    linhas = []
    for hit in resposta.get("hits", {}).get("hits", []):
        doc = hit.get("_source", {})
        mensagem = doc.get("message") or ""
        linhas.append({
            "_id": hit.get("_id"),
            "src_ip": doc.get("src_ip") or pega_campo(mensagem, "src_ip"),
            "dest_ip": doc.get("dest_ip") or pega_campo(mensagem, "dest_ip"),
            "action": doc.get("action") or pega_campo(mensagem, "action"),
            "message": mensagem,
        })
    return linhas


spark = (
    SparkSession.builder
    .appName("DenyList")
    .master("spark://spark-master:7077")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

try:
    with open(ARQUIVO_CSV, "x") as f:
        f.write("timestamp,src_ip,dest_ip,action,message\n")
except FileExistsError:
    pass

print("=" * 50)
print("Deny List iniciado")
print("Elasticsearch:", ES_URL)
print("Lendo:", INDEX_LOGS)
print("Gravando em:", INDEX_INCIDENTES)
print("IPs na lista:", ", ".join(DENY_LIST))
print("Ctrl+C para parar")
print("=" * 50)

ja_visto = set()

try:
    while True:
        try:
            logs = ler_logs()
        except Exception as exc:
            print(f"Aguardando {INDEX_LOGS} em {ES_URL} ...")
            print(f"  erro: {exc}")
            time.sleep(INTERVALO_SEGUNDOS)
            continue

        if not logs:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] índice vazio")
            time.sleep(INTERVALO_SEGUNDOS)
            continue

        df = spark.createDataFrame(logs)
        matches = df.filter(F.col("src_ip").isin(DENY_LIST))

        novos = 0
        for row in matches.collect():
            if row["_id"] in ja_visto:
                continue

            ja_visto.add(row["_id"])
            novos += 1
            agora = agora_iso()

            print("\n[ALERTA] IP da deny list encontrado:", row["src_ip"])
            print("         log:", row["message"])

            with open(ARQUIVO_CSV, "a") as f:
                f.write(
                    f"{agora},{row['src_ip']},{row['dest_ip']},"
                    f"{row['action']},{row['message']}\n"
                )

            chamar_elastic(
                f"/{INDEX_INCIDENTES}/_doc?refresh=true",
                metodo="POST",
                corpo={
                    "@timestamp": agora,
                    "src_ip": row["src_ip"],
                    "dest_ip": row["dest_ip"],
                    "action": row["action"],
                    "message": row["message"],
                },
            )

        if novos == 0:
            hora = datetime.now().strftime("%H:%M:%S")
            print(f"[{hora}] sem novos matches ({len(logs)} logs lidos)")
        else:
            print(f"Novos incidentes gravados: {novos}")

        time.sleep(INTERVALO_SEGUNDOS)

except KeyboardInterrupt:
    print("\nDeny List encerrado pelo usuário.")
    spark.stop()
