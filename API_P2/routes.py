"""
routes.py — Endpoints REST para análisis macroeconómico del Euro
================================================================
Estructura paralela al tutorial:
  /api/customers        → /api/indicators
  /api/transactions     → /api/datapoints
  /api/reports/daily    → /api/reports/summary
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, date
from sqlalchemy import func

from .models import db, MacroIndicator, DataPoint, AuditLog, create_audit_log

api = Blueprint('api', __name__, url_prefix='/api')


# ══════════════════════════════════════════
# BLOQUE 1 — MacroIndicator  (≈ customers)
# ══════════════════════════════════════════

@api.route('/indicators', methods=['GET'])
def get_indicators():
    """GET /api/indicators — Listar indicadores con filtros.

    Query params:
        activo     (bool)   — solo indicadores activos
        categoria  (str)    — "tipo_cambio", "inflacion", "pib", "empleo"
        frecuencia (str)    — "diaria", "mensual", "trimestral"
        page       (int)    — default 1
        per_page   (int)    — default 50

    """
    try:
        query = MacroIndicator.query

        activo     = request.args.get('activo')
        categoria  = request.args.get('categoria')
        frecuencia = request.args.get('frecuencia')

        if activo is not None:
            query = query.filter_by(activo=(activo.lower() == 'true'))
        if categoria:
            query = query.filter_by(categoria=categoria)
        if frecuencia:
            query = query.filter_by(frecuencia=frecuencia)

        page     = request.args.get('page',     1,  type=int)
        per_page = request.args.get('per_page', 50, type=int)
        result   = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'data': [i.to_dict() for i in result.items],
            'pagination': {
                'page':     page,
                'per_page': per_page,
                'total':    result.total,
                'pages':    result.pages,
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/indicators', methods=['POST'])
def create_indicator():
    """POST /api/indicators — Crear un nuevo indicador.

    Body JSON requerido:
        codigo   (str) — identificador único, ej. "EURUSD"
        nombre   (str) — nombre descriptivo

    Opcionales:
        categoria, unidad, frecuencia, fuente_datos, descripcion

    
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON requerido'}), 400

        required = ['codigo', 'nombre']
        missing  = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({'error': f'Campos requeridos: {missing}'}), 400

        if MacroIndicator.query.filter_by(codigo=data['codigo']).first():
            return jsonify({'error': f"El código '{data['codigo']}' ya existe"}), 409

        indicator = MacroIndicator(
            codigo       = data['codigo'].upper().strip(),
            nombre       = data['nombre'],
            categoria    = data.get('categoria'),
            unidad       = data.get('unidad'),
            frecuencia   = data.get('frecuencia'),
            fuente_datos = data.get('fuente_datos'),
            descripcion  = data.get('descripcion'),
        )
        db.session.add(indicator)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Indicador creado',
            'data': indicator.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ══════════════════════════════════════════
# BLOQUE 2 — DataPoint  (≈ transactions)
# ══════════════════════════════════════════

