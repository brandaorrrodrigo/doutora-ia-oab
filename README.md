# JURIS_IA_CORE_V1

## O Maior Aprovador de OAB do Brasil

Sistema integral e definitivo de inteligência artificial jurídica para formação, aprovação na OAB e atuação profissional.

---

## VISÃO GERAL

O **JURIS_IA_CORE_V1** é um sistema completo, modular e escalável que integra:

1. Formação jurídica completa
2. Aprovação na OAB 1ª fase
3. Aprovação na OAB 2ª fase
4. Atuação profissional assistida por IA

**Este NÃO é MVP. NÃO é protótipo. É o SISTEMA DEFINITIVO.**

---

## ESTRUTURA DO SISTEMA

```
JURIS_IA_CORE_V1/
├── docs/                           # Documentação completa
│   └── 00_SISTEMA_COMPLETO_JURIS_IA.txt
│
├── ontologia/                      # Base de conhecimento jurídico
│   ├── 01_ONTOLOGIA_JURIDICA_BASE.txt
│   ├── 02_ONTOLOGIA_JURIDICA_RAMOS_DETALHADOS.txt
│   └── [demais arquivos de ontologia]
│
├── lei_seca/                       # Legislação estruturada
│   ├── 01_CONSTITUICAO_FEDERAL_ESTRUTURADA.txt
│   ├── 02_CODIGO_CIVIL_ESTRUTURADO.txt
│   ├── 03_CODIGO_PENAL_ESTRUTURADO.txt
│   └── [demais códigos e leis]
│
├── oab_1fase/                      # Sistema OAB 1ª fase
│   ├── disciplinas/
│   ├── questoes/
│   ├── padroes_cobranca/
│   └── estrategias/
│
├── oab_2fase/                      # Sistema OAB 2ª fase
│   ├── pecas/
│   ├── checklist/
│   ├── modelos/
│   └── correcao/
│
├── motor_aprendizagem/             # Motor de IA adaptativa
│   ├── diagnostico/
│   ├── revisao_espacada/
│   ├── classificacao_erros/
│   └── ajuste_dinamico/
│
├── ia_profissional/                # IA pós-aprovação
│   ├── templates/
│   ├── jurisprudencia/
│   └── organizacao/
│
├── governanca/                     # Ética e segurança
│   ├── limites_ia/
│   ├── logs/
│   └── compliance/
│
├── engines/                        # Motores de IA
│   ├── types.ts
│   ├── modules_juridicos.ts
│   ├── decision_engine.ts
│   ├── explanation_engine.ts
│   └── [demais engines]
│
└── knowledge_base/                 # Base vetorial para RAG
    └── embeddings/
```

---

## MÓDULOS PRINCIPAIS

### 1. ONTOLOGIA JURÍDICA

Base de conhecimento completa do Direito brasileiro:

- **Conceitos fundamentais**: norma jurídica, ordenamento, fato jurídico, relação jurídica
- **Ramos detalhados**: Constitucional, Civil, Penal, Processual, Trabalho, Empresarial, etc.
- **Institutos jurídicos**: prescrição, responsabilidade civil, contratos, posse, propriedade, etc.
- **Hierarquia e relações lógicas** entre conceitos

**Formato**: RAG-ready, estruturado para consumo por LLM

### 2. LEI SECA ESTRUTURADA

Legislação completa indexada e anotada:

- Constituição Federal
- Códigos (Civil, Penal, Processo)
- Leis especiais (CDC, ECA, Lei de Drogas, etc.)
- Cada artigo contém:
  - Texto completo
  - Síntese objetiva
  - Conceitos relacionados
  - Pegadinhas OAB
  - Jurisprudência relevante
  - Aplicação prática

### 3. SISTEMA OAB 1ª FASE

Sistema completo para aprovação na 1ª fase:

- **17 disciplinas** estruturadas
- **Banco de questões** categorizado (5.000+)
- **Padrões de cobrança** por banca
- **Motor de explicação** multinível (técnica, didática, analogia, exemplo)
- **Diagnóstico de erros** (conceitual, leitura, pressa)
- **Estratégias de resolução** (ataque por alternativas, palavras-chave, etc.)

### 4. SISTEMA OAB 2ª FASE

Sistema completo para aprovação na 2ª fase:

- **Peças por área** (Civil, Penal, Trabalho, Tributário, etc.)
- **Checklist inteligente** de verificação
- **Motor de correção** automatizado
- **Fundamentação legal** organizada
- **Peças-modelo** comentadas
- **Simulador de prova**

### 5. MOTOR DE APRENDIZAGEM INTELIGENTE

IA adaptativa que acompanha o estudante:

- **Diagnóstico contínuo** de performance
- **Classificação de erros** por padrão
- **Revisão espaçada** científica (ciclo 1-24-7)
- **Ajuste dinâmico** de dificuldade
- **Detecção de regressão**
- **Mapas de calor** de conhecimento

### 6. IA JURÍDICA PROFISSIONAL

Suporte pós-aprovação:

- Templates profissionais
- Jurisprudência atualizada
- Organização de raciocínio jurídico
- Estudo contínuo orientado

### 7. GOVERNANÇA E ÉTICA

Limites claros e responsabilidade:

- IA não decide, orienta
- IA não substitui advogado
- Logs de auditoria
- Proteção de dados (LGPD)
- Disclaimers transparentes

---

## DIFERENCIAIS

### 🧠 ONTOLOGIA JURÍDICA COMPLETA
Não é apenas banco de questões. É mapa conceitual completo do Direito com relações lógicas e progressão didática.

