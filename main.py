from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, constr, validator
from supabase import create_client, Client
import re
import os

app = FastAPI()

# ---------------------------
# HABILITAR CORS
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # depois podemos limitar para o frontend render
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# CONEXÃO SUPABASE
# ---------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://xxxxx.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "coloque_sua_anon_key_aqui")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------
# MODELO DE EMPRESA
# ---------------------------
class Empresa(BaseModel):
    numero: constr(min_length=5, max_length=5)
    nome: str
    documento: constr(min_length=11, max_length=14)

    @validator("documento")
    def validar_documento(cls, v):
        if not re.fullmatch(r"\d{11}|\d{14}", v):
            raise ValueError("Documento deve ter 11 (CPF) ou 14 (CNPJ) dígitos")
        return v

# ---------------------------
# ROTAS
# ---------------------------
@app.get("/")
def read_root():
    return {"mensagem": "Olá, Wilton! Agora conectado ao Supabase 🎉"}

@app.post("/empresas")
def criar_empresa(empresa: Empresa):
    response = supabase.table("empresas").insert({
        "numero": empresa.numero,
        "nome": empresa.nome,
        "documento": empresa.documento
    }).execute()
    return {"mensagem": "Empresa cadastrada com sucesso!", "data": response.data}

@app.get("/empresas")
def listar_empresas():
    response = supabase.table("empresas").select("*").execute()
    return response.data


app = FastAPI()

# ---------------------------
# HABILITAR CORS
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

