from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui_muito_segura_2024'

# Configuração do banco de dados
DATABASE = 'rpg_fichas.db'

def init_db():
    """Inicializa o banco de dados com as tabelas necessárias"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Tabela de fichas (existente)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fichas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- INFORMAÇÕES BÁSICAS
            nome TEXT NOT NULL,
            tipo_corpo TEXT NOT NULL,
            classe TEXT NOT NULL,
            categoria TEXT NOT NULL,
            historia TEXT,
            elemento TEXT NOT NULL,
            ouro INTEGER DEFAULT 0,
            
            -- STATUS
            vida_atual INTEGER DEFAULT 10,
            vida_maxima INTEGER DEFAULT 10,
            mana_atual INTEGER DEFAULT 10,
            mana_maxima INTEGER DEFAULT 10,
            vigor_atual INTEGER DEFAULT 10,
            vigor_maximo INTEGER DEFAULT 10,
            sanidade_atual INTEGER DEFAULT 100,
            sanidade_maxima INTEGER DEFAULT 100,
            deslocamento INTEGER DEFAULT 0,
            resistencia INTEGER DEFAULT 5,
            armadura_fisica INTEGER DEFAULT 0,
            armadura_magica INTEGER DEFAULT 0,
            
            -- ATRIBUTOS
            forca INTEGER DEFAULT 0,
            destreza INTEGER DEFAULT 0,
            magia INTEGER DEFAULT 0,
            constituicao INTEGER DEFAULT 0,
            agilidade INTEGER DEFAULT 0,
            sabedoria INTEGER DEFAULT 0,
            carisma INTEGER DEFAULT 0,
            fe INTEGER DEFAULT 0,
            
            -- EQUIPAMENTOS
            armadura TEXT,
            arma TEXT,
            complemento TEXT,
            amuleto1 TEXT,
            amuleto2 TEXT,
            
            -- PROFICIÊNCIAS (0-5)
            prof_sobrevivencia INTEGER DEFAULT 0,
            prof_botanica INTEGER DEFAULT 0,
            prof_culinaria INTEGER DEFAULT 0,
            prof_religiao INTEGER DEFAULT 0,
            prof_pescaria INTEGER DEFAULT 0,
            prof_ferraria INTEGER DEFAULT 0,
            prof_artesanato INTEGER DEFAULT 0,
            prof_mixologia INTEGER DEFAULT 0,
            prof_musica INTEGER DEFAULT 0,
            prof_jogos_azar INTEGER DEFAULT 0,
            prof_rataria INTEGER DEFAULT 0,
            prof_navegacao INTEGER DEFAULT 0,
            prof_sacratismo INTEGER DEFAULT 0,
            prof_demonologia INTEGER DEFAULT 0,
            prof_guerra INTEGER DEFAULT 0,
            prof_acrobacia INTEGER DEFAULT 0,
            prof_combate_desarmado INTEGER DEFAULT 0,
            prof_armas_leves INTEGER DEFAULT 0,
            prof_armas_pesadas INTEGER DEFAULT 0,
            prof_armas_longa_distancia INTEGER DEFAULT 0,
            prof_arremesso INTEGER DEFAULT 0,
            
            -- PERÍCIAS MÁGICAS (0-5)
            per_maguslogia INTEGER DEFAULT 0,
            per_magia_elemental INTEGER DEFAULT 0,
            per_magia_obscura INTEGER DEFAULT 0,
            per_magia_estimulo INTEGER DEFAULT 0,
            per_magia_territorial INTEGER DEFAULT 0,
            
            -- RODA DE HABILIDADES
            habilidade_slot_1 INTEGER,
            habilidade_slot_2 INTEGER,
            habilidade_slot_3 INTEGER,
            habilidade_slot_4 INTEGER,
            habilidade_classe INTEGER,
            
            -- METADADOS
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de habilidades
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS habilidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ficha_id INTEGER NOT NULL,
            
            -- ESTRUTURA BÁSICA
            nome TEXT NOT NULL,
            nivel INTEGER NOT NULL CHECK(nivel >= 1 AND nivel <= 4),
            tipo_fisico_magico TEXT NOT NULL CHECK(tipo_fisico_magico IN ('FISICO', 'MAGICO')),
            tipo_ativacao TEXT NOT NULL CHECK(tipo_ativacao IN ('PASSIVA', 'ATIVA')),
            tipo_habilidade TEXT NOT NULL CHECK(tipo_habilidade IN ('Ataque', 'Defesa', 'Suporte', 'Terreno')),
            
            -- MECÂNICAS
            proficiencia TEXT NOT NULL,
            efeito TEXT NOT NULL,
            descricao TEXT NOT NULL,
            custo TEXT DEFAULT '',
            dt_atributo TEXT DEFAULT '',
            alcance TEXT DEFAULT '',
            
            -- ESPECÍFICO PARA MAGIAS
            eh_magia BOOLEAN DEFAULT 0,
            conjuracao TEXT DEFAULT '',
            elemento_magico TEXT DEFAULT '',
            
            -- METADADOS
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (ficha_id) REFERENCES fichas(id) ON DELETE CASCADE
        )
    ''')
    
    # Tabela de inventário
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ficha_id INTEGER NOT NULL,
            
            -- INFORMAÇÕES DO ITEM
            nome TEXT NOT NULL,
            descricao TEXT NOT NULL,
            categoria TEXT DEFAULT 'Geral',
            quantidade INTEGER DEFAULT 1,
            peso REAL DEFAULT 0.0,
            valor INTEGER DEFAULT 0,
            
            -- METADADOS
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (ficha_id) REFERENCES fichas(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado com sucesso!")

def atualizar_banco_habilidade_classe():
    """Adiciona o campo habilidade_classe na tabela fichas se não existir"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(fichas)")
        colunas = [coluna[1] for coluna in cursor.fetchall()]
        
        if 'habilidade_classe' not in colunas:
            # Adicionar a nova coluna
            cursor.execute('''
                ALTER TABLE fichas 
                ADD COLUMN habilidade_classe INTEGER
            ''')
            print("✅ Coluna 'habilidade_classe' adicionada com sucesso!")
        else:
            print("ℹ️ Coluna 'habilidade_classe' já existe.")
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ Erro ao atualizar banco: {e}")
    
    finally:
        conn.close()

