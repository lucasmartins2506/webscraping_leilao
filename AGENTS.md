# AGENTS.md — Diretrizes de UI/UX Anti-"AI Slop" (Design System & Guardrails)

> **Propósito deste arquivo**: Este documento consolida as regras práticas dos principais repositórios de engenharia de design do GitHub ([`pbakaus/impeccable`](https://github.com/pbakaus/impeccable), [`funboy322/avoid-ai-design`](https://github.com/funboy322/avoid-ai-design), [`LeoStehlik/no-slop-ui`](https://github.com/LeoStehlik/no-slop-ui), [`shadcn-ui/ui`](https://github.com/shadcn-ui/ui) e [`vercel/geist-font`](https://github.com/vercel/geist-font)).
> Sempre que um Agente de IA criar ou modificar qualquer interface (HTML, CSS, Tailwind, React, Next.js, Vue, etc.), **todas as regras abaixo são obrigatórias**.

---

## 1. Lista Negra Absoluta (O que NUNCA fazer — Anti-Patterns de IA)

Baseado na auditoria de anti-patterns do `pbakaus/impeccable` e `funboy322/avoid-ai-design`:

1. **PROIBIDO Gradientes "IA" (Roxo / Índigo / Rosa / Neon)**:
   - Nunca use `linear-gradient(135deg, #667eea, #764ba2)`, textos com `background-clip: text` colorido ou brilhos neon (`box-shadow: 0 0 30px rgba(139, 92, 246, ...)`).
2. **PROIBIDO "Cards dentro de Cards" (Nested Card Soup)**:
   - Nunca coloque um card com borda e sombra dentro de outro card com borda e sombra. Agrupe informações usando divisórias finas (`1px solid`), espaçamento ou mudança sutil de cor de fundo.
3. **PROIBIDO Sombras Pesadas e Glassmorphism Genérico**:
   - Não use `box-shadow: 0 20px 50px rgba(0,0,0,0.2)` nem `backdrop-filter: blur(20px)` flutuando sobre bolhas coloridas no fundo.
4. **PROIBIDO Cantos Exageradamente Arredondados**:
   - Evite `border-radius: 24px` ou `rounded-3xl` em containers de conteúdo. Use raios técnicos e precisos: `6px` para botões/inputs e `8px` para containers/tabelas.
5. **PROIBIDO Emojis como Ícones de Interface**:
   - Nunca use emojis (`🚀`, `✨`, `📊`, `🔥`) no lugar de ícones técnicos ou títulos de seções. Use ícones SVG limpos (`stroke-width: 1.75` ou `2`, estilo Lucide/Feather) ou tipografia pura.
6. **PROIBIDO Animações Lentas ou Elásticas**:
   - Nunca use transições maiores que `150ms` ou efeitos `bounce`/`spring` em ferramentas de produtividade. Micro-interações devem durar entre `75ms` e `120ms` (`ease` ou `ease-out`).
7. **PROIBIDO Textos Genéricos de Marketing**:
   - Nunca invente subtítulos vazios como *"Potencialize seu fluxo de trabalho com nossa solução revolucionária"*. Escreva microcopy direto, técnico e funcional.

---

## 2. Arquitetura Visual Obrigatória (Padrão Vercel Geist / Linear / shadcn)

### 2.1. Tipografia e Alinhamento Numérico (`vercel/geist-font`)
- **Fonte Principal (UI & Texto)**: `'Geist'`, `'Inter'` (com `cv02`, `cv03`, `cv04`) ou `'Plus Jakarta Sans'`.
- **Fonte Monoespaçada (Dados, Preços, IDs, Datas, Atalhos)**: `'Geist Mono'` ou `'JetBrains Mono'`.
- **Regra Obrigatória para Números**: Todo preço, métrica, contador, porcentagem, data ou coluna de tabela **DEVE** ter:
  ```css
  font-variant-numeric: tabular-nums;
  ```
- **Hierarquia Tipográfica**:
  - Títulos principais: `font-weight: 600`, `letter-spacing: -0.03em`.
  - Labels de métricas/tabelas: `font-size: 11px`, `text-transform: uppercase`, `letter-spacing: 0.05em`, cor secundária/muted.
  - Corpo de dados: `13px` a `14px` para alta densidade de informação.

### 2.2. Superfícies e Bordas Hairline (`1px solid`)
Em vez de sombras para separar elementos, construa a estrutura com **bordas arquiteturais de 1px**:
- **Hierarquia de 3 camadas**:
  1. `Canvas` (Fundo da página)
  2. `Surface` (Cards, tabelas, barra superior)
  3. `Subtle` (Cabeçalho de tabela, badges secundários, estados de hover)
- **Regra da Cor de Destaque (Accent)**:
  - O botão primário deve ser de **alto contraste monocromático** (Preto `#18181b` com texto branco no tema claro; Branco `#fafafa` com texto preto no tema escuro) ou **uma única cor sólida de marca** (sem degradê).
  - Cores semânticas (Verde Esmeralda para sucesso/ativo, Âmbar para alerta, Vermelho para erro) devem ser usadas apenas em *badges* de status ou indicadores pontuais.

---

## 3. Tokens CSS Prontos para Copiar em Qualquer Projeto

Sempre inicialize projetos web com esta base de variáveis CSS (suporte nativo a Light Mode e Dark Mode):

```css
:root,
[data-theme="light"] {
  --bg-canvas: #fafafa;
  --bg-surface: #ffffff;
  --bg-subtle: #f4f4f5;
  --bg-hover: #f4f4f5;
  --text-primary: #09090b;
  --text-secondary: #52525b;
  --text-muted: #71717a;
  --border-hairline: #e4e4e7;
  --border-strong: #d4d4d8;
  --accent-primary: #18181b;
  --accent-primary-fg: #fafafa;
  --status-success: #059669;
  --status-success-bg: #ecfdf5;
  --status-success-border: #a7f3d0;
  --focus-ring: #18181b;
  --radius-sm: 6px;
  --radius-md: 8px;
}

[data-theme="dark"] {
  --bg-canvas: #09090b;
  --bg-surface: #121215;
  --bg-subtle: #18181c;
  --bg-hover: #1f1f24;
  --text-primary: #fafafa;
  --text-secondary: #a1a1aa;
  --text-muted: #71717a;
  --border-hairline: #27272a;
  --border-strong: #3f3f46;
  --accent-primary: #fafafa;
  --accent-primary-fg: #09090b;
  --status-success: #10b981;
  --status-success-bg: rgba(16, 185, 129, 0.1);
  --status-success-border: rgba(16, 185, 129, 0.3);
  --focus-ring: #d4d4d8;
}
```

---

## 4. Regras de Componentes e UX (`LeoStehlik/no-slop-ui`)

1. **Keyboard-First (Foco em Produtividade)**:
   - Adicione atalhos úteis (ex: `/` ou `Ctrl+K` para focar na busca) e exiba um indicador discreto `<kbd>/</kbd>` em fonte monoespaçada.
   - Estados de foco (`:focus-visible` / `:focus-within`) devem usar um anel nítido de `1px` (`box-shadow: 0 0 0 1px var(--focus-ring)`), nunca um borrão azul padrão do navegador.
2. **Densidade de Dados e KPIs**:
   - Métricas de topo (KPIs) não devem ficar soltas em cards gigantes separados; agrupe-as em uma **faixa única dividida por linhas verticais de `1px`** (`grid` com `border-right: 1px solid var(--border-hairline)`).
3. **Estados de Carregamento, Vazio e Erro**:
   - Toda busca ou tabela deve tratar explicitamente os 3 estados: *Loading* (spinner discreto de `2px`), *Empty State* (mensagem clara sem ilustrações infantis) e *Error State*.
4. **Responsividade Real**:
   - Em telas menores (`< 768px`), grids de 4 colunas viram 2x2 e barras de ferramentas quebram linha de forma limpa (`flex-wrap: wrap`).

---

## 5. Checklist de Auditoria Antes de Entregar o Código (`/audit`)

Antes de finalizar qualquer tela, o agente deve verificar:
- [ ] Existe algum gradiente roxo/azul/rosa no CSS? *(Se sim, remova imediatamente)*.
- [ ] Todos os preços, datas, IDs e contadores estão com `tabular-nums` e fonte mono?
- [ ] Há algum card dentro de outro card? *(Se sim, achate a hierarquia usando divisórias de `1px`)*.
- [ ] Os botões e inputs têm entre `34px` e `40px` de altura com bordas de `6px`?
- [ ] O contraste de leitura funciona perfeitamente tanto no tema claro quanto no escuro?
