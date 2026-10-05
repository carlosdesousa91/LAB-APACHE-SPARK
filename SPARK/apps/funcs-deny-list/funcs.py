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