from fastapi import FastAPI
from pydantic import BaseModel, constr, validator
import re

app = FastAPI()

# ---------------------------
# MODELO DE EMPRESA
# ---------------------------
class Empresa(BaseModel):
    numero: constr(min_length=5, max_length=5)  # exatamente 5 dígitos
    nome: str
    documento: constr(min_length=11, max_length=14)  # CPF (11) ou CNPJ (14)

    @validator("documento")
    def validar_documento(cls, v):
        # apenas números
        if not re.fullmatch(r"\d{11}|\d{14}", v):
            raise ValueError("Documento deve ter 11 (CPF) ou 14 (CNPJ) dígitos numéricos")
        return v

# Lista para armazenar empresas (por enquanto em memória)
empresas = []

# ---------------------------
# ROTAS
# ---------------------------

@app.get("/")
def read_root():
    return {"mensagem": "Olá, Wilton! Seu sistema está rodando 🎉"}

@app.post("/empresas")
def criar_empresa(empresa: Empresa):
    empresas.append(empresa)
    return {"mensagem": "Empresa cadastrada com sucesso!", "empresa": empresa}

@app.get("/empresas")
def listar_empresas():
    return empresas
