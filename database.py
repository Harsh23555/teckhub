import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

DEFAULT_NEON_URL = 'postgresql://neondb_owner:npg_DkGxStjs6N7V@ep-misty-leaf-am593szq-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require'
DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_NEON_URL)
IS_POSTGRES = DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")

class DictRow(dict):
    """Dict wrapper that allows integer index access like row[0] for backward compatibility."""
    def __init__(self, data, keys=None):
        super().__init__(data)
        self._keys = list(keys) if keys else list(data.keys())
    
    def __getitem__(self, item):
        if isinstance(item, int):
            if 0 <= item < len(self._keys):
                return self[self._keys[item]]
            return None
        return self.get(item, None)

class UnifiedCursor:
    def __init__(self, cursor, is_postgres):
        self.cursor = cursor
        self.is_postgres = is_postgres

    def fetchall(self):
        rows = self.cursor.fetchall()
        if self.is_postgres:
            return [DictRow(dict(r)) for r in rows]
        else:
            return [DictRow(dict(r)) for r in rows]

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        return DictRow(dict(row))

class UnifiedConnection:
    def __init__(self, is_postgres=IS_POSTGRES, db_url=DATABASE_URL):
        self.is_postgres = is_postgres
        self.db_url = db_url
        self._connect()

    def _connect(self):
        if self.is_postgres:
            try:
                clean_url = self.db_url.replace("&channel_binding=require", "").replace("channel_binding=require&", "")
                self.conn = psycopg2.connect(clean_url)
            except Exception as err:
                print(f"[WARN] PostgreSQL connection failed: {err}. Falling back to local SQLite.")
                self.is_postgres = False
                self.conn = sqlite3.connect("novatech.db")
                self.conn.row_factory = sqlite3.Row
        else:
            self.conn = sqlite3.connect(self.db_url if self.db_url.endswith(".db") else "novatech.db")
            self.conn.row_factory = sqlite3.Row

    def rollback(self):
        try:
            self.conn.rollback()
        except Exception:
            pass

    def execute(self, query, params=()):
        if self.is_postgres:
            try:
                cursor = self.conn.cursor(cursor_factory=RealDictCursor)
                pg_query = query.replace("?", "%s")
                pg_query = pg_query.replace("datetime('now', '-2 minutes')", "NOW() - INTERVAL '2 minutes'")
                cursor.execute(pg_query, params)
            except (psycopg2.OperationalError, psycopg2.InterfaceError):
                self._connect()
                cursor = self.conn.cursor(cursor_factory=RealDictCursor)
                pg_query = query.replace("?", "%s")
                pg_query = pg_query.replace("datetime('now', '-2 minutes')", "NOW() - INTERVAL '2 minutes'")
                cursor.execute(pg_query, params)
            except Exception as e:
                self.rollback()
                raise e
        else:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            
        return UnifiedCursor(cursor, self.is_postgres)

    def executemany(self, query, params_list):
        if self.is_postgres:
            try:
                cursor = self.conn.cursor()
                pg_query = query.replace("?", "%s")
                cursor.executemany(pg_query, params_list)
            except (psycopg2.OperationalError, psycopg2.InterfaceError):
                self._connect()
                cursor = self.conn.cursor()
                pg_query = query.replace("?", "%s")
                cursor.executemany(pg_query, params_list)
            except Exception as e:
                self.rollback()
                raise e
        else:
            cursor = self.conn.cursor()
            cursor.executemany(query, params_list)

        return UnifiedCursor(cursor, self.is_postgres)

    def commit(self):
        try:
            self.conn.commit()
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            self._connect()
            self.conn.commit()

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass

def get_db_connection():
    return UnifiedConnection()

