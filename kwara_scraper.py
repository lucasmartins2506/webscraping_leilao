import asyncio
import pandas as pd
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError

async def fetch_page_data(page: Page, url: str, page_number: int):
    """
    Função dedicada para extrair dados de uma única página.
    Retorna uma lista de dicionários com 'Nome do produto' e 'Preço atual', 
    ou None caso não existam mais itens na página (fim do leilão).
    """
    try:
        # Acessa a URL atualizada e aguarda que a rede fique ociosa 
        # Isso é fundamental para um SPA carregar seus dados da API.
        await page.goto(url, wait_until="networkidle", timeout=30000)
    except PlaywrightTimeoutError:
        print(f"[Aviso] Timeout de rede na página {page_number}. Tentando continuar assim mesmo.")
        
    try:
        # Wait explícito na renderização do elemento principal dos lotes (título do lote).
        await page.wait_for_selector('a[title="Clique para abrir detalhes"] p', timeout=10000)
    except PlaywrightTimeoutError:
        # Se os itens não aparecerem, consideramos o fim da lista.
        return None
        
    # Extrair os dados injetando JS na página para obter o texto dos elementos diretamente.
    items = await page.evaluate('''() => {
        // Agora busca especificamente o <p> que possui a classe font-semibold (Nome real)
        const titleSelector = 'a[title="Clique para abrir detalhes"] p.font-semibold';
        const priceSelector = '.text-black.text-sm.font-bold';
        
        const titles = document.querySelectorAll(titleSelector);
        const prices = document.querySelectorAll(priceSelector);
        
        let data = [];
        for(let i = 0; i < titles.length; i++) {
            let titleText = titles[i].innerText.trim();
            // Previne falha caso algum card exista mas não possua a classe do preço
            let priceText = prices[i] ? prices[i].innerText.trim() : "Preço indisponível";
            
            data.push({
                "Nome do produto": titleText,
                "Preço atual": priceText
            });
        }
        return data;
    }''')
    
    return items

async def main_scraper():
    base_url = "https://www.kwara.com.br/busca"
    search_query = "geladeira"
    category_id = "1335572032305235599"
    
    all_products = []
    current_page = 1
    
    print("Iniciando scraper do leilão Kwara (Geladeiras)...\n")
    
    async with async_playwright() as p:
        # Headless=True oculta o Chromium durante a coleta. Para depurar visualmente passe False.
        browser = await p.chromium.launch(headless=True)
        
        # User-agent ajuda a evitar alguns bloqueios simples
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        while True:
            # Controle e detecção da paginação através da URL (mais seguro do que clicar em botão para SPAs)
            url = f"{base_url}?q={search_query}&currentPage={current_page}&assetCategoryIds%5B%5D={category_id}"
            print(f"-> Acessando Página {current_page}...")
            
            # Função dedicada é chamada assincronamente
            items_data = await fetch_page_data(page, url, current_page)
            
            # Condição de parada: a página retornou vazio (não encontrou lote).
            if not items_data:
                print(f"-> Nenhum item novo encontrado na Página {current_page}. Encerrando paginação.\n")
                break
                
            print(f"-> Página {current_page} coletada com sucesso. ({len(items_data)} itens extraídos)")
            all_products.extend(items_data)
            
            # Incrementa controle da página
            current_page += 1
            
            # Evita rate limiting ou suspensões. Aguarda tempo fixo entre requisições.
            await asyncio.sleep(2)

        await browser.close()
        
    return all_products

def run_scraper_and_export():
    try:
        dados = asyncio.run(main_scraper())
    except Exception as e:
        print(f"Erro crítico durante a execução do scraper playwight: {e}")
        return

    # Exportação para Excel
    if not dados:
        print("Aviso: A automação não encontrou nenhum dado nas páginas visitadas.")
        return
        
    nome_arquivo = "geladeiras_leilao.xlsx"
    print(f"\nExtração finalizada com {len(dados)} produtos no total.")
    print(f"Salvando resultados no arquivo '{nome_arquivo}'...")
    try:
        df = pd.DataFrame(dados)
        # engine=openpyxl é necessário para formatar arquivos .xlsx no pandas
        df.to_excel(nome_arquivo, index=False, engine='openpyxl')
        print(f"Sucesso: Arquivo salvo em '{nome_arquivo}' com sucesso!")
    except Exception as e:
        print(f"Falha ao gerar o Excel. Certifique-se de que instalou o openpyxl e pandas. Erro: {e}")

if __name__ == "__main__":
    run_scraper_and_export()
