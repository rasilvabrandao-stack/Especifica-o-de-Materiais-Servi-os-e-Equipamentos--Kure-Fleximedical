from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
import os
import logging
import json
import re
import google.generativeai as genai

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session management
CORS(app)  # Enable CORS for all routes

# Configure Gemini API
API_KEY = 'AIzaSyAAMYTHfooiOzcpHMHe1OG7ecEPHbOKnlY'
genai.configure(api_key=API_KEY)

# System instructions for the AI
CHAT_SYSTEM_INSTRUCTION = """You are an expert product manager AI. Your goal is to help users flesh out their product ideas into a detailed product specification.
Start by asking clarifying questions about the user's initial idea.
Ask one or two questions at a time to not overwhelm the user.
Analyze the user's responses and continue asking targeted questions to gather all necessary details.
Cover aspects like target audience, key features, user pain points, and potential monetization.
When you are confident you have enough information to write a comprehensive spec, end your message with the special token [GENERATE_SPEC].
Do not include this token until you have gathered sufficient detail."""

SPEC_GENERATION_INSTRUCTION = """You are an expert technical writer AI. Based on the provided conversation between a user and a product manager AI, generate a comprehensive product specification document.
The document must be in HTML format.
It should be well-structured, clear, and detailed.
Use appropriate HTML tags for structure (e.g., <h1> for the main title, <h2> for sections, <ul>, <li>, <p>, <strong>).
The document should include the following sections:
- "Introduction & Vision": A brief overview of the product and its purpose.
- "Target Audience": A detailed description of the ideal users.
- "Key Features": A prioritized list of features with detailed descriptions for each.
- "User Stories": Write several user stories in the format: "As a [type of user], I want [an action] so that [a benefit]."
- "Non-Functional Requirements": Address aspects like performance, security, and scalability.
- "Success Metrics": Define key performance indicators (KPIs) to measure the product's success."""

# Load dataset
DATASET_PATH = 'dataset.json'
if os.path.exists(DATASET_PATH):
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
else:
    dataset = {"categories": []}

