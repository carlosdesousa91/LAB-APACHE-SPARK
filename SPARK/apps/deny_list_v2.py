from datetime import datetime, timezone
import json
import time
import urllib.request

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

def ler_logs():

    url = "http://host.docker.internal:9200/logs-firewall/_search"
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=None, method="GET", headers=headers)
    
    with urllib.request.urlopen(req, timeout=15) as resp:
        resposta = json.loads(resp.read().decode("utf-8"))

    linhas = []
    for hit in resposta.get("hits", {}).get("hits", []):
        doc = hit.get("_source", {})
        mensagem = doc.get("message") or ""
        linhas.append({
            "_id": hit.get("_id"),
            "src_ip": doc.get("src_ip"),
            "dest_ip": doc.get("dest_ip") ,
            "action": doc.get("action"),
            "message": mensagem,
        })
    return linhas


INDEX_INCIDENTES = "incidentes"
ARQUIVO_CSV = "/opt/spark-apps/danylist.csv"
INTERVALO_SEGUNDOS = 10

DENY_LIST = [
    "203.0.113.10",
    "198.51.100.25",
    "192.0.2.50",
]


spark = (
    SparkSession.builder
    .appName("DenyList")
    .master("spark://spark-master:7077")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

ja_visto = set()

try:
    while True:
        logs = ler_logs()

        #df = spark.createDataFrame(logs)
        #matches = df.filter(F.col("src_ip").isin(DENY_LIST))

        #for row in matches.collect():

        #    print(row)
        print("conseguimos ler os logs: ", logs)

        time.sleep(INTERVALO_SEGUNDOS)

except KeyboardInterrupt:
    print("\nDeny List encerrado pelo usuário.")
    spark.stop()
