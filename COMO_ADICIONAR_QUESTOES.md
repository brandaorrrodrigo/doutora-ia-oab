# Como Adicionar Mais Questões OAB

## Visão Geral

O sistema possui **25 questões de alta qualidade** já importadas no banco Railway. Este guia ensina como adicionar mais questões.

---

## Método 1: Arquivo JSON (Recomendado)

### Passo 1: Criar arquivo JSON

Crie um arquivo JSON seguindo este formato:

```json
{
  "questoes": [
    {
      "disciplina": "Direito Civil",
      "topico": "Obrigações",
      "enunciado": "Texto da questão aqui...",
      "alternativas": {
        "A": "Primeira alternativa",
        "B": "Segunda alternativa",
        "C": "Terceira alternativa",
        "D": "Quarta alternativa"
      },
      "gabarito": "A",
      "explicacao": "Explicação detalhada da resposta correta...",
      "fundamentacao": "CC, art. XXX",
      "dificuldade": "medio",
      "ano_prova": 2024
    }
  ]
}
```

### Campos Obrigatórios:
- `disciplina`: Nome da disciplina
- `topico`: Tópico específico
- `enunciado`: Texto da questão
- `alternativas`: Objeto com A, B, C, D
- `gabarito`: Letra da alternativa correta
- `explicacao`: Explicação da resposta
- `fundamentacao`: Artigos de lei ou referências

### Campos Opcionais:
- `dificuldade`: "facil", "medio" ou "dificil" (padrão: "medio")
- `ano_prova`: Ano da prova (ex: 2024)
- `tags`: Array de tags (ex: ["contratos", "civil"])

### Passo 2: Importar

```bash
python importar_questoes.py seu_arquivo.json
```

---

## Método 2: Buscar de Fontes Externas

### Sites com Questões OAB (Públicas):

1. **FGV - Exames Anteriores** (oficial)
2. **QC - Questões de Concursos**
3. **Estratégia OAB**

### Como usar:

1. Baixe questões em formato texto/PDF
2. Converta para JSON no formato acima
3. Execute `python importar_questoes.py arquivo.json`

---

## Método 3: Criar Questões Programaticamente

### Script Python:

```python
questoes = []

for i in range(50):
    questao = {
        "disciplina": "Direito Penal",
        "topico": "Crimes contra o Patrimônio",
        "enunciado": f"Questão {i+1}...",
        # ... outros campos
    }
    questoes.append(questao)

# Salvar em JSON
import json
with open('novas_questoes.json', 'w') as f:
    json.dump({'questoes': questoes}, f, indent=2)
```

---

## Verificar Questões no Banco

```bash
python -c "from database.connection import get_db_session; from database.models import QuestaoBanco; from sqlalchemy import func; db = next(get_db_session()); print(f'Total: {db.query(func.count(QuestaoBanco.id)).scalar()} questões')"
```

---

## Estrutura do Banco

A tabela `questoes_banco` tem:
- **25 questões** atualmente
- Campos: disciplina, topico, enunciado, alternativas (JSONB), alternativa_correta
- Cada questão tem código único gerado automaticamente

---

## Disciplinas Disponíveis

As 25 questões cobrem:
- ✅ Direito Constitucional (6 questões)
- ✅ Direito Civil (4 questões)
- ✅ Direito Penal (4 questões)
- ✅ Direito Processual Civil (3 questões)
- ✅ Direito do Trabalho (2 questões)
- ✅ Direito Empresarial (2 questões)
- ✅ Ética Profissional (2 questões)
- ✅ Direito Tributário (1 questão)
- ✅ Direito Administrativo (1 questão)

**Recomendação:** Adicionar mais questões de Processo Penal, Tributário e Administrativo para balancear.

---

## Dicas para Criar Questões de Qualidade

### Boas Práticas:

1. **Enunciado Claro**: Seja objetivo e direto
2. **Alternativas Plausíveis**: Todas as alternativas devem ser razoáveis
3. **Fundamentação Legal**: Sempre cite os artigos de lei
4. **Explicação Didática**: Explique não só por que a correta está certa, mas por que as outras estão erradas
5. **Dificuldade Progressiva**: Misture questões fáceis, médias e difíceis

### Evite:

- ❌ Questões ambíguas
- ❌ Alternativas óbvias demais
- ❌ Pegadinhas sem valor pedagógico
- ❌ Desatualização legislativa

---

## Exemplos de Fontes para 10 mil Questões

### Opção A - FGV (Oficial):
- Baixar todos os exames anteriores da OAB
- ~200 questões por exame x 40 exames = 8.000 questões

### Opção B - Ferramentas de Scraping:
```python
# Exemplo conceitual - respeite os termos de uso
import requests
from bs4 import BeautifulSoup

# Extrair questões de sites públicos
# Converter para formato JSON
# Importar em lote
```

### Opção C - API ou Base de Dados:
- Se tiver acesso a uma API de questões OAB
- Integrar diretamente com o script de importação

---

## Script de Importação em Massa

Para importar MUITAS questões (1000+):

```bash
# Importar em lote
for arquivo in questoes_*.json; do
    python importar_questoes.py "$arquivo"
done
```

---

## Troubleshooting

### Erro: "Questão duplicada"
- O sistema detecta automaticamente duplicatas por código único
- Duplicadas são ignoradas automaticamente

### Erro: "Campo obrigatório ausente"
- Verifique se todos os campos obrigatórios estão presentes
- Use o validador: `python importar_questoes.py --validate arquivo.json`

### Erro: "Alternativa inválida"
- Gabarito deve ser A, B, C ou D
- Todas as 4 alternativas devem estar presentes

---

## Contato e Suporte

Se precisar de ajuda para adicionar questões em grande volume:
1. Verifique os logs do script de importação
2. Teste com um arquivo pequeno primeiro (5-10 questões)
3. Valide o formato JSON online: https://jsonlint.com

---

**Última atualização:** 2024-12-24
**Questões no banco:** 25
**Meta:** 10.000+ questões
