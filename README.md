# Web Scraping de Leilões (Kwara) — Terminal & Interface Web

Este projeto consiste em uma ferramenta de raspagem de dados (*web scraping*) em Python para pesquisar **qualquer item** em leilão no site [Kwara](https://www.kwara.com.br/), percorrer todas as páginas de resultados automaticamente e exportar os dados estruturados para uma planilha Excel (`.xlsx`).

Você pode utilizá-lo de **duas formas**:
1. **Pelo Terminal (CLI)**: digitando o nome do produto ou passando via argumento de linha de comando.
2. **Pela Interface Web (`kwara.search`)**: uma página HTML estilo Google Search com design minimalista moderno (inspirado no sistema **Vercel Geist / Linear / shadcn**, livre de clichês visuais de IA), exibindo fotos reais dos lotes, métricas de preços, filtros por estado (UF), ordenação, visualização em Grade ou Tabela e download imediato do Excel.

---

## 📌 Funcionalidades
- **Busca livre por qualquer produto**: Pesquise `"geladeira"`, `"notebook"`, `"ar condicionado"`, `"iphone"`, `"caminhão"`, etc.
- **Extração Híbrida Moderna (Next.js SSR JSON + Playwright)**:
  - **Modo Rápido SSR (Padrão)**: Extrai o JSON estruturado (`searchResult`) diretamente do payload *React Server Components* (`self.__next_f`) embutido no HTML da Kwara. Extrai múltiplas páginas em **menos de 2 segundos**.
  - **Modo Playwright (Fallback)**: Caso a estrutura SSR mude (ou usando a flag `--playwright`), o script aciona automaticamente o navegador headless Chromium.
- **Exportação Completa para Excel (`.xlsx`)**:
  - `Nome do produto`, `Preço atual`, `Valor numérico (R$)`, `Lances`, `Visitas`, `Estado (UF)`, `Encerramento` e `Link do lote`.

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
```bash
pip install pandas openpyxl playwright
playwright install chromium
```

### Opção 1: Interface Web Moderna (Estilo Google Search)
Inicie o servidor web local (ele abrirá automaticamente no navegador em `http://localhost:8000`):

```bash
python kwara_scraper.py --web
```
*(Ou execute diretamente `python web_app.py`, ou digite `web` quando iniciar `python kwara_scraper.py`).*

Na página web:
- Digite qualquer produto na barra central e pressione **Enter** (atalho `/` foca na busca).
- A barra desliza para o topo estilo Google, varre todas as páginas da Kwara, **já salva o arquivo `<item>_leilao.xlsx` na pasta do projeto** e libera o botão **Baixar Excel (.xlsx)** direto pelo navegador.
- Filtre por **Estado (UF)**, ordene por **Menor/Maior Preço** ou **Mais Lances**, e alterne entre **Grade com Fotos** e **Tabela Densa**.

### Opção 2: Uso pelo Terminal (CLI)
```bash
# Modo interativo (pergunta o item no terminal)
python kwara_scraper.py

# Passando o item direto no comando
python kwara_scraper.py geladeira
python kwara_scraper.py "ar condicionado"
python kwara_scraper.py notebook -o meus_notebooks.xlsx
```
