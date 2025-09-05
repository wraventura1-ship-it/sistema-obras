from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, constr, validator
from supabase import create_client, Client
from datetime import datetime
import re
import os

# ==========================
# CONFIGURAÇÃO FASTAPI
# ==========================
app = FastAPI()

# Habilitar CORS (permite o frontend acessar)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # pode trocar por seu frontend no Render
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================
# CONFIGURAÇÃO SUPABASE
# ==========================
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://syzkrbqvqiydopixiukk.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "SEU_SUPABASE_KEY_AQUI")  # ⚠️ substitua pela sua
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================
# MODELO DE EMPRESA
# ==========================
class Empresa(BaseModel):
    numero: constr(min_length=5, max_length=5)  # exatamente 5 dígitos
    nome: str
    documento: constr(min_length=11, max_length=14)  # CPF (11) ou CNPJ (14)

    @validator("documento")
    def validar_documento(cls, v):
        if not re.fullmatch(r"\d{11}|\d{14}", v):
            raise ValueError("Documento deve ter 11 (CPF) ou 14 (CNPJ) dígitos numéricos")
        return v

# ==========================
# ROTAS
# ==========================

@app.get("/")
def read_root():
    return {"mensagem": "Olá, Wilton! Seu sistema está rodando 🎉"}

@app.post("/empresas")
def criar_empresa(empresa: Empresa):
    try:
        data = {
            "numero": empresa.numero,
            "nome": empresa.nome,
            "documento": empresa.documento,
            "created_at": datetime.utcnow().isoformat()
        }
        response = supabase.table("empresas").insert(data).execute()
        return {"mensagem": "Empresa cadastrada com sucesso!", "empresa": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao cadastrar empresa: {str(e)}")

@app.get("/empresas")
def listar_empresas():
    try:
        response = supabase.table("empresas").select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar empresas: {str(e)}")
