from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, constr, validator
from typing import Optional
from supabase import create_client, Client
from datetime import datetime
import re
import os

# ==========================
# FASTAPI + CORS
# ==========================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # depois podemos restringir só ao seu frontend do Render
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================
# SUPABASE (env no Render)
# ==========================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    # Não falha silenciosamente: ajuda a detectar variável faltando
    raise RuntimeError("Variáveis de ambiente SUPABASE_URL e SUPABASE_KEY são obrigatórias.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================
# MODELOS
# ==========================
class Empresa(BaseModel):
    numero: constr(min_length=5, max_length=5)   # 5 dígitos
    nome: str
    documento: constr(min_length=11, max_length=14)  # CPF(11) ou CNPJ(14), só dígitos

    @validator("numero")
    def validar_numero(cls, v):
        if not re.fullmatch(r"\d{5}", v):
            raise ValueError("Número da empresa deve ter exatamente 5 dígitos.")
        return v

    @validator("documento")
    def validar_documento(cls, v):
        if not re.fullmatch(r"\d{11}|\d{14}", v):
            raise ValueError("Documento deve ter 11 (CPF) ou 14 (CNPJ) dígitos numéricos.")
        return v

class EmpresaUpdate(BaseModel):
    # todos opcionais (para PUT parcial)
    numero: Optional[constr(min_length=5, max_length=5)] = None
    nome: Optional[str] = None
    documento: Optional[constr(min_length=11, max_length=14)] = None

    @validator("numero")
    def validar_numero(cls, v):
        if v is not None and not re.fullmatch(r"\d{5}", v):
            raise ValueError("Número da empresa deve ter exatamente 5 dígitos.")
        return v

    @validator("documento")
    def validar_documento(cls, v):
        if v is not None and not re.fullmatch(r"\d{11}|\d{14}", v):
            raise ValueError("Documento deve ter 11 (CPF) ou 14 (CNPJ) dígitos numéricos.")
        return v

# ==========================
# ROTAS
# ==========================
@app.get("/")
def read_root():
    return {"mensagem": "Olá, Wilton! Seu sistema está rodando 🎉"}

@app.get("/empresas")
def listar_empresas():
    try:
        response = supabase.table("empresas").select("*").order("created_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar empresas: {str(e)}")

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
        return {"mensagem": "Empresa cadastrada com sucesso!", "empresa": (response.data or [None])[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao cadastrar empresa: {str(e)}")

@app.put("/empresas/{id}")
def atualizar_empresa(id: str, payload: EmpresaUpdate):
    try:
        # monta apenas os campos enviados
        update_data = {k: v for k, v in payload.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="Nenhum campo para atualizar.")
        response = supabase.table("empresas").update(update_data).eq("id", id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Empresa não encontrada.")
        return {"mensagem": "Empresa atualizada com sucesso!", "empresa": response.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar empresa: {str(e)}")

@app.delete("/empresas/{id}")
def excluir_empresa(id: str):
    try:
        response = supabase.table("empresas").delete().eq("id", id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Empresa não encontrada.")
        return {"mensagem": "Empresa excluída com sucesso!"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir empresa: {str(e)}")

