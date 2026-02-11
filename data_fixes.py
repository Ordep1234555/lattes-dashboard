from pathlib import Path
import pandas as pd

# Caminho do arquivo
input_file = Path("data/curriculos_processados.csv")

# Leitura do CSV
df = pd.read_csv(input_file,
                 dtype={
                     "ano_inicio": "Int64",
                     "ano_conclusao": "Int64"
                 })

# 1. Excluir a coluna numero_identificador (se existir)
if "numero_identificador" in df.columns:
    df = df.drop(columns=["numero_identificador"])

# 2. Transformações na coluna tipo_formacao
map_tipo_formacao = {
    "DOUTORADO": "Doutorado",
    "MESTRADO": "Mestrado",
    "MESTRADO-PROFISSIONALIZANTE": "Mestrado Profissionalizante",
}

df["tipo_formacao"] = df["tipo_formacao"].replace(map_tipo_formacao)

# 3. Transformações na coluna grande_area
map_grande_area = {
    "CIENCIAS_AGRARIAS": "Ciências Agrárias",
    "CIENCIAS_BIOLOGICAS": "Ciências Biológicas",
    "CIENCIAS_DA_SAUDE": "Ciências da Saúde",
    "CIENCIAS_EXATAS_E_DA_TERRA": "Ciências Exatas e da Terra",
    "CIENCIAS_HUMANAS": "Ciências Humanas",
    "CIENCIAS_SOCIAIS_APLICADAS": "Ciências Sociais Aplicadas",
    "ENGENHARIAS": "Engenharias",
    "LINGUISTICA_LETRAS_E_ARTES": "Linguística, Letras e Artes",
    "OUTROS": "Outros",
}


def normalizar_grande_area(valor):
    if pd.isna(valor):
        return valor

    areas = [a.strip() for a in valor.split(";")]

    areas_normalizadas = [
        map_grande_area.get(a, a)
        for a in areas
    ]

    return "; ".join(areas_normalizadas)


df["grande_area"] = df["grande_area"].apply(normalizar_grande_area)

# 4. Na coluna uf_instituicao, trocar 'ZZ' por NULL (NaN)
df.loc[df["uf_instituicao"] == "ZZ", "uf_instituicao"] = pd.NA

# 5. Salvar no mesmo CSV
df.to_csv(input_file, index=False)
