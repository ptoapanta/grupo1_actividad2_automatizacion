"""
app.py — Aplicación Flask principal
====================================
Inicializa la app, la BD, el middleware de autenticación
y registra las rutas. 
"""

import os
from flask import Flask, jsonify, request
from flask_cors import CORS

from .models import db, MacroIndicator, DataPoint
from .routes import api


def create_app(config=None):
    app = Flask(__name__)

    # ── Configuración ──────────────────────────────────────────
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', 'sqlite:///euro_macro.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if config:
        app.config.update(config)

    # ── Extensiones ────────────────────────────────────────────
    CORS(app)
    db.init_app(app)

    # ── Middleware de autenticación ────────────────────────────
       # Endpoints públicos: /api/health y /
    @app.before_request
    def verify_api_key():
        public = ['/api/health', '/']
        if request.path in public:
            return None

        api_key      = request.headers.get('X-API-Key')
        expected_key = os.getenv('API_KEY', 'euro_macro_key_2024')

        if api_key != expected_key:
            return jsonify({
                'error':   'No autorizado',
                'message': 'API key inválida o no proporcionada',
                'hint':    'Incluir header: X-API-Key: <clave>',
            }), 401

    # ── Rutas ──────────────────────────────────────────────────
    app.register_blueprint(api)

    @app.route('/')
    def index():
        return jsonify({
            'api':         'Euro Macro Analysis API',
            'version':     '1.0.0',
            'endpoints': [
                'GET  /api/health',
                'GET  /api/indicators',
                'POST /api/indicators',
                'GET  /api/datapoints',
                'POST /api/datapoints',
                'GET  /api/reports/summary',
            ]
        })

    # ── Crear tablas y datos de ejemplo ───────────────────────
    with app.app_context():
        db.create_all()
        _seed_initial_data()

    return app


def _seed_initial_data():
    """Poblar la BD con indicadores macro del Euro si está vacía."""
    if MacroIndicator.query.first():
        return  # ya hay datos, no duplicar

    indicadores = [
        MacroIndicator(
            codigo='EURUSD', nombre='Tipo de cambio EUR/USD',
            categoria='tipo_cambio', unidad='USD por EUR',
            frecuencia='diaria', fuente_datos='BCE',
            descripcion='Precio de 1 euro en dólares estadounidenses'
        ),
        MacroIndicator(
            codigo='CPI_EA', nombre='IPC Armonizado Eurozona',
            categoria='inflacion', unidad='% interanual',
            frecuencia='mensual', fuente_datos='Eurostat',
            descripcion='Índice de Precios al Consumo Armonizado de la zona euro'
        ),
        MacroIndicator(
            codigo='GDP_EA', nombre='PIB Eurozona',
            categoria='pib', unidad='miles de millones EUR',
            frecuencia='trimestral', fuente_datos='Eurostat',
            descripcion='Producto Interior Bruto de los 20 países de la zona euro'
        ),
        MacroIndicator(
            codigo='UNEMP_EA', nombre='Tasa de Desempleo Eurozona',
            categoria='empleo', unidad='%',
            frecuencia='mensual', fuente_datos='Eurostat',
            descripcion='Porcentaje de población activa desempleada en la zona euro'
        ),
        MacroIndicator(
            codigo='ECB_RATE', nombre='Tipo de Interés BCE',
            categoria='politica_monetaria', unidad='%',
            frecuencia='mensual', fuente_datos='BCE',
            descripcion='Tipo de interés de referencia del Banco Central Europeo'
        ),
    ]

    db.session.add_all(indicadores)
    db.session.commit()
    print("✓ Datos iniciales creados: 5 indicadores macro del Euro")


# ── Punto de entrada ────────────────────────────────────────
if __name__ == '__main__':
    application = create_app()
    application.run(debug=True, port=5000)
