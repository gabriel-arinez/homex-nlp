"""Relaciones conservadoras sobre texto literal; no depende de pesos externos."""

import re

from homex_nlp.contracts.evidence import Candidate, Warning
from homex_nlp.contracts.item import Color, Component
from homex_nlp.rules import NUMBER_WORDS, decimal_from_text, is_explicitly_negated, money

COMPONENTES = (
    r"panel frontal|panel(?:es)?|repisas?(?: interior(?:es)?| lateral(?:es)?| abiertas?)?|divisi[oó]n(?:es)?(?: interior(?:es)?)?|cubiertas?(?: superior(?:es)?)?|patas?(?: met[aá]licas?)?|estructura|tableros?|mes[oó]n(?:es)?(?: superior(?:es)?)?|"
    r"me\s+son(?=\s+engrosad[oa]s?\s+(?:a|de)\s+\d)|"
    r"lateral(?:es)?|tapa(?!\s+canto\b)|mesada|cuerpo|cajonera|cajones?(?: lateral(?:es)?)?|"
    r"puertas?(?: abatibles| inferior(?:es)?)?|papeleros?|archivador(?:es)?|estantes?|módulos? laterales|módulos? centrales"
)
MATERIALES = (
    r"melam[ií]nic[oa]s?|menam[ií]nic[oa]s?|"
    r"melamin[ae](?:\s+MDP)?|MDP|MDF|"
    r"vidrio(?:\s+templado)?|aluminio|metal|madera"
)
COLORES = (
    r"blanc[oa]|negr[oa](?: mate)?|gris(?: claro| oscuro| ceniza)?|"
    r"olmo|roble(?: claro| oscuro)?|nogal|no-gal|haya|transparente|madera clara"
)
NUMEROS = "|".join(NUMBER_WORDS)
NUMERO = rf"(?:{NUMEROS}|\d+)"
# Rectificaciones internas inequívocas: exige una señal positiva ("mejor")
# y una nueva cantidad explícita. No interpretamos un "no dos cajones"
# como instrucción suficiente para alterar la ficha.
CORRECCION_PIEZA = re.compile(
    rf"\s*[,;.]?\s*(?:no\s*,?\s*mejor|perd[oó]n\s*,?\s*mejor|"
    rf"corrijo\s*,?\s*mejor|mejor)\s+{NUMERO}\s+",
    re.I,
)
AMBIGUA_PIEZA = re.compile(rf"\s*[,;.]?\s*no\s*,\s*{NUMERO}\s+", re.I)
AMBIGUA_CANTIDAD = re.compile(
    rf"\s*[,;.]?\s*no\s*,\s*(?P<numero>{NUMERO})\b"
    rf"(?=\s*(?:[,;.]|$))",
    re.I,
)
CORRECCION_CANTIDAD = re.compile(
    rf"\s*[,;.]?\s*(?:no\s*,?\s*mejor|perd[oó]n\s*,?\s*mejor|"
    rf"corrijo\s*,?\s*mejor|mejor)\s+(?P<numero>{NUMERO})\b"
    rf"(?=\s*(?:[,;.]|$))",
    re.I,
)

# Cuando el ASR omite signos en correcciones ENCADENADAS, nunca se
# acepta silenciosamente la cantidad anterior ni una intermedia.
CORRECCION_INCOMPLETA = re.compile(
    rf"\s*[,;.]?\s*(?:no\s*,?\s*mejor|perd[oó]n\s*,?\s*mejor|"
    rf"corrijo\s*,?\s*mejor|mejor)\s+(?P<numero>{NUMERO})\b",
    re.I,
)


