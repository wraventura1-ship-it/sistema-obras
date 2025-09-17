from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
from asyncpg.exceptions import UniqueViolationError

app = FastAPI()

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # em produção coloque só o domínio do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# BANCO DE DADOS
# ==============================
DATABASE_URL = "postgresql://postgres:postgres@db.xxx.supabase.co:5432/postgres"  
# 👉 substitua pelo URL da sua instância do Supabase

async def get_db():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        await conn.close()

# ==============================
# EMPRESAS
# ==============================
@app.get("/empresas")
async def listar_empresas(conn=Depends(get_db)):
    rows = await conn.fetch("select * from empresas order by numero")
    return [dict(r) for r in rows]

@app.post("/empresas")
async def criar_empresa(empresa: dict, conn=Depends(get_db)):
    try:
        query = """
            insert into empresas (numero, nome, documento)
            values ($1, $2, $3)
            returning *;
        """
        row = await conn.fetchrow(query,
            empresa["numero"],
            empresa["nome"],
            empresa["documento"]
        )
        return dict(row)
    except UniqueViolationError:
        raise HTTPException(
            status_code=400,
            detail="Já existe uma empresa com esse número ou CNPJ."
        )

@app.put("/empresas/{empresa_id}")
async def atualizar_empresa(empresa_id: str, empresa: dict, conn=Depends(get_db)):
    try:
        query = """
            update empresas
            set numero=$1, nome=$2, documento=$3
            where id=$4
            returning *;
        """
        row = await conn.fetchrow(query,
            empresa["numero"],
            empresa["nome"],
            empresa["documento"],
            empresa_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Empresa não encontrada.")
        return dict(row)
    except UniqueViolationError:
        raise HTTPException(
            status_code=400,
            detail="Já existe uma empresa com esse número ou CNPJ."
        )

@app.delete("/empresas/{empresa_id}")
async def excluir_empresa(empresa_id: str, conn=Depends(get_db)):
    await conn.execute("delete from empresas where id=$1", empresa_id)
    return {"message": "Empresa excluída com sucesso"}

# ==============================
# OBRAS
# ==============================
@app.get("/empresas/{empresa_id}/obras")
async def listar_obras(empresa_id: str, conn=Depends(get_db)):
    rows = await conn.fetch(
        "select * from obras where empresa_id=$1 order by numero",
        empresa_id
    )
    return [dict(r) for r in rows]

@app.post("/empresas/{empresa_id}/obras")
async def criar_obra(empresa_id: str, obra: dict, conn=Depends(get_db)):
    try:
        query = """
            insert into obras (empresa_id, numero, nome, bloco, endereco)
            values ($1, $2, $3, $4, $5)
            returning *;
        """
        row = await conn.fetchrow(query,
            empresa_id,
            obra["numero"],
            obra["nome"],
            obra["bloco"],
            obra["endereco"]
        )
        return dict(row)
    except UniqueViolationError:
        raise HTTPException(
            status_code=400,
            detail="Já existe uma obra com esse número nesta empresa."
        )

@app.put("/obras/{obra_id}")
async def atualizar_obra(obra_id: str, obra: dict, conn=Depends(get_db)):
    try:
        query = """
            update obras
            set numero=$1, nome=$2, bloco=$3, endereco=$4
            where id=$5
            returning *;
        """
        row = await conn.fetchrow(query,
            obra["numero"],
            obra["nome"],
            obra["bloco"],
            obra["endereco"],
            obra_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Obra não encontrada.")
        return dict(row)
    except UniqueViolationError:
        raise HTTPException(
            status_code=400,
            detail="Já existe uma obra com esse número nesta empresa."
        )

@app.delete("/obras/{obra_id}")
async def excluir_obra(obra_id: str, conn=Depends(get_db)):
    await conn.execute("delete from obras where id=$1", obra_id)
    return {"message": "Obra excluída com sucesso"}
