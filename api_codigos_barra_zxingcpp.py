
from flask import Flask, request, jsonify
import cv2
import numpy as np
import os
import base64
import uuid
from zxingcpp import read_barcodes
import requests

app = Flask(__name__)
UPLOAD_FOLDER = "imagenes_guardadas"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# URL a la que se enviará el JSON resultante
DESTINO_URL = "https://prod-134.westus.logic.azure.com:443/workflows/200b309143674b8a8f405bb577c30d8f/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=b8lf9aIrkiU2sjOi2TZT-yNdNS7BLxTxdTN1LP3RWB4"  # Cambiar por tu URL real

def leer_codigos(imagen_np):
    gray = cv2.cvtColor(imagen_np, cv2.COLOR_BGR2GRAY)
    resultados = read_barcodes(gray)
    codigos = []

    for r in resultados:
        codigos.append({
            "valor": r.text
        })

    return codigos

@app.route("/api/leer-codigos", methods=["POST"])
def api_leer_codigos():
    if "imagen" not in request.files:
        return jsonify({"error": "No se envió ninguna imagen"}), 400

    imagen_file = request.files["imagen"]
    if imagen_file.filename == "":
        return jsonify({"error": "Nombre de archivo vacío"}), 400

    try:
        imagen_bytes = imagen_file.read()
        imagen_np = cv2.imdecode(np.frombuffer(imagen_bytes, np.uint8), cv2.IMREAD_COLOR)

        codigos_detectados = leer_codigos(imagen_np)

        nombre_archivo = f"{uuid.uuid4().hex}.jpg"
        ruta_guardado = os.path.join(UPLOAD_FOLDER, nombre_archivo)
        cv2.imwrite(ruta_guardado, imagen_np)

        resultado_json =codigos_detectados
        

        try:
            response = requests.post(DESTINO_URL, json=resultado_json, timeout=5)
            resultado = response.json()
         
        except Exception as e:
            resultado_json["respuesta_envio"] = {
                "error": str(e)
            }

        return jsonify(resultado)

    except Exception as e:
        return jsonify({"error2": str(e)}), 500


@app.route("/api/leer-codigosV2", methods=["POST"])
def api_leer_codigosV2():
    try:
        data = request.get_json()

        if not data or "$content" not in data or "$content-type" not in data:
            return jsonify({"error": "Faltan campos $content o $content-type"}), 400

        # Decodificar Base64
        imagen_base64 = data["$content"]
        try:
            imagen_bytes = base64.b64decode(imagen_base64)
        except Exception as e:
            return jsonify({"error": f"Error al decodificar imagen: {str(e)}"}), 400

        # Convertir a imagen numpy
        imagen_np = cv2.imdecode(np.frombuffer(imagen_bytes, np.uint8), cv2.IMREAD_COLOR)
        if imagen_np is None:
            return jsonify({"error": "No se pudo decodificar la imagen"}), 400

        # Procesar imagen
        codigos_detectados = leer_codigos(imagen_np)

        # Guardar archivo
        nombre_archivo = f"{uuid.uuid4().hex}.jpg"
        ruta_guardado = os.path.join(UPLOAD_FOLDER, nombre_archivo)
        cv2.imwrite(ruta_guardado, imagen_np)

        resultado_json = codigos_detectados

        # Enviar a otro sistema (opcional)
        try:
            response = requests.post(DESTINO_URL, json=resultado_json, timeout=5)
            resultado = response.json()
        except Exception as e:
            resultado = {
                "respuesta_envio": {"error": str(e)}
            }

        return jsonify(resultado)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