def atualizar_banco_inventario():
    """Adiciona a tabela de inventário se não existir"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        # Verificar se a tabela já existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventario'")
        tabela_existe = cursor.fetchone()
        
        if not tabela_existe:
            # Criar a tabela de inventário
            cursor.execute('''
                CREATE TABLE inventario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ficha_id INTEGER NOT NULL,
                    
                    -- INFORMAÇÕES DO ITEM
                    nome TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    categoria TEXT DEFAULT 'Geral',
                    quantidade INTEGER DEFAULT 1,
                    peso REAL DEFAULT 0.0,
                    valor INTEGER DEFAULT 0,
                    
                    -- METADADOS
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (ficha_id) REFERENCES fichas(id) ON DELETE CASCADE
                )
            ''')
            print("✅ Tabela 'inventario' criada com sucesso!")
        else:
            print("ℹ️ Tabela 'inventario' já existe.")
        
        # Criar índices para melhor performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventario_ficha_id ON inventario(ficha_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventario_categoria ON inventario(categoria)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventario_nome ON inventario(nome)")
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ Erro ao atualizar banco para inventário: {e}")
    
    finally:
        conn.close()

def get_db_connection():
    """Retorna uma conexão com o banco de dados"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Página inicial com lista de fichas"""
    conn = get_db_connection()
    fichas = conn.execute('SELECT * FROM fichas ORDER BY nome').fetchall()
    conn.close()
    return render_template('index.html', fichas=fichas)

@app.route('/criar_ficha')
def criar_ficha():
    """Página para criar nova ficha"""
    return render_template('criar_ficha.html')

