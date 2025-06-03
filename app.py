# app.py
import os
import json
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session, flash
from fpdf import FPDF
import tempfile
from datetime import datetime
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Cartella per i file temporanei
TEMP_DIR = tempfile.gettempdir()
UTENTI_FILE = os.path.join(os.path.dirname(__file__), 'utenti.json')

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
        self.set_font('Arial', 'B', 18)
        self.set_text_color(13, 71, 121)  # Blu scuro
        self.cell(0, 10, "SunTravel Agency", 0, 1, 'C')
        
        self.set_font('Arial', '', 12)
        self.set_text_color(251, 191, 36)  # Giallo oro
        self.cell(0, 10, "Conferma Prenotazione", 0, 1, 'C')
        
        # Data corrente
        self.set_font('Arial', '', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, 'R')
        
        # Linea decorativa
        self.set_draw_color(251, 191, 36)  # Giallo oro
        self.set_line_width(0.5)
        self.line(10, 45, self.w - 10, 45)
        self.ln(15)
    
    def footer(self):
        # Calcola la posizione Y per la linea di separazione
        separator_y = self.get_y() + 5
        
        # Disegna la linea di separazione
        self.set_draw_color(180, 180, 180)  # Grigio chiaro
        self.set_line_width(0.5)
        self.line(10, separator_y, self.w - 10, separator_y)
        
        # Spazio dopo la linea
        self.set_y(separator_y + 10)
        
        self.set_font('Arial', 'I', 6)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, "SunTravel Agency - Via del Viaggio, 103 - 00100 Roma", 0, 1, 'C')
        self.cell(0, 5, "Tel: +39 06 1034567 - Email: info@suntravel.it - P.IVA: 10345678901", 0, 1, 'C')
        self.cell(0, 5, f"Pagina {self.page_no()}", 0, 0, 'C')
    
    def add_section_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(224, 242, 254)  # Azzurro chiaro
        self.set_text_color(13, 71, 121)    # Blu scuro
        self.cell(0, 10, title, 0, 1, 'L', 1)
        self.ln(5)
    
    def add_travel_details(self, data):
        # Dettagli Cliente
        self.add_section_title("Dettagli Cliente")
        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0)
        
        self.cell(40, 8, "Nome e Cognome:", 0, 0)
        self.set_font('Arial', 'B', 10)
        self.cell(0, 8, f"{data['cliente']['nome']} {data['cliente']['cognome']}", 0, 1)
        
        self.set_font('Arial', '', 10)
        self.cell(40, 8, "Email:", 0, 0)
        self.set_font('Arial', 'B', 10)
        self.cell(0, 8, data['cliente']['email'], 0, 1)
        
        self.set_font('Arial', '', 10)
        self.cell(40, 8, "Telefono:", 0, 0)
        self.set_font('Arial', 'B', 10)
        self.cell(0, 8, data['cliente']['telefono'], 0, 1)
        self.ln(10)
        
        # Dettagli Viaggio
        self.add_section_title("Dettagli Viaggio")
        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0)
        
        self.cell(50, 8, "Destinazione:", 0, 0)
        self.set_font('Arial', 'B', 10)
        self.cell(0, 8, data['viaggio']['destinazione'], 0, 1)
        
        self.set_font('Arial', '', 10)
        self.cell(50, 8, "Data Partenza:", 0, 0)
        self.set_font('Arial', 'B', 10)
        self.cell(0, 8, data['viaggio']['data_partenza'], 0, 1)
        
        self.set_font('Arial', '', 10)
        self.cell(50, 8, "Data Ritorno:", 0, 0)
        self.set_font('Arial', 'B', 10)
        self.cell(0, 8, data['viaggio']['data_ritorno'], 0, 1)
        
        self.set_font('Arial', '', 10)
        self.cell(50, 8, "Numero Persone:", 0, 0)
        self.set_font('Arial', 'B', 10)
        self.cell(0, 8, data['viaggio']['numero_persone'], 0, 1)
        self.ln(15)
        
        # Servizi Aggiuntivi
        if data['servizi']:
            self.add_section_title("Servizi Aggiuntivi")
            self.set_font('Arial', 'B', 10)
            self.cell(100, 10, "Servizio", 0, 0)
            self.cell(0, 10, "Prezzo", 0, 1)
            self.set_draw_color(180, 180, 180)
            self.set_line_width(0.2)
            self.line(10, self.get_y(), self.w - 10, self.get_y())
            self.ln(2)
            
            for idx, servizio in enumerate(data['servizi']):
                self.set_font('Arial', '', 10)
                self.cell(100, 8, servizio['nome'], 0, 0)
                self.cell(0, 8, f"EUR {servizio['prezzo']}", 0, 1)
                
                if idx < len(data['servizi']) - 1:
                    self.set_draw_color(230, 230, 230)
                    self.set_line_width(0.1)
                    self.line(10, self.get_y(), self.w - 10, self.get_y())
                    self.ln(2)
            
            self.ln(5)
        
        # Totale
        self.set_font('Arial', 'B', 12)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(13, 71, 121)  # Blu scuro
        self.cell(100, 15, "TOTALE", 0, 0, 'R', 1)
        self.cell(0, 15, f"EUR {data['totale']}", 0, 1, 'R', 1)
        self.ln(18)
        
        
        self.set_font('Arial', 'I', 10)
        self.set_text_color(100, 100, 100)
        self.multi_cell(0, 6, "Grazie per aver scelto SunTravel! La presente conferma costituisce documento valido ai fini fiscali. Per qualsiasi modifica o cancellazione, contattare il nostro ufficio entro 7 giorni dalla data di partenza.")

