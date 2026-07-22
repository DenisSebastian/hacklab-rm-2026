# Corpus sintético local — Sesión 5.2

Generado sin APIs, sin modelos de lenguaje y sin conexión a servicios externos.

## Archivos

- `corpus_seguridad.csv`: corpus crudo entregable al alumnado.
- `clave_seguridad.csv`: etiquetas de referencia para el docente.
- `corpus_reciclaje.csv`: corpus crudo entregable al alumnado.
- `clave_reciclaje.csv`: etiquetas de referencia para el docente.
- `gen_corpus_5_2_local.py`: generador reproducible basado en reglas y plantillas.

## Tamaño

Cada corpus contiene 412 filas: 400 filas base y 12 duplicados exactos plantados (3%).

## Rasgos sintéticos plantados

Sobre las 400 filas base se asignan aproximadamente:

- 4% de casos ambiguos.
- 8% con datos personales ficticios de formato realista.
- 6% de posturas de disenso.
- 2% de respuestas vacías o casi vacías.
- 5% de respuestas fuera de tema.
- 30% sin comuna ni grupo de edad.
- 3% de duplicados exactos agregados al final de la generación y luego mezclados.

Todos los nombres, RUT, teléfonos y direcciones son sintéticos y no deben interpretarse como datos reales.

## Reproducción

```bash
python gen_corpus_5_2_local.py ambos 400 --seed 52 --out-dir ./corpus_5_2_local
```

También puede generarse solo un tema:

```bash
python gen_corpus_5_2_local.py seguridad 500 --seed 52 --out-dir ./salida
python gen_corpus_5_2_local.py reciclaje 500 --seed 52 --out-dir ./salida
```

El script usa únicamente la biblioteca estándar de Python.
