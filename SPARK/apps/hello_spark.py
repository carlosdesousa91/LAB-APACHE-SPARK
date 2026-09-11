"""
Primeiro teste com Apache Spark.
Cria um DataFrame simples, mostra os dados e conta as linhas.
"""

from pyspark.sql import SparkSession


def main():
    spark = (
        SparkSession.builder
        .appName("HelloSpark")
        .master("spark://spark-master:7077")
        .getOrCreate()
    )

    dados = [
        ("Ana", 25),
        ("Bruno", 30),
        ("Carla", 22),
        ("Diogo", 28),
    ]

    df = spark.createDataFrame(dados, ["nome", "idade"])

    print("=== DataFrame ===")
    df.show()

    print(f"Total de linhas: {df.count()}")
    print(f"Versão do Spark: {spark.version}")

    spark.stop()


if __name__ == "__main__":
    main()
