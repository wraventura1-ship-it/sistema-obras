from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = FastAPI()

# Configuração do CORS (ajuste o domínio do frontend no Render se quiser restringir)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # pode trocar por ["https://seu-frontend.onrender.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexão com o banco (Supabase usa Postgres)
def get_db_connection():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")
    return conn

# ----------------------
# MODELOS
# ----------------------
class Empresa(BaseModel):
    numero: str
    nome: str
    documento: str

class EmpresaDB(Empresa):
    id: str

class Obra(BaseModel):
    numero: str
    nome: str
    bloco: Optional[str]
    endereco: str

class ObraDB(Obra):
    id: str
    empresa_id: str

# ----------------------
# FUNÇÃO AUXILIAR: validar CNPJ
# ----------------------
def validar_cnpj(cnpj: str) -> bool:
    cnpj = ''.join(filter(str.isdigit, cnpj))
    if len(cnpj) != 14:
        return False
    if cnpj in (c * 14 for c in "1234567890"):
        return False

    def calcular_digito(cnpj_parcial, pesos):
        soma = sum(int(a) * b for a, b in zip(cnpj_parcial, pesos))
        resto = soma % 11
        return '0' if resto < 2 else str(11 - resto)

    primeiro = calcular_digito(cnpj[:12], list(range(5, 1, -1)) + list(range(9, 1, -1)))
    segundo = calcular_digito(cnpj[:12] + primeiro, list(range(6, 1, -1)) + list(range(9, 1, -1)))

    return cnpj[-2:] == primeiro + segundo

# ----------------------
# ROTAS EMPRESAS
# ----------------------

@app.get("/empresas", response_model=List[EmpresaDB])
def listar_empresas():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM empresas ORDER BY numero")
    empresas = cur.fetchall()
    cur.close()
    conn.close()
    return empresas

@app.post("/empresas", response_model=EmpresaDB)
def criar_empresa(emp: Empresa):
    if not validar_cnpj(emp.documento):
        raise HTTPException(status_code=400, detail="CNPJ inválido!")

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Verificar duplicidade de CNPJ
    cur.execute("SELECT * FROM empresas WHERE documento = %s", (emp.documento,))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Já existe uma empresa com este CNPJ.")

    cur.execute(
        "INSERT INTO empresas (numero, nome, documento) VALUES (%s, %s, %s) RETURNING *",
        (emp.numero.zfill(5), emp.nome.upper(), ''.join(filter(str.isdigit, emp.documento)))
    )
    nova = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return nova

@app.put("/empresas/{empresa_id}", response_model=EmpresaDB)
def atualizar_empresa(empresa_id: str, emp: Empresa):
    if not validar_cnpj(emp.documento):
        raise HTTPException(status_code=400, detail="CNPJ inválido!")

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute(
        "UPDATE empresas SET numero=%s, nome=%s, documento=%s WHERE id=%s RETURNING *",
        (emp.numero.zfill(5), emp.nome.upper(), ''.join(filter(str.isdigit, emp.documento)), empresa_id)
    )
    empresa_atualizada = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not empresa_atualizada:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    return empresa_atualizada

@app.delete("/empresas/{empresa_id}")
def excluir_empresa(empresa_id: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM empresas WHERE id = %s", (empresa_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"detail": "Empresa excluída com sucesso."}

# ----------------------
# ROTAS OBRAS
# ----------------------

@app.get("/empresas/{empresa_id}/obras", response_model=List[ObraDB])
def listar_obras(empresa_id: str):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM obras WHERE empresa_id = %s ORDER BY numero", (empresa_id,))
    obras = cur.fetchall()
    cur.close()
    conn.close()
    return obras

@app.post("/empresas/{empresa_id}/obras", response_model=ObraDB)
def criar_obra(empresa_id: str, obra: Obra):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Verificar duplicidade de número da obra dentro da empresa
    cur.execute("SELECT * FROM obras WHERE empresa_id = %s AND numero = %s", (empresa_id, obra.numero.zfill(4)))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Já existe uma obra com este número nesta empresa.")

    cur.execute(
        "INSERT INTO obras (empresa_id, numero, nome, bloco, endereco) VALUES (%s, %s, %s, %s, %s) RETURNING *",
        (empresa_id, obra.numero.zfill(4), obra.nome, obra.bloco, obra.endereco)
    )
    nova = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return nova

