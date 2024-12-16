from flask import Flask, render_template, request, flash, redirect, url_for
from hoy_no_circula import hoy_no_circula
from database import Database
import pymysql
from reportlab.pdfgen import canvas
from datetime import datetime
import io
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import black, lightgrey
app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'
def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="registroautos"
    )
@app.route('/registros')
def registros_autos():
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM registros")
    registros = cursor.fetchall()
    connection.close()
    return render_template('admin_panel.html', registros=registros)
@app.route('/')
def index():
    dia = ""
    if request.method == "POST":
        placa = request.form.get("placa")
        dia = request.form.get("dia")
        if placa and dia:
            dia = hoy_no_circula(placa, dia)
    return render_template("index.html", dia=dia)
@app.route("/administrativo")
def administrativo_view():
    return render_template("login.html")
@app.route("/login_action", methods=["POST"])
def login_action():
    username = request.form.get("username")
    password = request.form.get("password")
    if username == "admin" and password == "1234":  
        db = Database()
        registros = db.obtener_citas()
        return render_template("admin_panel.html", registros=registros)
    return "Usuario o contraseña incorrectos", 401
@app.route('/admin')
def admin_panel():
    db = Database()
    registros = db.obtener_citas()
    print("Registros obtenidos:", registros)
    return render_template('admin_panel.html', registros=registros)
@app.route('/registro_cita', methods=['GET', 'POST'])
def registro_cita():
    if request.method == 'POST':
        placa = request.form.get("placa")
        confirm_placa = request.form.get("confirm_placa")
        serie = request.form.get("serie")
        confirm_serie = request.form.get("confirm_serie")
        modelo = request.form.get("modelo")
        correo_electronico = request.form.get("correo_electronico")
        fecha_cita = request.form.get("fecha_cita")
        hora_cita = request.form.get("hora_cita")
        if not all([placa, confirm_placa, serie, confirm_serie, modelo, correo_electronico, fecha_cita, hora_cita]):
            flash("Por favor, completa todos los campos obligatorios.", "error")
            return redirect(url_for("registro_cita"))
        if placa != confirm_placa:
            flash("Las placas no coinciden.", "error")
            return redirect(url_for("registro_cita"))
        if serie != confirm_serie:
            flash("Las series no coinciden.", "error")
            return redirect(url_for("registro_cita"))
        if db.existe_cita(fecha_cita, hora_cita):
            flash("La cita ya existe para esta fecha y hora.", "error")
            return redirect(url_for("registro_cita"))
        db.registrar_cita(placa, confirm_placa, serie, confirm_serie, modelo, correo_electronico, fecha_cita, hora_cita)
        pdf_buffer = generate_pdf(placa, serie, modelo, fecha_cita, hora_cita)
        flash("Cita registrada con éxito. Se ha generado el comprobante.", "success")
        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="comprobante_cita.pdf"
        )
    dias_disponibles, horarios_disponibles = db.obtener_configuracion()
    return render_template("registro_cita.html", dias_disponibles=dias_disponibles, horarios_disponibles=horarios_disponibles)
def generate_pdf(placa, serie, modelo, fecha_cita, hora_cita):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin_x = 50
    title_y = height - 80
    section_start_y = title_y - 50
    line_height = 20
    now = datetime.now()
    fecha_registro = now.strftime("%Y-%m-%d")
    hora_registro = now.strftime("%H:%M:%S")
    c.setFont("Helvetica-Bold", 30)
    c.setFillColor(black)
    c.drawCentredString(width / 2, title_y, "Comprobante de Cita")
    c.setLineWidth(1)
    c.setStrokeColor(lightgrey)
    c.line(margin_x, title_y - 10, width - margin_x, title_y - 10)
    c.setFont("Helvetica", 12)
    c.setFillColor(black)
    c.drawString(margin_x, section_start_y, "Detalles de la Cita:")
    section_start_y -= line_height
    c.drawString(margin_x + 20, section_start_y, f"Placa: {placa}")
    section_start_y -= line_height
    c.drawString(margin_x + 20, section_start_y, f"Serie: {serie}")
    section_start_y -= line_height
    c.drawString(margin_x + 20, section_start_y, f"Modelo: {modelo}")
    section_start_y -= line_height
    c.drawString(margin_x + 20, section_start_y, f"Fecha de la Cita: {fecha_cita}")
    section_start_y -= line_height
    c.drawString(margin_x + 20, section_start_y, f"Hora de la Cita: {hora_cita}")
    section_start_y -= 20
    c.line(margin_x, section_start_y, width - margin_x, section_start_y)
    section_start_y -= line_height
    c.drawString(margin_x, section_start_y, "Registro de Cita:")
    section_start_y -= line_height
    c.drawString(margin_x + 20, section_start_y, f"Fecha de Registro: {fecha_registro}")
    section_start_y -= line_height
    c.drawString(margin_x + 20, section_start_y, f"Hora de Registro: {hora_registro}")
    c.setFont("Helvetica-Oblique", 10)
    footer_y = 40
    c.drawCentredString(width / 2, footer_y, "Gracias por usar nuestro servicio.")
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
@app.route('/verificar_hoy_no_circula', methods=['POST'])
def verificar_hoy_no_circula():
    placa = request.form.get('placa')
    dia = request.form.get('dia').lower()
    if not placa or not dia:
        return "Por favor, proporciona la placa y el día para verificar."
    resultado = hoy_no_circula(placa, dia)
    if resultado is None:
        return "El día seleccionado no es válido o la placa proporcionada no es válida."
    elif resultado:
        return f"La placa {placa} **NO** puede circular el día {dia.capitalize()}."
    else:
        return f"La placa {placa} **SÍ** puede circular el día {dia.capitalize()}."
