import sqlite3
import hashlib
import uuid
import os

def gerar_hash_senha(senha):
    """Criptografa a senha antes de salvar ou validar no banco."""
    return hashlib.sha256(senha.encode()).hexdigest()

def inicializar_banco_local():
    """Cria o banco SQLite e um usuário Admin padrão se não existir."""
    conn = sqlite3.connect('ecosol_local.db')
    cursor = conn.cursor()
    
    # Criação da tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id              TEXT PRIMARY KEY,
            nome            TEXT,
            login TEXT      UNIQUE,
            senha_hash      TEXT,
            nivel_acesso    TEXT,
            sincronizado    INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cadastros_ecosol (
            id                          TEXT PRIMARY KEY,
            tipo_cadastro               TEXT,
            razao_social_nome           TEXT, 
            endereco                    TEXT, 
            cep                         TEXT, 
            email                       TEXT, 
            cnpj                        TEXT, 
            cpf                         TEXT, 
            rg                          TEXT, 
            representante_legal         TEXT, 
            cor_raca                    TEXT,
            sexo                        TEXT,
            telefone                    TEXT,
            forma_organizacao_ecosol    TEXT, 
            forma_organizacao_emp       TEXT, 
            segmento_empreendimento     TEXT, 
            materia_prima               TEXT, 
            local_producao              TEXT, 
            onde_comercializa           TEXT, 
            beneficiarios_diretos_m     INTEGER, 
            beneficiarios_diretos_f     INTEGER, 
            beneficiarios_indiretos_m   INTEGER, 
            beneficiarios_indiretos_f   INTEGER, 
            maquina_cartao              TEXT, 
            pix                         TEXT, 
            classificacao_social        TEXT, 
            motivo_criacao              TEXT,
            formas_comercializacao      TEXT, 
            produtos_comercializados    TEXT, 
            pagam_taxa                  TEXT, 
            forma_contribuicao          TEXT, 
            renda_preponderante         TEXT, 
            para_quem_comercializa      TEXT, 
            dificuldade_comercializacao TEXT, 
            responsavel_vendas          TEXT, 
            obs                         TEXT, 
            local_cadastro              TEXT, 
            data_formulario             TEXT,
            data_cadastro               TEXT, 
            responsavel_id              TEXT, 
            sincronizado                INTEGER DEFAULT 0
        )
    ''')

    # Migração segura: adiciona a coluna 'sexo' se o banco já existia sem ela
    try:
        cursor.execute("ALTER TABLE cadastros_ecosol ADD COLUMN sexo TEXT")
    except sqlite3.OperationalError:
        pass  # Coluna já existe, tudo certo
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS arquivos_anexos (
            id TEXT         PRIMARY KEY, 
            cadastro_id     TEXT, 
            caminho_arquivo TEXT, 
            sincronizado    INTEGER DEFAULT 0
        )
    ''')
    
    # Injeta o Admin Padrão
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE login = 'admin'")
    if cursor.fetchone()[0] == 0:
        admin_id = str(uuid.uuid4())
        senha_padrao = gerar_hash_senha("123")
        cursor.execute("""
            INSERT INTO usuarios (id, nome, login, senha_hash, nivel_acesso, sincronizado)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (admin_id, "Administrador do Sistema", "admin", senha_padrao, "Admin", 0))
        
    conn.commit()
    conn.close()