def carica_utenti():
    if not os.path.exists(UTENTI_FILE):
        return []
    with open(UTENTI_FILE, 'r') as f:
        return json.load(f)

def salva_utenti(utenti):
    with open(UTENTI_FILE, 'w') as f:
        json.dump(utenti, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def salva_prenotazione_utente(email, data, pdf_path):
    """Salva la prenotazione nello storico dell'utente (file JSON per ogni utente)."""
    storico_dir = os.path.join(os.path.dirname(__file__), "storico_prenotazioni")
    os.makedirs(storico_dir, exist_ok=True)
    user_file = os.path.join(storico_dir, f"{email}.json")
    if os.path.exists(user_file):
        with open(user_file, "r") as f:
            storico = json.load(f)
    else:
        storico = []
    # Salva anche il path del PDF generato
    data['pdf_path'] = pdf_path
    # Salva anche il JSON della prenotazione
    json_path = os.path.join(storico_dir, f"{email}_{int(datetime.now().timestamp())}.json")
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)
    data['json_path'] = json_path
    storico.append(data)
    with open(user_file, "w") as f:
        json.dump(storico, f, indent=2)

def applica_offerte(data, totale):
    offerte_file = os.path.join(os.path.dirname(__file__), 'offerte.json')
    if not os.path.exists(offerte_file):
        return totale, None
    with open(offerte_file, 'r') as f:
        offerte = json.load(f)
    sconto_applicato = None
    oggi = datetime.now().date()
    for offerta in offerte:
        scadenza = datetime.strptime(offerta['scadenza'], "%Y-%m-%d").date()
        if oggi > scadenza:
            continue
        if offerta['tipo'] == 'percentuale':
            sconto = totale * offerta['valore'] / 100
            totale -= sconto
            sconto_applicato = f"{offerta['titolo']} (-{offerta['valore']}%)"
        elif offerta['tipo'] == 'famiglia':
            if int(data['viaggio']['numero_persone']) >= offerta['valore']:
                totale -= 350  # 1 quota gratis
                sconto_applicato = offerta['titolo']
    return int(totale), sconto_applicato

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/nuova_prenotazione')
def nuova_prenotazione():
    return render_template('prenotazione.html')

