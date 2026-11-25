#!/usr/bin/env python3
"""Verificador da wiki (OKF) do second brain da live.

Confere o que dá para conferir sem opinião:
  - frontmatter YAML presente, fechado e com `type` não vazio;
  - campos de tempo com fuso;
  - notas de rodapé [^id] usadas e definidas, e id presente em sources;
  - links internos (.md) que resolvem;
  - páginas fora do índice e páginas órfãs;
  - log.md sem frontmatter e index.md com okf_version;
  - raw/ igual ao manifesto (nada foi alterado).

Uso, dentro de exemplo/:  python3 ferramentas/checar-wiki.py
Sem dependências: roda com o python3 do macOS.
Saída: linhas ERRO / AVISO / OK e um resumo. Código de saída 1 se houver ERRO.
"""
import hashlib, pathlib, re, sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
WIKI = RAIZ / 'wiki'
RAW = RAIZ / 'raw'
MANIFESTO = pathlib.Path(__file__).resolve().parent / 'raw.sha256'
RESERVADOS = {'index.md', 'log.md'}
TEMPO = re.compile(r'^\s*(at|last_modified|stale_after|from|to):\s*["\']?(\S+?)["\']?\s*$')
FUSO = re.compile(r'(Z|[+-]\d{2}:\d{2})$')

erros, avisos = [], []
def erro(arq, msg): erros.append(f'ERRO  {arq}: {msg}')
def aviso(arq, msg): avisos.append(f'AVISO {arq}: {msg}')

def frontmatter(texto):
    if not texto.startswith('---\n'):
        return None, texto
    fim = texto.find('\n---', 4)
    if fim < 0:
        return 'aberto', texto
    return texto[4:fim], texto[fim + 4:]

def rel(p):
    return p.relative_to(RAIZ).as_posix()

def sem_codigo(corpo):
    """Tira blocos ``` e ~~~ e código inline, para não confundir exemplo com link."""
    corpo = re.sub(r'(```|~~~).*?\1', '', corpo, flags=re.S)
    return re.sub(r'`[^`\n]*`', '', corpo)

def manifesto_atual():
    linhas = []
    for f in sorted(RAW.rglob('*')):
        if f.is_file() and f.name != '.DS_Store':
            linhas.append(f'{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(RAIZ).as_posix()}')
    return '\n'.join(linhas) + '\n'

# --- raw/ -------------------------------------------------------------------
if '--gerar-manifesto' in sys.argv:
    MANIFESTO.write_text(manifesto_atual())
    print(f'manifesto gravado: {rel(MANIFESTO)}')
    sys.exit(0)
if MANIFESTO.exists():
    esperado = dict((l.split('  ', 1)[1], l.split('  ', 1)[0]) for l in MANIFESTO.read_text().splitlines() if l)
    atual = dict((l.split('  ', 1)[1], l.split('  ', 1)[0]) for l in manifesto_atual().splitlines() if l)
    for nome in sorted(set(esperado) | set(atual)):
        if nome not in atual:
            erro(nome, 'sumiu de raw/')
        elif nome not in esperado:
            aviso(nome, 'arquivo novo em raw/ (fora do manifesto): se for fonte nova, rode com --gerar-manifesto')
        elif esperado[nome] != atual[nome]:
            erro(nome, 'raw/ foi modificado (o agente nunca altera raw/)')
else:
    aviso('ferramentas/raw.sha256', 'sem manifesto: não dá para conferir se raw/ mudou')

# --- wiki/ ------------------------------------------------------------------
if not WIKI.exists():
    print('A wiki/ ainda não existe: nada a conferir além do raw/.')
    for l in erros + avisos: print(l)
    sys.exit(1 if erros else 0)

paginas = sorted(p for p in WIKI.rglob('*.md'))
conceitos = [p for p in paginas if p.name not in RESERVADOS]
alvos_de_link = {}           # página -> conjunto de páginas que apontam para ela
listadas_no_indice = set()

