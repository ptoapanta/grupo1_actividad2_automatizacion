"""
models.py — Modelos de datos para el análisis macroeconómico del Euro
=====================================================================

"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# ─────────────────────────────────────────────
# MODELO 1: MacroIndicator  (≈ Customer)
# Catálogo de indicadores macroeconómicos.
# ─────────────────────────────────────────────
class MacroIndicator(db.Model):
    """Catálogo de indicadores macroeconómicos del Euro.

    Cada fila representa UN indicador (ej. "PIB Eurozona",
    "IPC Armonizado", "Tipo de cambio EUR/USD").

    Equivale al modelo Customer del tutorial:
      - 'Customer'  → 'MacroIndicator'
      - email único → codigo único (ej. "EURUSD", "CPI_EA")
      - pais        → fuente_datos (BCE, Eurostat, etc.)
      - activo      → activo (seguimos publicando este indicador)
    """
    __tablename__ = 'macro_indicators'

    id          = db.Column(db.Integer, primary_key=True)
    codigo      = db.Column(db.String(50),  unique=True, nullable=False)  # "EURUSD", "CPI_EA"
    nombre      = db.Column(db.String(200), nullable=False)               # nombre largo
    categoria   = db.Column(db.String(50))   # "tipo_cambio", "inflacion", "pib", "empleo"
    unidad      = db.Column(db.String(50))   # "%", "índice", "millones EUR"
    frecuencia  = db.Column(db.String(20))   # "diaria", "mensual", "trimestral"
    fuente_datos = db.Column(db.String(100)) # "BCE", "Eurostat", "Fed", "Bloomberg"
    descripcion = db.Column(db.Text)
    activo      = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación 1→N con las series de datos
    series = db.relationship('DataPoint', backref='indicator', lazy=True)

    def to_dict(self):
        return {
            'id':          self.id,
            'codigo':      self.codigo,
            'nombre':      self.nombre,
            'categoria':   self.categoria,
            'unidad':      self.unidad,
            'frecuencia':  self.frecuencia,
            'fuente_datos': self.fuente_datos,
            'descripcion': self.descripcion,
            'activo':      self.activo,
            'total_observaciones': len(self.series),
            'created_at':  self.created_at.isoformat() if self.created_at else None,
        }


# ─────────────────────────────────────────────
# MODELO 2: DataPoint  (≈ Transaction)
# Una observación puntual de un indicador.
# ─────────────────────────────────────────────
class DataPoint(db.Model):
    """Punto de dato (observación) de un indicador macroeconómico.

    Equivale al modelo Transaction del tutorial:
      - 'Transaction'         → 'DataPoint'
      - customer_id  (FK)     → indicator_id (FK)
      - monto                 → valor
      - moneda                → moneda (EUR, USD…)
      - tipo                  → tipo_dato ("spot", "proyeccion", "revision")
      - estado                → estado ("confirmado", "preliminar", "revisado")
      - referencia_externa    → referencia_fuente (ID/URL del proveedor)
      - metadata (JSON)       → metadata (datos extra, ej. intervalo de confianza)
    """
    __tablename__ = 'data_points'

    id              = db.Column(db.Integer, primary_key=True)
    indicator_id    = db.Column(db.Integer, db.ForeignKey('macro_indicators.id'), nullable=False)

    # Valor y contexto
    valor           = db.Column(db.Numeric(18, 6), nullable=False)  # más decimales que precio
    valor_anterior  = db.Column(db.Numeric(18, 6))                  # período previo
    variacion_pct   = db.Column(db.Numeric(10, 4))                  # % cambio vs anterior

    # Moneda o contexto monetario (EUR, USD, puntos básicos…)
    moneda          = db.Column(db.String(10), default='EUR')

    # Tipo y estado del dato
    tipo_dato       = db.Column(db.String(30), nullable=False)       # spot, proyeccion, revision
    estado          = db.Column(db.String(20), default='confirmado') # confirmado, preliminar, revisado

    # Referencia al dato de la fuente
    referencia_fuente = db.Column(db.String(200))  # URL o ID del proveedor

    # Período al que corresponde el dato
    fecha_referencia = db.Column(db.Date, nullable=False)   # ej. 2024-Q1 → 2024-01-01
    periodo_label    = db.Column(db.String(20))             # "2024-Q1", "2024-03", "2024-03-27"

    # Metadatos flexibles (bandas de confianza, notas, revisiones, etc.)
    metadata         = db.Column(db.JSON)

    # Timestamps
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Auditoría
    audit_logs = db.relationship('AuditLog', backref='data_point', lazy=True)

    def to_dict(self):
        return {
            'id':               self.id,
            'indicator_id':     self.indicator_id,
            'indicator_codigo': self.indicator.codigo if self.indicator else None,
            'indicator_nombre': self.indicator.nombre if self.indicator else None,
            'valor':            float(self.valor),
            'valor_anterior':   float(self.valor_anterior) if self.valor_anterior else None,
            'variacion_pct':    float(self.variacion_pct)  if self.variacion_pct  else None,
            'moneda':           self.moneda,
            'tipo_dato':        self.tipo_dato,
            'estado':           self.estado,
            'referencia_fuente': self.referencia_fuente,
            'fecha_referencia': self.fecha_referencia.isoformat() if self.fecha_referencia else None,
            'periodo_label':    self.periodo_label,
            'metadata':         self.metadata,
            'created_at':       self.created_at.isoformat() if self.created_at else None,
        }


# ─────────────────────────────────────────────
# MODELO 3: AuditLog  
# Trazabilidad de cambios en los datos.
# ─────────────────────────────────────────────
class AuditLog(db.Model):
    """Registro de auditoría.

    """
    __tablename__ = 'audit_logs'

    id            = db.Column(db.Integer, primary_key=True)
    data_point_id = db.Column(db.Integer, db.ForeignKey('data_points.id'))

    accion            = db.Column(db.String(50), nullable=False)  # created, updated, deleted
    usuario           = db.Column(db.String(100))
    ip_address        = db.Column(db.String(50))
    datos_anteriores  = db.Column(db.JSON)
    datos_nuevos      = db.Column(db.JSON)
    timestamp         = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':               self.id,
            'data_point_id':    self.data_point_id,
            'accion':           self.accion,
            'usuario':          self.usuario,
            'ip_address':       self.ip_address,
            'timestamp':        self.timestamp.isoformat() if self.timestamp else None,
            'datos_anteriores': self.datos_anteriores,
            'datos_nuevos':     self.datos_nuevos,
        }


# ─────────────────────────────────────────────
# HELPER: crear log de auditoría
# ─────────────────────────────────────────────
def create_audit_log(data_point_id, accion, usuario='system',
                     datos_anteriores=None, datos_nuevos=None):
    """Registrar un cambio en audit_logs.

    Uso:
        log = create_audit_log(
            data_point_id=42,
            accion='updated',
            usuario='etl_pipeline',
            datos_anteriores={'estado': 'preliminar'},
            datos_nuevos={'estado': 'confirmado'}
        )
        db.session.commit()
    """
    from flask import request as flask_request
    log = AuditLog(
        data_point_id=data_point_id,
        accion=accion,
        usuario=usuario,
        ip_address=flask_request.remote_addr if flask_request else None,
        datos_anteriores=datos_anteriores,
        datos_nuevos=datos_nuevos,
    )
    db.session.add(log)
    return log
