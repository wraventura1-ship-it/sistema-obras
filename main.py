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
    raise RuntimeError("Variáveis de ambiente SUPABASE_URL e SUPABASE_KEY são obrigatórias.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================
# FUNÇÃO DE VALIDAÇÃO DE CNPJ
# ==========================
def is_valid_cnpj(cnpj: str) -> bool:
    c = re.sub(r"\D", "", cnpj)
    if len(c) != 14:
        return False
    if c == c[0] * 14:  # rejeita sequências repetidas
        return False

    def _calc(base: str) -> int:
        total = 0
        pos = len(base) - 7
        for ch in base:
            total += int(ch) * pos
            pos -= 1
            if pos < 2:
                pos = 9
        r = total % 11
        return 0 if r < 2 else 11 - r

    base = c[:12]
    dig1 = _calc(base)
    dig2 = _calc(base + str(dig1))
    return c.endswith(f"{dig1}{dig2}")

# ==========================
# MODELOS
# ==========================
class Empresa(BaseModel):
    numero: constr(min_length=1, max_length=5)   # aceito, normalizo depois
    nome: str
    documento: str  # será validado como CNPJ

    @validator("numero")
    def validar_numero(cls, v):
        if not re.fullmatch(r"\d{1,5}", v):
            raise ValueError("Número da empresa deve ter até 5 dígitos numéricos.")
        return v

    @validator("documento")
    def validar_documento(cls, v):
        digits = re.sub(r"\D", "", v)
        if len(digits) != 14:
            raise ValueError("Documento deve ter 14 dígitos (CNPJ).")
        if not is_valid_cnpj(digits):
            raise ValueError("CNPJ inválido.")
        return digits

class EmpresaUpdate(BaseModel):
    numero: Optional[constr(min_length=1, max_length=5)] = None
    nome: Optional[str] = None
    documento: Optional[str] = None

    @validator("numero")
    def validar_numero(cls, v):
        if v is not None and not re.fullmatch(r"\d{1,5}", v):
            raise ValueError("Número da empresa deve ter até 5 dígitos numéricos.")
        return v

    @validator("documento")
    def validar_documento(cls, v):
        if v is not None:
            digits = re.sub(r"\D", "", v)
            if len(digits) != 14:
                raise ValueError("Documento deve ter 14 dígitos (CNPJ).")
            if not is_valid_cnpj(digits):
                raise ValueError("CNPJ inválido.")
            return digits
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
        numero_norm = str(empresa.numero).zfill(5)
        nome_norm = empresa.nome.upper()
        documento_norm = re.sub(r"\D", "", empresa.documento)

        # checa duplicidade
        existing = supabase.table("empresas").select("id").eq("documento", documento_norm).execute()
        if existing.data and len(existing.data) > 0:
            raise HTTPException(status_code=400, detail="CNPJ já cadastrado.")

        data = {
            "numero": numero_norm,
            "nome": nome_norm,
            "documento": documento_norm,
            "created_at": datetime.utcnow().isoformat()
        }
        response = supabase.table("empresas").insert(data).execute()
        return {"mensagem": "Empresa cadastrada com sucesso!", "empresa": (response.data or [None])[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao cadastrar empresa: {str(e)}")

@app.put("/empresas/{id}")
def atualizar_empresa(id: str, payload: EmpresaUpdate):
    try:
        update_data = {k: v for k, v in payload.dict().items() if v is not None}

        if "numero" in update_data:
            update_data["numero"] = str(update_data["numero"]).zfill(5)

        if "nome" in update_data:
            update_data["nome"] = update_data["nome"].upper()

        if "documento" in update_data:
            doc_norm = re.sub(r"\D", "", update_data["documento"])
            if not is_valid_cnpj(doc_norm):
                raise HTTPException(status_code=400, detail="CNPJ inválido.")
            existing = supabase.table("empresas").select("id").eq("documento", doc_norm).execute()
            if existing.data:
                for row in existing.data:
                    if str(row.get("id")) != str(id):
                        raise HTTPException(status_code=400, detail="CNPJ já cadastrado por outra empresa.")
            update_data["documento"] = doc_norm

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
