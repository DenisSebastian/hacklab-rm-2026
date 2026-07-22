# -*- coding: utf-8 -*-
"""Generador local de corpus sintéticos para NLP y participación ciudadana.

No usa APIs, modelos externos ni paquetes de terceros.
Produce para cada tema:
  - corpus_<tema>.csv: datos entregados al alumnado.
  - clave_<tema>.csv: etiquetas y rasgos plantados para el docente.

Uso:
  python gen_corpus_5_2_local.py
  python gen_corpus_5_2_local.py seguridad 400 --seed 52 --out-dir ./salida
  python gen_corpus_5_2_local.py reciclaje 500
"""
from __future__ import annotations

import argparse
import csv
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

N_POR_CORPUS = 400
PCT_AMBIGUO = 0.04
PCT_PII = 0.08
PCT_DISENSO = 0.06
PCT_VACIA = 0.02
PCT_DUP = 0.03
PCT_OTRA = 0.05
PCT_SIN_CONTEXTO = 0.30

COMUNAS_RM = [
    "Maipú", "Puente Alto", "La Florida", "Pudahuel", "Peñalolén", "San Joaquín",
    "Recoleta", "Lo Espejo", "Huechuraba", "Paine", "San José de Maipo", "Santiago",
    "La Pintana", "El Bosque", "Renca", "Quilicura", "Estación Central", "Cerro Navia",
]
CANALES = ["consulta_web", "cabildo", "formulario_papel", "whatsapp_municipal", "buzón_vecinal"]
GRUPOS_EDAD = ["18-29", "30-44", "45-59", "60+"]

NOMBRES = ["Camila Rojas", "Juan Pérez", "María González", "Felipe Soto", "Patricia Muñoz", "Luis Araya"]
CALLES = ["Los Aromos", "Las Parcelas", "Vicuña Mackenna", "Santa Rosa", "El Molino", "La Estrella"]
LUGARES = ["plaza Los Copihues", "paradero 14", "pasaje Las Lilas", "villa El Sol", "cancha del barrio", "feria de los sábados"]

SEGURIDAD = {
    "microtráfico y narco": [
        "En {lugar} venden droga como si nada y en la noche se escuchan balazos.",
        "La casa de la esquina funciona como punto de venta, todos sabemos menos la muni parece.",
        "Hay cabros ofreciendo pasta cerca del colegio, esto ya se salió de control.",
        "Desde que llegaron esos narcos el barrio cambió, nadie deja jugar a los niños afuera.",
    ],
    "hurtos y robos": [
        "Me robaron el celu saliendo del metro y no había nadie patrullando.",
        "Otra vez se llevaron cables en {lugar}, quedamos sin luz toda la cuadra.",
        "Los portonazos están brigidos, uno ya entra mirando para todos lados.",
        "Se metieron a dos casas esta semana, necesitamos alguna medida concreta.",
    ],
    "incivilidades": [
        "Los carretes duran hasta las 5 am y nadie fiscaliza, imposible dormir.",
        "La esquina está llena de basura y peleas todos los fines de semana.",
        "El comercio ambulante dejó la vereda intransitable, pero tampoco es llegar y echarlos.",
        "Ponen música a todo chancho y cuando uno reclama se ponen violentos.",
    ],
    "iluminación y espacio público": [
        "La plaza está oscurísima, cambien las luminarias antes de poner más cámaras.",
        "El sitio eriazo de {lugar} está lleno de matorrales y da miedo pasar.",
        "Faltan luces en el pasaje, ahí se esconden para asaltar.",
        "Arreglaron la plaza y mejoró harto, ahora sí se ve gente usando el espacio.",
    ],
    "violencia intrafamiliar y convivencia vecinal": [
        "En la casa de al lado se escuchan gritos y golpes, alguien debería intervenir con cuidado.",
        "Hay una familia con problemas graves y el barrio solo comenta, falta apoyo profesional.",
        "Mi vecino amenaza a todos por el estacionamiento, ya no se puede conversar.",
        "La convivencia está pésima, cualquier discusión termina en insultos.",
    ],
    "percepción de miedo e inseguridad": [
        "No me ha pasado nada, pero igual no salgo después de las nueve por miedo.",
        "Antes caminaba tranquila, ahora pido que me vayan a buscar al paradero.",
        "Siento que todo está peor aunque quizás también influyen las noticias.",
        "El barrio no es tan peligroso como dicen, pero la sensación de inseguridad es real.",
    ],
    "presencia policial y municipal": [
        "Necesitamos más patrullaje de verdad, no una vuelta rápida para la foto.",
        "Las cámaras sirven si alguien las mira, si no son puro adorno.",
        "No quiero más vigilancia, prefiero iluminación y trabajo con los jóvenes.",
        "Carabineros pasa más seguido y se nota, aunque todavía falta coordinación con seguridad municipal.",
    ],
}