@app.route('/genera_json', methods=['POST'])
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
            "totale": 0
        }
        
        # Calcolo totale
        base_price = 350 * int(data["viaggio"]["numero_persone"])
        total = base_price
        
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
        
        totale, sconto_applicato = applica_offerte(data, total)
        data["totale"] = totale
        data["sconto_applicato"] = sconto_applicato
        
        # Salva il JSON temporaneamente
        json_path = os.path.join(TEMP_DIR, f"prenotazione_{datetime.now().timestamp()}.json")
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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        nome = request.form['nome']
        cognome = request.form['cognome']
        ruolo = request.form['ruolo']  # 'cliente' o 'operatore'
        utenti = carica_utenti()
        if any(u['email'] == email for u in utenti):
            flash("Email già registrata", "danger")
            return redirect(url_for('register'))
        utenti.append({
            "email": email,
            "password": hash_password(password),
            "nome": nome,
            "cognome": cognome,
            "ruolo": ruolo
        })
        salva_utenti(utenti)
        flash("Registrazione completata, ora puoi accedere.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        utenti = carica_utenti()
        user = next((u for u in utenti if u['email'] == email and u['password'] == hash_password(password)), None)
        if user:
            session['user'] = {
                "email": user['email'],
                "nome": user['nome'],
                "cognome": user['cognome'],
                "ruolo": user['ruolo']
            }
            flash("Login effettuato", "success")
            return redirect(url_for('area_riservata'))
        flash("Credenziali errate", "danger")
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logout effettuato", "info")
    return redirect(url_for('index'))

@app.route('/area_riservata')
def area_riservata():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('area_riservata.html', user=session['user'])

@app.route('/conferma_prenotazione', methods=['POST'])
def conferma_prenotazione():
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
            "totale": 0
        }

        # Calcolo totale
        base_price = 350 * int(data["viaggio"]["numero_persone"])
        total = base_price

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

        totale, sconto_applicato = applica_offerte(data, total)
        data["totale"] = totale
        data["sconto_applicato"] = sconto_applicato

        # Genera PDF
        pdf = PDFGenerator()
        pdf.add_page()
        pdf.add_travel_details(data)
        pdf_path = os.path.join(TEMP_DIR, f"prenotazione_{datetime.now().timestamp()}.pdf")
        pdf.output(pdf_path)

        # Salva nello storico
        salva_prenotazione_utente(data['cliente']['email'], data, pdf_path)

        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"conferma_viaggio_{data['cliente']['cognome']}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f"Errore nella generazione del PDF: {e}", "danger")
        return redirect(url_for('nuova_prenotazione'))

@app.route('/storico_prenotazioni')
def storico_prenotazioni():
    if 'user' not in session:
        return redirect(url_for('login'))
    email = session['user']['email']
    storico_dir = os.path.join(os.path.dirname(__file__), "storico_prenotazioni")
    user_file = os.path.join(storico_dir, f"{email}.json")
    storico = []
    if os.path.exists(user_file):
        with open(user_file, "r") as f:
            storico = json.load(f)
    # Ricerca per destinazione o data (opzionale)
    query = request.args.get("q", "").lower()
    if query:
        storico = [p for p in storico if query in p["viaggio"]["destinazione"].lower() or query in p["viaggio"]["data_partenza"]]
    return render_template("storico_prenotazioni.html", storico=storico, query=query)

@app.template_filter('basename')
def basename_filter(path):
    return os.path.basename(path)

@app.route('/download/pdf/<path:path>')
def download_prenotazione_pdf(path):
    if 'user' not in session:
        return redirect(url_for('login'))
    storico_dir = os.path.join(os.path.dirname(__file__), "storico_prenotazioni")
    pdf_path = os.path.join(storico_dir, path)
    return send_file(pdf_path, as_attachment=True, mimetype='application/pdf')

@app.route('/download/json/<path:path>')
def download_prenotazione_json(path):
    if 'user' not in session:
        return redirect(url_for('login'))
    storico_dir = os.path.join(os.path.dirname(__file__), "storico_prenotazioni")
    json_path = os.path.join(storico_dir, path)
    return send_file(json_path, as_attachment=True, mimetype='application/json')

@app.route('/offerte')
def offerte():
    offerte_file = os.path.join(os.path.dirname(__file__), 'offerte.json')
    offerte = []
    if os.path.exists(offerte_file):
        with open(offerte_file, 'r') as f:
            offerte = json.load(f)
    return render_template('offerte.html', offerte=offerte)

if __name__ == '__main__':
    app.run(debug=True)