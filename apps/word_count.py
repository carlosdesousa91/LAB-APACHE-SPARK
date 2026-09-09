"""
Contagem de palavras com Apache Spark (Word Count).
Lê um arquivo de texto e conta a frequência de cada palavra.
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def main():
    spark = (
        SparkSession.builder
        .appName("WordCount")
        .master("spark://spark-master:7077")
        .getOrCreate()
    )

    caminho = "/opt/spark-data/palavras.txt"

    # Lê o arquivo como texto (uma linha por registro)
    linhas = spark.read.text(caminho)

    # Quebra cada linha em palavras, normaliza e conta
    palavras = (
        linhas
        .select(F.explode(F.split(F.lower(F.col("value")), r"\W+")).alias("palavra"))
        .filter(F.col("palavra") != "")
        .groupBy("palavra")
        .count()
        .orderBy(F.desc("count"))
    )

    print("=== Contagem de palavras ===")
    palavras.show(20, truncate=False)

    spark.stop()


if __name__ == "__main__":
    main()