RECICLAJE = {
    "puntos limpios y contenedores": [
        "El punto limpio siempre está lleno, al final la gente deja todo afuera.",
        "Faltan contenedores para vidrio en {lugar}, el más cercano queda lejísimos.",
        "Pusieron un punto limpio pero está mal ubicado y casi nadie sabe que existe.",
        "El contenedor nuevo funciona bien, ojalá lo retiren antes de que colapse.",
    ],
    "retiro domiciliario y frecuencia del camión": [
        "El camión pasa cuando quiere y las bolsas quedan dos días en la calle.",
        "Deberían avisar los horarios por WhatsApp porque uno nunca sabe cuándo sacar el reciclaje.",
        "El retiro diferenciado dejó de pasar hace semanas, así nadie mantiene el hábito.",
        "Cuando el camión cumple el horario se nota mucho más limpio el barrio.",
    ],
    "microbasurales y vertederos ilegales": [
        "En el sitio eriazo de {lugar} botan colchones y escombros todas las noches.",
        "La muni limpia el microbasural y a los tres días está igual, falta fiscalización.",
        "Hay gente que viene de otras comunas a dejar basura en la esquina.",
        "Pongan barreras o cámaras porque ese vertedero ilegal crece cada semana.",
    ],
    "compostaje y residuos orgánicos": [
        "Quiero compostar pero vivo en depto y no tengo dónde llevar los orgánicos.",
        "La compostera comunitaria es buena idea, pero hay que controlar olores y moscas.",
        "Con los restos de la feria podríamos hacer compost para las áreas verdes.",
        "Probé compostaje en la casa y funciona, falta enseñar bien para que no quede la caga.",
    ],
    "educación y cultura del reciclaje": [
        "La gente mezcla todo porque nadie explica qué va en cada contenedor.",
        "No sirve otra campaña con folletos, hagan talleres en colegios y juntas de vecinos.",
        "En mi casa separamos hace años, pero varios vecinos todavía tiran todo junto.",
        "Hay que educar, aunque también facilitar el sistema; no puede depender solo de la buena voluntad.",
    ],
    "recicladores de base": [
        "Los recicladores de base hacen una pega enorme y deberían tener apoyo municipal.",
        "El cartonero deja desorden cuando revisa las bolsas, pero quitarlo no resuelve nada.",
        "Integren a los recicladores al sistema formal y paguen por el servicio.",
        "Hay conflicto por el ruido de los carros temprano, se necesita acordar horarios.",
    ],
    "economía circular y reutilización": [
        "Podrían organizar ferias de trueque y reparación en vez de botar todo.",
        "Hace falta un lugar para dejar muebles que todavía sirven.",
        "Reciclar está bien, pero primero deberíamos reducir envases y reutilizar.",
        "La feria de intercambio fue excelente, me gustaría que fuera mensual.",
    ],
}

OTRAS = [
    "Gracias por escuchar a los vecinos.", "¿Cuándo arreglan la vereda de mi calle?", "Necesitamos más áreas verdes.",
    "Buen día, no tengo comentarios.", "Quiero saber por los talleres deportivos.", "La atención del consultorio está muy lenta.",
]
VACIAS = ["", "no sé", "-", "nada", ".", "s/i"]

