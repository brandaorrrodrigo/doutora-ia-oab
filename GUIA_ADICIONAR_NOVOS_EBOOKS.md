# 📚 Guia: Como Adicionar Questões de Novos Ebooks

## Visão Geral

Você tem **8.261 questões** no banco. Para adicionar NOVAS questões de ebooks:

---

## Opção 1: Ebooks em PDF (Recomendado)

### Passo 1: Colocar PDF na pasta

```bash
# Copie o PDF para a pasta tools/
cp seu_novo_ebook.pdf D:\JURIS_IA_CORE_V1\tools\
```

### Passo 2: Extrair questões

```bash
cd D:\JURIS_IA_CORE_V1
python scripts/extracao/extrair_oab_ultra.py tools/seu_novo_ebook.pdf
```

**Scripts disponíveis:**
- `extrair_oab_ultra.py` - Mais completo (recomendado)
- `extrair_oab_final.py` - Alternativa
- `extrair_todos_pdfs.py` - Processa todos os PDFs de uma vez

### Passo 3: Revisar arquivo gerado

```bash
# Arquivo será salvo em tools/questoes_extraidas/
# Exemplo: q_seu_novo_ebook.json
```

### Passo 4: Consolidar com as existentes

```bash
# Editar e rodar consolidar_e_importar_questoes.py
# Ou adicionar manualmente ao banco
```

---

## Opção 2: Questões Já em JSON

Se você já tem questões em formato JSON:

### Formato Necessário:

```json
{
  "questoes": [
    {
      "disciplina": "Direito Civil",
      "topico": "Obrigações",
      "enunciado": "Texto da questão...",
      "alternativas": {
        "A": "Alternativa A",
        "B": "Alternativa B",
        "C": "Alternativa C",
        "D": "Alternativa D"
      },
      "gabarito": "A",
      "explicacao": "Explicação...",
      "dificuldade": "medio",
      "ano_prova": 2024
    }
  ]
}
```

### Importar Diretamente:

```bash
# Use o script que criamos:
python importar_questoes_formato_correto.py
```

---

## Opção 3: Script Automático Completo

### Processar TODOS os ebooks novos de uma vez:

```bash
# 1. Coloque todos os PDFs em tools/
# 2. Execute:
python scripts/extracao/extrair_todos_pdfs.py

# 3. Consolide tudo:
python consolidar_e_importar_questoes.py

# 4. Importe no banco:
python importar_questoes_formato_correto.py
```

---

## Verificar Questões no Banco

Após importar, verifique:

```bash
# Via Docker:
docker-compose exec postgres psql -U juris_ia_user -d juris_ia -c "SELECT COUNT(*) FROM questoes_banco;"

# Por disciplina:
docker-compose exec postgres psql -U juris_ia_user -d juris_ia -c "SELECT disciplina, COUNT(*) FROM questoes_banco GROUP BY disciplina;"
```

---

## Fluxo Completo (Novo Ebook → Sistema)

```
1. PDF novo
   ↓
2. scripts/extracao/extrair_oab_ultra.py
   ↓
3. questoes extraídas em JSON
   ↓
4. consolidar_e_importar_questoes.py (remove duplicatas)
   ↓
5. importar_questoes_formato_correto.py (adapta formato)
   ↓
6. questoes_banco (PostgreSQL)
   ↓
7. QuestionEngineDB (API já acessa automaticamente!)
   ↓
8. Sistema funcionando ✅
```

---

## Campos Importantes

Certifique-se que as questões têm:

**Obrigatórios:**
- ✅ `disciplina`
- ✅ `topico`
- ✅ `enunciado`
- ✅ `alternativa_a`, `alternativa_b`, `alternativa_c`, `alternativa_d`
- ✅ `alternativa_correta` (A, B, C ou D)

**Opcionais (melhoram qualidade):**
- `explicacao_nivel1_tecnico`
- `dificuldade`
- `ano`
- `tags`
- `artigos_lei`

---

## Dicas

1. **PDFs de Qualidade**: Quanto melhor a qualidade do PDF, melhor a extração
2. **Revisar Sempre**: Após extração, sempre revisar o JSON gerado
3. **Testar Pequeno**: Teste com 10-20 questões antes de importar milhares
4. **Backup**: Sempre faça backup do banco antes de importações grandes

---

## Comandos Úteis

```bash
# Ver estrutura da tabela:
docker-compose exec postgres psql -U juris_ia_user -d juris_ia -c "\d questoes_banco"

# Última questão adicionada:
docker-compose exec postgres psql -U juris_ia_user -d juris_ia -c "SELECT * FROM questoes_banco ORDER BY criado_em DESC LIMIT 1;"

# Estatísticas:
docker-compose exec postgres psql -U juris_ia_user -d juris_ia -c "SELECT disciplina, COUNT(*), AVG(total_acertos::float / NULLIF(total_resolucoes, 0)) as taxa_acerto FROM questoes_banco GROUP BY disciplina;"
```

---

## Resumo Rápido

**Para adicionar 1 ebook novo:**
```bash
python scripts/extracao/extrair_oab_ultra.py novo_ebook.pdf
python importar_questoes_formato_correto.py
```

**Para adicionar vários ebooks:**
```bash
python scripts/extracao/extrair_todos_pdfs.py
python consolidar_e_importar_questoes.py
python importar_questoes_formato_correto.py
```

**Fim!** As questões já estarão disponíveis na API automaticamente! ✅

---

**Status Atual:**
- 📊 **8.261 questões** no banco
- ✅ **QuestionEngineDB** integrado
- ✅ **API** acessando automaticamente
- 🚀 **Sistema pronto** para uso!
