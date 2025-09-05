from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, constr, validator
from supabase import create_client, Client
import re
import os

app = FastAPI()

# ---------------------------
# CORS
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # pode restringir para o frontend depois
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# MODELO
# ---------------------------
class Empresa(BaseModel):
    numero: constr(min_length=5, max_length=5)
    nome: str
    documento: constr(min_length=11, max_length=14)

    @validator("documento")
    def validar_documento(cls, v):
        if not re.fullmatch(r"\d{11}|\d{14}", v):
            raise ValueError("Documento deve ter 11 (CPF) ou 14 (CNPJ) dígitos numéricos")
        return v

# ---------------------------
# SUPABASE
# ---------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://syzkrbqvqiydopixiukk.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------
# ROTAS
# ---------------------------
@app.get("/")
def read_root():
    return {"mensagem": "Olá, Wilton! Seu sistema está rodando 🎉"}

@app.post("/empresas")
def criar_empresa(empresa: Empresa):
    try:
        print("📌 Tentando inserir:", empresa.dict())
        data, count = supabase.table("empresas").insert(empresa.dict()).execute()
        print("✅ Inserido no Supabase:", data)
        return {"mensagem": "Empresa cadastrada com sucesso!", "empresa": data}
    except Exception as e:
        print("❌ ERRO AO INSERIR:", str(e))
        return {"erro": str(e)}

@app.get("/empresas")
def listar_empresas():
    try:
        data, count = supabase.table("empresas").select("*").execute()
        return data
    except Exception as e:
        print("❌ ERRO AO LISTAR:", str(e))
        return {"erro": str(e)}