@dataclass
class Row:
    respuesta: str
    tema: str
    subtema: str
    lugar: str
    tono: str
    es_ambiguo: int = 0
    motivo_ambiguedad: str = ""
    contiene_pii: int = 0
    es_disenso: int = 0
    es_duplicado: int = 0
    id_origen_duplicado: str = ""


def largest_remainder(total: int, shares: dict[str, float]) -> dict[str, int]:
    raw = {k: total * v for k, v in shares.items()}
    out = {k: int(v) for k, v in raw.items()}
    remaining = total - sum(out.values())
    for k, _ in sorted(raw.items(), key=lambda kv: kv[1] - int(kv[1]), reverse=True)[:remaining]:
        out[k] += 1
    return out


def extract_place(text: str) -> str:
    for place in LUGARES:
        if place.lower() in text.lower():
            return place
    m = re.search(r"(?:calle|pasaje|avenida|av\.)\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ ]+(?:\s+\d{2,5})?", text)
    return m.group(0) if m else ""


def infer_tone(text: str) -> str:
    low = text.lower()
    positive = ["funciona bien", "mejoró", "excelente", "buena idea", "se nota", "tranquila", "apoyo"]
    negative = ["miedo", "robar", "balazo", "pésim", "lleno", "nunca", "falta", "problema", "basura", "violento", "oscur"]
    p = any(x in low for x in positive)
    n = any(x in low for x in negative)
    return "mixto" if p and n else "positivo" if p else "negativo" if n else "neutro"


def add_noise(text: str, rng: random.Random) -> str:
    if not text or rng.random() > 0.35:
        return text
    transforms: list[Callable[[str], str]] = [
        lambda s: s.replace("porque", "xq"),
        lambda s: s.replace("también", "tb"),
        lambda s: s.replace("para", "pa"),
        lambda s: s.replace("está", "ta"),
        lambda s: s.lower(),
        lambda s: s.upper(),
        lambda s: s.replace(",", ""),
        lambda s: s.rstrip(".") + "!!!",
    ]
    return rng.choice(transforms)(text)


def pii_fragment(rng: random.Random) -> str:
    kind = rng.choice(["nombre", "rut", "fono", "direccion"])
    if kind == "nombre":
        return f" Mi vecino {rng.choice(NOMBRES)} puede confirmar esto."
    if kind == "rut":
        return f" Dejé el reclamo a nombre de {rng.choice(NOMBRES)}, RUT {rng.randint(10, 24)}.{rng.randint(100,999)}.{rng.randint(100,999)}-{rng.choice('0123456789K')}."
    if kind == "fono":
        return f" Me pueden llamar al +569 {rng.randint(1000,9999)} {rng.randint(1000,9999)}."
    return f" Esto pasa frente a {rng.choice(CALLES)} {rng.randint(100,4999)}."