def completar_relaciones(item, candidates, text, warnings):
    """Asocia sólo dentro de la cláusula de una pieza, sin propagar atributos."""
    piezas = [
        pieza
        for pieza in re.finditer(r"\b(?:" + COMPONENTES + r")\b", text, re.I)
        if not (
            # «repisas laterales» usa un adjetivo, no otra pieza.
            re.fullmatch(r"lateral(?:es)?", pieza.group(), re.I)
            and re.search(
                r"\b(?:repisas?|cajones?|m[oó]dulos?|paneles?|puertas?|soportes?)\s+$",
                text[max(0, pieza.start() - 30) : pieza.start()],
                re.I,
            )
            or
            # No duplicar un producto principal como componente propio.
            any(
                c.label == "PRODUCTO"
                and c.decision == "ACCEPTED"
                and c.start == pieza.start()
                and c.end >= pieza.end()
                for c in candidates
            )
            or pieza.group().lower().startswith("tablero")
            and re.search(
                r"\bestructura\s+(?:con|en|de)\s+$",
                text[max(0, pieza.start() - 40) : pieza.start()],
                re.I,
            )
        )
    ]

    # Una cajonera integrada reiterada como «cajonera con N cajones»
    # describe su contenido, no una segunda pieza. No fusionar «otra».
    repeated = []
    for index, pieza in enumerate(piezas):
        if (
            pieza.group().casefold() == "cajonera"
            and re.match(r"\s+con\s+" + NUMERO + r"\s+cajones\b", text[pieza.end() :], re.I)
            and not re.search(
                r"\b(?:otra|segunda|dos|2)\s+$",
                text[max(0, pieza.start() - 15) : pieza.start()],
                re.I,
            )
            and any(
                old.group().casefold() == "cajonera"
                and re.match(r"[^.;]{0,45}\bintegrad[ao]\b", text[old.end() : pieza.start()], re.I)
                for old in piezas[:index]
            )
        ):
            repeated.append(pieza)
            candidates.append(
                Candidate(
                    candidate_id=f"c{len(candidates) + 1}",
                    label="COMPONENTE",
                    start=pieza.start(),
                    end=pieza.end(),
                    text=pieza.group(),
                    source="RULE",
                    decision="REJECTED",
                    reason="Reiteración descriptiva de la cajonera integrada",
                )
            )
    piezas = [p for p in piezas if p not in repeated]
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

    colores_explicitos = list(re.finditer(r"\b(?:" + COLORES + r")\b", text, re.I))

    def es_material(match):
        return not any(c.start() <= match.start() < c.end() for c in colores_explicitos)

    def evidencia(match, label, value=None, component=None, decision="ACCEPTED", reason=None):
        if (
            label in {"MATERIAL", "COLOR"}
            and decision == "ACCEPTED"
            and is_explicitly_negated(text, match.start())
        ):
            decision = "REJECTED"
            reason = "Atributo explícitamente excluido"
        if label == "COLOR" and match.group().casefold() == "no-gal":
            value = "nogal"
        if label == "MATERIAL" and re.fullmatch(r"melamine(?:\s+MDP)?", match.group(), re.I):
            value = re.sub("melamine", "melamina", match.group(), flags=re.I)
            warnings.append(
                Warning(
                    code="UNKNOWN_TERM",
                    path="/candidates",
                    severity="INFO",
                    message="Se interpretó 'melamine' como 'melamina'; confirme el material.",
                )
            )
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

    restricciones = [
        m.group().strip()
        for m in re.finditer(
            r"\b(?:sin|no\s+lleva)\s+(?:"
            + NUMERO
            + r"\s+)?(?:"
            + COMPONENTES
            + r"|chapas?(?: de seguridad)?|cerraduras?)\b",
            text,
            re.I,
        )
    ]
    if restricciones:
        item.observations = "; ".join(
            dict.fromkeys(filter(None, [item.observations, *restricciones]))
        )

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
        # Una nueva entidad coordinada corta el ámbito aunque su nombre
        # no esté en el vocabulario (p. ej. «y una etapa de 18 mm»).
        # No corregir ASR ni fabricar una tapa por similitud léxica.
        nueva_entidad = re.search(
            rf"\b(?:y|con)\s+{NUMERO}\s+"
            r"(?!(?:mm|cm|m|mil[ií]metros?|cent[ií]metros?|metros?)\b)\w+",
            text[pieza.end() : limite],
            re.I,
        )
        if nueva_entidad:
            limite = pieza.end() + nueva_entidad.start()
        ambitos.append((pieza.end(), limite))
        for material in re.finditer(r"\b(?:" + MATERIALES + r")\b", text, re.I):
            if pieza.end() <= material.start() < limite and es_material(material):
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
        if not rectificacion and not ambigua:
            # Una corrección explícita seguida de otra sin delimitadores no
            # satisface el patrón estricto: conservar todos los valores dudosos.
            ambigua = CORRECCION_INCOMPLETA.match(fragmento)
        # Varias rectificaciones sucesivas sin repetir la pieza no autorizan
        # a elegir una cantidad intermedia: se remite todo a revisión.
        if rectificacion and re.search(
            r"(?:[,;.]|\s)\s*no\s*,?\s*(?:mejor|\d+|" + NUMEROS + r")\b",
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
                    rf"(?:[,;.]|\s)\s*no\s*,?\s*mejor\s+(?P<numero>{NUMERO})\b",
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
            ("COLOR", r"\b(?:" + COLORES + r")\b"),
            ("ACABADO", r"\b(?:epoxi|satinado|canto termosellado|mate|brillante)\b"),
        ):
            for match in re.finditer(patron, text, re.I):
                if pieza.end() <= match.start() < limite:
                    evidencia(match, atributo, component=component)
        for dimension in item.dimensions:
            ref = next((c for c in candidates if c.candidate_id in dimension.evidence_ids), None)
            if (
                ref
                and ref.start < pieza.start() < ref.end
                and re.fullmatch(
                    r"(?:ancho|alto|altura|largo|profundidad|fondo)\s+de\s+",
                    text[ref.start : pieza.start()],
                    re.I,
                )
            ):
                dimension.component_ref = component
                ref.component_ref = component
            if ref and pieza.end() <= ref.start < limite:
                connector = text[pieza.end() : ref.start]
                if re.fullmatch(r"\s+(?:de|con)\s+", connector, re.I):
                    dimension.component_ref = component
                    ref.component_ref = component
        for accesorio in item.accessories:
            ref = next((c for c in candidates if c.candidate_id in accesorio.evidence_ids), None)
            if ref and pieza.end() <= ref.start < limite:
                accesorio.component_ref = component
                ref.component_ref = component
        for thickness in item.thicknesses:
            referencia = next(
                (c for c in candidates if c.candidate_id in thickness.evidence_ids), None
            )
            if referencia and pieza.end() <= referencia.start < limite:
                thickness.component_ref = component
                referencia.component_ref = component
    for thickness in item.thicknesses:
        if thickness.component_ref is None:
            warnings.append(
                Warning(
                    code="REQUIRED_FIELD_MISSING",
                    path="/item_proposal/thicknesses",
                    severity="REVIEW",
                    message=f"El espesor {thickness.original_text} requiere identificar su pieza.",
                )
            )
    for label, patron in (
        ("MATERIAL", MATERIALES),
        ("COLOR", COLORES),
    ):
        for match in re.finditer(r"\b(?:" + patron + r")\b", text, re.I):
            if label == "MATERIAL" and not es_material(match):
                continue
            if not any(inicio <= match.start() < fin for inicio, fin in ambitos):
                evidencia(match, label)
    # Segmentación ASR: prefijo explícito «color» unido a un valor conocido.
    # No normalizar el texto ni reconocer sufijos dentro de palabras libres.
    for unido in re.finditer(r"\bcolor(?P<color>" + COLORES + r")\b", text, re.I):
        inicio = unido.start("color")
        literal = re.compile(re.escape(unido.group("color"))).match(text, inicio)
        componente = next(
            (
                item.components[i].component_id
                for i, (a, b) in enumerate(ambitos)
                if a <= inicio < b
            ),
            None,
        )
        evidencia(literal, "COLOR", component=componente)
    # Sólo el atributo contiguo del producto principal. No propagar colores
    # de piezas, negaciones, alternativas o rectificaciones a primary_color.
    principal = next(
        (c for c in candidates if c.label == "PRODUCTO" and c.decision == "ACCEPTED"), None
    )
    if principal:
        especificacion = re.match(
            r"\s+de\s+(?P<material>"
            + MATERIALES
            + r")\s+(?P<color>"
            + COLORES
            + r")\b(?=\s*(?:[,.;]|$))",
            text[principal.end :],
            re.I,
        )
        colores = [c for c in candidates if c.label == "COLOR"]
        materiales = [c for c in candidates if c.label == "MATERIAL"]
        ambigua = re.search(
            r"\b(?:o|no|sino|mejor|perd[oó]n|corrijo|sin)\b", text[principal.end :], re.I
        )
        if especificacion and not ambigua and len(colores) == 1 and len(materiales) == 1:
            color = colores[0]
            inicio = principal.end + especificacion.start("color")
            if (
                color.start == inicio
                and color.component_ref is None
                and color.decision == "ACCEPTED"
            ):
                valor = re.sub(r"^blanca$", "blanco", color.text, flags=re.I)
                valor = re.sub(r"^negra", "negro", valor, flags=re.I).casefold()
                color.normalized_value = valor
                item.primary_color = Color(value=valor, evidence_ids=[color.candidate_id])
    # «dos lados de ...» describe geometría compuesta, no el largo global.
    # El contrato de dimensión sólo admite un eje por medida: solicitar croquis.
    lados = re.search(r"\b(?:dos|2)\s+lados\s+de\s+", text, re.I)
    if lados:
        for dimension in item.dimensions[:]:
            ref = next((c for c in candidates if c.candidate_id in dimension.evidence_ids), None)
            if ref and lados.end() <= ref.start <= lados.end() + 2:
                item.dimensions.remove(dimension)
                ref.label = "DIMENSION"
                ref.decision = "UNRESOLVED"
                ref.reason = "Medida de dos lados: requiere geometría explícita"
                item.unresolved.append(ref.candidate_id)
                warnings.append(
                    Warning(
                        code="MISSING_AXIS",
                        path="/item_proposal/dimensions",
                        severity="REVIEW",
                        message="Confirme por separado las medidas y orientación de ambos lados.",
                    )
                )
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
    cero_descuento = re.search(
        r"\bsin\s+descuento\b|\bdescuento\s+(?:de\s+)?(?:0(?:[.,]00)?|cero)\b", text, re.I
    )
    if cero_descuento:
        evidencia(cero_descuento, "DESCUENTO", "0.00")
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
    for excluded in negadas:
        boundary = next(
            (p.start() for p in piezas_originales if p.start() > excluded.start()), len(text)
        )
        stop = re.search(r"[,;.]|\b(?:pero|con)\b", text[excluded.end() : boundary], re.I)
        if stop:
            boundary = excluded.end() + stop.start()
        for c in candidates:
            if (
                c.label in {"COLOR", "MATERIAL", "ACABADO", "ESPESOR"}
                and excluded.end() <= c.start < boundary
            ):
                c.decision = "REJECTED"
                c.reason = "Atributo de una pieza excluida"
                item.thicknesses = [
                    m for m in item.thicknesses if c.candidate_id not in m.evidence_ids
                ]
    resolver_atributos(item, candidates, text, warnings)
    # La nueva ruta oral no afirma un espesor GENERAL por carecer de pieza.
    # El valor literal permanece trazable y resoluble por PRF-03. La ruta
    # numérica histórica conserva su representación contractual de pendiente.
    for thickness in item.thicknesses[:]:
        if thickness.component_ref is None and not re.search(r"\d", thickness.original_text):
            ref = next(c for c in candidates if c.candidate_id in thickness.evidence_ids)
            ref.decision = "UNRESOLVED"
            ref.reason = "Espesor oral sin pieza identificada"
            item.unresolved.append(ref.candidate_id)
            item.thicknesses.remove(thickness)
    return item