# Comprehensive Product Knowledge Base with expanded categories
product_knowledge = {
    'computador': {
        'keywords': ['computador', 'pc', 'desktop', 'notebook', 'laptop', 'all-in-one', 'ultrabook', 'gaming pc', 'workstation'],
        'price_ranges': {'básico': 'R$ 1.000 - R$ 3.000', 'intermediário': 'R$ 3.000 - R$ 8.000', 'premium': 'R$ 8.000 - R$ 15.000', 'luxo': 'R$ 15.000 - R$ 50.000+'},
        'recommendations': [
            'Dell: confiabilidade e suporte técnico',
            'HP: qualidade e inovação',
            'Lenovo: durabilidade e design',
            'Apple: performance e design premium',
            'ASUS: custo-benefício excelente'
        ],
        'tips': [
            'Verifique especificações técnicas (processador, memória, armazenamento)',
            'Considere o uso principal (trabalho, jogos, estudos)',
            'Avalie a necessidade de portabilidade',
            'Verifique compatibilidade com softwares necessários',
            'Considere garantia e suporte pós-venda'
        ],
        'followups': [
            'Qual o uso principal?',
            'Marca preferida?',
            'Orçamento disponível?',
            'Características importantes (processador, memória, etc.)?',
            'Portátil ou desktop?',
            'Já tem algum modelo em mente?',
            'Precisa de acessórios incluídos?',
            'Sistema operacional preferido?'
        ]
    },
    'alimento': {
        'keywords': ['comida', 'alimento', 'bebida', 'cerveja', 'vinho', 'refrigerante', 'suco', 'café', 'chá', 'chocolate', 'doce', 'salgado', 'pizza', 'hambúrguer', 'sorvete', 'iogurte', 'queijo', 'carne', 'fruta', 'verdura', 'legume'],
        'price_ranges': {'básico': 'R$ 2 - R$ 20', 'intermediário': 'R$ 20 - R$ 100', 'premium': 'R$ 100 - R$ 500+', 'luxo': 'R$ 500 - R$ 5.000+'},
        'recommendations': [
            'Produtos orgânicos: melhor qualidade nutricional',
            'Produtos locais: frescor e sustentabilidade',
            'Marcas premium: qualidade superior e ingredientes selecionados',
            'Produtos importados: sabores únicos e experiências especiais',
            'Produtos artesanais: autenticidade e tradição'
        ],
        'tips': [
            'Verifique data de validade e condições de armazenamento',
            'Considere restrições alimentares (alergias, intolerâncias)',
            'Avalie valor nutricional e composição',
            'Prefira produtos frescos e da estação'
        ],
        'followups': [
            'Qual o tipo de alimento?',
            'Marca ou origem?',
            'Quantidade/peso?',
            'Data de validade?',
            'Restrições alimentares?',
            'Preço aproximado?',
            'Estado de conservação?',
            'Embalagem?'
        ]
    },
    'medicamento': {
        'keywords': ['remédio', 'medicamento', 'comprimido', 'xarope', 'injeção', 'vacina', 'vitamina', 'suplemento', 'analgésico', 'antibiótico', 'anti-inflamatório', 'antialérgico'],
        'price_ranges': {'genérico': 'R$ 5 - R$ 50', 'similar': 'R$ 20 - R$ 100', 'referência': 'R$ 50 - R$ 300+', 'especial': 'R$ 100 - R$ 1.000+'},
        'recommendations': [
            'Medicamentos genéricos: mesma eficácia, preço menor',
            'Marcas de referência: confiança e qualidade comprovada',
            'Suplementos naturais: opções mais suaves',
            'Produtos manipulados: dosagem personalizada',
            'Farmácias de manipulação: fórmulas específicas'
        ],
        'tips': [
            'Sempre consulte um profissional de saúde',
            'Verifique bula e contraindicações',
            'Guarde em local adequado e fora do alcance de crianças',
            'Não use medicamentos vencidos',
            'Informe sobre alergias e outros medicamentos em uso'
        ],
        'followups': [
            'Qual o medicamento?',
            'Dosagem necessária?',
            'É receita médica?',
            'Marca preferida?',
            'Preço aproximado?',
            'Quantidade?',
            'Data de validade?',
            'Finalidade do tratamento?'
        ]
    },
    'ferramenta': {
        'keywords': ['ferramenta', 'martelo', 'chave', 'parafuso', 'prego', 'furadeira', 'serra', 'alicate', 'chave de fenda', 'nível', 'trena', 'marreta', 'plaina', 'lixadeira', 'equipamento', 'construção', 'reforma'],
        'price_ranges': {'básico': 'R$ 10 - R$ 100', 'intermediário': 'R$ 100 - R$ 500', 'profissional': 'R$ 500 - R$ 2.000+', 'industrial': 'R$ 2.000 - R$ 20.000+'},
        'recommendations': [
            'Ferramentas Stanley: durabilidade excepcional',
            'Bosch: potência e tecnologia avançada',
            'Tramontina: custo-benefício excelente',
            'Makita: qualidade profissional',
            'Ferramentas manuais: precisão e controle',
            'Equipamentos elétricos: eficiência e velocidade'
        ],
        'tips': [
            'Escolha ferramentas adequadas ao trabalho',
            'Verifique qualidade dos materiais',
            'Considere segurança no uso',
            'Mantenha ferramentas limpas e organizadas',
            'Use equipamentos de proteção individual'
        ],
        'followups': [
            'Qual o tipo de ferramenta?',
            'Uso específico?',
            'Marca preferida?',
            'Estado de conservação?',
            'Acessórios incluídos?',
            'Preço aproximado?',
            'Profissional ou uso doméstico?',
            'Voltagem (para ferramentas elétricas)?'
        ]
    },
    'brinquedo': {
        'keywords': ['brinquedo', 'boneca', 'carrinho', 'lego', 'quebra-cabeça', 'jogo', 'tabuleiro', 'pelúcia', 'bicicleta infantil', 'patinete', 'bola', 'videogame', 'console', 'jogo educativo'],
        'price_ranges': {'básico': 'R$ 10 - R$ 100', 'intermediário': 'R$ 100 - R$ 300', 'premium': 'R$ 300 - R$ 1.000+', 'colecionável': 'R$ 1.000 - R$ 10.000+'},
        'recommendations': [
            'LEGO: criatividade e desenvolvimento cognitivo',
            'Hot Wheels: carros colecionáveis',
            'Mattel: bonecas e acessórios clássicos',
            'Hasbro: jogos de tabuleiro divertidos',
            'Fisher-Price: brinquedos educativos para bebês',
            'Nintendo Switch: jogos interativos',
            'Produtos educativos: aprendizado através do brincar'
        ],
        'tips': [
            'Verifique faixa etária recomendada',
            'Considere segurança e certificações',
            'Avalie durabilidade e materiais',
            'Verifique se estimula o desenvolvimento',
            'Considere espaço de armazenamento'
        ],
        'followups': [
            'Qual o tipo de brinquedo?',
            'Faixa etária?',
            'Marca?',
            'Estado de conservação?',
            'Acessórios incluídos?',
            'Preço aproximado?',
            'Gênero (menino, menina, unissex)?',
            'Finalidade (brincar, educar, colecionar)?'
        ]
    },
    'serviço': {
        'keywords': ['serviço', 'manutenção', 'reparo', 'instalação', 'limpeza', 'pintura', 'eletricista', 'encanador', 'pedreiro', 'marceneiro', 'jardineiro', 'diarista', 'babá', 'professor', 'personal trainer', 'terapia'],
        'price_ranges': {'básico': 'R$ 50 - R$ 200', 'intermediário': 'R$ 200 - R$ 500', 'especializado': 'R$ 500 - R$ 2.000+', 'premium': 'R$ 2.000 - R$ 10.000+'},
        'recommendations': [
            'Profissionais qualificados e certificados',
            'Serviços com garantia',
            'Avaliações e referências positivas',
            'Contratos claros e detalhados',
            'Serviços emergenciais 24h',
            'Pacotes de manutenção preventiva'
        ],
        'tips': [
            'Pesquise referências e avaliações',
            'Solicite orçamento detalhado',
            'Verifique documentação e qualificações',
            'Combine prazos e condições de pagamento',
            'Exija nota fiscal e garantia'
        ],
        'followups': [
            'Qual o tipo de serviço?',
            'Urgência?',
            'Localização?',
            'Quando precisa?',
            'Orçamento disponível?',
            'Já tem profissional em mente?',
            'Precisa de materiais incluídos?',
            'Garantia necessária?'
        ]
    },
    'pet': {
        'keywords': ['pet', 'animal', 'cachorro', 'gato', 'pássaro', 'peixe', 'ração', 'remédio animal', 'acessório pet', 'coleira', 'cama pet', 'brinquedo pet', 'shampoo pet', 'vacina'],
        'price_ranges': {'básico': 'R$ 5 - R$ 50', 'intermediário': 'R$ 50 - R$ 200', 'premium': 'R$ 200 - R$ 1.000+', 'luxo': 'R$ 1.000 - R$ 5.000+'},
        'recommendations': [
            'Royal Canin: rações especializadas por raça/porte',
            'Pedigree: rações acessíveis e completas',
            'Whiskas: alimentos específicos para gatos',
            'Produtos naturais: opções mais saudáveis',
            'Acessórios personalizados: conforto e estilo',
            'Produtos veterinários: saúde e bem-estar'
        ],
        'tips': [
            'Consulte veterinário para recomendações específicas',
            'Verifique composição e qualidade dos alimentos',
            'Considere porte, idade e necessidades especiais',
            'Mantenha higiene e limpeza dos acessórios',
            'Vacinação e cuidados veterinários em dia'
        ],
        'followups': [
            'Qual o tipo de pet?',
            'Raça/porte?',
            'Idade?',
            'Qual o produto/acessório?',
            'Marca?',
            'Preço aproximado?',
            'Quantidade?',
            'Finalidade?'
        ]
    },
    'jardim': {
        'keywords': ['jardim', 'planta', 'flor', 'árvore', 'grama', 'vaso', 'adubo', 'pesticida', 'regador', 'tesoura poda', 'muda', 'semente', 'fertilizante', 'decoração jardim'],
        'price_ranges': {'básico': 'R$ 5 - R$ 50', 'intermediário': 'R$ 50 - R$ 200', 'premium': 'R$ 200 - R$ 1.000+', 'luxo': 'R$ 1.000 - R$ 10.000+'},
        'recommendations': [
            'Plantas de fácil manutenção: suculentas e cactos',
            'Plantas ornamentais: beleza e cor',
            'Árvores frutíferas: utilidade e sombra',
            'Produtos orgânicos: sustentabilidade',
            'Kits de jardinagem: praticidade',
            'Produtos automáticos: irrigação inteligente'
        ],
        'tips': [
            'Considere iluminação e exposição solar',
            'Verifique necessidade de água e manutenção',
            'Escolha plantas adequadas ao clima local',
            'Use produtos específicos para cada tipo de planta',
            'Mantenha equilíbrio ecológico no jardim'
        ],
        'followups': [
            'Qual o tipo de planta/produto?',
            'Espaço disponível?',
            'Exposição solar?',
            'Clima da região?',
            'Manutenção desejada?',
            'Preço aproximado?',
            'Quantidade?',
            'Finalidade (decoração, consumo, sombra)?'
        ]
    }
}

