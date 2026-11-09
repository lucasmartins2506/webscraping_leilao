import argparse
import asyncio
import json
import re
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError

BASE_URL = "https://www.kwara.com.br/busca"
SITE_URL = "https://www.kwara.com.br"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

EXCEL_COLUMNS = [
    "Nome do produto",
    "Preço atual",
    "Valor numérico (R$)",
    "Lances",
    "Visitas",
    "Estado (UF)",
    "Encerramento",
    "Link do lote",
]


def slugify_filename(text: str) -> str:
    """Converte o termo pesquisado em um nome de arquivo seguro (ex: 'ar condicionado' -> 'ar_condicionado')."""
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", normalized.strip().lower()).strip("_")
    return clean or "produtos"


def format_brl(cents: int | float | None) -> str:
    """Formata valor em centavos para o padrão brasileiro R$ 1.234,56."""
    if cents is None:
        return "Preço indisponível"
    reais = cents / 100.0
    formatted = f"{reais:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def format_iso_date(iso_str: str | None) -> str:
    """Formata data ISO-8601 para DD/MM/YYYY HH:MM."""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00")).astimezone()
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return iso_str


def build_search_url(query: str, page_number: int) -> str:
    """Monta a URL de busca para qualquer termo sem travar em uma categoria específica."""
    encoded_query = urllib.parse.quote_plus(query.strip())
    return f"{BASE_URL}?q={encoded_query}&currentPage={page_number}"


def extract_nextjs_search_result(html: str) -> dict | None:
    """
    Técnica moderna (SSR Hydration Extraction):
    Extrai o JSON estruturado ('searchResult') diretamente do payload React Server Components
    (self.__next_f.push) do Next.js da Kwara, sem precisar renderizar o DOM no navegador.
    """
    next_f_chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, re.S)
    decoder = json.JSONDecoder()

    for raw in next_f_chunks:
        if "searchResult" not in raw:
            continue
        try:
            decoded = json.loads('"' + raw + '"')
        except Exception:
            continue

        marker = '"searchResult":{'
        pos = decoded.find(marker)
        if pos != -1:
            start = pos + len('"searchResult":')
            try:
                obj, _ = decoder.raw_decode(decoded[start:])
                if isinstance(obj, dict) and "items" in obj:
                    return obj
            except Exception:
                continue
    return None


def parse_ssr_items(items: list[dict], include_metadata: bool = False) -> list[dict]:
    """Converte a lista de itens brutos do JSON da Kwara para dicionários prontos para o Excel ou Web UI."""
    parsed = []
    for item in items:
        cents = item.get("cachedPriceAmountCents")
        reais = round(cents / 100.0, 2) if isinstance(cents, (int, float)) else None
        slug = item.get("slug")
        link = f"{SITE_URL}/bens/{slug}" if slug else ""

        row = {
            "Nome do produto": (item.get("title") or "Sem título").strip(),
            "Preço atual": format_brl(cents),
            "Valor numérico (R$)": reais,
            "Lances": item.get("cachedBidsCount", 0),
            "Visitas": item.get("views", 0),
            "Estado (UF)": item.get("propertyState") or item.get("pickUpState") or "",
            "Encerramento": format_iso_date(item.get("currentEndAt") or item.get("scheduledEndAt")),
            "Link do lote": link,
        }

        if include_metadata:
            images = item.get("images") or []
            img_url = ""
            if images and isinstance(images[0], dict):
                img_url = images[0].get("catalogUrl") or images[0].get("thumbnailUrl") or images[0].get("url") or ""
            row["imagem"] = img_url
            row["id"] = item.get("id") or ""

        parsed.append(row)
    return parsed


def scrape_fast_ssr(search_query: str, include_metadata: bool = False) -> tuple[list[dict] | None, int]:
    """
    Coleta todas as páginas via requisição HTTP direta lendo o payload SSR do Next.js.
    Retorna (lista_de_produtos, total_de_paginas) ou (None, 0) caso precise do fallback em Playwright.
    """
    all_products: list[dict] = []
    current_page = 1
    total_pages = 0

    while True:
        url = build_search_url(search_query, current_page)
        print(
            f"-> [Modo Rápido SSR] Acessando Página {current_page}"
            + (f" de {total_pages}..." if total_pages else "...")
        )

        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"[Aviso] Falha na requisição HTTP da página {current_page}: {e}")
            return (None, 0) if current_page == 1 else (all_products, total_pages)

        search_result = extract_nextjs_search_result(html)
        if search_result is None:
            if current_page == 1:
                return None, 0
            break

        if current_page == 1:
            total_pages = search_result.get("totalPages", 0) or 0
            total_items = search_result.get("totalItems", 0) or 0
            print(f"   Encontrados {total_items} itens distribuídos em {total_pages} página(s).")
            if total_items == 0 or total_pages == 0:
                break

        raw_items = search_result.get("items") or []
        if not raw_items:
            break

        page_items = parse_ssr_items(raw_items, include_metadata=include_metadata)
        all_products.extend(page_items)
        print(f"-> Página {current_page} coletada com sucesso ({len(page_items)} itens extraídos).")

        if current_page >= total_pages:
            break

        current_page += 1

    return all_products, total_pages


