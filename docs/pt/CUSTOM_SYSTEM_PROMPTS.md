# Personalização de Prompts de Sistema

[English](../en/CUSTOM_SYSTEM_PROMPTS.md) | [简体中文](../zh-CN/CUSTOM_SYSTEM_PROMPTS.md) | [繁體中文](../zh-TW/CUSTOM_SYSTEM_PROMPTS.md) | [日本語](../ja/CUSTOM_SYSTEM_PROMPTS.md) | [한국어](../ko/CUSTOM_SYSTEM_PROMPTS.md) | [हिन्दी](../hi/CUSTOM_SYSTEM_PROMPTS.md) | [Tiếng Việt](../vi/CUSTOM_SYSTEM_PROMPTS.md) | [Français](../fr/CUSTOM_SYSTEM_PROMPTS.md) | [Русский](../ru/CUSTOM_SYSTEM_PROMPTS.md) | [Español](../es/CUSTOM_SYSTEM_PROMPTS.md) | **Português** | [Norsk](../no/CUSTOM_SYSTEM_PROMPTS.md) | [Svenska](../sv/CUSTOM_SYSTEM_PROMPTS.md) | [Deutsch](../de/CUSTOM_SYSTEM_PROMPTS.md) | [Nederlands](../nl/CUSTOM_SYSTEM_PROMPTS.md) | [Italiano](../it/CUSTOM_SYSTEM_PROMPTS.md)

Este guia explica como personalizar o prompt de sistema que o GAC usa para gerar mensagens de commit, permitindo que você defina seu próprio estilo e convenções de mensagens de commit.

## Sumário