def init_db():
    conn = get_db_connection()

    if IS_POSTGRES:
        pk_type = "SERIAL PRIMARY KEY"
    else:
        pk_type = "INTEGER PRIMARY KEY AUTOINCREMENT"

    # Contacts table
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS contacts (
        id {pk_type},
        ticket_id VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(255) NOT NULL,
        company VARCHAR(255),
        email VARCHAR(255) NOT NULL,
        phone VARCHAR(50),
        country VARCHAR(100),
        service VARCHAR(255),
        budget VARCHAR(100),
        timeline VARCHAR(100),
        message TEXT NOT NULL,
        status VARCHAR(50) DEFAULT 'New',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # FAQs table
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS faqs (
        id {pk_type},
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        category VARCHAR(100) NOT NULL
    )
    """)

    # Chat Knowledge table
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS chat_knowledge (
        id {pk_type},
        keyword VARCHAR(255) NOT NULL,
        response TEXT NOT NULL
    )
    """)

    # Meetings table
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS meetings (
        id {pk_type},
        ticket_id VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        phone VARCHAR(50),
        preferred_date VARCHAR(50) NOT NULL,
        preferred_time VARCHAR(50) NOT NULL,
        topic TEXT,
        status VARCHAR(50) DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Email Logs table
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS email_logs (
        id {pk_type},
        recipient VARCHAR(255) NOT NULL,
        subject VARCHAR(255) NOT NULL,
        body TEXT NOT NULL,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Users table
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS users (
        id {pk_type},
        name VARCHAR(255),
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255),
        auth_provider VARCHAR(50) DEFAULT 'email',
        avatar_url TEXT,
        email_verified BOOLEAN DEFAULT FALSE,
        username VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Revoked JWT Tokens table
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS revoked_tokens (
        id {pk_type},
        jti VARCHAR(255) UNIQUE NOT NULL,
        revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    try:
        conn.commit()
    except Exception:
        pass

    # Ensure missing columns exist if table was previously created
    extra_cols = [
        ("name", "VARCHAR(255)"),
        ("password_hash", "VARCHAR(255)"),
        ("auth_provider", "VARCHAR(50) DEFAULT 'email'"),
        ("avatar_url", "TEXT"),
        ("email_verified", "BOOLEAN DEFAULT FALSE"),
        ("username", "VARCHAR(255)")
    ]
    for col_name, col_def in extra_cols:
        try:
            c = get_db_connection()
            c.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
            c.commit()
            c.close()
        except Exception:
            pass

    # Legacy fix for Neon DB if 'username' or 'password_hash' column exists with NOT NULL
    try:
        c = get_db_connection()
        c.execute("ALTER TABLE users ALTER COLUMN username DROP NOT NULL")
        c.commit()
        c.close()
    except Exception:
        pass

    try:
        c = get_db_connection()
        c.execute("ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL")
        c.commit()
        c.close()
    except Exception:
        pass

    # Seed FAQs if empty
    faq_count = conn.execute("SELECT COUNT(*) as count FROM faqs").fetchone()["count"]
    if faq_count == 0:
        seed_faqs = [
            ("What services does NovaTech AI offer?", "NovaTech AI offers custom software development, web & mobile applications, AI/ML engineering, cloud architecture, DevOps, cybersecurity, blockchain solutions, and IT consulting.", "Services"),
            ("How do you handle project pricing and billing?", "We offer flexible pricing models: Fixed-Price contracts for well-defined projects, Dedicated Team retainers ($2,999–$7,499/mo), and Custom Enterprise billing.", "Pricing"),
            ("What is the typical timeline for an MVP or software project?", "Simple MVPs usually take 4 to 8 weeks. Larger custom enterprise platforms take 3 to 6 months depending on requirements and integrations.", "Process"),
            ("Do you sign an NDA and assign 100% intellectual property rights?", "Yes! Standard NDA and full IP transfer to the client are included in every contract.", "General"),
            ("How does your development process work?", "Our engineering process combines Agile sprints, continuous CI/CD, daily standups, and rigorous automated testing with weekly client reporting.", "Technical"),
            ("What support options are available after deployment?", "We provide ongoing software maintenance, 24/7 emergency support SLA for active clients, monitoring, and incremental feature updates.", "Support"),
            ("Can you help migrate our legacy system to the cloud?", "Yes, we specialize in seamless cloud migrations to AWS, GCP, and Azure with zero downtime and cloud cost optimization.", "Technical"),
            ("Where are your offices located?", "Our headquarters are in Koramangala, Bangalore, with international delivery centers in Singapore and Dubai.", "General"),
        ]
        conn.executemany("INSERT INTO faqs (question, answer, category) VALUES (?, ?, ?)", seed_faqs)
        conn.commit()

    # Seed Chat Knowledge if empty
    chat_count = conn.execute("SELECT COUNT(*) as count FROM chat_knowledge").fetchone()["count"]
    if chat_count == 0:
        seed_knowledge = [
            ("pricing", "Our plans start at $2,999/mo for the Starter tier and $7,499/mo for Growth tier. For a custom enterprise quote, visit our Contact page or schedule a meeting!"),
            ("services", "We offer 13 core software services including Custom Web/Mobile Development, AI/ML, Cloud Migration, DevOps, Cybersecurity, and Blockchain."),
            ("ai", "Our AI team specializes in Large Language Models (LLM), Computer Vision, NLP, and custom predictive models tailored for enterprise applications."),
            ("contact", "Reach us at teckhubofficals@gmail.com, call +91 98359 28274, or send us a message directly via our Contact form."),
            ("office", "Our main office is located in Koramangala, Bangalore (560034). We also have locations in Singapore and Dubai. Hours: Mon-Fri 9am-7pm IST."),
            ("hours", "Office hours are Monday through Friday, 9:00 AM to 7:00 PM IST. Emergency 24/7 support is available for active SLA clients."),
            ("team", "NovaTech AI consists of 80+ engineers, data scientists, cloud architects, and UI/UX designers across Bangalore, Singapore, and Dubai."),
            ("portfolio", "We have delivered over 200 projects across Fintech, Healthcare, E-Commerce, Logistics, and EdTech. Check our Portfolio page for case studies!"),
            ("technologies", "Our technology stack includes Python, React, Next.js, Flutter, Node.js, Go, FastAPI, Docker, Kubernetes, AWS, GCP, and PostgreSQL."),
            ("careers", "We are hiring for Full-Stack, AI/ML, DevOps, and Design roles! Check our Careers page to view open positions."),
            ("meeting", "You can request a 1-on-1 discovery meeting directly through our Contact & Support Center on the website."),
            ("support", "For support, email teckhubofficals@gmail.com or chat with our team on WhatsApp at +91 98359 28274. 24/7 SLA available for enterprise clients."),
            ("whatsapp", "Click the WhatsApp floating button or link to chat directly with our solutions team!"),
        ]
        conn.executemany("INSERT INTO chat_knowledge (keyword, response) VALUES (?, ?)", seed_knowledge)
        conn.commit()

    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database (Neon DB / PostgreSQL) initialized and seeded successfully!")