def resolver_atributos(item, candidates, text, warnings):
    """Resuelve alternativas/correcciones sólo en el mismo campo y ámbito.

    Los pendientes conservan los spans literales; no se selecciona el último
    color/material por orden de aparición. Las medidas sin rectificación
    permanecen múltiples para el arbitraje histórico de PRF-03.
    """
    grupos = {}
    for c in candidates:
        if c.decision == "ACCEPTED" and c.label in {"COLOR", "MATERIAL", "ACABADO"}:
            grupos.setdefault((c.label, c.component_ref), []).append(c)
    for valores in grupos.values():
        for anterior, siguiente in zip(valores, valores[1:]):
            tramo = text[anterior.end : siguiente.start]
            if re.fullmatch(
                r"\s*[,;]?\s*(?:corrijo|perd[oó]n|no\s*,?\s*mejor)\s*[,;]?\s*(?:de\s+)?",
                tramo,
                re.I,
            ):
                anterior.decision = "REJECTED"
                anterior.reason = "Atributo rectificado explícitamente"
            elif re.fullmatch(r"\s+o\s+(?:de\s+)?", tramo, re.I):
                for c in (anterior, siguiente):
                    c.decision = "UNRESOLVED"
                    c.reason = "Alternativa sin selección explícita"
                    if c.candidate_id not in item.unresolved:
                        item.unresolved.append(c.candidate_id)
                warnings.append(
                    Warning(
                        code="CONFLICTING_VALUES",
                        path="/candidates",
                        severity="REVIEW",
                        message="Seleccione una de las alternativas dictadas.",
                    )
                )
    for collection in (item.dimensions, item.thicknesses):
        scoped = {}
        ordered = sorted(
            collection,
            key=lambda m: next(c.start for c in candidates if c.candidate_id in m.evidence_ids),
        )
        for previous, following in zip(ordered, ordered[1:]):
            a = next(c for c in candidates if c.candidate_id in previous.evidence_ids)
            b = next(c for c in candidates if c.candidate_id in following.evidence_ids)
            if (
                following.component_ref is None
                and previous.component_ref is not None
                and getattr(previous, "axis", None) == getattr(following, "axis", None)
                and re.fullmatch(
                    r"\s*[,;]?\s*(?:corrijo|perd[oó]n|no\s*,?\s*mejor)\s*[,;]?\s*(?:de\s+)?",
                    text[a.end : b.start],
                    re.I,
                )
            ):
                following.component_ref = previous.component_ref
                b.component_ref = previous.component_ref
        for medida in collection:
            scoped.setdefault((getattr(medida, "axis", None), medida.component_ref), []).append(
                medida
            )
        for medidas in scoped.values():
            medidas.sort(
                key=lambda m: next(c.start for c in candidates if c.candidate_id in m.evidence_ids)
            )
            for anterior, siguiente in zip(medidas, medidas[1:]):
                a = next(c for c in candidates if c.candidate_id in anterior.evidence_ids)
                b = next(c for c in candidates if c.candidate_id in siguiente.evidence_ids)
                tramo = text[a.end : b.start]
                if re.fullmatch(
                    r"\s*[,;]?\s*(?:corrijo|perd[oó]n|no\s*,?\s*mejor)\s*[,;]?\s*(?:de\s+)?",
                    tramo,
                    re.I,
                ):
                    a.decision = "REJECTED"
                    a.reason = "Medida rectificada explícitamente"
                    if anterior in collection:
                        collection.remove(anterior)
    for collection in (item.dimensions, item.thicknesses):
        for value in collection[:]:
            ref = next(c for c in candidates if c.candidate_id in value.evidence_ids)
            if is_explicitly_negated(text, ref.start):
                ref.decision = "REJECTED"
                ref.reason = "Medida explícitamente negada"
                collection.remove(value)
    if item.primary_color:
        if any(
            c.candidate_id in item.primary_color.evidence_ids and c.decision != "ACCEPTED"
            for c in candidates
        ):
            item.primary_color = None
    # Un accesorio integrado sólo refiere a la pieza del mismo ámbito.
    # No se fabrican relaciones padre-hijo entre componentes.
