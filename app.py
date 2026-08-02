from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, make_response, g
from datetime import datetime, timezone, timedelta
from functools import wraps
import json, os, re, random, string, hashlib, uuid
import jwt
from dotenv import load_dotenv
import resend
from database import init_db, get_db_connection

# Load environment variables from .env file
load_dotenv()

# Initialize Database on application startup
init_db()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "novatech-ai-secret-2024-premium-contact-key")

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "novatech_jwt_super_secret_key_2026")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "teckhubofficals@gmail.com")

FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "teck-hub")
ADMIN_GOOGLE_EMAILS = {
    email.strip().lower()
    for email in os.environ.get("ADMIN_GOOGLE_EMAILS", "").split(",")
    if email.strip()
}
FIREBASE_WEB_CONFIG = {
    "apiKey": os.environ.get("FIREBASE_API_KEY", "AIzaSyApHRcrwLE-9jiebsXFy9isAJyalyMCV7A"),
    "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN", "teck-hub.firebaseapp.com"),
    "projectId": FIREBASE_PROJECT_ID,
    "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET", "teck-hub.firebasestorage.app"),
    "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID", "981920336841"),
    "appId": os.environ.get("FIREBASE_APP_ID", "1:981920336841:web:1c89a5115317ef97a87618"),
    "measurementId": os.environ.get("FIREBASE_MEASUREMENT_ID", "G-B8R0BCQY1G"),
}

