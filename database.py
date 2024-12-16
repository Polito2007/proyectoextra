from flask import flash
import pymysql

class Database:
    def __init__(self, host="localhost", user="root", password="", database="registroautos"):
        self.connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.connection.cursor()
    def obtener_citas(self):
        try:
            query = """
                SELECT Placa, Serie, Modelo, Correo_Electronico, Fecha_Cita, Hora_Cita 
                FROM registros
            """
            self.cursor.execute(query)
            citas = self.cursor.fetchall()
            registros = [
                {
                    'Placa': cita[0],
                    'Serie': cita[1],
                    'Modelo': cita[2],
                    'Correo_Electronico': cita[3],
                    'Fecha_Cita': cita[4],
                    'Hora_Cita': cita[5]
                }
                for cita in citas
            ]
            return registros
        except Exception as e:
            print("Error al obtener citas:", e)
            return []
    def obtener_configuracion(self):
        dias_disponibles = ["Lunes", "Miércoles", "Viernes"]
        horarios_disponibles = ["09:00", "10:00", "12:00"]
        return dias_disponibles, horarios_disponibles
    def obtener_horas_ocupadas(self, fecha_cita):
        query = """
        SELECT Hora_Cita FROM registros WHERE Fecha_Cita = %s
        """
        self.cursor.execute(query, (fecha_cita,))
        ocupadas = self.cursor.fetchall()
        return [hora[0] for hora in ocupadas]
    def registrar_cita(self, placa, confirm_placa, serie, confirm_serie, modelo, correo_electronico, fecha_cita, hora_cita):
        query = """
        INSERT INTO registros (Placa, Confirmar_Placa, Serie, Confirmar_Serie, Modelo, Correo_Electronico, Fecha_Cita, Hora_Cita)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        self.cursor.execute(query, (placa, confirm_placa, serie, confirm_serie, modelo, correo_electronico, fecha_cita, hora_cita))
        self.connection.commit()
    def existe_cita(self, fecha_cita, hora_cita):
        query = """
        SELECT COUNT(*) FROM registros WHERE Fecha_Cita = %s AND Hora_Cita = %s
        """
        self.cursor.execute(query, (fecha_cita, hora_cita))
        result = self.cursor.fetchone()
        return result[0] > 0
    def get_unavailable_days(self):
        query = "SELECT fecha FROM dias_no_disponibles"
        self.cursor.execute(query)
        return [row[0] for row in self.cursor.fetchall()]

    def get_unavailable_hours(self, fecha):
        query = "SELECT hora FROM horas_no_disponibles WHERE fecha = %s"
        self.cursor.execute(query, (fecha,))
        return [row[0] for row in self.cursor.fetchall()]

    def insert_unavailable_day(self, fecha):
        query = "INSERT INTO dias_no_disponibles (fecha) VALUES (%s)"
        self.cursor.execute(query, (fecha,))
        self.connection.commit()

    def insert_unavailable_hour(self, fecha, hora):
        query = "INSERT INTO horas_no_disponibles (fecha, hora) VALUES (%s, %s)"
        self.cursor.execute(query, (fecha, hora))
        self.connection.commit()