# Additional categories not in dataset
additional_categories = product_knowledge

class AISuggester:
    def __init__(self, all_categories):
        self.all_categories = all_categories

    def preprocess_text(self, text):
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text.split()

    def detect_category(self, tokens):
        for cat_id, cat_data in self.all_categories.items():
            if any(keyword in tokens for keyword in cat_data['keywords']):
                return cat_id, cat_data
        return None, None

    def calculate_completeness_score(self, text, followups):
        extracted = self.extract_details(text, followups)
        return len(extracted) / len(followups) if followups else 0

    def extract_details(self, text, followups):
        extracted = []
        text_lower = text.lower()
        for followup in followups:
            followup_lower = followup.lower()
            if any(word in text_lower for word in followup_lower.split()):
                extracted.append(followup)
        return extracted

    def generate_advanced_suggestions(self, text):
        tokens = self.preprocess_text(text)
        text_lower = text.lower()

        # Enhanced conversational responses
        if any(keyword in tokens for keyword in ['oi', 'ola', 'olá', 'bom', 'dia', 'tarde', 'noite', 'eae', 'opa']):
            responses = [
                "Olá! Sou Lucia, sua assistente IA profissional especializada em produtos e vendas. Posso ajudar com descrições, preços, recomendações e conversas sobre qualquer item. O que você precisa hoje?",
                "Oi! Bem-vindo! Sou Lucia, especialista em produtos e vendas. Posso te ajudar com preços, recomendações, descrições completas e muito mais. Como posso ajudar?",
                "Olá! Que bom ter você aqui! Sou Lucia, IA especializada em produtos. Posso ajudar com vendas, compras, preços e recomendações personalizadas. O que você gostaria de saber?",
                "Oi! Sou Lucia, sua assistente inteligente para produtos e vendas. Tenho conhecimento sobre milhares de itens, preços e recomendações. Como posso te ajudar hoje?"
            ]
            return [responses[len(text) % len(responses)]]

        if any(keyword in tokens for keyword in ['tchau', 'adeus', 'até', 'logo', 'sair', 'xau', 'bye']):
            responses = [
                "Até logo! Foi um prazer conversar com você. Lembre-se: estou sempre aqui para ajudar com produtos, preços e recomendações. Volte quando precisar!",
                "Tchau! Obrigada pela conversa! Se precisar de ajuda com produtos, vendas ou recomendações, é só chamar. Até a próxima!",
                "Até mais! Foi ótimo ajudar você. Lembre-se que posso ajudar com qualquer produto, preço ou recomendação. Volte sempre!",
                "Adeus! Espero ter ajudado bem. Estou sempre disponível para conversas sobre produtos, preços e vendas. Até logo!"
            ]
            return [responses[len(text) % len(responses)]]

        if any(keyword in tokens for keyword in ['obrigado', 'valeu', 'agradecido', 'thanks', 'obg', 'vlw']):
            responses = [
                "De nada! Fico feliz em ajudar. Se precisar de mais informações sobre produtos, preços ou recomendações, é só perguntar!",
                "Por nada! Estou sempre aqui para ajudar com suas dúvidas sobre produtos e vendas. Precisa de mais alguma coisa?",
                "Imagina! É um prazer ajudar. Se tiver mais perguntas sobre preços, recomendações ou descrições, pode contar comigo!",
                "Disponha! Fico contente em poder ajudar. Para qualquer coisa relacionada a produtos, vendas ou compras, estou à disposição!"
            ]
            return [responses[len(text) % len(responses)]]

        if any(keyword in tokens for keyword in ['como', 'vai', 'está', 'passando', 'beleza']):
            responses = [
                "Estou funcionando perfeitamente, processando milhares de dados sobre produtos! Como posso ajudar você hoje com suas vendas ou compras?",
                "Tudo ótimo! Meu banco de dados está atualizado com informações sobre milhares de produtos. Como posso ajudar você hoje?",
                "Funcionando 100%! Tenho acesso a dados de preços, recomendações e especificações de diversos produtos. O que você precisa?",
                "Perfeita! Estou pronta para ajudar com qualquer pergunta sobre produtos, preços ou recomendações. Como posso te auxiliar?"
            ]
            return [responses[len(text) % len(responses)]]

        if any(keyword in tokens for keyword in ['ajuda', 'socorro', 'preciso', 'auxilio', 'help']):
            responses = [
                "Claro! Sou especialista em produtos e posso ajudar com: descrições completas, faixas de preço, recomendações de marcas, análise de mercado e conversas sobre qualquer item. O que você precisa?",
                "Com certeza! Posso ajudar com: preços de produtos, recomendações personalizadas, descrições para anúncios, comparações de marcas e muito mais. O que você gostaria?",
                "Pode contar comigo! Minha especialidade é ajudar com produtos: preços, recomendações, descrições completas, análise de mercado e orientações de compra/venda. O que você precisa?",
                "Estou aqui para ajudar! Posso fornecer informações sobre preços, fazer recomendações, ajudar com descrições de produtos, comparar opções e muito mais. Como posso te auxiliar?"
            ]
            return [responses[len(text) % len(responses)]]

        if any(keyword in tokens for keyword in ['vender', 'vende', 'vendo', 'anunciar', 'venda']):
            responses = [
                "Excelente! Para criar anúncios de sucesso, descreva o produto que você quer vender. Posso sugerir preços competitivos, destacar características importantes e otimizar a descrição para atrair compradores.",
                "Perfeito para vendas! Conte-me sobre o produto que você quer vender. Posso ajudar com preços sugeridos, descrições atraentes e dicas para vender mais rápido.",
                "Ótimo! Vamos criar um anúncio incrível! Descreva o produto, marca, modelo, estado de conservação e características principais. Posso sugerir preços e melhorar a descrição.",
                "Vamos vender bem! Me dê detalhes sobre o produto: marca, modelo, condição, preço pretendido. Posso otimizar a descrição e sugerir estratégias de venda."
            ]
            return [responses[len(text) % len(responses)]]

        if any(keyword in tokens for keyword in ['comprar', 'compre', 'comprando', 'procurar', 'buscar']):
            responses = [
                "Perfeito! Conte-me o que você está procurando. Posso indicar as melhores opções, comparar preços, sugerir marcas confiáveis e ajudar a encontrar o produto ideal para suas necessidades.",
                "Vamos encontrar o produto ideal! Descreva o que você precisa: categoria, marca preferida, orçamento, características desejadas. Posso fazer recomendações personalizadas.",
                "Excelente! Para te ajudar a comprar, me diga: que tipo de produto, quanto quer gastar, quais características são importantes. Posso comparar opções e sugerir as melhores.",
                "Procurando compras inteligentes? Conte-me seus requisitos: produto desejado, orçamento disponível, preferências de marca. Posso ajudar a encontrar as melhores ofertas!"
            ]
            return [responses[len(text) % len(responses)]]

        # Enhanced price queries
        if 'preço' in text_lower or 'custa' in text_lower or 'valor' in text_lower or 'quanto' in text_lower or 'cara' in text_lower or 'barato' in text_lower:
            cat_id, cat_data = self.detect_category(tokens)
            if cat_data and 'price_ranges' in cat_data:
                price_info = cat_data['price_ranges']
                response = f"💰 Faixas de preço aproximadas para {cat_id}: "
                for level, range_price in price_info.items():
                    response += f"{level.capitalize()}: {range_price}; "
                response = response[:-2] + ". Posso dar recomendações específicas se você me der mais detalhes!"

                # Add tips if available
                if 'tips' in cat_data:
                    tips = cat_data['tips'][:2]
                    response += f" 💡 Dicas: {'; '.join(tips)}"

                return [response]
            else:
                responses = [
                    "Para informações de preço precisas, descreva o produto específico. Posso indicar faixas de preço e ajudar a encontrar as melhores ofertas!",
                    "Me dê mais detalhes sobre o produto (marca, modelo, características) para informar preços precisos. Posso comparar opções e sugerir os melhores valores!",
                    "Quanto custa depende do modelo e condição! Descreva melhor o produto que você quer saber o preço. Posso ajudar a encontrar boas ofertas!",
                    "Preços variam muito! Me conte mais sobre o produto específico que você quer saber o valor. Posso indicar faixas de preço e recomendações!"
                ]
                return [responses[len(text) % len(responses)]]

        # Enhanced recommendation queries
        if 'recomend' in text_lower or 'indic' in text_lower or 'suger' in text_lower or 'melhor' in text_lower or 'bom' in text_lower:
            cat_id, cat_data = self.detect_category(tokens)
            if cat_data and 'recommendations' in cat_data:
                recs = cat_data['recommendations'][:3]
                response = f"⭐ Minhas recomendações para {cat_id}: " + "; ".join(recs)
                response += ". Quer saber mais sobre alguma dessas opções?"

                # Add tips if available
                if 'tips' in cat_data:
                    tips = cat_data['tips'][:1]
                    response += f" 💡 Dica: {tips[0]}"

                return [response]
            else:
                responses = [
                    "Posso fazer recomendações personalizadas! Descreva o produto ou categoria que você está interessado e darei sugestões baseadas em qualidade, preço e popularidade.",
                    "Me conte o que você precisa e farei recomendações excelentes! Considere orçamento, uso principal e preferências para sugestões mais precisas.",
                    "Vamos encontrar a melhor opção! Descreva suas necessidades: tipo de produto, orçamento, características importantes. Posso recomendar as melhores escolhas!",
                    "Recomendações sob medida! Me diga o produto desejado, quanto quer gastar e para que vai usar. Posso indicar as opções mais adequadas!"
                ]
                return [responses[len(text) % len(responses)]]

        # Enhanced product description analysis
        cat_id, cat_data = self.detect_category(tokens)
        if cat_data:
            suggestions = []
            followups = cat_data['followups']
            score = self.calculate_completeness_score(text, followups)
            extracted = self.extract_details(text, followups)
            missing = [f for f in followups if not any(k in f.lower() for k in extracted)]

            # Add price information with emojis
            if 'price_ranges' in cat_data:
                price_info = cat_data['price_ranges']
                price_text = f"💰 Faixas de preço para {cat_id}: "
                for level, range_price in price_info.items():
                    price_text += f"{level.capitalize()} {range_price}, "
                suggestions.append(price_text[:-2])

            # Add recommendations with emojis
            if 'recommendations' in cat_data:
                recs = cat_data['recommendations'][:2]
                suggestions.append(f"⭐ Recomendações: {'; '.join(recs)}")

            # Add tips with emojis
            if 'tips' in cat_data:
                tips = cat_data['tips'][:2]
                suggestions.append(f"💡 Dicas importantes: {'; '.join(tips)}")

            # Completeness analysis
            if missing:
                suggestions.append(f"📝 Para {cat_id} (completude: {score:.1%}), considere adicionar: {'; '.join(missing[:3])}")
            else:
                suggestions.append(f"✅ A descrição de {cat_id} parece completa. Revise se todas as informações necessárias estão presentes.")

            # Intelligent questions
            suggestions.append("❓ Perguntas adicionais: Qual é o preço pretendido? Há alguma condição especial ou desconto?")
            return suggestions

        # Enhanced general conversation fallback
        fallback_responses = [
            "Sou uma IA especializada em produtos e vendas! Posso ajudar com descrições, preços, recomendações e conversas sobre qualquer item. Descreva o que você quer vender, comprar ou perguntar!",
            "Olá! Sou Lucia, especialista em produtos. Posso ajudar com preços, recomendações, descrições completas e orientações para vendas e compras. O que você precisa?",
            "Estou aqui para ajudar com qualquer coisa relacionada a produtos! Preços, recomendações, descrições, comparações... Descreva sua dúvida ou necessidade!",
            "Posso ajudar com vendas, compras, preços e recomendações de produtos! Me conte o que você está procurando ou vendendo. Vamos conversar sobre isso!",
            "Especialista em produtos à disposição! Posso fornecer informações sobre preços, fazer recomendações personalizadas e ajudar com descrições atraentes. Como posso ajudar?"
        ]
        return [fallback_responses[len(text) % len(fallback_responses)]]