# ── Data In-memory fallback stores ───────────────────────────────────────────
jobs = [
    {"id":1,"title":"Senior Full-Stack Developer","dept":"Engineering","location":"Remote","type":"Full-Time","desc":"Build scalable web applications using React, Node.js, and cloud technologies.","req":["5+ years experience","React/Node.js expertise","Cloud platform knowledge"]},
    {"id":2,"title":"AI/ML Engineer","dept":"AI Research","location":"Hybrid","type":"Full-Time","desc":"Design and deploy machine learning models for enterprise clients.","req":["Python, TensorFlow/PyTorch","MLOps experience","Research background preferred"]},
    {"id":3,"title":"UI/UX Designer","dept":"Design","location":"Remote","type":"Full-Time","desc":"Craft beautiful, accessible interfaces for our client projects.","req":["Portfolio of shipped products","Figma expertise","Design systems experience"]},
    {"id":4,"title":"DevOps Engineer","dept":"Infrastructure","location":"Remote","type":"Full-Time","desc":"Manage CI/CD pipelines, cloud infrastructure, and reliability.","req":["AWS/GCP/Azure","Kubernetes, Docker","Terraform/IaC"]},
    {"id":5,"title":"Business Development Manager","dept":"Sales","location":"On-site","type":"Full-Time","desc":"Drive new client acquisition and partnership development.","req":["3+ years B2B sales","Tech industry background","Strong communication"]},
]
blog_posts = [
    {"id":1,"title":"The Future of AI in Enterprise Software","category":"AI & ML","date":"Dec 12, 2024","read":"8 min","excerpt":"How large language models are reshaping how enterprises build and operate internal tools, from code generation to decision support.","author":"Arjun Mehta","img":"ai-blog"},
    {"id":2,"title":"Building Resilient Microservices with Go","category":"Backend","date":"Dec 5, 2024","read":"12 min","excerpt":"A practical guide to designing fault-tolerant microservices architectures that scale to millions of requests per day.","author":"Priya Sharma","img":"microservices-blog"},
    {"id":3,"title":"Why React Server Components Change Everything","category":"Frontend","date":"Nov 28, 2024","read":"6 min","excerpt":"RSC shifts the mental model for building React apps. Here's what it means for performance, DX, and the future of the web.","author":"Ravi Kumar","img":"react-blog"},
    {"id":4,"title":"Zero-Trust Security for SaaS Products","category":"Security","date":"Nov 20, 2024","read":"10 min","excerpt":"How to implement zero-trust architecture in a modern SaaS product without sacrificing developer velocity.","author":"Neha Singh","img":"security-blog"},
    {"id":5,"title":"From MVP to Scale: A Cloud Migration Story","category":"Cloud","date":"Nov 14, 2024","read":"9 min","excerpt":"We moved a fintech startup from a $200/month VPS to a fully auto-scaling AWS infrastructure. Here's what we learned.","author":"Arjun Mehta","img":"cloud-blog"},
    {"id":6,"title":"Designing Accessible Dark Mode","category":"Design","date":"Nov 7, 2024","read":"7 min","excerpt":"Dark mode is more than inverting colors. A guide to accessible, beautiful dark interfaces that work for everyone.","author":"Priya Sharma","img":"design-blog"},
]
services_data = [
    {"icon":"💻","title":"Custom Software Development","desc":"Bespoke software solutions engineered to your exact business requirements, from greenfield builds to complex legacy modernization.","tags":["Web Apps","Desktop","Enterprise"]},
    {"icon":"📱","title":"Web & Mobile App Development","desc":"High-performance web and native mobile apps (iOS, Android, Flutter) with pixel-perfect UI and robust backends.","tags":["React","Flutter","React Native"]},
    {"icon":"🤖","title":"AI & Machine Learning","desc":"Intelligent automation, predictive analytics, NLP, computer vision, and custom LLM integrations that deliver measurable ROI.","tags":["LLM","Computer Vision","NLP"]},
    {"icon":"☁️","title":"Cloud Computing & Migration","desc":"Cloud-native architecture design, migration from legacy infrastructure, and ongoing cloud cost optimization.","tags":["AWS","GCP","Azure"]},
    {"icon":"⚙️","title":"DevOps & CI/CD","desc":"Automated pipelines, containerization, Kubernetes orchestration, and SRE practices for shipping faster with confidence.","tags":["Docker","K8s","Terraform"]},
    {"icon":"🎨","title":"UI/UX Design","desc":"Research-driven design process producing intuitive, beautiful interfaces backed by user testing and accessibility standards.","tags":["Figma","Design Systems","A11y"]},
    {"icon":"🔌","title":"API Design & Integration","desc":"RESTful and GraphQL API design, third-party integrations (payment, auth, analytics), and API gateway management.","tags":["REST","GraphQL","Webhooks"]},
    {"icon":"🔒","title":"Cybersecurity","desc":"Security audits, penetration testing, OWASP compliance, zero-trust architecture, and incident response planning.","tags":["PenTest","OWASP","Zero Trust"]},
    {"icon":"⛓️","title":"Blockchain Development","desc":"Smart contracts, DeFi protocols, NFT platforms, and enterprise blockchain solutions on Ethereum, Solana, and more.","tags":["Solidity","Web3","DeFi"]},
    {"icon":"🚀","title":"SaaS Solutions","desc":"End-to-end SaaS product development — multi-tenant architecture, subscription billing, usage-based pricing, and analytics.","tags":["Multi-tenant","Stripe","B2B SaaS"]},
    {"icon":"📊","title":"ERP & CRM Development","desc":"Custom enterprise resource planning and CRM systems built around your workflows, not the other way around.","tags":["ERP","CRM","Automation"]},
    {"icon":"🧩","title":"IT Consulting","desc":"Strategic technology advisory — architecture reviews, technology selection, digital transformation roadmaps.","tags":["Strategy","Architecture","Advisory"]},
    {"icon":"🛠️","title":"Software Maintenance","desc":"Ongoing maintenance, performance monitoring, bug triage, and incremental feature development for live products.","tags":["Support","Monitoring","Updates"]},
]
testimonials = [
    {"name":"Sarah Chen","role":"CTO, Nexus Fintech","text":"NovaTech rebuilt our entire payment infrastructure in 4 months. The new system processes 10x the volume with zero downtime since launch. Exceptional engineering and communication throughout.","stars":5,"avatar":"SC"},
    {"name":"Marcus Okafor","role":"VP Product, HealthBridge","text":"We needed an AI triage assistant fast. NovaTech delivered a HIPAA-compliant, production-ready product in 8 weeks. The quality was extraordinary for the timeline.","stars":5,"avatar":"MO"},
    {"name":"Elena Vasquez","role":"Founder, ShopWave","text":"Our mobile commerce app went from concept to 50k downloads in three months. NovaTech's Flutter team is world-class. I can't imagine building without them.","stars":5,"avatar":"EV"},
    {"name":"James Whitfield","role":"CIO, LogiCore Logistics","text":"The ERP they built replaced three legacy systems and saved us $2M annually in operational overhead. ROI was visible within the first quarter.","stars":5,"avatar":"JW"},
]
portfolio_items = [
    {"title":"Nexus Pay","category":"Fintech","tech":["React","Node.js","AWS","PostgreSQL"],"desc":"Real-time payment processing platform handling $50M+ daily transactions.","outcome":"10x throughput, 99.99% uptime"},
    {"title":"HealthBridge AI","category":"Healthcare","tech":["Python","FastAPI","GPT-4","Docker"],"desc":"AI-powered patient triage system deployed across 12 hospitals.","outcome":"40% reduction in ER wait times"},
    {"title":"ShopWave","category":"E-commerce","tech":["Flutter","Firebase","Stripe","GCP"],"desc":"Mobile-first shopping app with AI product recommendations.","outcome":"50k downloads in 90 days"},
    {"title":"LogiCore ERP","category":"Logistics","tech":["Django","React","PostgreSQL","Redis"],"desc":"Custom ERP replacing 3 legacy systems for a $500M logistics firm.","outcome":"$2M annual savings"},
    {"title":"EduSpark LMS","category":"EdTech","tech":["Next.js","Node.js","MongoDB","WebRTC"],"desc":"Live learning platform with real-time collaboration for 200k students.","outcome":"200k active users, 4.8★ rating"},
    {"title":"BlockVault","category":"Blockchain","tech":["Solidity","React","Ethereum","IPFS"],"desc":"Decentralized asset vault with smart contract insurance.","outcome":"$30M TVL in 6 months"},
]
stats = [
    {"value":"200+","label":"Projects Delivered"},
    {"value":"98%","label":"Client Satisfaction"},
    {"value":"50+","label":"Enterprise Clients"},
    {"value":"8+","label":"Years of Excellence"},
]
tech_stack = {
    "Frontend":  ["React","Next.js","Vue.js","Angular","Flutter","TypeScript","Tailwind CSS","Three.js"],
    "Backend":   ["Node.js","Python","Django","FastAPI","Go","Rust","NestJS","GraphQL"],
    "Cloud":     ["AWS","Google Cloud","Azure","Vercel","Docker","Kubernetes","Terraform","Linux"],
    "AI & Data": ["TensorFlow","PyTorch","LangChain","OpenAI","Hugging Face","Pandas","Spark","Airflow"],
    "Database":  ["PostgreSQL","MongoDB","Redis","MySQL","Elasticsearch","Supabase","DynamoDB","Pinecone"],
}
industries = [
    {"icon":"🏦","name":"Fintech","desc":"Payment systems, trading platforms, risk engines"},
    {"icon":"🏥","name":"Healthcare","desc":"HIPAA-compliant apps, EMR, AI diagnostics"},
    {"icon":"🛒","name":"E-commerce","desc":"Marketplaces, inventory, recommendation engines"},
    {"icon":"📚","name":"EdTech","desc":"LMS, live learning, adaptive assessments"},
    {"icon":"🏭","name":"Manufacturing","desc":"ERP, IoT integration, supply chain visibility"},
    {"icon":"🚚","name":"Logistics","desc":"Fleet management, route optimization, tracking"},
    {"icon":"🏠","name":"Real Estate","desc":"PropTech, virtual tours, smart contracts"},
    {"icon":"⚡","name":"Energy","desc":"Grid management, smart meter platforms, analytics"},
]
plans = [
    {"name":"Starter","price":"$2,999","period":"/mo","badge":"","color":"secondary","features":["Up to 2 projects","Dedicated PM","100 dev hours/mo","Weekly reporting","Email support","Basic cloud setup"],"cta":"Get Started","popular":False},
    {"name":"Growth","price":"$7,499","period":"/mo","badge":"Most Popular","color":"primary","features":["Up to 6 projects","Dedicated team","300 dev hours/mo","Daily standups","Priority support","Full DevOps pipeline","QA automation","Analytics dashboard"],"cta":"Start Growing","popular":True},
    {"name":"Enterprise","price":"Custom","period":"","badge":"","color":"secondary","features":["Unlimited projects","On-site team option","Unlimited dev hours","24/7 support SLA","White-label option","Custom integrations","Security audit","Compliance consulting"],"cta":"Contact Sales","popular":False},
]
values = [
    {"icon":"🎯","title":"Client-First","desc":"Your success is our metric. We measure outcomes, not outputs."},
    {"icon":"💡","title":"Innovation","desc":"We push the frontier — in tools, process, and thinking."},
    {"icon":"🤝","title":"Transparency","desc":"No surprises. Clear communication at every stage."},
    {"icon":"⚡","title":"Velocity","desc":"Speed without shortcuts. Shipped fast, built to last."},
    {"icon":"🔬","title":"Precision","desc":"Engineering discipline and craft in every line of code."},
    {"icon":"🌍","title":"Impact","desc":"We care about the real-world effect of what we build."},
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def valid_email(e):
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", e)

def generate_ticket_id(prefix="NT"):
    rand_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{datetime.now().year}-{rand_part}"

def send_email_notification(recipient, subject, body):
    try:
        conn = get_db_connection()
        conn.execute("INSERT INTO email_logs (recipient, subject, body) VALUES (?, ?, ?)",
                     (recipient, subject, body))
        conn.commit()
        conn.close()
    except Exception as err:
        print("Email log error:", err)

# ── JWT Auth Helpers ──────────────────────────────────────────────────────────
def create_admin_jwt(username):
    payload = {
        "user": username,
        "role": "admin",
        "jti": str(uuid.uuid4()),
        "exp": datetime.now(timezone.utc) + timedelta(days=1),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

def decode_admin_jwt(token):
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        jti = payload.get("jti")
        if jti:
            conn = get_db_connection()
            revoked = conn.execute("SELECT id FROM revoked_tokens WHERE jti = ?", (jti,)).fetchone()
            conn.close()
            if revoked:
                return None
        return payload
    except Exception:
        return None

def revoke_jwt_token(token):
    if not token:
        return
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        jti = payload.get("jti")
        if jti:
            conn = get_db_connection()
            conn.execute("INSERT INTO revoked_tokens (jti) VALUES (?)", (jti,))
            conn.commit()
            conn.close()
    except Exception as err:
        print("Revoke JWT error:", err)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get("jwt_token")
        decoded = decode_admin_jwt(token)
        
        if not decoded and request.headers.get("Authorization"):
            auth_hdr = request.headers.get("Authorization")
            if auth_hdr.startswith("Bearer "):
                token = auth_hdr.split(" ")[1]
                decoded = decode_admin_jwt(token)

        if not decoded and session.get("admin_logged_in"):
            username = session.get("admin_user", ADMIN_USERNAME)
            fresh_jwt = create_admin_jwt(username)
            decoded = decode_admin_jwt(fresh_jwt)
            if decoded:
                session["admin_logged_in"] = True
                session["admin_user"] = decoded.get("user", "Admin")
                res = make_response(f(*args, **kwargs))
                res.set_cookie("jwt_token", fresh_jwt, httponly=True, max_age=86400, samesite="Lax")
                return res

        if not decoded:
            session.clear()
            flash("Admin authentication required. Please log in.", "danger")
            return redirect(url_for("admin_login"))

        session["admin_logged_in"] = True
        session["admin_user"] = decoded.get("user", "Admin")
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_logged_in"):
            if request.method == "POST":
                return jsonify({"ok": False, "error": "Authentication required. Please log in first."}), 401
            flash("Please log in to access the contact and support center.", "warning")
            return redirect(url_for("user_login"))
        return f(*args, **kwargs)
    return decorated_function

def verify_firebase_id_token(id_token: str):
    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token as google_id_token
    except Exception:
        return None, "Google OAuth dependencies are not installed on the server."

    if not id_token:
        return None, "Missing Firebase ID token."

    try:
        decoded = google_id_token.verify_firebase_token(id_token, google_requests.Request())
    except Exception:
        return None, "Unable to verify Google sign-in token."

    if not decoded:
        return None, "Invalid Google sign-in token."

    token_project = decoded.get("aud")
    if token_project != FIREBASE_PROJECT_ID:
        return None, "Token project does not match server configuration."

    if decoded.get("iss") != f"https://securetoken.google.com/{FIREBASE_PROJECT_ID}":
        return None, "Token issuer is invalid."

    if not decoded.get("email"):
        return None, "Google account email not found in token."

    if not decoded.get("email_verified", False):
        return None, "Google account email is not verified."

    return decoded, None

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html", stats=stats, services=services_data[:6],
        testimonials=testimonials, tech_stack=tech_stack, industries=industries,
        blog_posts=blog_posts[:3], portfolio=portfolio_items[:3], year=datetime.now().year)

@app.route("/about")
def about():
    team = [
        {"name":"Arjun Mehta","role":"CEO & Co-founder","bio":"10+ years building enterprise software. Former engineering lead at Infosys Labs.","avatar":"AM","linkedin":"#"},
        {"name":"Priya Sharma","role":"CTO & Co-founder","bio":"PhD CS. Former AI researcher at IIT Bombay. Specialises in ML systems at scale.","avatar":"PS","linkedin":"#"},
        {"name":"Ravi Kumar","role":"Head of Design","bio":"8 years crafting world-class product design. Previously at Razorpay and Freshworks.","avatar":"RK","linkedin":"#"},
        {"name":"Neha Singh","role":"Head of Delivery","bio":"PMP certified. Delivered 80+ projects on time, on budget. Zero missed SLAs.","avatar":"NS","linkedin":"#"},
        {"name":"Dev Patel","role":"Lead DevOps Engineer","bio":"AWS certified solutions architect. Built infra handling 1B+ events/day.","avatar":"DP","linkedin":"#"},
        {"name":"Aisha Khan","role":"Head of Sales","bio":"Closed $20M+ in enterprise contracts. Passionate about tech-for-good.","avatar":"AK","linkedin":"#"},
    ]
    timeline = [
        {"year":"2016","title":"Founded","desc":"Arjun and Priya start NovaTech AI from a co-working space in Bangalore with 3 engineers."},
        {"year":"2017","title":"First Enterprise Client","desc":"Signed our first ₹1 Cr contract with a leading NBFC to rebuild their loan origination system."},
        {"year":"2019","title":"AI Division Launched","desc":"Dedicated AI research team established. First ML product shipped to production."},
        {"year":"2021","title":"Global Expansion","desc":"Opened offices in Singapore and Dubai. Team grew to 80+ across 3 countries."},
        {"year":"2023","title":"100+ Clients","desc":"Crossed 100 enterprise clients and $10M ARR. Launched our proprietary DevOps platform."},
        {"year":"2024","title":"Series A — $15M","desc":"Raised Series A led by Sequoia India to scale AI capabilities and global delivery."},
    ]
    return render_template("about.html", team=team, timeline=timeline, values=values, year=datetime.now().year)

@app.route("/services")
def services():
    return render_template("services.html", services=services_data, year=datetime.now().year)

@app.route("/portfolio")
def portfolio():
    cats = sorted(set(p["category"] for p in portfolio_items))
    return render_template("portfolio.html", portfolio=portfolio_items, categories=cats, year=datetime.now().year)

@app.route("/pricing")
def pricing():
    conn = get_db_connection()
    faqs_rows = conn.execute("SELECT question as q, answer as a FROM faqs ORDER BY id ASC").fetchall()
    faqs = [dict(r) for r in faqs_rows]
    conn.close()
    return render_template("pricing.html", plans=plans, faqs=faqs, year=datetime.now().year)

@app.route("/contact", methods=["GET", "POST"])
@user_required
def contact():
    if request.method == "POST":
        # Honeypot check for spam prevention
        if request.form.get("website_url") or request.form.get("honeypot"):
            t_id = generate_ticket_id("NT")
            return jsonify({"ok": True, "ticket_id": t_id, "message": "Thank you for your submission!"})

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        company = request.form.get("company", "").strip()
        country = request.form.get("country", "").strip()
        service = request.form.get("service", "").strip()
        budget = request.form.get("budget", "").strip()
        timeline = request.form.get("timeline", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            return jsonify({"ok": False, "error": "Full Name, Email, and Message are required."}), 400

        if not valid_email(email):
            return jsonify({"ok": False, "error": "Please enter a valid email address."}), 400

        if phone and not re.match(r"^[+]*[(]?[0-9]{1,4}[)]?[-\s./0-9]*$", phone):
            return jsonify({"ok": False, "error": "Please enter a valid phone number."}), 400

        conn = get_db_connection()

        # Check duplicate submission (same email & message within last 2 mins)
        dup = conn.execute("""
            SELECT id FROM contacts 
            WHERE email = ? AND message = ? AND created_at > datetime('now', '-2 minutes')
        """, (email, message)).fetchone()

        if dup:
            conn.close()
            return jsonify({"ok": False, "error": "You recently submitted this exact message. We are currently processing it!"}), 429

        ticket_id = generate_ticket_id("NT")

        conn.execute("""
            INSERT INTO contacts (ticket_id, name, company, email, phone, country, service, budget, timeline, message, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'New')
        """, (ticket_id, name, company, email, phone, country, service, budget, timeline, message))
        conn.commit()
        conn.close()

        # Dispatch email via Resend.com to receiver email specified in .env
        resend_admin_sent = False
        resend_cust_sent = False
        if RESEND_API_KEY and RESEND_API_KEY != "re_123456789_your_resend_api_key_here":
            resend.api_key = RESEND_API_KEY
            
            # 1. Send to admin (RECEIVER_EMAIL)
            try:
                resend.Emails.send({
                    "from": "NovaTech <onboarding@resend.dev>",
                    "to": [RECEIVER_EMAIL],
                    "subject": f"New Contact Message [{ticket_id}] from {name}",
                    "html": f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; background-color: #ffffff;">
                        <h2 style="color: #4f46e5; border-bottom: 2px solid #4f46e5; padding-bottom: 10px;">New Contact Form Submission</h2>
                        <p style="font-size: 14px;"><strong>Ticket Reference:</strong> <code style="background: #f3f4f6; padding: 2px 6px; border-radius: 4px;">{ticket_id}</code></p>
                        
                        <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                            <tr><td style="padding: 6px 0; color: #6b7280; width: 140px;"><strong>Sender Name:</strong></td><td style="padding: 6px 0; color: #111827;">{name}</td></tr>
                            <tr><td style="padding: 6px 0; color: #6b7280;"><strong>Email Address:</strong></td><td style="padding: 6px 0; color: #111827;"><a href="mailto:{email}">{email}</a></td></tr>
                            <tr><td style="padding: 6px 0; color: #6b7280;"><strong>Phone / WhatsApp:</strong></td><td style="padding: 6px 0; color: #111827;">{phone or 'Not Provided'}</td></tr>
                            <tr><td style="padding: 6px 0; color: #6b7280;"><strong>Company:</strong></td><td style="padding: 6px 0; color: #111827;">{company or 'Not Provided'}</td></tr>
                            <tr><td style="padding: 6px 0; color: #6b7280;"><strong>Country:</strong></td><td style="padding: 6px 0; color: #111827;">{country or 'Not Provided'}</td></tr>
                            <tr><td style="padding: 6px 0; color: #6b7280;"><strong>Service Interested:</strong></td><td style="padding: 6px 0; color: #111827;">{service or 'General Inquiry'}</td></tr>
                            <tr><td style="padding: 6px 0; color: #6b7280;"><strong>Budget:</strong></td><td style="padding: 6px 0; color: #111827;">{budget or 'Not Specified'}</td></tr>
                            <tr><td style="padding: 6px 0; color: #6b7280;"><strong>Timeline:</strong></td><td style="padding: 6px 0; color: #111827;">{timeline or 'Not Specified'}</td></tr>
                        </table>
                        
                        <div style="margin-top: 20px; padding: 15px; background: #f9fafb; border-left: 4px solid #4f46e5; border-radius: 4px;">
                            <p style="margin: 0 0 8px 0; color: #374151; font-weight: bold;">Message Content:</p>
                            <p style="margin: 0; color: #1f2937; white-space: pre-wrap; line-height: 1.5;">{message}</p>
                        </div>
                        
                        <p style="font-size: 12px; color: #9ca3af; margin-top: 25px; text-align: center;">Sent automatically via Resend.com for NovaTech AI Support System.</p>
                    </div>
                    """
                })
                resend_admin_sent = True
                send_email_notification(RECEIVER_EMAIL, f"Resend Email Sent: New Lead [{ticket_id}] from {name}", f"Message successfully delivered to {RECEIVER_EMAIL} via Resend.com API.")
            except Exception as resend_err:
                print("Resend Admin Email error:", resend_err)
                send_email_notification(RECEIVER_EMAIL, f"New Lead [{ticket_id}] from {name} (Resend Exception)", f"Resend Error: {resend_err}\n\nMessage:\n{message}")
                
            # 2. Send confirmation to the customer
            try:
                resend.Emails.send({
                    "from": "NovaTech <onboarding@resend.dev>",
                    "to": [email],
                    "subject": f"We received your message [{ticket_id}] - NovaTech AI",
                    "html": f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; background-color: #ffffff;">
                        <h2 style="color: #4f46e5; border-bottom: 2px solid #4f46e5; padding-bottom: 10px;">Message Received</h2>
                        <p>Hi {name},</p>
                        <p>Thank you for contacting NovaTech AI! We have received your message and our team will get back to you shortly.</p>
                        <p style="font-size: 14px;"><strong>Your Ticket Reference:</strong> <code style="background: #f3f4f6; padding: 2px 6px; border-radius: 4px;">{ticket_id}</code></p>
                        
                        <div style="margin-top: 20px; padding: 15px; background: #f9fafb; border-left: 4px solid #4f46e5; border-radius: 4px;">
                            <p style="margin: 0 0 8px 0; color: #374151; font-weight: bold;">Your Message:</p>
                            <p style="margin: 0; color: #1f2937; white-space: pre-wrap; line-height: 1.5;">{message}</p>
                        </div>
                        
                        <p style="font-size: 12px; color: #9ca3af; margin-top: 25px; text-align: center;">This is an automated confirmation from NovaTech AI Support.</p>
                    </div>
                    """
                })
                resend_cust_sent = True
            except Exception as cust_err:
                print("Resend Customer Email error:", cust_err)

        if not resend_admin_sent:
            admin_body = f"New Enquiry from {name} ({email}) | Phone: {phone} | Service: {service} | Budget: {budget}\nTicket: {ticket_id}\n\nMessage:\n{message}"
            send_email_notification(RECEIVER_EMAIL, f"New Lead [{ticket_id}] from {name}", admin_body)

        if not resend_cust_sent:
            cust_body = f"Hi {name},\n\nThank you for contacting NovaTech AI.\nYour Ticket ID is {ticket_id}.\nWe will review your inquiry regarding '{service or 'General'}' and get back to you within 24 hours.\n\nBest regards,\nNovaTech AI Support"
            send_email_notification(email, f"Enquiry Received [{ticket_id}] — NovaTech AI", cust_body)

        return jsonify({
            "ok": True,
            "ticket_id": ticket_id,
            "message": f"Thank you, {name}! Your message has been submitted successfully.",
            "details": {
                "ticket_id": ticket_id,
                "name": name,
                "email": email,
                "service": service,
                "created_at": datetime.now().strftime("%b %d, %Y %I:%M %p")
            }
        })

    # GET request
    conn = get_db_connection()
    faqs = [dict(row) for row in conn.execute("SELECT * FROM faqs ORDER BY id ASC").fetchall()]
    conn.close()
    return render_template("contact.html", faqs=faqs, year=datetime.now().year)

@app.route("/meeting/request", methods=["POST"])
@user_required
def meeting_request():
    if request.form.get("website_url") or request.form.get("honeypot"):
        return jsonify({"ok": True, "ticket_id": generate_ticket_id("MT"), "message": "Meeting request received!"})

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    pref_date = request.form.get("preferred_date", "").strip()
    pref_time = request.form.get("preferred_time", "").strip()
    topic = request.form.get("topic", "").strip()

    if not name or not email or not pref_date or not pref_time:
        return jsonify({"ok": False, "error": "Name, Email, Preferred Date, and Preferred Time are required."}), 400

    if not valid_email(email):
        return jsonify({"ok": False, "error": "Please enter a valid email address."}), 400

    ticket_id = generate_ticket_id("MT")

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO meetings (ticket_id, name, email, phone, preferred_date, preferred_time, topic, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
    """, (ticket_id, name, email, phone, pref_date, pref_time, topic))
    conn.commit()
    conn.close()

    resend_admin_sent = False
    resend_cust_sent = False
    if RESEND_API_KEY and RESEND_API_KEY != "re_123456789_your_resend_api_key_here":
        resend.api_key = RESEND_API_KEY
        
        # 1. Send to admin
        try:
            resend.Emails.send({
                "from": "NovaTech <onboarding@resend.dev>",
                "to": [RECEIVER_EMAIL],
                "subject": f"New Meeting Request [{ticket_id}] from {name}",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; background-color: #ffffff;">
                    <h2 style="color: #4f46e5; border-bottom: 2px solid #4f46e5; padding-bottom: 10px;">New Meeting Request</h2>
                    <p style="font-size: 14px;"><strong>Ticket Reference:</strong> <code style="background: #f3f4f6; padding: 2px 6px; border-radius: 4px;">{ticket_id}</code></p>
                    
                    <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                        <tr><td style="padding: 6px 0; color: #6b7280; width: 140px;"><strong>Client Name:</strong></td><td style="padding: 6px 0; color: #111827;">{name}</td></tr>
                        <tr><td style="padding: 6px 0; color: #6b7280;"><strong>Email Address:</strong></td><td style="padding: 6px 0; color: #111827;"><a href="mailto:{email}">{email}</a></td></tr>
                        <tr><td style="padding: 6px 0; color: #6b7280;"><strong>Phone / WhatsApp:</strong></td><td style="padding: 6px 0; color: #111827;">{phone or 'Not Provided'}</td></tr>
                        <tr><td style="padding: 6px 0; color: #6b7280;"><strong>Preferred Date:</strong></td><td style="padding: 6px 0; color: #111827;">{pref_date}</td></tr>
                        <tr><td style="padding: 6px 0; color: #6b7280;"><strong>Preferred Time:</strong></td><td style="padding: 6px 0; color: #111827;">{pref_time}</td></tr>
                        <tr><td style="padding: 6px 0; color: #6b7280;"><strong>Topic:</strong></td><td style="padding: 6px 0; color: #111827;">{topic or 'General Discussion'}</td></tr>
                    </table>
                    
                    <p style="font-size: 12px; color: #9ca3af; margin-top: 25px; text-align: center;">Sent automatically via Resend.com for NovaTech AI Support System.</p>
                </div>
                """
            })
            resend_admin_sent = True
        except Exception as resend_err:
            print("Resend Admin Email error:", resend_err)
        
        # 2. Send confirmation to customer
        try:
            resend.Emails.send({
                "from": "NovaTech <onboarding@resend.dev>",
                "to": [email],
                "subject": f"Meeting Request Confirmed [{ticket_id}] - NovaTech AI",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; background-color: #ffffff;">
                    <h2 style="color: #4f46e5; border-bottom: 2px solid #4f46e5; padding-bottom: 10px;">Meeting Request Received</h2>
                    <p>Hi {name},</p>
                    <p>Thank you for requesting a meeting with NovaTech AI! We have received your request for <strong>{pref_date}</strong> at <strong>{pref_time}</strong>.</p>
                    <p style="font-size: 14px;"><strong>Your Ticket Reference:</strong> <code style="background: #f3f4f6; padding: 2px 6px; border-radius: 4px;">{ticket_id}</code></p>
                    <p>Our team will review this and confirm your slot shortly via email.</p>
                    
                    <p style="font-size: 12px; color: #9ca3af; margin-top: 25px; text-align: center;">This is an automated confirmation from NovaTech AI Support.</p>
                </div>
                """
            })
            resend_cust_sent = True
        except Exception as cust_err:
            print("Resend Customer Meeting Email error:", cust_err)

    if not resend_admin_sent:
        admin_body = f"New Meeting Request from {name} ({email}) | Phone: {phone} \nDate: {pref_date} | Time: {pref_time} | Topic: {topic}\nTicket: {ticket_id}"
        send_email_notification(RECEIVER_EMAIL, f"Meeting Request [{ticket_id}] from {name}", admin_body)

    if not resend_cust_sent:
        cust_msg = f"Hi {name},\n\nYour meeting request for {pref_date} at {pref_time} has been received.\nTicket Reference: {ticket_id}\n\nOur team will confirm your meeting slot shortly."
        send_email_notification(email, f"Meeting Request [{ticket_id}] — NovaTech AI", cust_msg)

    return jsonify({
        "ok": True,
        "ticket_id": ticket_id,
        "message": f"Meeting request submitted! Ticket ID: {ticket_id}. We will confirm your appointment via email."
    })

@app.route("/faq/search", methods=["GET"])
def faq_search():
    q = request.args.get("q", "").strip().lower()
    cat = request.args.get("category", "").strip()

    conn = get_db_connection()
    query = "SELECT * FROM faqs WHERE 1=1"
    params = []

    if cat and cat.lower() != "all":
        query += " AND category = ?"
        params.append(cat)

    if q:
        query += " AND (LOWER(question) LIKE ? OR LOWER(answer) LIKE ? OR LOWER(category) LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])

    query += " ORDER BY id ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    msg = data.get("message", "").strip().lower()
    if not msg:
        return jsonify({"reply": "Hello! How can NovaTech AI assist you today?"})

    conn = get_db_connection()

    # 1. Direct keyword search in chat_knowledge
    knowledge_rows = conn.execute("SELECT keyword, response FROM chat_knowledge").fetchall()
    for row in knowledge_rows:
        kw = row["keyword"].lower()
        if kw in msg:
            conn.close()
            return jsonify({"reply": row["response"]})

    # 2. Search FAQs for text match
    words = [w for w in re.findall(r'\w+', msg) if len(w) > 3]
    faqs_rows = conn.execute("SELECT question, answer FROM faqs").fetchall()
    for faq in faqs_rows:
        q_text = faq["question"].lower()
        if any(word in q_text for word in words):
            conn.close()
            return jsonify({"reply": f"Here is what I found:\n\n**{faq['question']}**\n{faq['answer']}"})

    conn.close()

    # 3. Fallback response with suggested actions
    return jsonify({
        "reply": "I couldn't find a specific match in my database for that question. Would you like to speak with our support team or leave us a message?",
        "unknown": True,
        "actions": [
            {"label": "💬 WhatsApp Support", "url": "https://wa.me/919835928274?text=Hello%20TechHub%2C%20I%20need%20assistance."},
            {"label": "✉️ Send Message", "action": "open_contact"},
            {"label": "📅 Book Meeting", "action": "open_meeting"}
        ]
    })

# ── Admin Routes ─────────────────────────────────────────────────────────────
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        # Support both traditional form POSTs and JSON POSTs (fetch/ajax)
        data_json = request.get_json(silent=True)
        if data_json:
            username = str(data_json.get("username", "")).strip()
            password = str(data_json.get("password", ""))
            source = 'json'
        else:
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            source = 'form'

        # Debug info (do not print raw passwords)
        try:
            content_type = request.headers.get('Content-Type')
            masked_pw = '*' * len(password)
            print(f"[DEBUG] /admin/login POST via {source} content-type={content_type} username='{username}' password_mask='{masked_pw}'")
        except Exception:
            print("[DEBUG] /admin/login POST (unable to print debug details)")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            session["admin_user"] = username
            token = create_admin_jwt(username)
            flash("Welcome to NovaTech Admin Dashboard! Authenticated via JWT.", "success")
            resp = make_response(redirect(url_for("admin_dashboard")))
            resp.set_cookie("jwt_token", token, httponly=True, max_age=86400, samesite="Lax")
            return resp
        else:
            # Debug: log failed admin login attempts (do not expose password in logs)
            try:
                user_match = (username == ADMIN_USERNAME)
                pass_match = (password == ADMIN_PASSWORD)
                print(f"[DEBUG] Admin login failed. username='{username}' user_match={user_match} pass_match={pass_match}")
            except Exception:
                print("[DEBUG] Admin login failed (unable to compute match details)")
            flash("Invalid admin username or password.", "danger")
    return render_template(
        "admin_login.html",
        year=datetime.now().year,
        firebase_config=json.dumps(FIREBASE_WEB_CONFIG),
    )

@app.route("/auth/google-login", methods=["POST"])
def auth_google_login():
    payload = request.get_json(silent=True) or {}
    id_token = payload.get("idToken", "")

    decoded, err = verify_firebase_id_token(id_token)
    if err:
        return jsonify({"ok": False, "error": err}), 401

    user_email = decoded["email"].strip().lower()

    if ADMIN_GOOGLE_EMAILS and user_email not in ADMIN_GOOGLE_EMAILS:
        return jsonify({"ok": False, "error": "This Google account is not allowed for admin access."}), 403

    session["admin_logged_in"] = True
    session["admin_user"] = user_email
    token = create_admin_jwt(user_email)
    
    resp = jsonify({"ok": True, "redirect": url_for("admin_dashboard")})
    resp.set_cookie("jwt_token", token, httponly=True, max_age=86400, samesite="Lax")
    return resp

@app.route("/admin/logout")
def admin_logout():
    token = request.cookies.get("jwt_token")
    if token:
        revoke_jwt_token(token)
    session.clear()
    flash("Logged out successfully. JWT token revoked and removed from cookies.", "info")
    resp = make_response(redirect(url_for("admin_login")))
    resp.set_cookie("jwt_token", "", expires=0, max_age=0, httponly=True)
    return resp

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

@app.route("/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        email = data.get("email", "").strip().lower()
        password = data.get("password", "").strip()

        if not email or not password:
            return jsonify({"ok": False, "error": "Email and password are required."}), 400
        if not valid_email(email):
            return jsonify({"ok": False, "error": "Please enter a valid email address."}), 400

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if not user:
            return jsonify({"ok": False, "error": "No account found with this email. Please sign up first."}), 401
        if user.get("auth_provider") == "google":
            return jsonify({"ok": False, "error": "This account uses Google sign-in. Please use the Google button."}), 401
        if user.get("password_hash") != hash_password(password):
            return jsonify({"ok": False, "error": "Incorrect password. Please try again."}), 401

        session["user_logged_in"] = True
        session["user_email"] = user.get("email", email)
        session["user_name"] = user.get("name", "User")
        session["user_avatar"] = user.get("avatar_url", "")

        return jsonify({"ok": True, "redirect": url_for("index"), "message": f"Welcome back, {user.get('name', 'User')}!"})

    return render_template(
        "user_auth.html",
        year=datetime.now().year,
        auth_mode="login",
        page_title="Login",
        firebase_config=json.dumps(FIREBASE_WEB_CONFIG),
    )

@app.route("/register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "").strip()
        confirm_password = data.get("confirm_password", "").strip()

        if not name or not email or not password:
            return jsonify({"ok": False, "error": "Name, email, and password are required."}), 400
        if len(name) < 2:
            return jsonify({"ok": False, "error": "Name must be at least 2 characters."}), 400
        if not valid_email(email):
            return jsonify({"ok": False, "error": "Please enter a valid email address."}), 400
        if len(password) < 6:
            return jsonify({"ok": False, "error": "Password must be at least 6 characters."}), 400
        if password != confirm_password:
            return jsonify({"ok": False, "error": "Passwords do not match."}), 400

        conn = get_db_connection()
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            conn.close()
            return jsonify({"ok": False, "error": "An account with this email already exists. Try logging in."}), 409

        try:
            conn.execute(
                "INSERT INTO users (name, email, password_hash, auth_provider, username) VALUES (?, ?, ?, 'email', ?)",
                (name, email, hash_password(password), email)
            )
        except Exception:
            conn.execute(
                "INSERT INTO users (name, email, password_hash, auth_provider) VALUES (?, ?, ?, 'email')",
                (name, email, hash_password(password))
            )
        conn.commit()
        conn.close()

        session["user_logged_in"] = True
        session["user_email"] = email
        session["user_name"] = name

        return jsonify({"ok": True, "redirect": url_for("index"), "message": f"Welcome to TeckHub, {name}!"})

    return render_template(
        "user_auth.html",
        year=datetime.now().year,
        auth_mode="register",
        page_title="Sign Up",
        firebase_config=json.dumps(FIREBASE_WEB_CONFIG),
    )

@app.route("/auth/google-user", methods=["POST"])
def auth_google_user():
    payload = request.get_json(silent=True) or {}
    id_token = payload.get("idToken", "")

    decoded, err = verify_firebase_id_token(id_token)
    if err:
        return jsonify({"ok": False, "error": err}), 401

    user_email = decoded["email"].strip().lower()
    user_name = decoded.get("name", "User")
    user_picture = decoded.get("picture", "")

    # Upsert user in DB
    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (user_email,)).fetchone()
    if not existing:
        try:
            conn.execute(
                "INSERT INTO users (name, email, auth_provider, avatar_url, email_verified, username) VALUES (?, ?, 'google', ?, TRUE, ?)",
                (user_name, user_email, user_picture, user_email)
            )
        except Exception:
            conn.execute(
                "INSERT INTO users (name, email, auth_provider, avatar_url, email_verified) VALUES (?, ?, 'google', ?, TRUE)",
                (user_name, user_email, user_picture)
            )
        conn.commit()
    conn.close()

    session["user_logged_in"] = True
    session["user_email"] = user_email
    session["user_name"] = user_name
    session["user_avatar"] = user_picture

    return jsonify({"ok": True, "redirect": url_for("index"), "message": f"Welcome, {user_name}!"})

@app.route("/logout")
def user_logout():
    token = request.cookies.get("jwt_token")
    if token:
        revoke_jwt_token(token)
    session.pop("user_logged_in", None)
    session.pop("user_email", None)
    session.pop("user_name", None)
    session.pop("user_avatar", None)
    session.clear()
    flash("You have been logged out and your token has been revoked.", "info")
    resp = make_response(redirect(url_for("user_login")))
    resp.set_cookie("jwt_token", "", expires=0, max_age=0, httponly=True)
    return resp

@app.route("/admin")
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    contacts_list = [dict(r) for r in conn.execute("SELECT * FROM contacts ORDER BY id DESC").fetchall()]
    meetings_list = [dict(r) for r in conn.execute("SELECT * FROM meetings ORDER BY id DESC").fetchall()]
    faqs_list = [dict(r) for r in conn.execute("SELECT * FROM faqs ORDER BY id ASC").fetchall()]
    knowledge_list = [dict(r) for r in conn.execute("SELECT * FROM chat_knowledge ORDER BY keyword ASC").fetchall()]
    email_logs_list = [dict(r) for r in conn.execute("SELECT * FROM email_logs ORDER BY id DESC LIMIT 50").fetchall()]

    stats_data = {
        "total_contacts": len(contacts_list),
        "new_contacts": sum(1 for c in contacts_list if c["status"] == "New"),
        "total_meetings": len(meetings_list),
        "pending_meetings": sum(1 for m in meetings_list if m["status"] == "Pending"),
        "total_faqs": len(faqs_list),
        "total_keywords": len(knowledge_list)
    }
    conn.close()
    return render_template("admin.html",
                           contacts=contacts_list,
                           meetings=meetings_list,
                           faqs=faqs_list,
                           knowledge=knowledge_list,
                           email_logs=email_logs_list,
                           stats=stats_data,
                           admin_username=ADMIN_USERNAME,
                           year=datetime.now().year)

@app.route("/admin/contact/status", methods=["POST"])
@admin_required
def admin_update_contact_status():
    cid = request.form.get("id")
    status = request.form.get("status")
    conn = get_db_connection()
    conn.execute("UPDATE contacts SET status = ? WHERE id = ?", (status, cid))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/admin/contact/delete", methods=["POST"])
@admin_required
def admin_delete_contact():
    cid = request.form.get("id")
    conn = get_db_connection()
    conn.execute("DELETE FROM contacts WHERE id = ?", (cid,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/admin/meeting/status", methods=["POST"])
@admin_required
def admin_update_meeting_status():
    mid = request.form.get("id")
    status = request.form.get("status")
    conn = get_db_connection()
    conn.execute("UPDATE meetings SET status = ? WHERE id = ?", (status, mid))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/admin/meeting/delete", methods=["POST"])
@admin_required
def admin_delete_meeting():
    mid = request.form.get("id")
    conn = get_db_connection()
    conn.execute("DELETE FROM meetings WHERE id = ?", (mid,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/admin/faq/save", methods=["POST"])
@admin_required
def admin_save_faq():
    fid = request.form.get("id")
    question = request.form.get("question", "").strip()
    answer = request.form.get("answer", "").strip()
    category = request.form.get("category", "General").strip()

    if not question or not answer:
        return jsonify({"ok": False, "error": "Question and Answer are required."}), 400

    conn = get_db_connection()
    if fid:
        conn.execute("UPDATE faqs SET question = ?, answer = ?, category = ? WHERE id = ?", (question, answer, category, fid))
    else:
        conn.execute("INSERT INTO faqs (question, answer, category) VALUES (?, ?, ?)", (question, answer, category))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/admin/faq/delete", methods=["POST"])
@admin_required
def admin_delete_faq():
    fid = request.form.get("id")
    conn = get_db_connection()
    conn.execute("DELETE FROM faqs WHERE id = ?", (fid,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/admin/chat-knowledge/save", methods=["POST"])
@admin_required
def admin_save_chat_knowledge():
    kid = request.form.get("id")
    keyword = request.form.get("keyword", "").strip().lower()
    response_text = request.form.get("response", "").strip()

    if not keyword or not response_text:
        return jsonify({"ok": False, "error": "Keyword and Response are required."}), 400

    conn = get_db_connection()
    if kid:
        conn.execute("UPDATE chat_knowledge SET keyword = ?, response = ? WHERE id = ?", (keyword, response_text, kid))
    else:
        conn.execute("INSERT INTO chat_knowledge (keyword, response) VALUES (?, ?)", (keyword, response_text))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/admin/chat-knowledge/delete", methods=["POST"])
@admin_required
def admin_delete_chat_knowledge():
    kid = request.form.get("id")
    conn = get_db_connection()
    conn.execute("DELETE FROM chat_knowledge WHERE id = ?", (kid,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/blog")
def blog():
    cats = ["All"] + sorted(set(p["category"] for p in blog_posts))
    return render_template("blog.html", posts=blog_posts, categories=cats, year=datetime.now().year)

@app.route("/blog/<int:post_id>")
def blog_post(post_id):
    post = next((p for p in blog_posts if p["id"]==post_id), None)
    if not post: return redirect(url_for("blog"))
    related = [p for p in blog_posts if p["id"]!=post_id][:3]
    return render_template("blog_post.html", post=post, related=related, year=datetime.now().year)

@app.route("/technologies")
def technologies():
    return render_template("technologies.html", tech_stack=tech_stack, year=datetime.now().year)

@app.route("/industries")
def industries_page():
    return render_template("industries.html", industries=industries, year=datetime.now().year)

@app.route("/careers")
def careers():
    depts = ["All"] + sorted(set(j["dept"] for j in jobs))
    return render_template("careers.html", jobs=jobs, departments=depts, values=values, year=datetime.now().year)

@app.route("/privacy")
def privacy():
    return render_template("privacy.html", year=datetime.now().year)

@app.route("/terms")
def terms():
    return render_template("terms.html", year=datetime.now().year)

@app.route("/newsletter", methods=["POST"])
def newsletter_sub():
    email = request.json.get("email","").strip() if request.json else request.form.get("email", "").strip()
    if not valid_email(email):
        return jsonify({"ok":False,"error":"Invalid email address."})

    conn = get_db_connection()
    send_email_notification(email, "Subscribed to NovaTech Insights", "Welcome! You have been subscribed to NovaTech Insights newsletter.")
    conn.close()
    return jsonify({"ok":True,"message":"You're subscribed! Welcome to NovaTech Insights."})

# ── Global Error Handlers (Return JSON for API/AJAX/POST requests) ─────────────
def is_api_request():
    return (
        request.is_json
        or request.method == "POST"
        or request.headers.get("Accept") == "application/json"
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or any(request.path.startswith(prefix) for prefix in ["/auth/", "/admin/", "/chat", "/contact", "/meeting/", "/faq/", "/newsletter"])
    )

@app.errorhandler(404)
def handle_404(e):
    if is_api_request():
        return jsonify({"ok": False, "error": "The requested API endpoint was not found (404)."}), 404
    return render_template("index.html", year=datetime.now().year), 404

@app.errorhandler(500)
def handle_500(e):
    if is_api_request():
        return jsonify({"ok": False, "error": "Internal server error (500). Please try again later."}), 500
    return render_template("index.html", year=datetime.now().year), 500

@app.errorhandler(Exception)
def handle_exception(e):
    # Pass through standard HTTP errors (like 404, 500 handled above)
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        if is_api_request():
            return jsonify({"ok": False, "error": f"{e.description} ({e.code})"}), e.code
        return e
    import traceback
    traceback.print_exc()
    print(f"[ERROR] Unhandled Server Exception: {e}")
    if is_api_request():
        err_msg = str(e) if (app.debug or str(e)) else "An internal server error occurred. Please try again."
        return jsonify({"ok": False, "error": err_msg}), 500
    return render_template("index.html", year=datetime.now().year), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
