import sqlite3

def db():
    conn = sqlite3.connect("parking.db")
    conn.row_factory = sqlite3.Row
    return conn

def init():
    conn = db()
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS utilizadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        tipo TEXT NOT NULL
    )
    ''')
    # tipo server_admin,park_admin

    c.execute('''
    CREATE TABLE IF NOT EXISTS parques (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        localizacao TEXT,
        capacidade INTEGER NOT NULL,
        preco_base REAL DEFAULT 1,
        preco_min REAL DEFAULT 0.05,      
        ativo INTEGER DEFAULT 1
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS admin_parques (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER NOT NULL,
        parque_id INTEGER NOT NULL,

        FOREIGN KEY(admin_id) REFERENCES utilizadores(id),
        FOREIGN KEY(parque_id) REFERENCES parques(id)
    )
    ''')

    # c.execute('''
    # CREATE TABLE IF NOT EXISTS carros (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     matricula TEXT,
    #     entrada TEXT,
    #     saida TEXT,
    #     preco REAL,
    #     tempo INTEGER,
    #     ativo INTEGER,
    #     pago TEXT
    # )
    # ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS carros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        parque_id INTEGER NOT NULL,

        matricula TEXT NOT NULL,

        entrada TEXT NOT NULL,
        saida TEXT,

        preco REAL DEFAULT 0,
        tempo INTEGER DEFAULT 0,

        ativo INTEGER DEFAULT 1,
        pago INTEGER DEFAULT 0,

        FOREIGN KEY(parque_id) REFERENCES parques(id)
    )
    ''')

    # c.execute('''
    # CREATE TABLE IF NOT EXISTS reservas (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     matricula TEXT,
    #     inicio TEXT,
    #     expira TEXT,
    #     ativo INTEGER
    # )
    # ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        parque_id INTEGER NOT NULL,

        matricula TEXT NOT NULL,

        inicio TEXT NOT NULL,
        expira TEXT NOT NULL,

        ativo INTEGER DEFAULT 1,

        FOREIGN KEY(parque_id) REFERENCES parques(id)
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        carro_id INTEGER NOT NULL,

        valor REAL NOT NULL,
        metodo TEXT,
        data TEXT NOT NULL,

        FOREIGN KEY(carro_id) REFERENCES carros(id)
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        token TEXT UNIQUE NOT NULL,

        criado_em TEXT NOT NULL,

        usado INTEGER DEFAULT 0,

        max_parques INTEGER DEFAULT 1,

        usado_em TEXT
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS pagamentos_pendentes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        carro_id INTEGER NOT NULL UNIQUE,

        criado_em TEXT NOT NULL,

        FOREIGN KEY(carro_id) REFERENCES carros(id)
    )
    ''')
    
    # =========================
    # ADMIN DEFAULT
    # =========================

    c.execute("""
        SELECT id
        FROM utilizadores
        WHERE username = ?
    """, ("AdminS",))

    admin = c.fetchone()

    if not admin:

        c.execute("""
            INSERT INTO utilizadores (
                nome,
                username,
                password,
                tipo
            )
            VALUES (?, ?, ?, ?)
        """, (
            "Ben",
            "AdminS",
            "123",
            "server_admin"
    ))
    c.execute("""
        SELECT id
        FROM utilizadores
        WHERE username = ?
    """, ("Ado1",))

    user_ado = c.fetchone()

    if not user_ado:
        c.execute("""
            INSERT INTO utilizadores (
                nome,
                username,
                password,
                tipo
            )
            VALUES (?, ?, ?, ?)
        """, (
            "Ado",
            "Ado1",
            "123",
            "park_admin"
    ))
    # =========================
    # PARQUES DEFAULT
    # =========================

    c.execute("""
        SELECT id
        FROM parques
        WHERE nome = ?
    """, ("Parque Central",))

    if not c.fetchone():

        c.execute("""
            INSERT INTO parques (
                nome,
                localizacao,
                capacidade
            )
            VALUES (?, ?, ?)
        """, (
            "Parque Central",
            "Leiria",
            50
    ))


    c.execute("""
        SELECT id
        FROM parques
        WHERE nome = ?
    """, ("Parque Shopping",))

    if not c.fetchone():

        c.execute("""
            INSERT INTO parques (
                nome,
                localizacao,
                capacidade
            )
            VALUES (?, ?, ?)
        """, (
            "Parque Shopping",
            "Porto",
            30
    ))

    # INDEXs
    # carros
    c.execute('''
    CREATE INDEX IF NOT EXISTS idx_carros_matricula
    ON carros(matricula)
    ''')

    c.execute('''
    CREATE INDEX IF NOT EXISTS idx_carros_parque
    ON carros(parque_id)
    ''')

    c.execute('''
    CREATE INDEX IF NOT EXISTS idx_carros_ativo
    ON carros(ativo)
    ''')

    # reservas
    c.execute('''
    CREATE INDEX IF NOT EXISTS idx_reservas_parque
    ON reservas(parque_id)
    ''')

    c.execute('''
    CREATE INDEX IF NOT EXISTS idx_reservas_matricula
    ON reservas(matricula)
    ''')

    # admin_parques
    c.execute('''
    CREATE INDEX IF NOT EXISTS idx_admin_parques_admin
    ON admin_parques(admin_id)
    ''')

    c.execute('''
    CREATE INDEX IF NOT EXISTS idx_admin_parques_parque
    ON admin_parques(parque_id)
    ''')

    # utilizadores
    c.execute('''
    CREATE INDEX IF NOT EXISTS idx_utilizadores_username
    ON utilizadores(username)
    ''')

    conn.commit()
    conn.close()