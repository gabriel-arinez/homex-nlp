"""Relaciones conservadoras sobre texto literal; no depende de pesos externos."""

import re

from homex_nlp.contracts.evidence import Candidate, Warning
from homex_nlp.contracts.item import Component
from homex_nlp.rules import NUMBER_WORDS, decimal_from_text, money

COMPONENTES = r"panel frontal|estructura|tapa|mesada|cuerpo|cajonera|cajones?|puertas?|estantes?|módulos? laterales|módulos? centrales"
MATERIALES = r"melamina(?:\s+MDP)?|MDP|MDF|vidrio(?:\s+templado)?|aluminio|metal|madera"
NUMEROS = "|".join(NUMBER_WORDS)


def completar_relaciones(item, candidates, text, warnings):
    """Asocia sólo dentro de la cláusula de una pieza, sin propagar atributos."""
    piezas = list(re.finditer(r"\b(?:" + COMPONENTES + r")\b", text, re.I))

    def evidencia(match, label, value=None, component=None):
        identifier = f"c{len(candidates) + 1}"
        candidates.append(
            Candidate(
                candidate_id=identifier,
                label=label,
                start=match.start(),
                end=match.end(),
                text=match.group(),
                source="RULE",
                normalized_value=value,
                component_ref=component,
                decision="ACCEPTED",
            )
        )
        return identifier

    ambitos = []
    for indice, pieza in enumerate(piezas):
        component = f"pieza-{indice + 1}"
        evidencia_id = evidencia(pieza, "COMPONENTE", component=component)
        item.components.append(
            Component(component_id=component, name=pieza.group(), evidence_ids=[evidencia_id])
        )
        limite = piezas[indice + 1].start() if indice + 1 < len(piezas) else len(text)
        separador = re.search(r"[;.]", text[pieza.end() : limite])
        if separador:
            limite = pieza.end() + separador.start()
        fin_ambito = re.search(
            r"\b(?:dimensiones|ancho|alto|profundidad|precio|pedido|cantidad)\b|,\s*(?:melamina|MDP|MDF|vidrio)\b",
            text[pieza.end() : limite],
            re.I,
        )
        if fin_ambito:
            limite = pieza.end() + fin_ambito.start()
        ambitos.append((pieza.end(), limite))
        for material in re.finditer(r"\b(?:" + MATERIALES + r")\b", text, re.I):
            if pieza.end() <= material.start() < limite:
                evidencia(material, "MATERIAL", component=component)
        antes = text[max(0, pieza.start() - 20) : pieza.start()]
        cantidad = re.search(r"\b(" + NUMEROS + r"|\d+)\s*$", antes, re.I)
        if cantidad:
            inicio = max(0, pieza.start() - 20) + cantidad.start(1)
            fin = max(0, pieza.start() - 20) + cantidad.end(1)
            match = re.compile(re.escape(text[inicio:fin])).search(text, inicio, fin)
            token = text[inicio:fin].lower()
            valor = NUMBER_WORDS.get(token, int(token) if token.isdigit() else None)
            if valor:
                evidencia(match, "CANTIDAD_INTERNA", valor, component)
        for atributo, patron in (
            ("COLOR", r"\b(?:blanco|negro(?: mate)?|gris(?: ceniza)?|olmo|roble|transparente)\b"),
            ("ACABADO", r"\b(?:epoxi|satinado|canto termosellado|mate|brillante)\b"),
        ):
            for match in re.finditer(patron, text, re.I):
                if pieza.end() <= match.start() < limite:
                    evidencia(match, atributo, component=component)
        for thickness in item.thicknesses:
            referencia = next(
                (c for c in candidates if c.candidate_id in thickness.evidence_ids), None
            )
            if referencia and pieza.end() <= referencia.start < limite:
                thickness.component_ref = component
                referencia.component_ref = component
    for label, patron in (
        ("MATERIAL", MATERIALES),
        ("COLOR", r"blanco|negro(?: mate)?|gris(?: ceniza)?|olmo|roble|transparente"),
    ):
        for match in re.finditer(r"\b(?:" + patron + r")\b", text, re.I):
            if not any(inicio <= match.start() < fin for inicio, fin in ambitos):
                evidencia(match, label)
    grupos = list(
        re.finditer(
            r"\bconjunto\s+([a-záéíóúñ ]{1,40}?)(?=\s+(?:con|compuesto)|[:;,.])", text, re.I
        )
    )
    for indice, grupo in enumerate(grupos):
        limite = grupos[indice + 1].start() if indice + 1 < len(grupos) else len(text)
        miembros = [
            c for c in candidates if c.label == "COMPONENTE" and grupo.end() <= c.start < limite
        ]
        if not miembros:
            continue
        group_id = f"grupo-{indice + 1}"
        evidencia(grupo, "CONJUNTO", {"group_id": group_id, "name": grupo.group(1).strip()})
        for miembro in miembros:
            miembro.normalized_value = {"conjunto_ref": group_id}
    # Los componentes internos no se duplican como accesorios independientes.
    item.accessories = [
        a
        for a in item.accessories
        if not any(
            p.start()
            <= next((c.start for c in candidates if c.candidate_id in a.evidence_ids), -1)
            < p.end()
            for p in piezas
        )
    ]
    descuento = re.search(
        r"\bdescuento(?:\s+(?:de\s+)?l[ií]nea|\s+monetario\s+total)?\s*(?:Bs\.?|BOB)?\s*([\d.,]+)",
        text,
        re.I,
    )
    if descuento:
        importe = decimal_from_text(descuento.group(1))
        if importe is not None:
            evidencia(descuento, "DESCUENTO", money(importe))
    unidad = re.search(r"\b(juegos?|piezas?|unidades?)\b", text, re.I)
    if unidad:
        evidencia(
            unidad,
            "UNIDAD_MEDIDA",
            "JUEGO" if unidad.group().lower().startswith("juego") else "PIEZA",
        )
    for match in re.finditer(r"\b\d+(?:[,.]\d+)?\s*[x×]\s*\d+(?:[,.]\d+)?\b", text):
        identifier = f"c{len(candidates) + 1}"
        candidates.append(
            Candidate(
                candidate_id=identifier,
                label="DIMENSION",
                start=match.start(),
                end=match.end(),
                text=match.group(),
                source="RULE",
                decision="UNRESOLVED",
            )
        )
        item.unresolved.append(identifier)
        warnings.append(
            Warning(
                code="MISSING_AXIS",
                path="/item_proposal/dimensions",
                severity="REVIEW",
                message=f"Indique ejes y unidades de {match.group()}.",
            )
        )
    return item
