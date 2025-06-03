# app.py
import os
import json
from flask import Flask, render_template, request, jsonify, send_file
from fpdf import FPDF
import tempfile
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Cartella per i file temporanei
TEMP_DIR = tempfile.gettempdir()

class PDFGenerator(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Conferma Prenotazione Viaggio', 0, 1, 'C')
        self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')
    
    def add_travel_details(self, data):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Dettagli Cliente', 0, 1)
        self.set_font('Arial', '', 12)
        self.cell(0, 10, f'Nome: {data["cliente"]["nome"]} {data["cliente"]["cognome"]}', 0, 1)
        self.cell(0, 10, f'Email: {data["cliente"]["email"]}', 0, 1)
        self.cell(0, 10, f'Telefono: {data["cliente"]["telefono"]}', 0, 1)
        self.ln(5)
        
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Dettagli Viaggio', 0, 1)
        self.set_font('Arial', '', 12)
        self.cell(0, 10, f'Destinazione: {data["viaggio"]["destinazione"]}', 0, 1)
        self.cell(0, 10, f'Data Partenza: {data["viaggio"]["data_partenza"]}', 0, 1)
        self.cell(0, 10, f'Data Ritorno: {data["viaggio"]["data_ritorno"]}', 0, 1)
        self.cell(0, 10, f'Numero Persone: {data["viaggio"]["numero_persone"]}', 0, 1)
        self.ln(5)
        
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Servizi Aggiuntivi', 0, 1)
        self.set_font('Arial', '', 12)
        for servizio in data["servizi"]:
            self.cell(0, 10, f'- {servizio["nome"]}: EUR {servizio["prezzo"]}', 0, 1)
        self.ln(10)
        
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, f'Totale: EUR {data["totale"]}', 0, 1, 'R')

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
        
        data["totale"] = total
        
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

if __name__ == '__main__':
    app.run(debug=True)