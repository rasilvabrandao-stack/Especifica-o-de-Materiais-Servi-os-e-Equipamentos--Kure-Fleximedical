from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import re
import json
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load dataset
DATASET_PATH = 'dataset.json'
if os.path.exists(DATASET_PATH):
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
else:
    dataset = {"categories": []}

# Comprehensive Product Knowledge Base
product_knowledge = {
    'computador': {
        'keywords': ['computador', 'pc', 'desktop', 'notebook', 'laptop', 'all-in-one', 'ultrabook', 'gaming pc', 'workstation'],
        'price_ranges': {'básico': 'R$ 1.500 - R$ 3.000', 'intermediário': 'R$ 3.000 - R$ 6.000', 'avançado': 'R$ 6.000 - R$ 15.000+', 'premium': 'R$ 15.000 - R$ 30.000+'},
        'recommendations': [
            'Para trabalho básico: i3/8GB RAM/256GB SSD',
            'Para trabalho avançado: i5/16GB RAM/512GB SSD',
            'Para jogos leves: i5/8GB RAM/GTX 1650',
            'Para jogos pesados: i7/16GB RAM/RTX 3060',
            'Para edição profissional: i9/32GB RAM/RTX 3080',
            'Para estudantes: Chromebook ou notebook básico',
            'Para designers: MacBook Pro com M2'
        ],
        'tips': [
            'Verifique a garantia e suporte técnico',
            'Considere a portabilidade para notebooks',
            'Avalie a necessidade de upgrade futuro',
            'Compare consumo de energia'
        ],
        'followups': [
            'Qual o uso principal (trabalho, jogos, estudos)?',
            'Qual o modelo desejado?',
            'Qual o processador (ex: Intel i5, AMD Ryzen)?',
            'Quantidade de memória RAM?',
            'Armazenamento (SSD/HDD e capacidade)?',
            'Placa de vídeo necessária?',
            'Sistema operacional?',
            'Cor preferida?',
            'Tamanho da tela (para notebooks)?',
            'Marca preferida?',
            'Necessita de garantia estendida?',
            'Acessórios incluídos?',
            'Budget disponível?',
            'Preferência por marca (Dell, HP, Lenovo, Asus)?'
        ]
    },
    'celular': {
        'keywords': ['celular', 'smartphone', 'telefone', 'mobile', 'tablet', 'iphone', 'android', 'samsung', 'xiaomi', 'motorola'],
        'price_ranges': {'básico': 'R$ 800 - R$ 1.500', 'intermediário': 'R$ 1.500 - R$ 3.000', 'premium': 'R$ 3.000 - R$ 8.000+', 'top': 'R$ 8.000 - R$ 15.000+'},
        'recommendations': [
            'Samsung Galaxy A54: ótimo custo-benefício, câmera boa',
            'iPhone 13: câmera excepcional, ecossistema Apple',
            'Xiaomi Redmi Note 12: bateria duradoura, preço acessível',
            'Samsung Galaxy S23: flagship com recursos premium',
            'iPhone SE: compacto e acessível para iOS',
            'Motorola Edge 30: design premium, câmera versátil',
            'Google Pixel 7: fotografia computacional excepcional'
        ],
        'tips': [
            'Verifique compatibilidade com operadoras',
            'Avalie duração da bateria para seu uso',
            'Considere tamanho da tela para ergonomia',
            'Verifique suporte de software (atualizações)'
        ],
        'followups': [
            'Qual o uso principal (chamadas, internet, jogos, câmera)?',
            'Qual o modelo?',
            'Marca?',
            'Capacidade de armazenamento?',
            'Sistema operacional?',
            'Cor preferida?',
            'Tamanho da tela?',
            'Câmera principal (quantidade de lentes)?',
            'Bateria (capacidade em mAh)?',
            'Resistência à água?',
            'Preço aproximado?',
            'Acessórios incluídos?',
            'Preferência por iOS ou Android?'
        ]
    },
    'roupa': {
        'keywords': ['roupa', 'vestuário', 'camisa', 'calça', 'sapato', 'blusa', 'jaqueta', 'vestido', 'short', 'bermuda', 'meia', 'cueca'],
        'price_ranges': {'básico': 'R$ 20 - R$ 100', 'intermediário': 'R$ 100 - R$ 300', 'luxo': 'R$ 300 - R$ 1.000+', 'premium': 'R$ 1.000 - R$ 5.000+'},
        'recommendations': [
            'Verifique sempre a tabela de medidas',
            'Materiais: algodão para conforto diário',
            'Poliéster para durabilidade e secagem rápida',
            'Marcas: Nike, Adidas, Zara para qualidade',
            'H&M, Uniqlo para preços acessíveis',
            'Lacoste, Ralph Lauren para luxo',
            'Considere sustentabilidade e materiais ecológicos'
        ],
        'tips': [
            'Verifique composição do tecido',
            'Avalie conforto e praticidade',
            'Considere lavagem e manutenção',
            'Verifique origem e condições de produção'
        ],
        'followups': [
            'Qual o tipo de roupa?',
            'Qual o tamanho?',
            'Cor?',
            'Material?',
            'Marca?',
            'Estilo (casual, esportivo, formal)?',
            'Gênero (masculino, feminino, unissex)?',
            'Ocasião de uso?',
            'Preço aproximado?',
            'Condição (novo/usado)?',
            'Tamanho disponível?',
            'Composição do tecido?'
        ]
    },
    'eletrodoméstico': {
        'keywords': ['geladeira', 'fogão', 'microondas', 'máquina de lavar', 'aspirador', 'liquidificador', 'batedeira', 'cafeteira', 'forno', 'lava-louças'],
        'price_ranges': {'básico': 'R$ 200 - R$ 800', 'intermediário': 'R$ 800 - R$ 2.000', 'premium': 'R$ 2.000 - R$ 10.000+', 'luxo': 'R$ 10.000 - R$ 50.000+'},
        'recommendations': [
            'Brastemp: geladeiras eficientes e duráveis',
            'Electrolux: máquinas de lavar com tecnologia avançada',
            'Arno: liquidificadores potentes e acessíveis',
            'Philips Walita: batedeiras profissionais',
            'Nespresso: cafeteiras premium',
            'Samsung: fornos com funções inteligentes',
            'Bosch: lava-louças silenciosos e eficientes'
        ],
        'tips': [
            'Verifique consumo de energia (selo Procel)',
            'Avalie dimensões para o espaço disponível',
            'Considere garantia e assistência técnica',
            'Verifique voltagem (110V ou 220V)'
        ],
        'followups': [
            'Qual o tipo de eletrodoméstico?',
            'Marca?',
            'Modelo?',
            'Capacidade?',
            'Voltagem?',
            'Cor?',
            'Estado de conservação?',
            'Acessórios incluídos?',
            'Preço aproximado?',
            'Consumo de energia?',
            'Dimensões?',
            'Funções especiais?'
        ]
    },
    'carro': {
        'keywords': ['carro', 'automóvel', 'veículo', 'moto', 'bicicleta', 'honda', 'toyota', 'volkswagen', 'fiat', 'ford', 'chevrolet'],
        'price_ranges': {'popular': 'R$ 30.000 - R$ 60.000', 'intermediário': 'R$ 60.000 - R$ 120.000', 'luxo': 'R$ 120.000 - R$ 500.000+', 'premium': 'R$ 500.000 - R$ 2.000.000+'},
        'recommendations': [
            'Honda Civic: confiabilidade e economia',
            'Toyota Corolla: durabilidade excepcional',
            'Volkswagen Polo: custo-benefício excelente',
            'Fiat Argo: urbano e econômico',
            'Ford Ka: acessível e prático',
            'Chevrolet Onix: popular e espaçoso',
            'BMW 3 Series: luxo e performance',
            'Mercedes C-Class: conforto premium'
        ],
        'tips': [
            'Verifique histórico no Detran',
            'Faça revisão completa antes da compra',
            'Avalie consumo de combustível',
            'Considere custos de manutenção',
            'Verifique documentação completa'
        ],
        'followups': [
            'Qual o tipo (carro, moto, bicicleta)?',
            'Marca e modelo?',
            'Ano?',
            'Quilometragem?',
            'Combustível?',
            'Cor?',
            'Estado de conservação?',
            'Documentação completa?',
            'Preço pretendido?',
            'Finalidade (cidade, estrada, trabalho)?',
            'Quantidade de portas/assentos?',
            'Transmissão (manual/automática)?'
        ]
    },
    'eletroeletrônico': {
        'keywords': ['tv', 'televisão', 'smart tv', 'monitor', 'fone', 'headphone', 'caixa de som', 'console', 'playstation', 'xbox', 'nintendo', 'fone bluetooth'],
        'price_ranges': {'básico': 'R$ 100 - R$ 500', 'intermediário': 'R$ 500 - R$ 2.000', 'premium': 'R$ 2.000 - R$ 10.000+', 'top': 'R$ 10.000 - R$ 50.000+'},
        'recommendations': [
            'Samsung QLED: qualidade de imagem excepcional',
            'LG OLED: pretos perfeitos e cores vibrantes',
            'Sony WH-1000XM4: fones premium com cancelamento de ruído',
            'JBL Go 3: caixas de som portáteis acessíveis',
            'PlayStation 5: jogos imersivos e gráficos incríveis',
            'Xbox Series X: potência e retrocompatibilidade',
            'Nintendo Switch: versatilidade e jogos exclusivos',
            'Dell UltraSharp: monitores profissionais'
        ],
        'tips': [
            'Verifique resolução e tecnologia de tela',
            'Avalie conectividade (HDMI, USB, Bluetooth)',
            'Considere tamanho adequado ao ambiente',
            'Verifique compatibilidade com outros dispositivos'
        ],
        'followups': [
            'Qual o tipo de produto?',
            'Marca e modelo?',
            'Tamanho da tela?',
            'Resolução?',
            'Conectividade?',
            'Estado de conservação?',
            'Acessórios incluídos?',
            'Preço aproximado?',
            'Uso principal (TV, jogos, trabalho)?',
            'Recursos especiais?',
            'Compatibilidade com outros dispositivos?'
        ]
    },
    'móvel': {
        'keywords': ['sofá', 'mesa', 'cadeira', 'cama', 'armário', 'estante', 'prateleira', 'rack', 'aparador', 'cômoda', 'poltrona'],
        'price_ranges': {'básico': 'R$ 100 - R$ 500', 'intermediário': 'R$ 500 - R$ 2.000', 'luxo': 'R$ 2.000 - R$ 10.000+', 'premium': 'R$ 10.000 - R$ 100.000+'},
        'recommendations': [
            'Madeira maciça: durabilidade e beleza natural',
            'MDF: custo-benefício e versatilidade',
            'Couro sintético: fácil manutenção',
            'Marcenaria local: personalização e qualidade',
            'IKEA: designs modernos e acessíveis',
            'Tok&Stok: móveis planejados',
            'Madeira certificada: sustentabilidade'
        ],
        'tips': [
            'Mede o espaço disponível antes da compra',
            'Verifique materiais e acabamento',
            'Considere montagem e desmontagem',
            'Avalie resistência e durabilidade',
            'Verifique se cabe nas portas/escadas'
        ],
        'followups': [
            'Qual o tipo de móvel?',
            'Material?',
            'Dimensões?',
            'Cor/estilo?',
            'Estado de conservação?',
            'Montagem necessária?',
            'Preço aproximado?',
            'Ambiente de uso?',
            'Estilo de decoração?',
            'Quantidade de peças?',
            'Material do estofamento?'
        ]
    },
    'livro': {
        'keywords': ['livro', 'revista', 'ebook', 'didático', 'romance', 'ficção', 'biografia', 'autoajuda', 'técnico'],
        'price_ranges': {'básico': 'R$ 10 - R$ 50', 'intermediário': 'R$ 50 - R$ 100', 'premium': 'R$ 100 - R$ 300+', 'colecionador': 'R$ 300 - R$ 10.000+'},
        'recommendations': [
            'Editora Companhia das Letras: qualidade literária',
            'Editora Intrínseca: best-sellers internacionais',
            'Editora Rocco: livros infantis e jovens',
            'Editora Saraiva: livros técnicos e didáticos',
            'Amazon Kindle: e-books acessíveis',
            'Livrarias Cultura: variedade e atendimento'
        ],
        'tips': [
            'Verifique edição e ano de publicação',
            'Avalie estado de conservação',
            'Considere resumos e críticas',
            'Verifique se é edição especial ou comum'
        ],
        'followups': [
            'Qual o título?',
            'Autor?',
            'Gênero?',
            'Editora?',
            'Ano de publicação?',
            'Estado de conservação?',
            'Edição?',
            'Preço aproximado?',
            'Motivo da venda/compra?'
        ]
    },
    'esporte': {
        'keywords': ['bola', 'raquete', 'bicicleta', 'equipamento', 'academia', 'corrida', 'futebol', 'basquete', 'tênis', 'natação'],
        'price_ranges': {'básico': 'R$ 20 - R$ 200', 'intermediário': 'R$ 200 - R$ 1.000', 'premium': 'R$ 1.000 - R$ 5.000+', 'profissional': 'R$ 5.000 - R$ 50.000+'},
        'recommendations': [
            'Nike: tênis e roupas esportivas de qualidade',
            'Adidas: equipamentos completos',
            'Puma: estilo e performance',
            'Under Armour: roupas técnicas',
            'Decathlon: acessórios acessíveis',
            'Centauro: variedade completa'
        ],
        'tips': [
            'Verifique tamanho e ajuste adequado',
            'Avalie materiais e durabilidade',
            'Considere uso específico',
            'Verifique certificações de qualidade'
        ],
        'followups': [
            'Qual o esporte?',
            'Qual o equipamento?',
            'Marca?',
            'Tamanho?',
            'Estado de conservação?',
            'Preço aproximado?',
            'Nível de uso (iniciante, intermediário, profissional)?',
            'Acessórios incluídos?'
        ]
    },
    'beleza': {
        'keywords': ['maquiagem', 'perfume', 'cosméticos', 'creme', 'shampoo', 'condicionador', 'hidratante', 'batom', 'sombra'],
        'price_ranges': {'básico': 'R$ 5 - R$ 50', 'intermediário': 'R$ 50 - R$ 200', 'luxo': 'R$ 200 - R$ 1.000+', 'premium': 'R$ 1.000 - R$ 10.000+'},
        'recommendations': [
            'MAC: maquiagem profissional',
            'NARS: cosméticos de alta qualidade',
            'The Body Shop: produtos naturais',
            'Avon: acessíveis e variados',
            'L\'Oréal: inovação e qualidade',
            'Maybelline: preços acessíveis',
            'Chanel: luxo e sofisticação'
        ],
        'tips': [
            'Verifique data de validade',
            'Teste amostras quando possível',
            'Considere tipo de pele/cabelo',
            'Verifique composição e alergênicos'
        ],
        'followups': [
            'Qual o produto?',
            'Marca?',
            'Tipo de pele/cabelo?',
            'Finalidade?',
            'Estado da embalagem?',
            'Preço aproximado?',
            'Data de validade?',
            'Quantidade?'
        ]
    },
    'instrumento': {
        'keywords': ['guitarra', 'violão', 'piano', 'teclado', 'bateria', 'microfone', 'amplificador', 'violino', 'flauta'],
        'price_ranges': {'básico': 'R$ 50 - R$ 500', 'intermediário': 'R$ 500 - R$ 2.000', 'profissional': 'R$ 2.000 - R$ 20.000+', 'premium': 'R$ 20.000 - R$ 100.000+'},
        'recommendations': [
            'Yamaha: qualidade e durabilidade',
            'Fender: guitarras icônicas',
            'Gibson: instrumentos premium',
            'Roland: teclados digitais',
            'Pearl: baterias profissionais',
            'Shure: microfones de estúdio'
        ],
        'tips': [
            'Teste o instrumento antes da compra',
            'Verifique afinação e regulagem',
            'Considere nível do usuário',
            'Avalie acessórios incluídos'
        ],
        'followups': [
            'Qual o instrumento?',
            'Marca?',
            'Modelo?',
            'Estado de conservação?',
            'Acessórios incluídos?',
            'Preço aproximado?',
            'Nível do usuário?',
            'Finalidade (profissional, hobby)?'
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

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'Texto vazio'}), 400

    suggestions = analyze_and_suggest(text)
    return jsonify({'suggestions': suggestions})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
