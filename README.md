# Web Scraping de Geladeiras em Leilão (Kwara)

Este projeto consiste em um script de automação e raspagem de dados (web scraping) desenvolvido em Python utilizando **Playwright** para extrair informações sobre geladeiras em leilão no site [Kwara](https://www.kwara.com.br/).

## 📌 Objetivo
Extrair automaticamente uma lista de produtos (geladeiras) contendo:
- Nome do item (título do lote)
- Valor atual do lance (preço atual exibido)

E exportar os dados estruturados para um arquivo Excel (`.xlsx`).

---

## 🛠️ Tecnologias Utilizadas
- **Python 3**
- **Playwright** (automação do navegador para lidar com páginas dinâmicas/SPA)
- **Pandas** & **Openpyxl** (manipulação de dados e exportação para Excel)

---

## 🔍 Resumo do Processo de Desenvolvimento

### 1. Análise da Página e Identificação dos Seletores
Como o site da Kwara é uma **Single Page Application (SPA)** renderizada dinamicamente com JavaScript, foi necessário usar automação de navegador (Playwright) em vez de uma requisição estática com BeautifulSoup.

Durante a análise do DOM, os seguintes seletores CSS foram mapeados:
- **Nome do Produto**: Inicialmente tentou-se buscar apenas `a[title="Clique para abrir detalhes"] p`, porém, alguns lotes retornavam o número do lote (ex: "Lote 012") ao invés do nome da geladeira. O seletor foi corrigido e refinado para:
  `a[title="Clique para abrir detalhes"] p.font-semibold`
  Isso garante que apenas o nome do produto seja extraído, pois ele possui a classe CSS `font-semibold`.
- **Preço Atual**: `.text-black.text-sm.font-bold`
- **Paginação**: Controlada diretamente incrementando o parâmetro `currentPage` na URL da busca, o que se mostrou mais robusto e rápido do que clicar nos botões de paginação.

### 2. Fluxo da Automação
1. O script inicia o navegador Chromium (headless) e define um `User-Agent` para evitar bloqueios.
2. Faz a navegação pela URL incrementando a página (`currentPage=1`, `currentPage=2`, etc.).
3. Aguarda o carregamento dinâmico dos elementos na página usando `wait_for_selector`.
4. Executa um script JS no contexto da página para extrair os nomes e lances dos lotes.
5. Se a página não retornar nenhum item (fim do leilão ou sem mais resultados), o loop de paginação é interrompido.
6. Os dados são salvos em uma lista de dicionários.
7. O Pandas lê a lista de dados e gera o arquivo `geladeiras_leilao.xlsx`.

---

## 🚀 Como Executar o Projeto

### Prerrequisitos
Instale as dependências necessárias:

```bash
pip install pandas openpyxl playwright
playwright install chromium
```

### Executando o Scraper
Execute o arquivo principal:

```bash
python kwara_scraper.py
```

Após a execução, o arquivo `geladeiras_leilao.xlsx` será criado no diretório raiz contendo todos os dados extraídos.
