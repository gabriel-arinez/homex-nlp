"""Relaciones conservadoras sobre texto literal; no depende de pesos externos."""

import re

from homex_nlp.contracts.evidence import Candidate, Warning
from homex_nlp.contracts.item import Component
from homex_nlp.rules import NUMBER_WORDS, decimal_from_text, is_explicitly_negated, money

COMPONENTES = (
    r"panel frontal|estructura|tableros?|mes[oó]n(?:es)?|"
    r"me\s+son(?=\s+engrosad[oa]s?\s+(?:a|de)\s+\d)|"
    r"tapa(?!\s+canto\b)|mesada|cuerpo|cajonera|cajones?|"
    r"puertas?|estantes?|módulos? laterales|módulos? centrales"
)
MATERIALES = (
    r"melam[ií]nic[oa]s?|menam[ií]nic[oa]s?|"
    r"melamina(?:\s+MDP)?|MDP|MDF|"
    r"vidrio(?:\s+templado)?|aluminio|metal|madera"
)
NUMEROS = "|".join(NUMBER_WORDS)
NUMERO = rf"(?:{NUMEROS}|\d+)"
# Rectificaciones internas inequívocas: exige una señal positiva ("mejor")
# y una nueva cantidad explícita. No interpretamos un "no dos cajones"
# como instrucción suficiente para alterar la ficha.
CORRECCION_PIEZA = re.compile(
    rf"\s*[,;]\s*(?:no\s*,?\s*mejor|perd[oó]n\s*,?\s*mejor|"
    rf"corrijo\s*,?\s*mejor|mejor)\s+{NUMERO}\s+",
    re.I,
)
AMBIGUA_PIEZA = re.compile(rf"\s*[,;]\s*no\s*,\s*{NUMERO}\s+", re.I)
AMBIGUA_CANTIDAD = re.compile(
    rf"\s*[,;]\s*no\s*,\s*(?P<numero>{NUMERO})\b"
    rf"(?=\s*(?:[,;.]|$))",
    re.I,
)
CORRECCION_CANTIDAD = re.compile(
    rf"\s*[,;]\s*(?:no\s*,?\s*mejor|perd[oó]n\s*,?\s*mejor|"
    rf"corrijo\s*,?\s*mejor|mejor)\s+(?P<numero>{NUMERO})\b"
    rf"(?=\s*(?:[,;.]|$))",
    re.I,
)


