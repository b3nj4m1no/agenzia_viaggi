# app.py
import os
import json
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from fpdf import FPDF
import tempfile
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import csv
from flask import Response

app = Flask(__name__)
app.config['SECRET_KEY'] = 'uSjjaCvtgXUe'

# Cartella per i file temporanei
TEMP_DIR = tempfile.gettempdir()

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model (esempio base)
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

# Utenti demo (in produzione usa un database!)
users = {
    "admin": User(id=1, username="admin", password_hash=generate_password_hash("password123"))
}

@login_manager.user_loader
def load_user(user_id):
    for user in users.values():
        if str(user.id) == str(user_id):
            return user
    return None

# app.py (modifiche alla classe PDFGenerator)
class PDFGenerator(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.watermark_path = os.path.join(os.path.dirname(__file__), 'static/watermark.png')
    
    def header(self):
        # Immagine di sfondo
        if os.path.exists(self.watermark_path):
            self.image(self.watermark_path, x=0, y=0, w=self.w, h=self.h, type='PNG')
        
        # Logo e intestazione
        self.set_y(15)
        self.set_font('Arial', 'B', 24)
        self.set_text_color(13, 71, 161)  # Blu scuro
        self.cell(0, 9, "SunTravel Agency", 0, 1, 'C')
        
        self.set_font('Arial', '', 16)
        self.set_text_color(251, 191, 36)  # Giallo oro
        self.cell(0, 9, "Conferma Prenotazione", 0, 1, 'C')
        
        # Data corrente
        self.set_font('Arial', '', 9)
        self.set_text_color(90, 90, 90)
        self.cell(0, 9, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, 'R')
        
        # Linea decorativa
        self.set_draw_color(251,191,36)  # Giallo oro
        self.set_line_width(0.5)
        self.line(9, 45, self.w - 9, 45)
        self.ln(15)
    
    def footer(self):
        # Calcola la posizione Y per la linea di separazione
        separator_y = self.get_y() + 5
        
        # Disegna la linea di separazione
        self.set_draw_color(200, 200, 200)  # Grigio chiaro
        self.set_line_width(0.5)
        self.line(10, separator_y, self.w - 10, separator_y)
        
        # Spazio dopo la linea
        self.set_y(separator_y + 10)
        
        self.set_font('Arial', 'I', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, "SunTravel Agency - Via del Viaggio, 123 - 00100 Roma", 0, 1, 'C')
        self.cell(0, 5, "Tel: +39 06 1234567 - Email: info@suntravel.it - P.IVA: 12345678901", 0, 1, 'C')
        self.cell(0, 5, f"Pagina {self.page_no()}", 0, 0, 'C')
    
    def add_section_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_fill_color(224, 242, 254)  # Azzurro chiaro
        self.set_text_color(13, 71, 161)    # Blu scuro
        self.cell(0, 9, title, 0, 1, 'L', 1)
        self.ln(5)
    
    def add_travel_details(self, data):
        # Dettagli Cliente
        self.add_section_title("Dettagli Cliente")
        self.set_font('Arial', '', 12)
        self.set_text_color(0, 0, 0)
        
        self.cell(40, 8, "Nome e Cognome:", 0, 0)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, f"{data['cliente']['nome']} {data['cliente']['cognome']}", 0, 1)
        
        self.set_font('Arial', '', 12)
        self.cell(40, 8, "Email:", 0, 0)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, data['cliente']['email'], 0, 1)
        
        self.set_font('Arial', '', 12)
        self.cell(40, 8, "Telefono:", 0, 0)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, data['cliente']['telefono'], 0, 1)
        self.ln(9)
        
        # Dettagli Viaggio
        self.add_section_title("Dettagli Viaggio")
        self.set_font('Arial', '', 12)
        self.set_text_color(0, 0, 0)
        
        self.cell(50, 8, "Destinazione:", 0, 0)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, data['viaggio']['destinazione'], 0, 1)
        
        self.set_font('Arial', '', 12)
        self.cell(50, 8, "Data Partenza:", 0, 0)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, data['viaggio']['data_partenza'], 0, 1)
        
        self.set_font('Arial', '', 12)
        self.cell(50, 8, "Data Ritorno:", 0, 0)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, data['viaggio']['data_ritorno'], 0, 1)
        
        self.set_font('Arial', '', 12)
        self.cell(50, 8, "Numero Persone:", 0, 0)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, data['viaggio']['numero_persone'], 0, 1)
        self.ln(15)
        
        # Servizi Aggiuntivi
        if data['servizi']:
            self.add_section_title("Servizi Aggiuntivi")
            self.set_font('Arial', 'B', 12)
            self.cell(120, 9, "Servizio", 0, 0)
            self.cell(0, 9, "Prezzo", 0, 1)
            self.set_draw_color(200, 200, 200)
            self.set_line_width(0.2)
            self.line(9, self.get_y(), self.w - 9, self.get_y())
            self.ln(2)
            
            for idx, servizio in enumerate(data['servizi']):
                self.set_font('Arial', '', 12)
                self.cell(120, 8, servizio['nome'], 0, 0)
                self.cell(0, 8, f"EUR {servizio['prezzo']}", 0, 1)
                
                if idx < len(data['servizi']) - 1:
                    self.set_draw_color(230, 230, 230)
                    self.set_line_width(0.1)
                    self.line(9, self.get_y(), self.w - 9, self.get_y())
                    self.ln(2)
            
            self.ln(5)
        
        # Totale
        self.set_font('Arial', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(13, 71, 161)  # Blu scuro
        self.cell(120, 15, "TOTALE", 0, 0, 'R', 1)
        self.cell(0, 15, f"EUR {data['totale']}", 0, 1, 'R', 1)
        self.ln(20)
        
        # Note
        self.set_font('Arial', 'I', 9)
        self.set_text_color(90, 90, 90)
        self.multi_cell(0, 6, "Grazie per aver scelto SunTravel! La presente conferma costituisce documento valido ai fini fiscali. Per qualsiasi modifica o cancellazione, contattare il nostro ufficio entro 7 giorni dalla data di partenza.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/genera_json', methods=['POST'])
@login_required
def genera_json():
    try:
        data = {
            "timestamp": datetime.now().isoformat(),
            "cliente": {
                "nome": request.form['nome'],
                "cognome": request.form['cognome'],
                "email": request.form['email'],
                "telefono": request.form['telefono']
            },
            "viaggio": {
                "destinazione": request.form['destinazione'],
                "data_partenza": request.form['data_partenza'],
                "data_ritorno": request.form['data_ritorno'],
                "numero_persone": request.form['numero_persone']
            },
            "servizi": [],
            "totale": 0,
            "utente": current_user.username
        }
        
        # Calcolo totale
        base_price = 350 * int(data["viaggio"]["numero_persone"])
        total = base_price

        # Applica sconto se c'è un'offerta valida
        from datetime import date
        data_partenza = data["viaggio"]["data_partenza"]
        for offerta in OFFERTE:
            if (offerta["destinazione"].lower() == data["viaggio"]["destinazione"].lower() and
                data_partenza <= offerta["scadenza"]):
                sconto = (base_price * offerta["sconto_percentuale"]) // 100
                total -= sconto
                data["offerta_applicata"] = offerta["nome"]
                data["sconto"] = sconto
                break

        # Servizi aggiuntivi
        servizi_mapping = {
            "assicurazione": {"nome": "Assicurazione", "prezzo": 50},
            "trasferimento": {"nome": "Trasferimento Aeroporto", "prezzo": 30},
            "wifi": {"nome": "WiFi Viaggio", "prezzo": 20}
        }
        
        for servizio in servizi_mapping:
            if servizio in request.form:
                data["servizi"].append(servizi_mapping[servizio])
                total += servizi_mapping[servizio]["prezzo"]
        
        data["totale"] = total
        
        # Cartella storico per utente
        user_dir = os.path.join(TEMP_DIR, f"storico_{current_user.username}")
        os.makedirs(user_dir, exist_ok=True)
        json_filename = f"prenotazione_{datetime.now().timestamp()}.json"
        json_path = os.path.join(user_dir, json_filename)
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=4)
            
        return jsonify({
            "success": True,
            "message": "JSON generato con successo",
            "data": data,
            "json_path": json_path
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route('/genera_pdf', methods=['POST'])
def genera_pdf():
    try:
        json_data = request.json
        pdf = PDFGenerator()
        pdf.add_page()
        pdf.add_travel_details(json_data)
        
        # Salva il PDF temporaneamente
        pdf_path = os.path.join(TEMP_DIR, f"prenotazione_{datetime.now().timestamp()}.pdf")
        pdf.output(pdf_path)
        
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"conferma_viaggio_{json_data['cliente']['cognome']}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            if user.username == "admin":
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Credenziali non valide")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return render_template('register.html', error="Username già esistente")
        user = User(id=len(users)+1, username=username, password_hash=generate_password_hash(password))
        users[username] = user
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/storico')
@login_required
def storico():
    user_dir = os.path.join(TEMP_DIR, f"storico_{current_user.username}")
    prenotazioni = []
    if os.path.exists(user_dir):
        for filename in os.listdir(user_dir):
            if filename.endswith('.json'):
                with open(os.path.join(user_dir, filename)) as f:
                    data = json.load(f)
                    data['filename'] = filename
                    prenotazioni.append(data)
    # Ricerca per destinazione (opzionale)
    query = request.args.get('q')
    if query:
        prenotazioni = [p for p in prenotazioni if query.lower() in p['viaggio']['destinazione'].lower()]
    prenotazioni.sort(key=lambda x: x['timestamp'], reverse=True)
    return render_template('storico.html', prenotazioni=prenotazioni, query=query or "")

@app.route('/download_json/<filename>')
@login_required
def download_json(filename):
    user_dir = os.path.join(TEMP_DIR, f"storico_{current_user.username}")
    file_path = os.path.join(user_dir, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File non trovato", 404

@app.route('/download_pdf/<filename>')
@login_required
def download_pdf(filename):
    user_dir = os.path.join(TEMP_DIR, f"storico_{current_user.username}")
    json_path = os.path.join(user_dir, filename)
    if not os.path.exists(json_path):
        return "File non trovato", 404
    with open(json_path) as f:
        data = json.load(f)
    pdf = PDFGenerator()
    pdf.add_page()
    pdf.add_travel_details(data)
    pdf_path = os.path.join(user_dir, filename.replace('.json', '.pdf'))
    pdf.output(pdf_path)
    return send_file(pdf_path, as_attachment=True)

# Esempio di rotta protetta
@app.route('/area_riservata')
@login_required
def area_riservata():
    return f"Ciao {current_user.username}, questa è l'area riservata!"

@app.route('/dashboard')
@login_required
def dashboard():
    # Carica offerte
    offerte = OFFERTE

    # Carica riepilogo recensioni
    recensioni = carica_recensioni()
    riepilogo = []
    for destinazione, lista in recensioni.items():
        if lista:
            media = round(sum(r['voto'] for r in lista) / len(lista), 1)
            riepilogo.append({
                "destinazione": destinazione,
                "media": media,
                "num": len(lista)
            })
    # Ordina per media voto decrescente
    riepilogo.sort(key=lambda x: x["media"], reverse=True)

    return render_template('dashboard.html', offerte=offerte, riepilogo_recensioni=riepilogo)

@app.route('/offerte')
def offerte():
    return render_template('offerte.html', offerte=OFFERTE)

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.username != "admin":
        return "Accesso negato", 403

    # Raccogli tutte le prenotazioni di tutti gli utenti
    stats = {
        "totale_prenotazioni": 0,
        "totale_incassi": 0,
        "destinazioni": {}
    }
    all_prenotazioni = []
    for user_folder in os.listdir(TEMP_DIR):
        if user_folder.startswith("storico_"):
            user_dir = os.path.join(TEMP_DIR, user_folder)
            for filename in os.listdir(user_dir):
                if filename.endswith('.json'):
                    with open(os.path.join(user_dir, filename)) as f:
                        data = json.load(f)
                        all_prenotazioni.append(data)
                        stats["totale_prenotazioni"] += 1
                        stats["totale_incassi"] += data.get("totale", 0)
                        dest = data["viaggio"]["destinazione"]
                        stats["destinazioni"][dest] = stats["destinazioni"].get(dest, 0) + 1

    # Destinazioni più richieste (top 5)
    top_dest = sorted(stats["destinazioni"].items(), key=lambda x: x[1], reverse=True)[:5]

    return render_template(
        "admin_dashboard.html",
        stats=stats,
        top_dest=top_dest,
        all_prenotazioni=all_prenotazioni
    )

@app.route('/admin/export_csv')
@login_required
def export_csv():
    if current_user.username != "admin":
        return "Accesso negato", 403

    # Raccogli tutte le prenotazioni
    rows = []
    for user_folder in os.listdir(TEMP_DIR):
        if user_folder.startswith("storico_"):
            user_dir = os.path.join(TEMP_DIR, user_folder)
            for filename in os.listdir(user_dir):
                if filename.endswith('.json'):
                    with open(os.path.join(user_dir, filename)) as f:
                        data = json.load(f)
                        rows.append([
                            data["utente"],
                            data["cliente"]["nome"],
                            data["cliente"]["cognome"],
                            data["viaggio"]["destinazione"],
                            data["viaggio"]["data_partenza"],
                            data["viaggio"]["data_ritorno"],
                            data["viaggio"]["numero_persone"],
                            data.get("totale", 0)
                        ])
    # Prepara CSV
    def generate():
        header = ['Utente', 'Nome', 'Cognome', 'Destinazione', 'Data Partenza', 'Data Ritorno', 'Numero Persone', 'Totale']
        yield ','.join(header) + '\n'
        for row in rows:
            yield ','.join(map(str, row)) + '\n'
    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=prenotazioni.csv"})

OFFERTE = [
    {
        "nome": "Last Minute Maldive",
        "destinazione": "Maldive",
        "descrizione": "Sconto 20% per partenze entro il mese!",
        "sconto_percentuale": 20,
        "scadenza": "2025-06-30"
    },
    {
        "nome": "Pacchetto Family Grecia",
        "destinazione": "Grecia",
        "descrizione": "Pacchetto famiglia: 2 adulti + 2 bambini, WiFi incluso.",
        "sconto_percentuale": 15,
        "scadenza": "2025-07-31"
    },
    {
        "nome": "Speciale New York",
        "destinazione": "New York",
        "descrizione": "Trasferimento aeroporto gratuito e assicurazione inclusa.",
        "sconto_percentuale": 10,
        "scadenza": "2025-08-15"
    }
]

RECENSIONI_PATH = os.path.join(TEMP_DIR, "recensioni.json")

def carica_recensioni():
    if os.path.exists(RECENSIONI_PATH):
        with open(RECENSIONI_PATH) as f:
            return json.load(f)
    return {}

def salva_recensioni(recensioni):
    with open(RECENSIONI_PATH, "w") as f:
        json.dump(recensioni, f, indent=2)

@app.route('/recensisci/<destinazione>', methods=['GET', 'POST'])
@login_required
def recensisci(destinazione):
    recensioni = carica_recensioni()
    if request.method == 'POST':
        testo = request.form['testo']
        voto = int(request.form['voto'])
        user = current_user.username
        nuova_recensione = {
            "utente": user,
            "testo": testo,
            "voto": voto,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        recensioni.setdefault(destinazione, []).append(nuova_recensione)
        salva_recensioni(recensioni)
        return redirect(url_for('storico'))
    return render_template('recensisci.html', destinazione=destinazione)

@app.route('/recensioni/<destinazione>')
def recensioni_destinazione(destinazione):
    recensioni = carica_recensioni()
    lista = recensioni.get(destinazione, [])
    media = round(sum(r['voto'] for r in lista) / len(lista), 1) if lista else None
    return render_template('recensioni.html', destinazione=destinazione, recensioni=lista, media=media)

@app.route('/nuova_prenotazione', methods=['GET', 'POST'])
@login_required
def nuova_prenotazione():
    # --- Ricerca avanzata viaggi ---
    viaggi = []
    for user_folder in os.listdir(TEMP_DIR):
        if user_folder.startswith("storico_"):
            user_dir = os.path.join(TEMP_DIR, user_folder)
            for filename in os.listdir(user_dir):
                if filename.endswith('.json'):
                    with open(os.path.join(user_dir, filename)) as f:
                        data = json.load(f)
                        viaggi.append(data)
    # Filtri
    destinazione = request.args.get('destinazione', '').lower()
    prezzo_min = request.args.get('prezzo_min')
    prezzo_max = request.args.get('prezzo_max')
    data_da = request.args.get('data_da')
    data_a = request.args.get('data_a')
    servizio = request.args.get('servizio')

    risultati = []
    for v in viaggi:
        if destinazione and destinazione not in v['viaggio']['destinazione'].lower():
            continue
        if prezzo_min and v['totale'] < int(prezzo_min):
            continue
        if prezzo_max and v['totale'] > int(prezzo_max):
            continue
        if data_da and v['viaggio']['data_partenza'] < data_da:
            continue
        if data_a and v['viaggio']['data_ritorno'] > data_a:
            continue
        if servizio and servizio not in [s['nome'].lower() for s in v['servizi']]:
            continue
        risultati.append(v)

    destinazioni_mappa = list({v['viaggio']['destinazione'] for v in risultati})

    # --- Fine ricerca avanzata ---

    # ...qui il resto della tua logica per la prenotazione (form, ecc)...
    return render_template(
        'prenotazione.html',
        risultati=risultati,
        destinazioni_mappa=destinazioni_mappa,
        query=request.args
        # ...altri parametri che già passi...
    )

if __name__ == '__main__':
    app.run(debug=True)