### 📚 EXPLICAÇÕES MULTINÍVEL
Adapta-se ao nível do aluno:
- Nível 1: Técnica (para quem domina)
- Nível 2: Didática (explicação simples)
- Nível 3: Analogias (compreensão intuitiva)
- Nível 4: Exemplos práticos (aplicação real)

### 🎯 FOCO EM PADRÕES DE ERRO
Não apenas "acertou/errou". Classifica tipo de erro (conceitual, leitura, pressa) e corrige causa raiz.

### 🤖 MOTOR DE APRENDIZAGEM INTELIGENTE
Ajusta-se continuamente ao desempenho. Revisão espaçada científica (1-24-7).

### 📝 SISTEMA OAB 2ª FASE ESTRUTURADO
Checklist lógico de construção + verificação automatizada + correção detalhada.

### 💼 PÓS-APROVAÇÃO INTEGRADO
Sistema continua como assistente profissional após aprovação.

---

## TECNOLOGIAS

### Backend
- Python (FastAPI, Pydantic, SQLAlchemy)
- TypeScript (Node.js, Express)
- PostgreSQL
- Redis
- Elasticsearch

### IA e ML
- LLM local: Ollama (Llama 3, Mistral)
- Embeddings: sentence-transformers
- RAG: LangChain, Faiss
- Classificação: scikit-learn

### Frontend
- Next.js 14
- React 18
- TailwindCSS
- Shadcn/ui

---

## COMO USAR

### Para Desenvolvimento

1. Clone o repositório
2. Instale dependências:
   ```bash
   npm install
   pip install -r requirements.txt
   ```
3. Configure variáveis de ambiente
4. Inicie os serviços:
   ```bash
   docker-compose up -d
   npm run dev
   ```

### Para Estudo (Aluno)

1. Faça cadastro e diagnóstico inicial
2. Sistema gera plano personalizado
3. Estude módulos progressivamente
4. Resolva questões com explicações
5. Faça simulados e ajuste fino
6. Treine peças (2ª fase)
7. Aprove!

---

## MÉTRICAS DE SUCESSO

### Do Aluno
- Taxa de aprovação na OAB
- Nota média nos simulados
- Tempo até aprovação
- Satisfação (NPS)

### Do Sistema
- Precisão das explicações (>85%)
- Tempo de resposta (<2s)
- Uptime (>99.9%)
- Acurácia de classificação de erros (>85%)

---

## ROADMAP

### ✅ FASE 1: MVP FUNCIONAL (4 semanas)
- Ontologia base (5 ramos principais)
- Lei seca estruturada (CF + 3 códigos)
- Sistema 1ª fase (5 disciplinas)
- Motor de explicação básico

### 🚧 FASE 2: SISTEMA COMPLETO 1ª FASE (8 semanas)
- Ontologia completa (todos os ramos)
- Lei seca completa
- Sistema 1ª fase (17 disciplinas)
- Banco de 5.000+ questões
- Motor de aprendizagem inteligente

### 📅 FASE 3: SISTEMA 2ª FASE (8 semanas)
- Sistema de peças (7 áreas)
- Checklist e verificação
- Correção automatizada

### 📅 FASE 4: POLIMENTO (4 semanas)
- Otimização de performance
- Interface refinada
- Gamificação

### 📅 FASE 5: PÓS-APROVAÇÃO (contínuo)
- IA profissional
- Templates avançados
- Especialização

---

## MODELO DE NEGÓCIO

### Planos

#### GRATUITO
- Acesso limitado à ontologia
- 10 questões/dia
- Explicações básicas

#### ESSENCIAL (R$ 97/mês)
- Ontologia completa
- Questões ilimitadas
- Explicações multinível
- 1 simulado completo/mês

#### PRO (R$ 197/mês)
- Tudo do Essencial
- Sistema 2ª fase
- Simulados ilimitados
- Correção de peças (5/mês)

#### PREMIUM (R$ 397/mês)
- Tudo do Pro
- Correção ilimitada
- IA profissional pós-aprovação
- Mentoria mensal (1h)
- Acesso vitalício após aprovação

### Garantia
Aprovado ou seu dinheiro de volta (plano anual)

---

## GOVERNANÇA E ÉTICA

### Princípios

1. **TRANSPARÊNCIA**: IA não é caixa preta
2. **RESPONSABILIDADE**: IA não substitui advogado
3. **PRIVACIDADE**: Dados confidenciais (LGPD)
4. **SEGURANÇA**: Criptografia e backup
5. **ACESSIBILIDADE**: Plano gratuito robusto

### Disclaimer

> O JURIS_IA_CORE_V1 é um sistema educacional de apoio à formação jurídica e preparação para a OAB. Ele NÃO substitui professores, cursos presenciais, leitura de doutrinas ou a orientação de profissionais experientes. A IA não presta consultoria jurídica, não decide casos concretos e não substitui o julgamento profissional de um advogado.

---

## CONTATO

Para dúvidas, sugestões ou parcerias:

- Email: contato@juris-ia.com.br
- Site: https://juris-ia.com.br
- GitHub: https://github.com/juris-ia/core

---

## LICENÇA

Proprietary - Todos os direitos reservados

© 2025 JURIS_IA_CORE_V1

---

## CONTRIBUINDO

Este é um projeto proprietário. Para contribuir, entre em contato conosco.

---

**JURIS_IA_CORE_V1 - O Maior Aprovador de OAB do Brasil** 🎓⚖️