async def fetch_page_data_playwright(page: Page, url: str, page_number: int) -> list[dict] | None:
    """
    Fallback usando Playwright: extrai dados renderizando a página no navegador Chromium.
    """
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except PlaywrightTimeoutError:
        print(f"[Aviso] Timeout de carregamento na página {page_number}. Tentando continuar assim mesmo.")

    try:
        await page.wait_for_selector('a[title="Clique para abrir detalhes"] p.font-semibold', timeout=8000)
    except PlaywrightTimeoutError:
        return None

    items = await page.evaluate('''() => {
        const titleLinks = document.querySelectorAll('a[title="Clique para abrir detalhes"]');
        let data = [];

        for (const link of titleLinks) {
            const titleEl = link.querySelector('p.font-semibold');
            if (!titleEl) continue;

            const card = link.closest('div.flex-col') || link.parentElement;
            const priceEl = card ? card.querySelector('.text-black.text-sm.font-bold') : null;
            const priceText = priceEl ? priceEl.innerText.trim() : "Preço indisponível";

            const rawHref = link.getAttribute('href') || '';
            const cleanUrl = rawHref ? new URL(rawHref, window.location.origin).href.split('?')[0] : '';

            data.push({
                "Nome do produto": titleEl.innerText.trim(),
                "Preço atual": priceText,
                "Link do lote": cleanUrl
            });
        }
        return data;
    }''')

    return items


async def scrape_with_playwright(search_query: str) -> tuple[list[dict], int]:
    """Executa a paginação completa utilizando o navegador headless Playwright."""
    all_products: list[dict] = []
    current_page = 1
    pages_scraped = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=USER_AGENT)
        page = await context.new_page()

        while True:
            url = build_search_url(search_query, current_page)
            print(f"-> [Playwright] Acessando Página {current_page}...")

            items_data = await fetch_page_data_playwright(page, url, current_page)
            if not items_data:
                print(f"-> Nenhum item encontrado na Página {current_page}. Encerrando paginação.\n")
                break

            print(f"-> Página {current_page} coletada com sucesso ({len(items_data)} itens extraídos).")
            all_products.extend(items_data)
            pages_scraped = current_page
            current_page += 1
            await asyncio.sleep(1.0)

        await browser.close()

    return all_products, pages_scraped


def scrape_kwara(
    search_query: str,
    force_playwright: bool = False,
    include_metadata: bool = False,
) -> tuple[list[dict], int]:
    """Função unificada que executa o scraper (SSR rápido ou Playwright) e retorna (itens, total_paginas)."""
    dados = None
    total_pages = 0

    if not force_playwright:
        dados, total_pages = scrape_fast_ssr(search_query, include_metadata=include_metadata)
        if dados is None:
            print("[Aviso] Estrutura SSR não encontrada. Alternando automaticamente para o modo Playwright...\n")

    if dados is None:
        dados, total_pages = asyncio.run(scrape_with_playwright(search_query))

    return dados or [], total_pages


def export_to_excel(dados: list[dict], nome_arquivo: str) -> None:
    """Exporta os dados coletados para um arquivo Excel (.xlsx) ajustando a largura das colunas."""
    clean_rows = []
    for row in dados:
        clean_rows.append({col: row.get(col, "") for col in EXCEL_COLUMNS if col in row or col in EXCEL_COLUMNS[:2]})

    df = pd.DataFrame(clean_rows)
    with pd.ExcelWriter(nome_arquivo, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leilao_Kwara")
        worksheet = writer.sheets["Leilao_Kwara"]
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 65)


def run_scraper_and_export(search_query: str, output_file: str | None = None, force_playwright: bool = False) -> str | None:
    search_query = search_query.strip()
    if not search_query:
        print("Erro: O termo de busca não pode ser vazio.")
        return None

    print(f"\nIniciando busca no leilão Kwara para: '{search_query}'\n")

    try:
        dados, _ = scrape_kwara(search_query, force_playwright=force_playwright, include_metadata=False)
    except Exception as e:
        print(f"Erro crítico durante a execução do scraper: {e}")
        return None

    if not dados:
        print(f"\nNenhum produto encontrado para o termo '{search_query}'.")
        return None

    nome_arquivo = output_file or f"{slugify_filename(search_query)}_leilao.xlsx"
    if not nome_arquivo.lower().endswith(".xlsx"):
        nome_arquivo += ".xlsx"

    print(f"\nExtração finalizada com {len(dados)} produto(s) no total.")
    print(f"Salvando resultados na planilha '{nome_arquivo}'...")
    try:
        export_to_excel(dados, nome_arquivo)
        print(f"Sucesso! Arquivo salvo em '{nome_arquivo}'.")
        return nome_arquivo
    except PermissionError:
        print(f"Erro: Feche o arquivo '{nome_arquivo}' no Excel antes de salvar novamente.")
    except Exception as e:
        print(f"Falha ao gerar o Excel: {e}")
    return None


def parse_args():
    parser = argparse.ArgumentParser(
        description="Web Scraper de Leilões da Kwara - Modo Terminal e Modo Interface Web."
    )
    parser.add_argument(
        "query",
        nargs="*",
        help="Nome do item que deseja pesquisar (ex: geladeira, notebook, carro, ar condicionado).",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Nome do arquivo Excel de saída (opcional). Padrão: <item>_leilao.xlsx",
    )
    parser.add_argument(
        "--playwright",
        action="store_true",
        help="Força o uso do navegador Chromium (Playwright) em vez da extração rápida SSR.",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Inicia a interface web moderna no navegador (estilo Google Search).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Porta do servidor web local quando executado com --web (padrão: 8000).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.web:
        from web_app import start_server
        start_server(port=args.port, open_browser=True)
        raise SystemExit(0)

    termo = " ".join(args.query).strip()
    if not termo:
        try:
            termo = input(
                "Digite o item para pesquisar no terminal (ou digite 'web' para abrir a página HTML): "
            ).strip()
        except EOFError:
            termo = ""

    if termo.lower() == "web":
        from web_app import start_server
        start_server(port=args.port, open_browser=True)
    elif termo:
        run_scraper_and_export(termo, output_file=args.output, force_playwright=args.playwright)
    else:
        print("Nenhum item informado. Encerrando.")
