"""
Ferramentas de navegação curricular — específicas para Física (UFABC).

Estas ferramentas complementam as ferramentas genéricas do template com
funcionalidades voltadas para a navegação do currículo de um curso inteiro,
não apenas de uma disciplina individual.

Física é oferecido em duas modalidades — Bacharelado e
Licenciatura — com núcleo comum e diferenças (ex: na Licenciatura, disciplinas
pedagógicas e estágio supervisionado em docência). Os primeiros ciclos também
diferem: BCT para o Bacharelado e LCNE para a Licenciatura (ver PRIMEIRO_CICLO). Por isso as ferramentas
recebem um parâmetro opcional `modalidade`; omitido, a resposta cobre as duas
e indica as diferenças.

Convenção de conteúdo: arquivos de content/syllabus/ e content/bibliography/
que contenham "bacharelado" ou "licenciatura" no nome são atribuídos à
modalidade correspondente; os demais valem para ambas.
"""

from __future__ import annotations

from mcp import types

from ..resources.loader import ContentLoader

MODALIDADES = ["bacharelado", "licenciatura"]
PRIMEIRO_CICLO = {"bacharelado": "BCT", "licenciatura": "LCNE"}


def register_curriculum_tools(
    tools: list[types.Tool],
    handlers: dict,
    loader: ContentLoader,
    config: dict,
) -> None:
    if not config.get("features", {}).get("curriculum_navigation"):
        return

    course_name = config.get("course_name", "Física")
    modalidades_cfg = config.get("modalidades", {})

    modalidade_schema = {
        "type": "string",
        "enum": MODALIDADES,
        "description": (
            "Modalidade do curso: 'bacharelado' ou 'licenciatura'. "
            "Omita para cobrir as duas e destacar as diferenças."
        ),
    }

    def label(modalidade: str) -> str:
        if not modalidade:
            return f"{course_name} (Bacharelado e Licenciatura)"
        return modalidades_cfg.get(modalidade, {}).get("name") or (
            f"{modalidade.title()} em {course_name}"
        )

    def ppc_of(modalidade: str) -> str:
        if modalidade:
            version = modalidades_cfg.get(modalidade, {}).get("ppc_version")
        else:
            version = config.get("metadata", {}).get("ppc_version")
        return version or "vigente"

    def matches(name: str, modalidade: str) -> bool:
        """A file belongs to a modality if it names it, or names neither."""
        lowered = name.lower()
        named = [m for m in MODALIDADES if m in lowered]
        return not modalidade or not named or modalidade in named

    def filter_results(results: list[dict], modalidade: str) -> list[dict]:
        return [r for r in results if matches(r["uri"], modalidade)]

    def scope_note(modalidade: str) -> str:
        if modalidade:
            return f"restringindo-se à modalidade {modalidade}"
        return (
            "cobrindo Bacharelado e Licenciatura e indicando explicitamente o que é "
            "comum às duas e o que é exclusivo de cada modalidade"
        )

    # --- get_curriculum_structure ---
    tools.append(
        types.Tool(
            name="get_curriculum_structure",
            description=(
                f"Retorna a estrutura curricular de {course_name} na UFABC: "
                "disciplinas obrigatórias, de opção limitada, livres, extensão, estágio e TCC. "
                "Na Licenciatura inclui as disciplinas pedagógicas e o estágio supervisionado. "
                "Baseado nos arquivos carregados em content/syllabus/."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "modalidade": modalidade_schema,
                    "ppc": {
                        "type": "string",
                        "description": "Versão do PPC a consultar. Padrão: a vigente da modalidade.",
                    },
                },
                "required": [],
            },
        )
    )

    async def handle_get_curriculum_structure(args: dict) -> str:
        modalidade = args.get("modalidade", "")
        ppc = args.get("ppc") or ppc_of(modalidade)

        all_syllabus = [i for i in loader.get_section("syllabus") if matches(i["name"], modalidade)]
        ppc_items = [i for i in all_syllabus if ppc in i["name"]]
        items = ppc_items if ppc_items else all_syllabus

        if not items:
            bib_results = loader.search("obrigatória", section="bibliography")
            bib_results = filter_results(bib_results, modalidade)
            if bib_results:
                snippets = "\n\n".join(r["snippet"] for r in bib_results[:5])
                return (
                    f"## Estrutura Curricular — {label(modalidade)} (PPC {ppc})\n\n"
                    f"[Extraído da bibliografia]\n\n{snippets}\n\n"
                    f"[O assistente deve apresentar a estrutura curricular completa "
                    f"com base nos trechos acima, {scope_note(modalidade)}.]"
                )
            return (
                "Nenhum arquivo de ementa carregado ainda. "
                "Adicione arquivos em content/syllabus/ (ex: curriculo_bacharelado.md, "
                "curriculo_licenciatura.md) ou verifique se os PDFs dos PPCs estão em "
                "content/bibliography/ e se o suporte a PDF está instalado "
                "(`pip install -e \".[pdf]\"`). "
            )

        combined = "\n\n---\n\n".join(f"# {i['name']}\n\n{i['text']}" for i in items)
        return (
            f"## Estrutura Curricular — {label(modalidade)} (PPC {ppc})\n\n"
            f"{combined}"
        )

    handlers["get_curriculum_structure"] = handle_get_curriculum_structure

    # --- compare_modalidades ---
    tools.append(
        types.Tool(
            name="compare_modalidades",
            description=(
                "Compara o Bacharelado e a Licenciatura em Física: núcleo comum, "
                "disciplinas exclusivas, carga horária, estágio, TCC, perfil do egresso e "
                "atuação profissional. Útil para decidir a modalidade ou cursar as duas."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "aspect": {
                        "type": "string",
                        "description": (
                            "Aspecto específico a comparar, ex: 'estágio', 'TCC', "
                            "'carga horária', 'atuação profissional', 'dupla diplomação'. "
                            "Omita para uma comparação geral."
                        ),
                    }
                },
                "required": [],
            },
        )
    )

    async def handle_compare_modalidades(args: dict) -> str:
        aspect = args.get("aspect", "").strip()

        sections = []
        for modalidade in MODALIDADES:
            query = aspect if aspect else modalidade
            results = loader.search(query, section="syllabus")
            results += loader.search(query, section="bibliography")
            results = [r for r in results if modalidade in r["uri"].lower()]
            if results:
                snippets = "\n\n".join(r["snippet"] for r in results[:4])
            else:
                snippets = "Nenhum material específico desta modalidade carregado."
            sections.append(f"### {label(modalidade)}\n\n{snippets}")

        aspect_note = f" — {aspect}" if aspect else ""
        return (
            f"## Bacharelado × Licenciatura — {course_name}{aspect_note}\n\n"
            + "\n\n".join(sections)
            + "\n\n[O assistente deve comparar as duas modalidades"
            f"{' quanto a ' + aspect if aspect else ''} em uma tabela "
            "(núcleo comum / só Bacharelado / só Licenciatura), destacando estágio, TCC, "
            "disciplinas pedagógicas e atuação profissional (pesquisa, mercado, docência na "
            "educação básica). Indique se é possível cursar as duas modalidades e o que seria "
            "aproveitado. Fundamente nos trechos acima e avise quando faltar material.]"
        )

    handlers["compare_modalidades"] = handle_compare_modalidades

    # --- list_subjects_by_area ---
    tools.append(
        types.Tool(
            name="list_subjects_by_area",
            description=(
                "Lista as disciplinas de Física agrupadas por área "
                "(ex: Mecânica Clássica, Eletromagnetismo, Termodinâmica e Física Estatística, Mecânica Quântica, Física Moderna, Física Matemática e Computacional, Ensino de Física). "
                "Útil para explorar opções limitadas e livres."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "area": {
                        "type": "string",
                        "description": (
                            "Área a filtrar (ex: 'mecânica', 'eletromagnetismo', 'termodinâmica', 'quântica', 'física moderna', 'física computacional', 'ensino'). Omita para listar todas."
                        ),
                    },
                    "modalidade": modalidade_schema,
                },
                "required": [],
            },
        )
    )

    async def handle_list_subjects_by_area(args: dict) -> str:
        area = args.get("area", "").strip().lower()
        modalidade = args.get("modalidade", "")

        query = area if area else "disciplina"
        results = filter_results(loader.search(query, section="syllabus"), modalidade)
        if not results:
            results = filter_results(loader.search(query, section="bibliography"), modalidade)

        context_block = ""
        if results:
            snippets = "\n\n".join(r["snippet"] for r in results[:6])
            context_block = f"\n\n## Trechos relevantes dos materiais\n\n{snippets}"

        area_label = f" — Área: {area.title()}" if area else ""
        return (
            f"## Disciplinas — {label(modalidade)}{area_label}\n"
            f"{context_block}\n\n"
            f"[O assistente deve listar as disciplinas"
            f"{' na área de ' + area if area else ''}, "
            f"organizadas por categoria (obrigatória / opção limitada / livre), "
            f"indicando quais já são cursadas no primeiro ciclo (BCT para o Bacharelado, LCNE para a Licenciatura), {scope_note(modalidade)}.]"
        )

    handlers["list_subjects_by_area"] = handle_list_subjects_by_area

    # --- get_disciplinas_limitadas ---
    tools.append(
        types.Tool(
            name="get_disciplinas_limitadas",
            description=(
                "Retorna as disciplinas de opção limitada de Física e as "
                "disciplinas com oferta restrita, a partir do PPC ou do planejamento de oferta. "
                "Útil para planejar a matrícula com antecedência."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "area": {
                        "type": "string",
                        "description": "Filtrar por área ou nome de disciplina (opcional).",
                    },
                    "modalidade": modalidade_schema,
                },
                "required": [],
            },
        )
    )

    async def handle_get_disciplinas_limitadas(args: dict) -> str:
        area = args.get("area", "").strip()
        modalidade = args.get("modalidade", "")

        results = loader.search("limitad", section="syllabus")
        results += loader.search("limitad", section="bibliography")
        results = filter_results(results, modalidade)
        if area:
            results = [r for r in results if area.lower() in r["snippet"].lower()] or results

        if not results:
            return (
                "Nenhum material sobre disciplinas de opção limitada encontrado. "
                "Adicione os PPCs ou a lista de oferta em content/bibliography/ "
                "e verifique se o suporte a PDF está instalado "
                "(`pip install -e \".[pdf]\"`). "
            )

        snippets = "\n\n".join(r["snippet"] for r in results[:8])
        filter_note = f" (filtrado por: '{area}')" if area else ""
        return (
            f"## Disciplinas de Opção Limitada — {label(modalidade)}{filter_note}\n\n"
            f"{snippets}\n\n"
            f"[O assistente deve apresentar as disciplinas de opção limitada "
            f"listadas nos trechos acima de forma organizada, indicando nomes e códigos, "
            f"{scope_note(modalidade)}.]"
        )

    handlers["get_disciplinas_limitadas"] = handle_get_disciplinas_limitadas

    # --- get_progression_requirements ---
    tools.append(
        types.Tool(
            name="get_progression_requirements",
            description=(
                "Retorna os requisitos de ingresso (Bacharelado via BCT, Licenciatura via LCNE), "
                "progressão e formatura em Física: créditos mínimos por categoria, TCC, estágio (na Licenciatura, "
                "estágio supervisionado em docência), extensão, coeficientes e jubilamento."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": (
                            "Aspecto específico a consultar, ex: 'ingresso', 'TCC', "
                            "'estágio supervisionado', 'extensão', 'coeficiente de rendimento'."
                        ),
                    },
                    "modalidade": modalidade_schema,
                },
                "required": [],
            },
        )
    )

    async def handle_get_progression_requirements(args: dict) -> str:
        topic = args.get("topic", "").strip()
        modalidade = args.get("modalidade", "")

        query = topic if topic else "créditos"
        results = filter_results(loader.search(query, section="syllabus"), modalidade)
        if not results:
            results = filter_results(loader.search(query, section="bibliography"), modalidade)

        context_block = ""
        if results:
            snippets = "\n\n".join(r["snippet"] for r in results[:5])
            context_block = f"\n\n## Trechos relevantes dos materiais\n\n{snippets}"

        topic_note = f" — {topic.title()}" if topic else ""
        return (
            f"## Requisitos de Progressão e Formatura — {label(modalidade)}{topic_note}\n"
            f"{context_block}\n\n"
            f"[O assistente deve descrever os requisitos{' relacionados a ' + topic if topic else ''} "
            f"para ingresso, progressão e formatura (PPC {ppc_of(modalidade)}), "
            f"{scope_note(modalidade)}, baseando-se nos materiais acima. "
            f"Se não houver material carregado, avise que a resposta não está fundamentada "
            f"nos documentos oficiais.]"
        )

    handlers["get_progression_requirements"] = handle_get_progression_requirements

    # --- plan_academic_journey ---
    tools.append(
        types.Tool(
            name="plan_academic_journey",
            description=(
                "Gera um planejamento acadêmico sugerido rumo ao curso de Física, "
                "considerando a modalidade (ou as duas, para dupla diplomação), o quadrimestre "
                "atual, disciplinas já cursadas e a área de interesse. "
                "Sugere disciplinas para os próximos quadrimestres."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "current_quarter": {
                        "type": "integer",
                        "description": "Quadrimestre atual na UFABC (contando desde o ingresso no BCT ou na LCNE).",
                    },
                    "modalidade": {
                        "type": "string",
                        "enum": MODALIDADES + ["ambas"],
                        "description": (
                            "Modalidade pretendida: 'bacharelado', 'licenciatura' ou 'ambas' "
                            "(dupla diplomação)."
                        ),
                    },
                    "completed_subjects": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de disciplinas já concluídas (nomes ou códigos).",
                    },
                    "focus_area": {
                        "type": "string",
                        "description": (
                            "Área de interesse para orientar as opções limitadas e livres, ex: "
                            "'Física da Matéria Condensada', 'Astrofísica e Cosmologia', 'Física Teórica', 'Física Médica', 'Ensino de Física'."
                        ),
                    },
                },
                "required": ["current_quarter"],
            },
        )
    )

    async def handle_plan_academic_journey(args: dict) -> str:
        quarter = args.get("current_quarter", 1)
        modalidade = args.get("modalidade", "")
        completed = args.get("completed_subjects", [])
        focus = args.get("focus_area", "")

        filter_modalidade = "" if modalidade == "ambas" else modalidade
        syllabus_items = [
            i for i in loader.get_section("syllabus") if matches(i["name"], filter_modalidade)
        ]
        syllabus_text = (
            "\n\n".join(f"# {i['name']}\n\n{i['text']}" for i in syllabus_items)
            if syllabus_items
            else "Nenhuma ementa carregada."
        )

        modalidade_note = (
            f"\n**Modalidade:** {'Bacharelado e Licenciatura (dupla diplomação)' if modalidade == 'ambas' else modalidade.title()}"
            if modalidade
            else "\n**Modalidade:** não informada"
        )
        completed_note = (
            f"\nDisciplinas concluídas: {', '.join(completed)}" if completed else ""
        )
        focus_note = f"\nÁrea de interesse: {focus}" if focus else ""

        if modalidade == "ambas":
            modalidade_instruction = (
                "Como o estudante pretende as duas modalidades, maximize o núcleo comum, "
                "intercale as disciplinas pedagógicas e o estágio supervisionado da "
                "Licenciatura com as específicas do Bacharelado, verifique o que falta do BCT "
                "e da LCNE (primeiros ciclos de cada modalidade) e indique o tempo total estimado."
            )
        elif modalidade:
            modalidade_instruction = (
                f"Considere apenas os requisitos da modalidade {modalidade}, cujo primeiro "
                f"ciclo é {'o BCT' if modalidade == 'bacharelado' else 'a LCNE'}."
            )
        else:
            modalidade_instruction = (
                "Como a modalidade não foi informada, pergunte ao estudante ou apresente "
                "o plano para cada modalidade separadamente."
            )

        return (
            f"## Planejamento Acadêmico — {course_name}\n"
            f"**Quadrimestre atual:** {quarter}"
            f"{modalidade_note}"
            f"{completed_note}"
            f"{focus_note}\n\n"
            f"## Referência curricular\n\n{syllabus_text}\n\n"
            f"[O assistente deve sugerir um planejamento quadrimestral a partir do "
            f"quadrimestre {quarter}, separando o que ainda falta do primeiro ciclo (BCT ou LCNE) e as "
            f"obrigatórias do curso, respeitando a cadeia de pré-requisitos recomendados"
            f"{' e priorizando opções limitadas ligadas a ' + focus if focus else ''}. "
            f"{modalidade_instruction} "
            f"Apresente o plano em tabela ou lista por quadrimestre.]"
        )

    handlers["plan_academic_journey"] = handle_plan_academic_journey