@app.route('/hoy_no_circula')
def hoy_no_circula_view():
    return render_template('hoy_no_circula.html', message=None)
@app.route('/comprobante/<int:id_cita>')
def comprobante(id_cita):
    return send_file(f"ruta/del/comprobante_{id_cita}.pdf", as_attachment=False)
db = Database()
@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        placa = request.form['placa']
        confirm_placa = request.form['confirm_placa']
        serie = request.form['serie']
        confirm_serie = request.form['confirm_serie']
        modelo = request.form['modelo']
        correo_electronico = request.form['correo_electronico']
        fecha_cita = request.form['fecha_cita']
        hora_cita = request.form['hora_cita']
        if not all([placa, confirm_placa, serie, confirm_serie, modelo, correo_electronico, fecha_cita, hora_cita]):
            flash('Por favor, completa todos los campos obligatorios.', 'error')
            return redirect(url_for('registrar'))
        if placa != confirm_placa:
            flash('Las placas no coinciden.', 'error')
            return redirect(url_for('registrar'))
        if serie != confirm_serie:
            flash('Las series no coinciden.', 'error')
        if db.existe_cita(fecha_cita, hora_cita):
            flash('La cita ya existe para esta fecha y hora.', 'error')
            return redirect(url_for('registrar'))
        db.registrar_cita(placa, confirm_placa, serie, confirm_serie, modelo, correo_electronico, fecha_cita, hora_cita)
        flash('Cita registrada con éxito.', 'success')
        return redirect(url_for('registrar'))
    dias_disponibles, horarios_disponibles = db.obtener_configuracion()
    return render_template('registro_cita.html', dias_disponibles=dias_disponibles, horarios_disponibles=horarios_disponibles)
if __name__ == "__main__":
    app.run(debug=True)


# Ruta para los registros de autos en el panel administrativo
@app.route('/registros')
def registros_autos():
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM registros")
    registros = cursor.fetchall()  # Obtiene todos los registros
    connection.close()
    return render_template('admin_panel.html', registros=registros)

# Ruta para registrar una cita
@app.route('/registro_cita', methods=['GET', 'POST'])
def registro_cita():
    if request.method == 'POST':
        placa = request.form.get("placa")
        confirm_placa = request.form.get("confirm_placa")
        serie = request.form.get("serie")
        confirm_serie = request.form.get("confirm_serie")
        modelo = request.form.get("modelo")
        correo_electronico = request.form.get("correo_electronico")
        fecha_cita = request.form.get("fecha_cita")
        hora_cita = request.form.get("hora_cita")
        
        if not all([placa, confirm_placa, serie, confirm_serie, modelo, correo_electronico, fecha_cita, hora_cita]):
            flash("Por favor, completa todos los campos obligatorios.", "error")
            return redirect(url_for("registro_cita"))
        if placa != confirm_placa:
            flash("Las placas no coinciden.", "error")
            return redirect(url_for("registro_cita"))
        if serie != confirm_serie:
            flash("Las series no coinciden.", "error")
            return redirect(url_for("registro_cita"))

        # Insertar en la base de datos
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO citas (placa, serie, modelo, correo_electronico, fecha_cita, hora_cita)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (placa, serie, modelo, correo_electronico, fecha_cita, hora_cita))
        connection.commit()
        connection.close()

        # Generar PDF de confirmación
        pdf_buffer = generate_pdf(placa, serie, modelo, fecha_cita, hora_cita)
        flash("Cita registrada con éxito. Se ha generado el comprobante.", "success")
        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="comprobante_cita.pdf"
        )

    return render_template("registro_cita.html")

from flask import Flask, request, jsonify

@app.route('/verificar_hoy_no_circula', methods=['POST'])
def verificar_hoy_no_circula():
    placa = request.form.get('placa')
    dia = request.form.get('dia')

    # Aquí debes verificar la placa y el día según las reglas de "Hoy No Circula"
    # Este es solo un ejemplo ficticio:
    if placa[-1] in ['1', '3', '5', '7', '9']:  # Si la última cifra es impar
        estado = "No puede circular"
    else:
        estado = "Puede circular"

    # Responder con los datos en formato JSON
    return jsonify({"placa": placa, "dia": dia, "estado": estado})

if __name__ == '__main__':
    app.run(debug=True)