- [Personalização de Prompts de Sistema](#personalização-de-prompts-de-sistema)
  - [Sumário](#sumário)
  - [O Que São Prompts de Sistema?](#o-que-são-prompts-de-sistema)
  - [Por Que Usar Prompts de Sistema Personalizados?](#por-que-usar-prompts-de-sistema-personalizados)
  - [Início Rápido](#início-rápido)
  - [Escrevendo Seu Prompt de Sistema Personalizado](#escrevendo-seu-prompt-de-sistema-personalizado)
  - [Exemplos](#exemplos)
    - [Estilo de Commit Baseado em Emoji](#estilo-de-commit-baseado-em-emoji)
    - [Convenções Específicas de Equipe](#convenções-específicas-de-equipe)
    - [Estilo Técnico Detalhado](#estilo-técnico-detalhado)
  - [Melhores Práticas](#melhores-práticas)
    - [Faça:](#faça)
    - [Não Faça:](#não-faça)
    - [Dicas:](#dicas)
  - [Solução de Problemas](#solução-de-problemas)
    - [Mensagens ainda têm prefixo "chore:"](#mensagens-ainda-têm-prefixo-chore) -[IA ignorando minhas instruções](#ia-ignorando-minhas-instruções)
    - [Mensagens estão muito longas/curtas](#mensagens-estão-muito-longascurtas)
    - [Prompt personalizado não sendo usado](#prompt-personalizado-não-sendo-usado)
    - [Quero voltar ao padrão](#quero-voltar-ao-padrão)
  - [Documentação Relacionada](#documentação-relacionada)
  - [Precisa de Ajuda?](#precisa-de-ajuda)

## O Que São Prompts de Sistema?

O GAC usa dois prompts ao gerar mensagens de commit:

1. **Prompt de Sistema** (personalizável): Instruções que definem o papel, estilo e convenções para mensagens de commit
2. **Prompt de Usuário** (automático): Os dados do diff do git mostrando o que mudou

O prompt de sistema diz à IA _como_ escrever mensagens de commit, enquanto o prompt de usuário fornece o _o quê_ (as mudanças reais no código).

## Por Que Usar Prompts de Sistema Personalizados?

Você pode querer um prompt de sistema personalizado se:

- Sua equipe usa um estilo de mensagem de commit diferente dos commits convencionais
- Você prefere emojis, prefixos ou outros formatos personalizados
- Você quer mais ou menos detalhes nas mensagens de commit
- Você tem diretrizes ou modelos específicos da empresa
- Você quer combinar com a voz e tom da sua equipe
- Você quer mensagens de commit em um idioma diferente (veja Configuração de Idioma abaixo)

## Início Rápido

1. **Crie seu arquivo de prompt de sistema personalizado:**

   ```bash
   # Copie o exemplo como ponto de partida
   cp custom_system_prompt.example.txt ~/.config/gac/my_system_prompt.txt

   # Ou crie o seu do zero
   vim ~/.config/gac/my_system_prompt.txt
   ```

2. **Adicione ao seu arquivo `.gac.env`:**

   ```bash
   # Em ~/.gac.env ou .gac.env de nível de projeto
   GAC_SYSTEM_PROMPT_PATH=/path/to/your/custom_system_prompt.txt
   ```

3. **Teste:**

   ```bash
   uvx gac --dry-run
   ```

É isso! O GAC agora usará suas instruções personalizadas em vez do padrão.

## Escrevendo Seu Prompt de Sistema Personalizado

Seu prompt de sistema personalizado pode ser texto simples—nenhum formato especial ou tags XML necessárias. Apenas escreva instruções claras sobre como a IA deve gerar mensagens de commit.

**Coisas-chave para incluir:**

1. **Definição de papel** - O que a IA deve atuar como
2. **Requisitos de formato** - Estrutura, comprimento, estilo
3. **Exemplos** - Mostre como mensagens de commit boas parecem
4. **Restrições** - O que evitar ou requisitos para atender

**Exemplo de estrutura:**

```text
You are a commit message writer for [your project/team].

When analyzing code changes, create a commit message that:

1. [First requirement]
2. [Second requirement]
3. [Third requirement]

Example format:
[Show an example commit message]

Your entire response will be used directly as the commit message.
```

## Exemplos

### Estilo de Commit Baseado em Emoji

Veja [`custom_system_prompt.example.txt`](../../examples/custom_system_prompt.example.txt) para um exemplo completo baseado em emoji.

**Trecho rápido:**

```text
You are a commit message writer that uses emojis and a friendly tone.

Start each message with an emoji:
- 🎉 for new features
- 🐛 for bug fixes
- 📝 for documentation
- ♻️ for refactoring

Keep the first line under 72 characters and explain WHY the change matters.
```

### Convenções Específicas de Equipe

```text
You are writing commit messages for an enterprise banking application.

Requirements:
1. Start with a JIRA ticket number in brackets (e.g., [BANK-1234])
2. Use formal, professional tone
3. Include security implications if relevant
4. Reference any compliance requirements (PCI-DSS, SOC2, etc.)
5. Keep messages concise but complete

Format:
[TICKET-123] Brief summary of change

Detailed explanation of what changed and why. Include:
- Business justification
- Technical approach
- Risk assessment (if applicable)

Example:
[BANK-1234] Implement rate limiting for login endpoints

Added Redis-based rate limiting to prevent brute force attacks.
Limits login attempts to 5 per IP per 15 minutes.
Complies with SOC2 security requirements for access control.
```

### Estilo Técnico Detalhado

```text
You are a technical commit message writer who creates comprehensive documentation.

For each commit, provide:

1. A clear, descriptive title (under 72 characters)
2. A blank line
3. WHAT: What was changed (2-3 sentences)
4. WHY: Why the change was necessary (2-3 sentences)
5. HOW: Technical approach or key implementation details
6. IMPACT: Files/components affected and potential side effects

Use technical precision. Reference specific functions, classes, and modules.
Use present tense and active voice.

Example:
Refactor authentication middleware to use dependency injection

WHAT: Replaced global auth state with injectable AuthService. Updated
all route handlers to accept AuthService through constructor injection.

WHY: Global state made testing difficult and created hidden dependencies.
Dependency injection improves testability and makes dependencies explicit.

HOW: Created AuthService interface, implemented JWTAuthService and
MockAuthService. Modified route handler constructors to require AuthService.
Updated dependency injection container configuration.

IMPACT: Affects all authenticated routes. No behavior changes for users.
Tests now run 3x faster with MockAuthService. Migration required for
routes/auth.ts, routes/api.ts, and routes/admin.ts.
```

## Melhores Práticas

### Faça

- ✅ **Seja específico** - Instruções claras produzem melhores resultados
- ✅ **Inclua exemplos** - Mostre à IA o que é bom
- ✅ **Teste iterativamente** - Tente seu prompt, refine com base nos resultados
- ✅ **Mantenha o foco** - Muitas regras podem confundir a IA
- ✅ **Use terminologia consistente** - Mantenha os mesmos termos throughout
- ✅ **Termine com um lembrete** - Reforce que a resposta será usada como está

### Não Faça

- ❌ **Use tags XML** - Texto simples funciona melhor (a menos que você queira especificamente essa estrutura)
- ❌ **Torne muito longo** - Procure 200-500 palavras de instruções
- ❌ **Contradiga a si mesmo** - Seja consistente em seus requisitos
- ❌ **Esqueça o final** - Sempre lembre: "Your entire response will be used directly as the commit message"

### Dicas

- **Comece com o exemplo** - Copie `../../examples/custom_system_prompt.example.txt` e modifique-o
- **Teste com `--dry-run`** - Veja o resultado sem fazer um commit
- **Use `--show-prompt`** - Veja o que está sendo enviado para a IA
- **Itere com base nos resultados** - Se as mensagens não estiverem corretas, ajuste suas instruções
- **Controle de versão do seu prompt** - Mantenha seu prompt personalizado no repositório da sua equipe
- **Prompts específicos de projeto** - Use `.gac.env` de nível de projeto para estilos específicos de projeto

## Solução de Problemas

### Mensagens ainda têm prefixo "chore:"

**Problema:** Suas mensagens de emoji personalizadas estão recebendo "chore:" adicionado.

**Solução:** Isso não deveria acontecer—o GAC desabilita automaticamente a aplicação de commits convencionais ao usar prompts de sistema personalizados. Se você vir isso, por favor [abra uma issue](https://github.com/cellwebb/gac/issues).

### IA ignorando minhas instruções

**Problema:** Mensagens geradas não seguem seu formato personalizado.

**Solução:**

1. Torne suas instruções mais explícitas e específicas
2. Adicione exemplos claros do formato desejado
3. Termine com: "Your entire response will be used directly as the commit message"
4. Reduza o número de requisitos—muitos podem confundir a IA
5. Tente usar um modelo diferente (alguns seguem instruções melhor que outros)

### Mensagens estão muito longas/curtas

**Problema:** Mensagens geradas não correspondem aos seus requisitos de comprimento.

**Solução:**

- Seja explícito sobre o comprimento (ex: "Keep messages under 50 characters")
- Mostre exemplos do comprimento exato que você quer
- Considere usar a flag `--one-liner` também para mensagens curtas

### Prompt personalizado não sendo usado

**Problema:** O GAC ainda usa o formato de commit padrão.

**Solução:**

1. Verifique se `GAC_SYSTEM_PROMPT_PATH` está definido corretamente:

   ```bash
   uvx gac config get GAC_SYSTEM_PROMPT_PATH
   ```

2. Verifique se o caminho do arquivo existe e é legível:

   ```bash
   cat "$GAC_SYSTEM_PROMPT_PATH"
   ```

3. Verifique os arquivos `.gac.env` nesta ordem:
   - Nível do projeto: `./.gac.env`
   - Nível do usuário: `~/.gac.env`
4. Tente um caminho absoluto em vez de caminho relativo

### Configuração de Idioma

**Nota:** Você não precisa de um prompt de sistema personalizado para mudar o idioma da mensagem de commit!

Se você só quer mudar o idioma das suas mensagens de commit (mantendo o formato de commit convencional padrão), use o seletor de idioma interativo:

```bash
uvx gac language
```

Isso apresentará um menu interativo com 25+ idiomas em seus scripts nativos (Español, Français, 日本語, etc.). Selecione seu idioma preferido, e ele definirá automaticamente `GAC_LANGUAGE` no seu arquivo `~/.gac.env`.

Alternativamente, você pode definir manualmente o idioma:

```bash
# Em ~/.gac.env ou .gac.env de nível de projeto
GAC_LANGUAGE=Spanish
```

Por padrão, prefixos de commits convencionais (feat:, fix:, etc.) permanecem em inglês para compatibilidade com ferramentas de changelog e pipelines CI/CD, enquanto todo o outro texto está no seu idioma especificado.

**Quer traduzir prefixos também?** Defina `GAC_TRANSLATE_PREFIXES=true` no seu `.gac.env` para localização completa:

```bash
GAC_LANGUAGE=Spanish
GAC_TRANSLATE_PREFIXES=true
```

Isso traduzirá tudo, incluindo prefixos (ex: `corrección:` em vez de `fix:`).

Isso é mais simples do que criar um prompt de sistema personalizado se o idioma for sua única necessidade de personalização.

### Quero voltar ao padrão

**Problema:** Quer usar temporariamente prompts padrão.

**Solução:**

```bash
# Opção 1: Remover a variável de ambiente
uvx gac config unset GAC_SYSTEM_PROMPT_PATH

# Opção 2: Comentar em .gac.env
# GAC_SYSTEM_PROMPT_PATH=/path/to/custom_prompt.txt

# Opção 3: Usar um .gac.env diferente para projetos específicos
```

---

## Documentação Relacionada

- [USAGE.md](../USAGE.md) - Flags e opções de linha de comando
- [README.md](../README.md) - Instalação e configuração básica
- [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) - Solução geral de problemas

## Precisa de Ajuda?

- Reportar problemas: [GitHub Issues](https://github.com/cellwebb/gac/issues)
- Compartilhe seus prompts personalizados: Contribuições bem-vindas!