# Instantiate the AI
all_categories = {**{cat['id']: cat for cat in dataset.get('categories', [])}, **additional_categories}
ai_suggester = AISuggester(all_categories)

def analyze_and_suggest(text):
    """
    Analisa o texto de descrição do item e sugere melhorias para torná-lo mais completo.
    Retorna uma lista de sugestões.
    """
    return ai_suggester.generate_advanced_suggestions(text)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/style.css')
def style():
    return send_from_directory('.', 'style.css')

@app.route('/assets/<path:filename>')
def serve_img(filename):
    return send_from_directory('assets', filename)

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        text = data.get('text', '')
        history = data.get('history', [])

        if not text:
            return jsonify({'error': 'Texto vazio'}), 400

        # If history is provided, use Gemini chat
        if history:
            # Convert history to Gemini format
            gemini_history = []
            for msg in history:
                if msg.get('author') != 'system':
                    gemini_history.append({
                        'role': 'user' if msg.get('author') == 'user' else 'model',
                        'parts': [{'text': msg.get('content', '')}]
                    })

            # Add current message
            gemini_history.append({
                'role': 'user',
                'parts': [{'text': text}]
            })

            # Create chat session
            model = genai.GenerativeModel(
                model_name='gemini-2.0-flash-exp',
                system_instruction=CHAT_SYSTEM_INSTRUCTION
            )

            chat = model.start_chat(history=gemini_history[:-1])  # Exclude current message from history
            response = chat.send_message(text)

            ai_response = response.text

            # Check if spec generation is requested
            if '[GENERATE_SPEC]' in ai_response:
                # Generate spec from full conversation
                full_history = history + [{'author': 'user', 'content': text}, {'author': 'assistant', 'content': ai_response}]

                spec_model = genai.GenerativeModel(
                    model_name='gemini-1.5-pro',
                    system_instruction=SPEC_GENERATION_INSTRUCTION
                )

                conversation_text = '\n\n'.join([
                    f"{'User' if msg['author'] == 'user' else 'Product Manager'}: {msg['content']}"
                    for msg in full_history if msg['author'] != 'system'
                ])

                spec_prompt = f"Here is the conversation history:\n\n---\n\n{conversation_text}\n\n---\n\nPlease generate the product specification document based on this conversation."

                spec_response = spec_model.generate_content(spec_prompt)
                spec_html = spec_response.text

                return jsonify({
                    'response': ai_response.replace('[GENERATE_SPEC]', ''),
                    'spec': spec_html,
                    'type': 'spec_generated'
                })
            else:
                return jsonify({
                    'response': ai_response,
                    'type': 'chat'
                })
        else:
            # Fallback to old logic if no history
            suggestions = analyze_and_suggest(text)
            return jsonify({'suggestions': suggestions})

    except Exception as e:
        logger.error(f"Error in analyze endpoint: {e}")
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask app on port {port}")
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Error starting Flask app: {e}")
        raise