for p in paginas:
    texto = p.read_text(encoding='utf-8')
    fm, corpo = frontmatter(texto)
    nome = rel(p)

    if p.name == 'log.md':
        if fm is not None:
            erro(nome, 'log.md não pode ter frontmatter')
    elif p.name == 'index.md':
        if p.parent == WIKI:
            if not fm or 'okf_version' not in fm:
                erro(nome, 'index.md da raiz precisa declarar okf_version no frontmatter')
        elif fm is not None:
            erro(nome, 'index.md de subdiretório não pode ter frontmatter')
    else:
        if fm is None:
            erro(nome, 'sem frontmatter YAML')
            fm = ''
        elif fm == 'aberto':
            erro(nome, 'frontmatter não fecha com ---')
            fm = ''
        m = re.search(r'^type:\s*(.*)$', fm, re.M)
        if not m or not m.group(1).strip().strip('"\''):
            erro(nome, '`type` ausente ou vazio')
        for chave in re.findall(r'^([A-Za-z_]\w*):', fm, re.M):
            if len(re.findall(rf'^{chave}:', fm, re.M)) > 1:
                erro(nome, f'chave `{chave}` duplicada no frontmatter')
                break
        for linha in fm.splitlines():
            t = TEMPO.match(linha)
            if t and re.match(r'\d{4}-\d{2}-\d{2}T', t.group(2)) and not FUSO.search(t.group(2)):
                erro(nome, f'campo de tempo sem fuso: {linha.strip()}')
        st = re.search(r'^status:\s*(\S+)', fm, re.M)
        if st and st.group(1).strip('"\'') not in ('draft', 'stable', 'deprecated'):
            erro(nome, f'status inválido: {st.group(1)}')
        ids = set(re.findall(r'^\s*-\s*id:\s*["\']?([^"\'\s]+)', fm, re.M))
        corpo_limpo = sem_codigo(corpo)
        usadas = set(re.findall(r'\[\^([^\]]+)\](?!:)', corpo_limpo))
        definidas = set(re.findall(r'^\[\^([^\]]+)\]:', corpo_limpo, re.M))
        for f in sorted(usadas - definidas):
            erro(nome, f'nota [^{f}] usada mas não definida no rodapé')
        for f in sorted((usadas | definidas) - ids):
            erro(nome, f'nota [^{f}] não corresponde a nenhum sources[].id')
        if 'sources:' in fm and not usadas:
            aviso(nome, 'tem sources, mas nenhuma afirmação cita uma nota de rodapé')

    # links internos
    for alvo in re.findall(r'\]\(([^)\s]+?\.md)(?:#[^)]*)?\)', sem_codigo(corpo)):
        if re.match(r'^[a-z]+://', alvo):
            continue
        destino = (WIKI / alvo.lstrip('/')) if alvo.startswith('/') else (p.parent / alvo)
        destino = destino.resolve()
        if not destino.exists():
            if '/raw/' in destino.as_posix() or alvo.startswith('../'):
                if not destino.exists():
                    erro(nome, f'link para fora da wiki não resolve: {alvo}')
            else:
                erro(nome, f'link quebrado: {alvo}')
            continue
        alvos_de_link.setdefault(destino, set()).add(p.resolve())
        if p.name == 'index.md':
            listadas_no_indice.add(destino)

for p in conceitos:
    nome = rel(p)
    if p.resolve() not in listadas_no_indice:
        erro(nome, 'não aparece em nenhum index.md')
    entradas = {o for o in alvos_de_link.get(p.resolve(), set()) if o.name != 'index.md'}
    if not entradas:
        aviso(nome, 'órfã: nenhuma página (fora dos índices) aponta para ela')

log = WIKI / 'log.md'
if not log.exists():
    erro('wiki/log.md', 'não existe')
elif not re.search(r'^## \d{4}-\d{2}-\d{2}$', log.read_text(), re.M):
    erro('wiki/log.md', 'sem grupo de data no formato ## AAAA-MM-DD')
if not (WIKI / 'index.md').exists():
    erro('wiki/index.md', 'não existe')

for l in erros + avisos:
    print(l)
print(f'\nResumo: {len(conceitos)} páginas de conceito · {len(erros)} erro(s) · {len(avisos)} aviso(s)')
print('OK' if not erros else 'HÁ ERROS')
sys.exit(1 if erros else 0)
