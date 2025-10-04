"""
Configuración de los pesos para el cálculo de puntuaciones de candidatos.

Este archivo centraliza todos los parámetros que afectan cómo se calculan las puntuaciones
de los candidatos, facilitando su ajuste sin modificar la lógica principal.
"""

# Pesos para la experiencia laboral (máximo 20 puntos)
EXPERIENCE_WEIGHTS = {
    'years_multiplier': 2,  # Puntos por año de experiencia
    'max_points': 20        # Puntos máximos por experiencia
}

# Puntos por nivel educativo (máximo 15 puntos)
EDUCATION_WEIGHTS = {
    'doctorado': 15,
    'maestria': 12,
    'licenciatura': 10,
    'universitario': 8,
    'técnico': 6,
    'bachiller': 4,
    'secundaria': 2
}

# Puntos por habilidades (máximo 20 puntos)
SKILLS_WEIGHTS = {
    'per_skill': 2,        # Puntos por habilidad
    'max_points': 20       # Puntos máximos por habilidades
}

# Puntos por historial (máximo 30 puntos)
HISTORY_WEIGHTS = {
    'postulacion': {
        'per_item': 1,     # Puntos por postulación
        'max_points': 5    # Puntos máximos por postulaciones
    },
    'entrevista': {
        'per_item': 2,     # Puntos por entrevista
        'max_points': 10   # Puntos máximos por entrevistas
    },
    'contratacion': {
        'per_item': 5,     # Puntos por contratación previa
        'max_points': 15   # Puntos máximos por contrataciones
    },
    'max_total': 30        # Puntos máximos totales por historial
}

# Puntos por disponibilidad (máximo 10 puntos)
AVAILABILITY_WEIGHTS = {
    'inmediata': 10,
    'inmediato': 10,
    '1 semana': 7,
    '1-2 semanas': 7,
    '2-4 semanas': 5,
    '1 mes': 5,
    'otro': 3,
    'default': 0
}

# Configuración de la tarea periódica de recálculo
RECALCULATION_CONFIG = {
    'stale_days': 7,       # Número de días para considerar una puntuación "estancada"
    'batch_size': 1000,    # Número máximo de candidatos a recalcular por lote
    'hour': 2,             # Hora del día para ejecutar el recálculo (2 AM)
    'minute': 0
}

# Umbrales para categorización de candidatos
SCORE_THRESHOLDS = {
    'excelente': 85,    # 85-100 puntos
    'bueno': 70,        # 70-84 puntos
    'regular': 50,      # 50-69 puntos
    'bajo': 0           # 0-49 puntos
}

def get_candidate_category(score):
    """
    Devuelve la categoría de un candidato basada en su puntuación.
    
    Args:
        score (int): Puntuación del candidato (0-100)
        
    Returns:
        str: Categoría del candidato
    """
    if score >= SCORE_THRESHOLDS['excelente']:
        return 'excelente'
    elif score >= SCORE_THRESHOLDS['bueno']:
        return 'bueno'
    elif score >= SCORE_THRESHOLDS['regular']:
        return 'regular'
    return 'bajo'