@app.route('/salvar_ficha', methods=['POST'])
def salvar_ficha():
    """Salva uma nova ficha no banco de dados"""
    dados = request.form
    
    # Validação básica
    campos_obrigatorios = ['nome', 'tipo_corpo', 'classe', 'categoria', 'elemento']
    for campo in campos_obrigatorios:
        if not dados.get(campo):
            flash(f'Campo obrigatório faltando: {campo}', 'error')
            return redirect(url_for('criar_ficha'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Função para obter valor seguro
        def get_safe_value(campo, default=0, tipo=int):
            try:
                valor = dados.get(campo, default)
                if valor == '' or valor is None:
                    return default
                return tipo(valor)
            except (ValueError, TypeError):
                return default
        
        # Função para obter texto seguro
        def get_safe_text(campo, default=''):
            valor = dados.get(campo, default)
            return valor if valor is not None else default
        
        cursor.execute('''
            INSERT INTO fichas (
                nome, tipo_corpo, classe, categoria, historia, elemento, ouro,
                vida_atual, vida_maxima, mana_atual, mana_maxima, 
                vigor_atual, vigor_maximo, sanidade_atual, sanidade_maxima,
                deslocamento, resistencia, armadura_fisica, armadura_magica,
                forca, destreza, magia, constituicao, agilidade, sabedoria, carisma, fe,
                armadura, arma, complemento, amuleto1, amuleto2,
                prof_sobrevivencia, prof_botanica, prof_culinaria, prof_religiao, prof_pescaria,
                prof_ferraria, prof_artesanato, prof_mixologia, prof_musica, prof_jogos_azar,
                prof_rataria, prof_navegacao, prof_sacratismo, prof_demonologia, prof_guerra,
                prof_acrobacia, prof_combate_desarmado, prof_armas_leves, prof_armas_pesadas,
                prof_armas_longa_distancia, prof_arremesso,
                per_maguslogia, per_magia_elemental, per_magia_obscura, per_magia_estimulo, per_magia_territorial
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            get_safe_text('nome'),
            get_safe_text('tipo_corpo'),
            get_safe_text('classe'),
            get_safe_text('categoria'),
            get_safe_text('historia', ''),
            get_safe_text('elemento'),
            get_safe_value('ouro', 0),
            get_safe_value('vida_atual', 10),
            get_safe_value('vida_maxima', 10),
            get_safe_value('mana_atual', 10),
            get_safe_value('mana_maxima', 10),
            get_safe_value('vigor_atual', 10),
            get_safe_value('vigor_maximo', 10),
            get_safe_value('sanidade_atual', 100),
            get_safe_value('sanidade_maxima', 100),
            get_safe_value('deslocamento', 0),
            get_safe_value('resistencia', 5),
            get_safe_value('armadura_fisica', 0),
            get_safe_value('armadura_magica', 0),
            get_safe_value('forca', 0),
            get_safe_value('destreza', 0),
            get_safe_value('magia', 0),
            get_safe_value('constituicao', 0),
            get_safe_value('agilidade', 0),
            get_safe_value('sabedoria', 0),
            get_safe_value('carisma', 0),
            get_safe_value('fe', 0),
            get_safe_text('armadura', ''),
            get_safe_text('arma', ''),
            get_safe_text('complemento', ''),
            get_safe_text('amuleto1', ''),
            get_safe_text('amuleto2', ''),
            get_safe_value('prof_sobrevivencia', 0),
            get_safe_value('prof_botanica', 0),
            get_safe_value('prof_culinaria', 0),
            get_safe_value('prof_religiao', 0),
            get_safe_value('prof_pescaria', 0),
            get_safe_value('prof_ferraria', 0),
            get_safe_value('prof_artesanato', 0),
            get_safe_value('prof_mixologia', 0),
            get_safe_value('prof_musica', 0),
            get_safe_value('prof_jogos_azar', 0),
            get_safe_value('prof_rataria', 0),
            get_safe_value('prof_navegacao', 0),
            get_safe_value('prof_sacratismo', 0),
            get_safe_value('prof_demonologia', 0),
            get_safe_value('prof_guerra', 0),
            get_safe_value('prof_acrobacia', 0),
            get_safe_value('prof_combate_desarmado', 0),
            get_safe_value('prof_armas_leves', 0),
            get_safe_value('prof_armas_pesadas', 0),
            get_safe_value('prof_armas_longa_distancia', 0),
            get_safe_value('prof_arremesso', 0),
            get_safe_value('per_maguslogia', 0),
            get_safe_value('per_magia_elemental', 0),
            0,  # per_magia_obscura sempre 0 (bloqueada)
            get_safe_value('per_magia_estimulo', 0),
            get_safe_value('per_magia_territorial', 0)
        ))
        
        conn.commit()
        flash('Ficha criada com sucesso!', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        print(f"Erro detalhado: {e}")
        flash(f'Erro ao criar ficha: {str(e)}', 'error')
        return redirect(url_for('criar_ficha'))
    
    finally:
        conn.close()

@app.route('/visualizar_ficha/<int:ficha_id>')
def visualizar_ficha(ficha_id):
    """Visualiza uma ficha específica"""
    conn = get_db_connection()
    
    try:
        ficha = conn.execute('SELECT * FROM fichas WHERE id = ?', (ficha_id,)).fetchone()
        
        if ficha is None:
            flash('Ficha não encontrada!', 'error')
            return redirect(url_for('index'))
        
        # Buscar habilidades da roda de habilidades (incluindo habilidade de classe)
        habilidades_roda = []
        for slot in ['habilidade_slot_1', 'habilidade_slot_2', 'habilidade_slot_3', 'habilidade_slot_4']:
            habilidade_id = ficha[slot]
            if habilidade_id:
                habilidade = conn.execute('SELECT * FROM habilidades WHERE id = ?', (habilidade_id,)).fetchone()
                if habilidade:
                    habilidades_roda.append(habilidade)
        
        # Buscar habilidade de classe
        habilidade_classe = None
        if ficha['habilidade_classe']:
            habilidade_classe = conn.execute('SELECT * FROM habilidades WHERE id = ?', (ficha['habilidade_classe'],)).fetchone()
        
        # Buscar todas as habilidades do personagem para seleção
        todas_habilidades = conn.execute('SELECT * FROM habilidades WHERE ficha_id = ? ORDER BY nome', (ficha_id,)).fetchall()
        
        # Buscar estatísticas do inventário
        stats_inventario = conn.execute('''
            SELECT 
                COUNT(*) as total_itens,
                COALESCE(SUM(peso * quantidade), 0) as peso_total,
                COALESCE(SUM(valor * quantidade), 0) as valor_total
            FROM inventario 
            WHERE ficha_id = ?
        ''', (ficha_id,)).fetchone()
        
        return render_template('visualizar_ficha.html', 
                             ficha=ficha, 
                             habilidades_roda=habilidades_roda, 
                             habilidade_classe=habilidade_classe,
                             todas_habilidades=todas_habilidades,
                             stats_inventario=stats_inventario)
        
    except Exception as e:
        print(f"Erro ao visualizar ficha: {e}")
        flash(f'Erro ao carregar ficha: {str(e)}', 'error')
        return redirect(url_for('index'))
    
    finally:
        conn.close()

@app.route('/editar_ficha/<int:ficha_id>')
def editar_ficha(ficha_id):
    """Página para editar uma ficha existente"""
    conn = get_db_connection()
    
    try:
        ficha = conn.execute('SELECT * FROM fichas WHERE id = ?', (ficha_id,)).fetchone()
        
        if ficha is None:
            flash('Ficha não encontrada!', 'error')
            return redirect(url_for('index'))
        
        return render_template('editar_ficha.html', ficha=ficha)
        
    except Exception as e:
        print(f"Erro ao carregar ficha para edição: {e}")
        flash(f'Erro ao carregar ficha: {str(e)}', 'error')
        return redirect(url_for('index'))
    
    finally:
        conn.close()

@app.route('/atualizar_ficha/<int:ficha_id>', methods=['POST'])
def atualizar_ficha(ficha_id):
    """Atualiza uma ficha existente"""
    dados = request.form
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Função para obter valor seguro
        def get_safe_value(campo, default=0, tipo=int):
            try:
                valor = dados.get(campo, default)
                if valor == '' or valor is None:
                    return default
                return tipo(valor)
            except (ValueError, TypeError):
                return default
        
        # Função para obter texto seguro
        def get_safe_text(campo, default=''):
            valor = dados.get(campo, default)
            return valor if valor is not None else default
        
        cursor.execute('''
            UPDATE fichas SET
                nome = ?, tipo_corpo = ?, classe = ?, categoria = ?, historia = ?, elemento = ?, ouro = ?,
                vida_atual = ?, vida_maxima = ?, mana_atual = ?, mana_maxima = ?,
                vigor_atual = ?, vigor_maximo = ?, sanidade_atual = ?, sanidade_maxima = ?,
                deslocamento = ?, resistencia = ?, armadura_fisica = ?, armadura_magica = ?,
                forca = ?, destreza = ?, magia = ?, constituicao = ?, agilidade = ?, sabedoria = ?, carisma = ?, fe = ?,
                armadura = ?, arma = ?, complemento = ?, amuleto1 = ?, amuleto2 = ?,
                prof_sobrevivencia = ?, prof_botanica = ?, prof_culinaria = ?, prof_religiao = ?, prof_pescaria = ?,
                prof_ferraria = ?, prof_artesanato = ?, prof_mixologia = ?, prof_musica = ?, prof_jogos_azar = ?,
                prof_rataria = ?, prof_navegacao = ?, prof_sacratismo = ?, prof_demonologia = ?, prof_guerra = ?,
                prof_acrobacia = ?, prof_combate_desarmado = ?, prof_armas_leves = ?, prof_armas_pesadas = ?,
                prof_armas_longa_distancia = ?, prof_arremesso = ?,
                per_maguslogia = ?, per_magia_elemental = ?, per_magia_obscura = ?, per_magia_estimulo = ?, per_magia_territorial = ?,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            get_safe_text('nome'),
            get_safe_text('tipo_corpo'),
            get_safe_text('classe'),
            get_safe_text('categoria'),
            get_safe_text('historia'),
            get_safe_text('elemento'),
            get_safe_value('ouro'),
            get_safe_value('vida_atual', 10),
            get_safe_value('vida_maxima', 10),
            get_safe_value('mana_atual', 10),
            get_safe_value('mana_maxima', 10),
            get_safe_value('vigor_atual', 10),
            get_safe_value('vigor_maximo', 10),
            get_safe_value('sanidade_atual', 100),
            get_safe_value('sanidade_maxima', 100),
            get_safe_value('deslocamento'),
            get_safe_value('resistencia', 5),
            get_safe_value('armadura_fisica'),
            get_safe_value('armadura_magica'),
            get_safe_value('forca'),
            get_safe_value('destreza'),
            get_safe_value('magia'),
            get_safe_value('constituicao'),
            get_safe_value('agilidade'),
            get_safe_value('sabedoria'),
            get_safe_value('carisma'),
            get_safe_value('fe'),
            get_safe_text('armadura'),
            get_safe_text('arma'),
            get_safe_text('complemento'),
            get_safe_text('amuleto1'),
            get_safe_text('amuleto2'),
            get_safe_value('prof_sobrevivencia'),
            get_safe_value('prof_botanica'),
            get_safe_value('prof_culinaria'),
            get_safe_value('prof_religiao'),
            get_safe_value('prof_pescaria'),
            get_safe_value('prof_ferraria'),
            get_safe_value('prof_artesanato'),
            get_safe_value('prof_mixologia'),
            get_safe_value('prof_musica'),
            get_safe_value('prof_jogos_azar'),
            get_safe_value('prof_rataria'),
            get_safe_value('prof_navegacao'),
            get_safe_value('prof_sacratismo'),
            get_safe_value('prof_demonologia'),
            get_safe_value('prof_guerra'),
            get_safe_value('prof_acrobacia'),
            get_safe_value('prof_combate_desarmado'),
            get_safe_value('prof_armas_leves'),
            get_safe_value('prof_armas_pesadas'),
            get_safe_value('prof_armas_longa_distancia'),
            get_safe_value('prof_arremesso'),
            get_safe_value('per_maguslogia'),
            get_safe_value('per_magia_elemental'),
            0,  # per_magia_obscura sempre 0
            get_safe_value('per_magia_estimulo'),
            get_safe_value('per_magia_territorial'),
            ficha_id
        ))
        
        conn.commit()
        flash('Ficha atualizada com sucesso!', 'success')
        return redirect(url_for('visualizar_ficha', ficha_id=ficha_id))
        
    except Exception as e:
        print(f"Erro ao atualizar ficha: {e}")
        flash(f'Erro ao atualizar ficha: {str(e)}', 'error')
        return redirect(url_for('editar_ficha', ficha_id=ficha_id))
    
    finally:
        conn.close()

@app.route('/deletar_ficha/<int:ficha_id>', methods=['POST'])
def deletar_ficha(ficha_id):
    """Deleta uma ficha"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Deletar habilidades primeiro (por causa da foreign key)
        cursor.execute('DELETE FROM habilidades WHERE ficha_id = ?', (ficha_id,))
        # Deletar itens do inventário
        cursor.execute('DELETE FROM inventario WHERE ficha_id = ?', (ficha_id,))
        # Deletar a ficha
        cursor.execute('DELETE FROM fichas WHERE id = ?', (ficha_id,))
        conn.commit()
        flash('Ficha deletada com sucesso!', 'success')
        
    except Exception as e:
        print(f"Erro ao deletar ficha: {e}")
        flash(f'Erro ao deletar ficha: {str(e)}', 'error')
    
    finally:
        conn.close()
    
    return redirect(url_for('index'))

# === ROTAS PARA HABILIDADES ===

@app.route('/habilidades/<int:ficha_id>')
def gerenciar_habilidades(ficha_id):
    """Página para gerenciar habilidades de uma ficha"""
    conn = get_db_connection()
    
    try:
        # Buscar a ficha
        ficha = conn.execute('SELECT * FROM fichas WHERE id = ?', (ficha_id,)).fetchone()
        if ficha is None:
            flash('Ficha não encontrada!', 'error')
            return redirect(url_for('index'))
        
        # Buscar todas as habilidades desta ficha
        habilidades = conn.execute('SELECT * FROM habilidades WHERE ficha_id = ? ORDER BY nome', (ficha_id,)).fetchall()
        
        print(f"Debug: Encontradas {len(habilidades)} habilidades para ficha {ficha_id}")
        
        return render_template('gerenciar_habilidades.html', ficha=ficha, habilidades=habilidades)
        
    except Exception as e:
        print(f"Erro ao gerenciar habilidades: {e}")
        flash(f'Erro ao carregar habilidades: {str(e)}', 'error')
        return redirect(url_for('visualizar_ficha', ficha_id=ficha_id))
    
    finally:
        conn.close()

@app.route('/criar_habilidade/<int:ficha_id>')
def criar_habilidade(ficha_id):
    """Página para criar nova habilidade"""
    conn = get_db_connection()
    
    try:
        ficha = conn.execute('SELECT * FROM fichas WHERE id = ?', (ficha_id,)).fetchone()
        
        if ficha is None:
            flash('Ficha não encontrada!', 'error')
            return redirect(url_for('index'))
        
        return render_template('criar_habilidade.html', ficha=ficha)
        
    except Exception as e:
        print(f"Erro ao carregar página criar habilidade: {e}")
        flash(f'Erro ao carregar página: {str(e)}', 'error')
        return redirect(url_for('gerenciar_habilidades', ficha_id=ficha_id))
    
    finally:
        conn.close()

@app.route('/salvar_habilidade/<int:ficha_id>', methods=['POST'])
def salvar_habilidade(ficha_id):
    """Salva uma nova habilidade"""
    dados = request.form
    
    # Debug
    print(f"Debug: Salvando habilidade para ficha {ficha_id}")
    print(f"Debug: Dados recebidos: {dict(dados)}")
    
    # Validação básica
    campos_obrigatorios = ['nome', 'nivel', 'tipo_fisico_magico', 'tipo_ativacao', 'tipo_habilidade', 'proficiencia', 'efeito', 'descricao']
    for campo in campos_obrigatorios:
        if not dados.get(campo):
            flash(f'Campo obrigatório faltando: {campo}', 'error')
            return redirect(url_for('criar_habilidade', ficha_id=ficha_id))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar se a ficha existe
        ficha = conn.execute('SELECT id FROM fichas WHERE id = ?', (ficha_id,)).fetchone()
        if not ficha:
            flash('Ficha não encontrada!', 'error')
            return redirect(url_for('index'))
        
        eh_magia = dados.get('eh_magia') == 'on'
        
        cursor.execute('''
            INSERT INTO habilidades (
                ficha_id, nome, nivel, tipo_fisico_magico, tipo_ativacao, tipo_habilidade,
                proficiencia, efeito, descricao, custo, dt_atributo, alcance,
                eh_magia, conjuracao, elemento_magico
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ficha_id,
            dados.get('nome').strip(),
            int(dados.get('nivel')),
            dados.get('tipo_fisico_magico'),
            dados.get('tipo_ativacao'),
            dados.get('tipo_habilidade'),
            dados.get('proficiencia'),
            dados.get('efeito').strip(),
            dados.get('descricao').strip(),
            dados.get('custo', '').strip(),
            dados.get('dt_atributo', '').strip(),
            dados.get('alcance', '').strip(),
            eh_magia,
            dados.get('conjuracao', '').strip() if eh_magia else '',
            dados.get('elemento_magico', '') if eh_magia else ''
        ))
        
        conn.commit()
        print(f"Debug: Habilidade criada com sucesso! ID: {cursor.lastrowid}")
        flash('Habilidade criada com sucesso!', 'success')
        return redirect(url_for('gerenciar_habilidades', ficha_id=ficha_id))
        
    except Exception as e:
        print(f"Erro ao criar habilidade: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Erro ao criar habilidade: {str(e)}', 'error')
        return redirect(url_for('criar_habilidade', ficha_id=ficha_id))
    
    finally:
        conn.close()

@app.route('/editar_habilidade/<int:habilidade_id>')
def editar_habilidade(habilidade_id):
    """Página para editar habilidade"""
    conn = get_db_connection()
    
    try:
        habilidade = conn.execute('SELECT * FROM habilidades WHERE id = ?', (habilidade_id,)).fetchone()
        
        if habilidade is None:
            flash('Habilidade não encontrada!', 'error')
            return redirect(url_for('index'))
        
        ficha = conn.execute('SELECT * FROM fichas WHERE id = ?', (habilidade['ficha_id'],)).fetchone()
        
        if ficha is None:
            flash('Ficha não encontrada!', 'error')
            return redirect(url_for('index'))
        
        return render_template('editar_habilidade.html', habilidade=habilidade, ficha=ficha)
        
    except Exception as e:
        print(f"Erro ao carregar habilidade para edição: {e}")
        flash(f'Erro ao carregar habilidade: {str(e)}', 'error')
        return redirect(url_for('index'))
    
    finally:
        conn.close()

@app.route('/atualizar_habilidade/<int:habilidade_id>', methods=['POST'])
def atualizar_habilidade(habilidade_id):
    """Atualiza uma habilidade existente"""
    dados = request.form
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        habilidade = conn.execute('SELECT ficha_id FROM habilidades WHERE id = ?', (habilidade_id,)).fetchone()
        if not habilidade:
            flash('Habilidade não encontrada!', 'error')
            return redirect(url_for('index'))
        
        ficha_id = habilidade['ficha_id']
        eh_magia = dados.get('eh_magia') == 'on'
        
        cursor.execute('''
            UPDATE habilidades SET
                nome = ?, nivel = ?, tipo_fisico_magico = ?, tipo_ativacao = ?, tipo_habilidade = ?,
                proficiencia = ?, efeito = ?, descricao = ?, custo = ?, dt_atributo = ?, alcance = ?,
                eh_magia = ?, conjuracao = ?, elemento_magico = ?, atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            dados.get('nome').strip(),
            int(dados.get('nivel')),
            dados.get('tipo_fisico_magico'),
            dados.get('tipo_ativacao'),
            dados.get('tipo_habilidade'),
            dados.get('proficiencia'),
            dados.get('efeito').strip(),
            dados.get('descricao').strip(),
            dados.get('custo', '').strip(),
            dados.get('dt_atributo', '').strip(),
            dados.get('alcance', '').strip(),
            eh_magia,
            dados.get('conjuracao', '').strip() if eh_magia else '',
            dados.get('elemento_magico', '') if eh_magia else '',
            habilidade_id
        ))
        
        conn.commit()
        flash('Habilidade atualizada com sucesso!', 'success')
        return redirect(url_for('gerenciar_habilidades', ficha_id=ficha_id))
        
    except Exception as e:
        print(f"Erro ao atualizar habilidade: {e}")
        flash(f'Erro ao atualizar habilidade: {str(e)}', 'error')
        return redirect(url_for('editar_habilidade', habilidade_id=habilidade_id))
    
    finally:
        conn.close()

@app.route('/deletar_habilidade/<int:habilidade_id>', methods=['POST'])
def deletar_habilidade(habilidade_id):
    """Deleta uma habilidade"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Buscar ficha_id antes de deletar
        habilidade = conn.execute('SELECT ficha_id FROM habilidades WHERE id = ?', (habilidade_id,)).fetchone()
        if not habilidade:
            flash('Habilidade não encontrada!', 'error')
            return redirect(url_for('index'))
        
        ficha_id = habilidade['ficha_id']
        
        # Remover habilidade dos slots da roda de habilidades (incluindo habilidade de classe)
        cursor.execute('''
            UPDATE fichas SET
                habilidade_slot_1 = CASE WHEN habilidade_slot_1 = ? THEN NULL ELSE habilidade_slot_1 END,
                habilidade_slot_2 = CASE WHEN habilidade_slot_2 = ? THEN NULL ELSE habilidade_slot_2 END,
                habilidade_slot_3 = CASE WHEN habilidade_slot_3 = ? THEN NULL ELSE habilidade_slot_3 END,
                habilidade_slot_4 = CASE WHEN habilidade_slot_4 = ? THEN NULL ELSE habilidade_slot_4 END,
                habilidade_classe = CASE WHEN habilidade_classe = ? THEN NULL ELSE habilidade_classe END
            WHERE id = ?
        ''', (habilidade_id, habilidade_id, habilidade_id, habilidade_id, habilidade_id, ficha_id))
        
        # Deletar a habilidade
        cursor.execute('DELETE FROM habilidades WHERE id = ?', (habilidade_id,))
        conn.commit()
        flash('Habilidade deletada com sucesso!', 'success')
        return redirect(url_for('gerenciar_habilidades', ficha_id=ficha_id))
        
    except Exception as e:
        print(f"Erro ao deletar habilidade: {e}")
        flash(f'Erro ao deletar habilidade: {str(e)}', 'error')
        return redirect(url_for('gerenciar_habilidades', ficha_id=ficha_id))
    
    finally:
        conn.close()

@app.route('/atualizar_roda_habilidades/<int:ficha_id>', methods=['POST'])
def atualizar_roda_habilidades(ficha_id):
    """Atualiza as habilidades selecionadas na roda de habilidades"""
    dados = request.form
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Função para obter ID da habilidade ou None
        def get_habilidade_id(slot):
            valor = dados.get(slot)
            return int(valor) if valor and valor != '' else None
        
        cursor.execute('''
            UPDATE fichas SET
                habilidade_slot_1 = ?,
                habilidade_slot_2 = ?,
                habilidade_slot_3 = ?,
                habilidade_slot_4 = ?,
                habilidade_classe = ?,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            get_habilidade_id('habilidade_slot_1'),
            get_habilidade_id('habilidade_slot_2'),
            get_habilidade_id('habilidade_slot_3'),
            get_habilidade_id('habilidade_slot_4'),
            get_habilidade_id('habilidade_classe'),
            ficha_id
        ))
        
        conn.commit()
        flash('Roda de habilidades atualizada com sucesso!', 'success')
        
    except Exception as e:
        print(f"Erro ao atualizar roda de habilidades: {e}")
        flash(f'Erro ao atualizar roda de habilidades: {str(e)}', 'error')
    
    finally:
        conn.close()
    
    return redirect(url_for('visualizar_ficha', ficha_id=ficha_id))

# === ROTAS PARA INVENTÁRIO ===

@app.route('/inventario/<int:ficha_id>')
def gerenciar_inventario(ficha_id):
    """Página para gerenciar inventário de uma ficha"""
    conn = get_db_connection()
    
    try:
        # Buscar a ficha
        ficha = conn.execute('SELECT * FROM fichas WHERE id = ?', (ficha_id,)).fetchone()
        if ficha is None:
            flash('Ficha não encontrada!', 'error')
            return redirect(url_for('index'))
        
        # Buscar todos os itens do inventário
        itens = conn.execute('''
            SELECT * FROM inventario 
            WHERE ficha_id = ? 
            ORDER BY categoria, nome
        ''', (ficha_id,)).fetchall()
        
        # Calcular estatísticas
        total_itens = len(itens)
        peso_total = sum(item['peso'] * item['quantidade'] for item in itens)
        valor_total = sum(item['valor'] * item['quantidade'] for item in itens)
        
        estatisticas = {
            'total_itens': total_itens,
            'peso_total': peso_total,
            'valor_total': valor_total
        }
        
        return render_template('gerenciar_inventario.html', 
                             ficha=ficha, 
                             itens=itens,
                             estatisticas=estatisticas)
        
    except Exception as e:
        print(f"Erro ao gerenciar inventário: {e}")
        flash(f'Erro ao carregar inventário: {str(e)}', 'error')
        return redirect(url_for('visualizar_ficha', ficha_id=ficha_id))
    
    finally:
        conn.close()

@app.route('/criar_item/<int:ficha_id>')
def criar_item(ficha_id):
    """Página para criar novo item"""
    conn = get_db_connection()
    
    try:
        ficha = conn.execute('SELECT * FROM fichas WHERE id = ?', (ficha_id,)).fetchone()
        
        if ficha is None:
            flash('Ficha não encontrada!', 'error')
            return redirect(url_for('index'))
        
        return render_template('criar_item.html', ficha=ficha)
        
    except Exception as e:
        print(f"Erro ao carregar página criar item: {e}")
        flash(f'Erro ao carregar página: {str(e)}', 'error')
        return redirect(url_for('gerenciar_inventario', ficha_id=ficha_id))
    
    finally:
        conn.close()

@app.route('/salvar_item/<int:ficha_id>', methods=['POST'])
def salvar_item(ficha_id):
    """Salva um novo item no inventário"""
    dados = request.form
    
    # Validação básica
    if not dados.get('nome') or not dados.get('descricao'):
        flash('Nome e descrição são obrigatórios!', 'error')
        return redirect(url_for('criar_item', ficha_id=ficha_id))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar se a ficha existe
        ficha = conn.execute('SELECT id FROM fichas WHERE id = ?', (ficha_id,)).fetchone()
        if not ficha:
            flash('Ficha não encontrada!', 'error')
            return redirect(url_for('index'))
        
        # Função para obter valor seguro
        def get_safe_value(campo, default=0, tipo=int):
            try:
                valor = dados.get(campo, default)
                if valor == '' or valor is None:
                    return default
                return tipo(valor)
            except (ValueError, TypeError):
                return default
        
        def get_safe_text(campo, default=''):
            valor = dados.get(campo, default)
            return valor.strip() if valor is not None else default
        
        cursor.execute('''
            INSERT INTO inventario (
                ficha_id, nome, descricao, categoria, quantidade, peso, valor
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            ficha_id,
            get_safe_text('nome'),
            get_safe_text('descricao'),
            get_safe_text('categoria', 'Geral'),
            get_safe_value('quantidade', 1),
            get_safe_value('peso', 0.0, float),
            get_safe_value('valor', 0)
        ))
        
        conn.commit()
        flash('Item adicionado ao inventário com sucesso!', 'success')
        return redirect(url_for('gerenciar_inventario', ficha_id=ficha_id))
        
    except Exception as e:
        print(f"Erro ao criar item: {e}")
        flash(f'Erro ao criar item: {str(e)}', 'error')
        return redirect(url_for('criar_item', ficha_id=ficha_id))
    
    finally:
        conn.close()

@app.route('/editar_item/<int:item_id>')
def editar_item(item_id):
    """Página para editar item"""
    conn = get_db_connection()
    
    try:
        item = conn.execute('SELECT * FROM inventario WHERE id = ?', (item_id,)).fetchone()
        
        if item is None:
            flash('Item não encontrado!', 'error')
            return redirect(url_for('index'))
        
        ficha = conn.execute('SELECT * FROM fichas WHERE id = ?', (item['ficha_id'],)).fetchone()
        
        if ficha is None:
            flash('Ficha não encontrada!', 'error')
            return redirect(url_for('index'))
        
        return render_template('editar_item.html', item=item, ficha=ficha)
        
    except Exception as e:
        print(f"Erro ao carregar item para edição: {e}")
        flash(f'Erro ao carregar item: {str(e)}', 'error')
        return redirect(url_for('index'))
    
    finally:
        conn.close()

@app.route('/atualizar_item/<int:item_id>', methods=['POST'])
def atualizar_item(item_id):
    """Atualiza um item existente"""
    dados = request.form
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        item = conn.execute('SELECT ficha_id FROM inventario WHERE id = ?', (item_id,)).fetchone()
        if not item:
            flash('Item não encontrado!', 'error')
            return redirect(url_for('index'))
        
        ficha_id = item['ficha_id']
        
        # Função para obter valor seguro
        def get_safe_value(campo, default=0, tipo=int):
            try:
                valor = dados.get(campo, default)
                if valor == '' or valor is None:
                    return default
                return tipo(valor)
            except (ValueError, TypeError):
                return default
        
        def get_safe_text(campo, default=''):
            valor = dados.get(campo, default)
            return valor.strip() if valor is not None else default
        
        cursor.execute('''
            UPDATE inventario SET
                nome = ?, descricao = ?, categoria = ?, quantidade = ?, 
                peso = ?, valor = ?, atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            get_safe_text('nome'),
            get_safe_text('descricao'),
            get_safe_text('categoria', 'Geral'),
            get_safe_value('quantidade', 1),
            get_safe_value('peso', 0.0, float),
            get_safe_value('valor', 0),
            item_id
        ))
        
        conn.commit()
        flash('Item atualizado com sucesso!', 'success')
        return redirect(url_for('gerenciar_inventario', ficha_id=ficha_id))
        
    except Exception as e:
        print(f"Erro ao atualizar item: {e}")
        flash(f'Erro ao atualizar item: {str(e)}', 'error')
        return redirect(url_for('editar_item', item_id=item_id))
    
    finally:
        conn.close()

@app.route('/deletar_item/<int:item_id>', methods=['POST'])
def deletar_item(item_id):
    """Deleta um item do inventário"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Buscar ficha_id antes de deletar
        item = conn.execute('SELECT ficha_id FROM inventario WHERE id = ?', (item_id,)).fetchone()
        if not item:
            flash('Item não encontrado!', 'error')
            return redirect(url_for('index'))
        
        ficha_id = item['ficha_id']
        
        # Deletar o item
        cursor.execute('DELETE FROM inventario WHERE id = ?', (item_id,))
        conn.commit()
        flash('Item removido do inventário com sucesso!', 'success')
        return redirect(url_for('gerenciar_inventario', ficha_id=ficha_id))
        
    except Exception as e:
        print(f"Erro ao deletar item: {e}")
        flash(f'Erro ao deletar item: {str(e)}', 'error')
        return redirect(url_for('gerenciar_inventario', ficha_id=ficha_id))
    
    finally:
        conn.close()

# === APIs ===

# APIs para atualizações rápidas
@app.route('/api/atualizar_status', methods=['POST'])
def atualizar_status():
    """API para atualizar status rapidamente"""
    dados = request.json
    ficha_id = dados.get('ficha_id')
    campo = dados.get('campo')
    valor = dados.get('valor')
    
    # Campos permitidos para atualização
    campos_permitidos = [
        'vida_atual', 'mana_atual', 'vigor_atual', 'sanidade_atual',
        'armadura_fisica', 'armadura_magica', 'ouro'
    ]
    
    if campo not in campos_permitidos:
        return jsonify({'success': False, 'error': 'Campo não permitido'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            f'UPDATE fichas SET {campo} = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?',
            (valor, ficha_id)
        )
        conn.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Erro ao atualizar status: {e}")
        return jsonify({'success': False, 'error': str(e)})
    
    finally:
        conn.close()

# API para estatísticas do inventário
@app.route('/api/inventario_stats/<int:ficha_id>')
def api_inventario_stats(ficha_id):
    """API para obter estatísticas do inventário de uma ficha"""
    conn = get_db_connection()
    
    try:
        # Verificar se a ficha existe
        ficha = conn.execute('SELECT id FROM fichas WHERE id = ?', (ficha_id,)).fetchone()
        if not ficha:
            return jsonify({'success': False, 'error': 'Ficha não encontrada'})
        
        # Buscar estatísticas do inventário
        stats = conn.execute('''
            SELECT 
                COUNT(*) as total_itens,
                COALESCE(SUM(quantidade), 0) as quantidade_total,
                COALESCE(SUM(peso * quantidade), 0) as peso_total,
                COALESCE(SUM(valor * quantidade), 0) as valor_total
            FROM inventario 
            WHERE ficha_id = ?
        ''', (ficha_id,)).fetchone()
        
        # Buscar distribuição por categoria
        categorias = conn.execute('''
            SELECT categoria, COUNT(*) as count, SUM(quantidade) as quantidade
            FROM inventario 
            WHERE ficha_id = ? 
            GROUP BY categoria 
            ORDER BY count DESC
        ''', (ficha_id,)).fetchall()
        
        # Buscar itens mais valiosos
        itens_valiosos = conn.execute('''
            SELECT nome, valor, quantidade, (valor * quantidade) as valor_total
            FROM inventario 
            WHERE ficha_id = ? AND valor > 0
            ORDER BY valor_total DESC 
            LIMIT 5
        ''', (ficha_id,)).fetchall()
        
        resultado = {
            'success': True,
            'stats': {
                'total_itens': stats['total_itens'],
                'quantidade_total': stats['quantidade_total'],
                'peso_total': float(stats['peso_total']),
                'valor_total': stats['valor_total']
            },
            'categorias': [
                {
                    'categoria': cat['categoria'],
                    'count': cat['count'],
                    'quantidade': cat['quantidade']
                } for cat in categorias
            ],
            'itens_valiosos': [
                {
                    'nome': item['nome'],
                    'valor_unitario': item['valor'],
                    'quantidade': item['quantidade'],
                    'valor_total': item['valor_total']
                } for item in itens_valiosos
            ]
        }
        
        return jsonify(resultado)
        
    except Exception as e:
        print(f"Erro ao buscar estatísticas do inventário: {e}")
        return jsonify({'success': False, 'error': str(e)})
    
    finally:
        conn.close()

# API para operações rápidas no inventário
@app.route('/api/inventario_acao', methods=['POST'])
def api_inventario_acao():
    """API para ações rápidas no inventário (aumentar/diminuir quantidade, etc.)"""
    dados = request.json
    acao = dados.get('acao')
    item_id = dados.get('item_id')
    
    if not acao or not item_id:
        return jsonify({'success': False, 'error': 'Ação e ID do item são obrigatórios'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar se o item existe
        item = conn.execute('SELECT * FROM inventario WHERE id = ?', (item_id,)).fetchone()
        if not item:
            return jsonify({'success': False, 'error': 'Item não encontrado'})
        
        if acao == 'aumentar_quantidade':
            nova_quantidade = item['quantidade'] + 1
            cursor.execute(
                'UPDATE inventario SET quantidade = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?',
                (nova_quantidade, item_id)
            )
            
        elif acao == 'diminuir_quantidade':
            nova_quantidade = max(1, item['quantidade'] - 1)  # Mínimo 1
            cursor.execute(
                'UPDATE inventario SET quantidade = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?',
                (nova_quantidade, item_id)
            )
            
        elif acao == 'definir_quantidade':
            quantidade = dados.get('quantidade', 1)
            quantidade = max(1, int(quantidade))  # Mínimo 1
            cursor.execute(
                'UPDATE inventario SET quantidade = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?',
                (quantidade, item_id)
            )
            
        else:
            return jsonify({'success': False, 'error': 'Ação não reconhecida'})
        
        conn.commit()
        
        # Buscar item atualizado
        item_atualizado = conn.execute('SELECT * FROM inventario WHERE id = ?', (item_id,)).fetchone()
        
        return jsonify({
            'success': True,
            'item': {
                'id': item_atualizado['id'],
                'nome': item_atualizado['nome'],
                'quantidade': item_atualizado['quantidade'],
                'peso_total': float(item_atualizado['peso'] * item_atualizado['quantidade']),
                'valor_total': item_atualizado['valor'] * item_atualizado['quantidade']
            }
        })
        
    except Exception as e:
        print(f"Erro na ação do inventário: {e}")
        return jsonify({'success': False, 'error': str(e)})
    
    finally:
        conn.close()

# Rota para debug - remover em produção
@app.route('/debug/fichas')
def debug_fichas():
    """Debug: Listar todas as fichas e habilidades"""
    conn = get_db_connection()
    
    try:
        fichas = conn.execute('SELECT id, nome FROM fichas ORDER BY id').fetchall()
        resultado = {"fichas": []}
        
        for ficha in fichas:
            habilidades = conn.execute('SELECT id, nome FROM habilidades WHERE ficha_id = ?', (ficha['id'],)).fetchall()
            itens = conn.execute('SELECT id, nome FROM inventario WHERE ficha_id = ?', (ficha['id'],)).fetchall()
            resultado["fichas"].append({
                "id": ficha['id'],
                "nome": ficha['nome'],
                "habilidades": [{"id": h['id'], "nome": h['nome']} for h in habilidades],
                "itens": [{"id": i['id'], "nome": i['nome']} for i in itens]
            })
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({"error": str(e)})
    
    finally:
        conn.close()

# Tratamento de erros
@app.errorhandler(404)
def not_found(error):
    flash('Página não encontrada!', 'error')
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_error(error):
    flash('Erro interno do servidor. Tente novamente.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Verificar se o diretório templates existe
    if not os.path.exists('templates'):
        print("❌ Erro: Diretório 'templates' não encontrado!")
        print("📁 Certifique-se de que todos os arquivos HTML estão na pasta 'templates'")
        exit(1)
    
    # Inicializa o banco de dados
    print("🔧 Inicializando banco de dados...")
    init_db()
    
    # Atualizar banco para adicionar habilidade de classe
    print("🔄 Atualizando banco para habilidade de classe...")
    atualizar_banco_habilidade_classe()
    
    # Atualizar banco para inventário
    print("🎒 Atualizando banco para sistema de inventário...")
    atualizar_banco_inventario()
    
    # Roda a aplicação
    print("🚀 Iniciando servidor Flask...")
    print("🌐 Acesse: http://127.0.0.1:5000")
    
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)