def ambiguous_row(topic: str, rng: random.Random) -> Row:
    if topic == "seguridad":
        options = [
            ("Desde que pusieron cámaras ya no se juntan en la plaza; quedó más tranquila, pero ahora parece cárcel.", "presencia policial y municipal", "cámaras y uso del espacio público", "mixto", "Evalúa positivamente la reducción de reuniones, pero critica la vigilancia y el deterioro de la convivencia."),
            ("La plaza está oscura y por eso se presta pa carretes, basura y asaltos; no sé si faltan luces o patrullas.", "iluminación y espacio público", "oscuridad, incivilidades y robos", "negativo", "Combina iluminación, incivilidades, percepción de inseguridad y delitos sin una causa principal clara."),
            ("Qué bueno que nunca pasa nada por acá, salvo los portonazos de todas las semanas.", "hurtos y robos", "ironía sobre frecuencia de portonazos", "mixto", "La formulación irónica parece positiva, pero comunica una evaluación fuertemente negativa."),
        ]
    else:
        options = [
            ("El punto limpio está impecable porque nadie lo usa: queda lejos y nunca explicaron qué recibe.", "puntos limpios y contenedores", "ubicación y educación", "mixto", "El elogio es irónico y mezcla infraestructura, acceso y educación ambiental."),
            ("Separar sirve, supongo, aunque después el camión junta todo y uno queda de payaso.", "retiro domiciliario y frecuencia del camión", "desconfianza en la trazabilidad", "mixto", "Expresa una adhesión débil al reciclaje junto con escepticismo y posible sarcasmo."),
            ("La compostera ayuda a la huerta, pero el olor tiene chatos a los vecinos.", "compostaje y residuos orgánicos", "beneficio ambiental y externalidades", "mixto", "Contiene simultáneamente una evaluación positiva y una queja vecinal."),
        ]
    text, tema, sub, tono, motivo = rng.choice(options)
    return Row(add_noise(text, rng), tema, sub, extract_place(text), tono, es_ambiguo=1, motivo_ambiguedad=motivo)


def dissent_row(topic: str, rng: random.Random) -> Row:
    if topic == "seguridad":
        options = [
            ("No quiero más cámaras ni controles, el problema se arregla con oportunidades y trabajo comunitario.", "presencia policial y municipal", "rechazo a vigilancia punitiva"),
            ("El barrio no está peor; las redes sociales exageran y terminamos desconfiando de todos.", "percepción de miedo e inseguridad", "cuestionamiento de la percepción dominante"),
            ("Más patrullas no siempre significa más seguridad, a varios jóvenes los controlan solo por cómo se ven.", "presencia policial y municipal", "efectos adversos del control"),
        ]
    else:
        options = [
            ("No voy a separar mientras las empresas sigan llenando todo de plástico; no carguen la responsabilidad al vecino.", "educación y cultura del reciclaje", "responsabilidad empresarial"),
            ("Los puntos limpios son greenwashing si después mezclan todo en el mismo camión.", "puntos limpios y contenedores", "escepticismo sobre trazabilidad"),
            ("Prefiero que cobren a quienes producen envases antes que hacer otra campaña para culpabilizar a la gente.", "economía circular y reutilización", "responsabilidad extendida del productor"),
        ]
    text, tema, sub = rng.choice(options)
    return Row(add_noise(text, rng), tema, sub, extract_place(text), infer_tone(text), es_disenso=1)


def regular_row(topic: str, rng: random.Random) -> Row:
    taxonomy = SEGURIDAD if topic == "seguridad" else RECICLAJE
    tema = rng.choice(list(taxonomy))
    text = rng.choice(taxonomy[tema]).format(lugar=rng.choice(LUGARES))
    text = add_noise(text, rng)
    sub = tema
    if " y " in tema:
        sub = tema.split(" y ")[0]
    return Row(text, tema, sub, extract_place(text), infer_tone(text))


def generate_base(topic: str, n: int, rng: random.Random) -> list[Row]:
    counts = largest_remainder(n, {
        "ambiguo": PCT_AMBIGUO,
        "pii": PCT_PII,
        "disenso": PCT_DISENSO,
        "vacia": PCT_VACIA,
        "otra": PCT_OTRA,
        "regular": 1 - (PCT_AMBIGUO + PCT_PII + PCT_DISENSO + PCT_VACIA + PCT_OTRA),
    })
    rows: list[Row] = []
    rows += [ambiguous_row(topic, rng) for _ in range(counts["ambiguo"])]
    rows += [dissent_row(topic, rng) for _ in range(counts["disenso"])]
    rows += [Row(rng.choice(VACIAS), "otra", "respuesta vacía o insuficiente", "", "neutro") for _ in range(counts["vacia"])]
    rows += [Row(add_noise(rng.choice(OTRAS), rng), "otra", "fuera de tema", "", infer_tone(OTRAS[0])) for _ in range(counts["otra"])]
    for _ in range(counts["pii"]):
        row = regular_row(topic, rng)
        row.respuesta += pii_fragment(rng)
        row.contiene_pii = 1
        row.lugar = extract_place(row.respuesta)
        rows.append(row)
    rows += [regular_row(topic, rng) for _ in range(counts["regular"])]
    rng.shuffle(rows)
    return rows