def completar_relaciones(item, candidates, text, warnings):
    """Asocia sólo dentro de la cláusula de una pieza, sin propagar atributos."""
    piezas = [
        pieza
        for pieza in re.finditer(r"\b(?:" + COMPONENTES + r")\b", text, re.I)
        if not (
            pieza.group().lower().startswith("tablero")
            and re.search(
                r"\bestructura\s+(?:con|en|de)\s+$",
                text[max(0, pieza.start() - 40) : pieza.start()],
                re.I,
            )
        )
    ]

    piezas_originales = piezas[:]
    # Una pausa de ASR tras «no,» no basta para decidir qué pieza se pidió.
    piezas_ambiguas = []
    for anterior, siguiente in zip(piezas_originales, piezas_originales[1:]):
        if AMBIGUA_PIEZA.fullmatch(text[anterior.end() : siguiente.start()]):
            for pieza in (anterior, siguiente):
                if pieza not in piezas_ambiguas:
                    piezas_ambiguas.append(pieza)
    negadas = [
        pieza
        for pieza in piezas
        if pieza not in piezas_ambiguas and is_explicitly_negated(text, pieza.start())
    ]
    piezas = [pieza for pieza in piezas if pieza not in negadas and pieza not in piezas_ambiguas]
    for negada in negadas:
        candidates.append(
            Candidate(
                candidate_id=f"c{len(candidates) + 1}",
                label="COMPONENTE",
                start=negada.start(),
                end=negada.end(),
                text=negada.group(),
                source="RULE",
                decision="REJECTED",
                reason="Componente explícitamente excluido",
            )
        )

    def evidencia(match, label, value=None, component=None, decision="ACCEPTED", reason=None):
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
                decision=decision,
                reason=reason,
            )
        )
        return identifier

    def cantidad_anterior(pieza):
        comienzo = max(0, pieza.start() - 20)
        antes = text[comienzo : pieza.start()]
        cantidad = re.search(r"\b(" + NUMEROS + r"|\d+)\s*$", antes, re.I)
        if not cantidad:
            return None
        inicio = comienzo + cantidad.start(1)
        fin = comienzo + cantidad.end(1)
        token = text[inicio:fin]
        valor = NUMBER_WORDS.get(token.casefold(), int(token) if token.isdigit() else None)
        if not valor:
            return None
        return re.compile(re.escape(token)).match(text, inicio), valor

    for ambigua in piezas_ambiguas:
        identifier = evidencia(
            ambigua,
            "COMPONENTE",
            decision="UNRESOLVED",
            reason="Rectificación interna ambigua: falta señal afirmativa",
        )
        item.unresolved.append(identifier)
        cantidad = cantidad_anterior(ambigua)
        if cantidad:
            identifier = evidencia(
                cantidad[0],
                "CANTIDAD_INTERNA",
                cantidad[1],
                decision="UNRESOLVED",
                reason="Cantidad interna ambigua",
            )
            item.unresolved.append(identifier)
    # Descartar sólo la mención sustituida por una corrección inequívoca:
    # «tres cajones, no, mejor dos cajones» → un único componente de dos.
    descartadas = []
    for anterior, siguiente in zip(piezas, piezas[1:]):
        tramo = text[anterior.end() : siguiente.start()]
        if CORRECCION_PIEZA.fullmatch(tramo):
            descartadas.append(anterior)
    for antigua in descartadas:
        evidencia(
            antigua,
            "COMPONENTE",
            decision="REJECTED",
            reason="Pieza sustituida por rectificación explícita",
        )
        cantidad = cantidad_anterior(antigua)
        if cantidad:
            evidencia(
                cantidad[0],
                "CANTIDAD_INTERNA",
                cantidad[1],
                decision="REJECTED",
                reason="Cantidad interna rectificada",
            )
    piezas = [pieza for pieza in piezas if pieza not in descartadas]
    correcciones = bool(descartadas)
    incertidumbre = bool(piezas_ambiguas)

    ambitos = []
    for indice, pieza in enumerate(piezas):
        component = f"pieza-{indice + 1}"
        alias_asr = bool(re.fullmatch(r"me\s+son", pieza.group(), re.I))
        nombre = "mesón" if alias_asr else pieza.group()
        evidencia_id = evidencia(
            pieza,
            "COMPONENTE",
            value=nombre if alias_asr else None,
            component=component,
        )
        item.components.append(
            Component(component_id=component, name=nombre, evidence_ids=[evidencia_id])
        )
        if alias_asr:
            warnings.append(
                Warning(
                    code="UNKNOWN_TERM",
                    path="/item_proposal/components",
                    severity="INFO",
                    message="Se interpretó 'me son engrosado' como 'mesón'; confirme la pieza.",
                )
            )
        limite = piezas[indice + 1].start() if indice + 1 < len(piezas) else len(text)
        separador = re.search(r";|[.,](?!\d)", text[pieza.end() : limite])
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
        cantidad = cantidad_anterior(pieza)
        # «tres cajones, no, mejor dos» sustituye únicamente la cantidad
        # del componente inmediatamente anterior. No extenderla a otra pieza.
        frontera = piezas_originales.index(pieza) + 1
        proxima = (
            piezas_originales[frontera].start() if frontera < len(piezas_originales) else len(text)
        )
        fragmento = text[pieza.end() : proxima]
        rectificacion = CORRECCION_CANTIDAD.match(fragmento)
        ambigua = AMBIGUA_CANTIDAD.match(fragmento) if not rectificacion else None
        # Varias rectificaciones sucesivas sin repetir la pieza no autorizan
        # a elegir una cantidad intermedia: se remite todo a revisión.
        if rectificacion and re.search(
            r"[,;]\s*no\s*,?\s*(?:mejor|\d+|" + NUMEROS + r")\b",
            fragmento[rectificacion.end() :],
            re.I,
        ):
            ambigua = rectificacion
            rectificacion = None
        if cantidad:
            estado = "UNRESOLVED" if ambigua else "REJECTED" if rectificacion else "ACCEPTED"
            identifier = evidencia(
                cantidad[0],
                "CANTIDAD_INTERNA",
                cantidad[1],
                component,
                decision=estado,
                reason="Cantidad interna dudosa"
                if ambigua
                else "Cantidad interna rectificada"
                if rectificacion
                else None,
            )
            if ambigua:
                item.unresolved.append(identifier)
        nueva_cantidad = rectificacion or ambigua
        if nueva_cantidad:
            comienzo = pieza.end() + nueva_cantidad.start("numero")
            token = nueva_cantidad.group("numero")
            numero = NUMBER_WORDS.get(token.casefold(), int(token) if token.isdigit() else None)
            if numero is not None and numero > 0:
                nueva = re.compile(re.escape(token)).match(text, comienzo)
                identifier = evidencia(
                    nueva,
                    "CANTIDAD_INTERNA",
                    numero,
                    component,
                    decision="UNRESOLVED" if ambigua else "ACCEPTED",
                    reason="Cantidad interna dudosa" if ambigua else None,
                )
                if ambigua:
                    item.unresolved.append(identifier)
                    incertidumbre = True
                else:
                    correcciones = True
            # La rectificación encadenada también queda registrada como
            # evidencia UNRESOLVED: no seleccionar silenciosamente «dos»
            # cuando se dicta «dos, no, mejor cuatro».
            if ambigua and rectificacion is None:
                for adicional in re.finditer(
                    rf"[,;]\s*no\s*,?\s*mejor\s+(?P<numero>{NUMERO})\b",
                    fragmento[nueva_cantidad.end() :],
                    re.I,
                ):
                    token = adicional.group("numero")
                    comienzo = pieza.end() + nueva_cantidad.end() + adicional.start("numero")
                    match = re.compile(re.escape(token)).match(text, comienzo)
                    valor = NUMBER_WORDS.get(
                        token.casefold(), int(token) if token.isdigit() else None
                    )
                    if valor:
                        identifier = evidencia(
                            match,
                            "CANTIDAD_INTERNA",
                            valor,
                            component,
                            decision="UNRESOLVED",
                            reason="Correcciones sucesivas ambiguas",
                        )
                        item.unresolved.append(identifier)
        for atributo, patron in (
            ("COLOR", r"\b(?:blanco|negro(?: mate)?|gris(?: ceniza)?|olmo|roble|transparente)\b"),
            ("ACABADO", r"\b(?:epoxi|satinado|canto termosellado|mate|brillante)\b"),
        ):
            for match in re.finditer(patron, text, re.I):
                if pieza.end() <= match.start() < limite:
                    evidencia(match, atributo, component=component)
        for dimension in item.dimensions:
            ref = next((c for c in candidates if c.candidate_id in dimension.evidence_ids), None)
            if ref and pieza.end() <= ref.start < limite:
                connector = text[pieza.end() : ref.start]
                if re.fullmatch(r"\s+(?:de|con)\s+", connector, re.I):
                    dimension.component_ref = component
                    ref.component_ref = component
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
            c
            for c in candidates
            if c.label == "COMPONENTE"
            and c.decision == "ACCEPTED"
            and grupo.end() <= c.start < limite
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
            for p in piezas_originales
        )
    ]
    # Los candidatos accesorio asociados a una pieza rectificada no pueden
    # permanecer afirmativos después de descartar la mención original.
    for candidata in candidates:
        if candidata.label == "ACCESORIO" and candidata.decision == "ACCEPTED":
            if any(p.start() <= candidata.start < p.end() for p in descartadas):
                candidata.decision = "REJECTED"
                candidata.reason = "Accesorio nombrado como pieza rectificada"
            elif any(p.start() <= candidata.start < p.end() for p in piezas_ambiguas):
                candidata.decision = "UNRESOLVED"
                candidata.reason = "Accesorio nombrado como pieza ambigua"
    if correcciones:
        warnings.append(
            Warning(
                code="CONFLICTING_VALUES",
                path="/item_proposal/components",
                severity="REVIEW",
                message="Se aplicó una rectificación de pieza o cantidad interna; confirme el resultado.",
            )
        )
    if incertidumbre:
        warnings.append(
            Warning(
                code="CONFLICTING_VALUES",
                path="/item_proposal/components",
                severity="REVIEW",
                message="Una corrección interna no identifica una cantidad o pieza inequívoca.",
            )
        )
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
