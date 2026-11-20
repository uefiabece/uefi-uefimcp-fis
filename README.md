# uefi-uefimcp-fis

Servidor MCP de **Física**, UFABC, nas duas modalidades: **Bacharelado** e **Licenciatura**. Nível: **curso** (segundo ciclo: Bacharelado a partir do BCT, Licenciatura a partir da LCNE).

## Origem

Derivado de [`uefi-uefimcp`](https://github.com/uefiabece/uefi-uefimcp) por `git clone`
(commit de origem registrado em `config/subject.json`), sem importar materiais acadêmicos.
A estrutura de duas modalidades vem do `uefi-uefimcp-bio`; a camada compartilhada (PDF,
SDK MCP v1, `scripts/check_mcp.py`) vem de `uefi-uefimcp-bct` e `uefi-uefimcp-neuro`.

```text
uefi-uefimcp
  ├── uefi-uefimcp-bct   (1º ciclo do Bacharelado)
  ├── uefi-uefimcp-lcne  (1º ciclo da Licenciatura)
  └── uefi-uefimcp-fis
      └── (disciplinas de Física)
```

## Bacharelado e Licenciatura

- `config/subject.json` tem um bloco `modalidades` com nome, primeiro ciclo (`prerequisite_course`: BCT ou LCNE), sigla, versão do PPC e créditos de **cada** modalidade.
- As ferramentas de currículo aceitam `modalidade` (`bacharelado` ou `licenciatura`). Omitido, a resposta cobre as duas e separa o que é comum do que é exclusivo.
- `compare_modalidades` compara as duas diretamente; `plan_academic_journey` aceita também `ambas` (dupla diplomação).
- **Convenção de arquivos:** em `content/`, arquivos com `bacharelado` ou `licenciatura` no nome valem só para aquela modalidade; os demais, para ambas.

## Executar

Requer Python 3.11 ou superior. No diretório deste repositório:

```sh
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[pdf,math]"
.venv/Scripts/python run.py
```

O processo usa transporte **stdio**: deve ser iniciado por um cliente MCP.
Em Linux/macOS, use `.venv/bin/python`.

## Conectar

```sh
claude mcp add --scope user uefi-uefimcp-fis -- "CAMINHO_ABSOLUTO/uefi-uefimcp-fis/.venv/Scripts/python.exe" "CAMINHO_ABSOLUTO/uefi-uefimcp-fis/run.py"
```

Outros clientes: veja `config/mcp.example.json`.

## Ferramentas

18 ferramentas:

- **Conteúdo / ensino / exercícios (template):** `get_syllabus`, `get_bibliography`, `get_past_exams`, `search_content`, `get_notes`, `explain_concept`, `get_topic_outline`, `generate_study_plan`, `get_exercises`, `solve_exercise`, `generate_exercise`, `generate_flashcards`
- **Navegação curricular:** `get_curriculum_structure`, `compare_modalidades`, `list_subjects_by_area`, `get_disciplinas_limitadas`, `get_progression_requirements`, `plan_academic_journey`

Prompts: `teach` e `solve`.

## Conteúdo

As pastas de `content/` estão vazias. Sugestões:

- `content/bibliography/ppc_bacharelado_<ano>.pdf` e `ppc_licenciatura_<ano>.pdf`
- `content/syllabus/curriculo_bacharelado.md` e `curriculo_licenciatura.md`
- Material comum às duas sem a modalidade no nome

Ao adicionar os PPCs, preencha o bloco `modalidades` em `config/subject.json`.

## Verificar

```sh
.venv/Scripts/python scripts/check_mcp.py
```