@api.route('/datapoints', methods=['GET'])
def get_datapoints():
    """GET /api/datapoints — Listar observaciones con filtros.

    Query params:
        indicator_id   (int)  — filtrar por indicador
        codigo         (str)  — filtrar por código (ej. "EURUSD")
        tipo_dato      (str)  — spot | proyeccion | revision
        estado         (str)  — confirmado | preliminar | revisado
        fecha_desde    (ISO)  — fecha_referencia >= fecha_desde
        fecha_hasta    (ISO)  — fecha_referencia <= fecha_hasta
        page / per_page

    
    """
    try:
        query = DataPoint.query

        indicator_id = request.args.get('indicator_id', type=int)
        codigo       = request.args.get('codigo')
        tipo_dato    = request.args.get('tipo_dato')
        estado       = request.args.get('estado')
        fecha_desde  = request.args.get('fecha_desde')
        fecha_hasta  = request.args.get('fecha_hasta')

        if indicator_id:
            query = query.filter_by(indicator_id=indicator_id)
        if codigo:
            ind = MacroIndicator.query.filter_by(codigo=codigo.upper()).first()
            if not ind:
                return jsonify({'error': f"Código '{codigo}' no encontrado"}), 404
            query = query.filter_by(indicator_id=ind.id)
        if tipo_dato:
            query = query.filter_by(tipo_dato=tipo_dato)
        if estado:
            query = query.filter_by(estado=estado)
        if fecha_desde:
            query = query.filter(DataPoint.fecha_referencia >= fecha_desde)
        if fecha_hasta:
            query = query.filter(DataPoint.fecha_referencia <= fecha_hasta)

        query = query.order_by(DataPoint.fecha_referencia.desc())

        page     = request.args.get('page',     1,  type=int)
        per_page = request.args.get('per_page', 50, type=int)
        result   = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'data': [dp.to_dict() for dp in result.items],
            'pagination': {
                'page':     page,
                'per_page': per_page,
                'total':    result.total,
                'pages':    result.pages,
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/datapoints', methods=['POST'])
def create_datapoint():
    """POST /api/datapoints — Registrar una nueva observación.

    Body JSON requerido:
        indicator_id    (int)
        valor           (float)
        tipo_dato       (str)   — spot | proyeccion | revision
        fecha_referencia (ISO)  — fecha del período

    Opcionales:
        valor_anterior, variacion_pct, moneda, estado,
        referencia_fuente, periodo_label, metadata

    
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON requerido'}), 400

        required = ['indicator_id', 'valor', 'tipo_dato', 'fecha_referencia']
        missing  = [f for f in required if data.get(f) is None]
        if missing:
            return jsonify({'error': f'Campos requeridos: {missing}'}), 400

        if not MacroIndicator.query.get(data['indicator_id']):
            return jsonify({'error': f"indicator_id {data['indicator_id']} no existe"}), 404

        dp = DataPoint(
            indicator_id      = data['indicator_id'],
            valor             = data['valor'],
            valor_anterior    = data.get('valor_anterior'),
            variacion_pct     = data.get('variacion_pct'),
            moneda            = data.get('moneda', 'EUR'),
            tipo_dato         = data['tipo_dato'],
            estado            = data.get('estado', 'confirmado'),
            referencia_fuente = data.get('referencia_fuente'),
            fecha_referencia  = date.fromisoformat(data['fecha_referencia']),
            periodo_label     = data.get('periodo_label'),
            metadata          = data.get('metadata'),
        )
        db.session.add(dp)
        db.session.commit()

        create_audit_log(
            data_point_id=dp.id,
            accion='created',
            datos_nuevos=dp.to_dict()
        )
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Observación registrada',
            'data': dp.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ══════════════════════════════════════════
# BLOQUE 3 — Reports  (≈ reports/daily)
# ══════════════════════════════════════════

@api.route('/reports/summary', methods=['GET'])
def macro_summary():
    """GET /api/reports/summary — Resumen macroeconómico del Euro.


    Query params:
        fecha_desde (ISO) — inicio del período (default: hace 30 días)
        fecha_hasta (ISO) — fin del período (default: hoy)
        categoria   (str) — filtrar por categoría de indicador

    Respuesta:
    {
      "periodo": {"desde": "...", "hasta": "..."},
      "total_observaciones": 120,
      "indicadores_activos": 8,
      "por_categoria": {
        "tipo_cambio": {"count": 30, "ultimo_valor": 1.0821, "variacion_promedio_pct": 0.12}
      },
      "por_estado": {"confirmado": 110, "preliminar": 10},
      "alertas": [
        {"codigo": "EURUSD", "mensaje": "Variación > 1% detectada", "valor": 1.12}
      ]
    }
    """
    try:
        hoy         = date.today()
        fecha_hasta = request.args.get('fecha_hasta', hoy.isoformat())
        fecha_desde = request.args.get('fecha_desde',
                       date(hoy.year, hoy.month, 1).isoformat())  # inicio de mes
        categoria   = request.args.get('categoria')

        query = DataPoint.query.filter(
            DataPoint.fecha_referencia >= fecha_desde,
            DataPoint.fecha_referencia <= fecha_hasta,
        )
        if categoria:
            query = query.join(MacroIndicator).filter(MacroIndicator.categoria == categoria)

        puntos = query.all()
        total  = len(puntos)

        if total == 0:
            return jsonify({
                'success': True,
                'periodo': {'desde': fecha_desde, 'hasta': fecha_hasta},
                'total_observaciones': 0,
                'mensaje': 'Sin datos para el período solicitado'
            })

        # Indicadores únicos en el período
        indicadores_unicos = len(set(p.indicator_id for p in puntos))

        # Agrupar por categoría
        por_categoria = {}
        for p in puntos:
            cat = p.indicator.categoria or 'sin_categoria'
            if cat not in por_categoria:
                por_categoria[cat] = {
                    'count': 0,
                    'valores': [],
                    'variaciones': [],
                    'ultimo_valor': None,
                    'ultima_fecha': None,
                }
            por_categoria[cat]['count'] += 1
            por_categoria[cat]['valores'].append(float(p.valor))
            if p.variacion_pct is not None:
                por_categoria[cat]['variaciones'].append(float(p.variacion_pct))
            if (por_categoria[cat]['ultima_fecha'] is None
                    or p.fecha_referencia > por_categoria[cat]['ultima_fecha']):
                por_categoria[cat]['ultimo_valor'] = float(p.valor)
                por_categoria[cat]['ultima_fecha']  = p.fecha_referencia

        # Limpiar datos internos y calcular estadísticas
        resumen_cat = {}
        for cat, v in por_categoria.items():
            vals = v['valores']
            vars_ = v['variaciones']
            resumen_cat[cat] = {
                'count':                  v['count'],
                'ultimo_valor':           v['ultimo_valor'],
                'valor_maximo':           round(max(vals), 6),
                'valor_minimo':           round(min(vals), 6),
                'variacion_promedio_pct': round(sum(vars_) / len(vars_), 4) if vars_ else None,
            }

        # Agrupar por estado
        por_estado = {}
        for p in puntos:
            por_estado[p.estado] = por_estado.get(p.estado, 0) + 1

        # Alertas automáticas: variación > 1%
        alertas = []
        for p in puntos:
            if p.variacion_pct and abs(float(p.variacion_pct)) > 1.0:
                alertas.append({
                    'codigo':  p.indicator.codigo if p.indicator else None,
                    'mensaje': f"Variación significativa detectada: {float(p.variacion_pct):+.2f}%",
                    'valor':   float(p.valor),
                    'fecha':   p.fecha_referencia.isoformat(),
                })

        return jsonify({
            'success': True,
            'periodo': {'desde': fecha_desde, 'hasta': fecha_hasta},
            'total_observaciones':  total,
            'indicadores_activos':  indicadores_unicos,
            'por_categoria':        resumen_cat,
            'por_estado':           por_estado,
            'alertas':              alertas[:20],  # máximo 20 alertas
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ══════════════════════════════════════════
# BLOQUE 4 — Health check
# ══════════════════════════════════════════

@api.route('/health', methods=['GET'])
def health():
    """GET /api/health — Estado de la API (endpoint público)."""
    return jsonify({
        'status':  'ok',
        'service': 'Euro Macro API',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat(),
    })