def add_duplicates(rows: list[Row], n_requested: int, rng: random.Random) -> list[Row]:
    ndup = round(PCT_DUP * n_requested)
    out = list(rows)
    eligible = [i for i, r in enumerate(rows) if r.respuesta.strip()]
    for source_idx in rng.sample(eligible, k=min(ndup, len(eligible))):
        src = rows[source_idx]
        dup = Row(**src.__dict__)
        dup.es_duplicado = 1
        dup.id_origen_duplicado = str(source_idx + 1)
        out.append(dup)
    rng.shuffle(out)
    return out


def write_topic(topic: str, rows: list[Row], out_dir: Path, rng: random.Random) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    corpus_path = out_dir / f"corpus_{topic}.csv"
    key_path = out_dir / f"clave_{topic}.csv"
    context_mask = [False] * round(PCT_SIN_CONTEXTO * len(rows)) + [True] * (len(rows) - round(PCT_SIN_CONTEXTO * len(rows)))
    rng.shuffle(context_mask)

    with corpus_path.open("w", newline="", encoding="utf-8-sig") as fc, key_path.open("w", newline="", encoding="utf-8-sig") as fk:
        wc, wk = csv.writer(fc), csv.writer(fk)
        wc.writerow(["id", "respuesta", "comuna", "canal", "grupo_edad"])
        wk.writerow(["id", "tema", "subtema", "lugar", "tono", "es_ambiguo", "motivo_ambiguedad", "contiene_pii", "es_disenso", "es_duplicado", "id_origen_duplicado"])
        for i, (row, has_ctx) in enumerate(zip(rows, context_mask), start=1):
            rid = f"{topic[:3].upper()}-{i:04d}"
            comuna = rng.choice(COMUNAS_RM) if has_ctx else ""
            edad = rng.choice(GRUPOS_EDAD) if has_ctx else ""
            canal = rng.choice(CANALES)
            wc.writerow([rid, row.respuesta, comuna, canal, edad])
            wk.writerow([rid, row.tema, row.subtema, row.lugar, row.tono, row.es_ambiguo, row.motivo_ambiguedad, row.contiene_pii, row.es_disenso, row.es_duplicado, row.id_origen_duplicado])
    return corpus_path, key_path


def summarize(topic: str, rows: list[Row]) -> str:
    return (f"{topic}: {len(rows)} filas | ambiguas={sum(r.es_ambiguo for r in rows)} | "
            f"PII={sum(r.contiene_pii for r in rows)} | disenso={sum(r.es_disenso for r in rows)} | "
            f"duplicados={sum(r.es_duplicado for r in rows)} | otra={sum(r.tema == 'otra' for r in rows)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("tema", nargs="?", choices=["seguridad", "reciclaje", "ambos"], default="ambos")
    parser.add_argument("n", nargs="?", type=int, default=N_POR_CORPUS, help="Filas base antes de agregar duplicados")
    parser.add_argument("--seed", type=int, default=52)
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent / "corpus_5_2_local")
    args = parser.parse_args()
    if args.n < 20:
        parser.error("n debe ser al menos 20 para representar los rasgos plantados.")

    topics = ["seguridad", "reciclaje"] if args.tema == "ambos" else [args.tema]
    for j, topic in enumerate(topics):
        rng = random.Random(args.seed + j * 1009)
        rows = add_duplicates(generate_base(topic, args.n, rng), args.n, rng)
        corpus, key = write_topic(topic, rows, args.out_dir, rng)
        print(summarize(topic, rows))
        print(f"  {corpus}\n  {key}")


if __name__ == "__main__":
    main()
