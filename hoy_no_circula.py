from flask import Flask, request, render_template
import re
app = Flask(__name__)
def validar_placa(placa):
    return re.fullmatch(r'[A-Za-z]{3}\d{1,4}', placa) is not None
def hoy_no_circula(placa, dia):
    restricciones = {
        "lunes": [5, 6],
        "martes": [7, 8],
        "miercoles": [4, 3],
        "miércoles": [4, 3],
        "jueves": [1, 2],
        "viernes": [0, 9],
    }
    if dia not in restricciones:
        return None
    ultimo_digito = int(placa[-1]) if placa[-1].isdigit() else None
    if ultimo_digito is None:
        return None
    return ultimo_digito in restricciones[dia]
@app.route('/')
def index():
    return render_template('index.html', message=None)
@app.route('/verificar_hoy_no_circula', methods=['POST'])
def verificar_hoy_no_circula():
    placa = request.form.get('placa')
    if not placa:
        message = "Por favor, proporciona una placa válida."
    elif not validar_placa(placa):
        message = "Por favor, introduce una placa válida (ejemplo: ABC1234)."
    else:
        dia_no_circula = hoy_no_circula(placa)
        if dia_no_circula is None:
            message = "La placa no es válida."
        else:
            message = f"La placa {placa} <strong>NO</strong> puede circular el día {dia_no_circula.capitalize()}."
    return render_template('index.html', message=message)
if __name__ == "__main__":
    app.run(debug=True)