"""Seeds the database with initial data from supabase-schema-corrigido.sql."""

import json
import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings


PERGUNTAS_OPCOES = [
    {
        "id": "I01",
        "categoria": "Disponibilidade",
        "pergunta": "Em relação aos dados necessários para desempenhar minhas atividades, tenho acesso a:",
        "tipo": "radio",
        "opcoes": [{"valor": 0, "texto": "Parte deles"}, {"valor": 1, "texto": "Todos"}],
        "ordem": 1,
    },
    {
        "id": "I02",
        "categoria": "Disponibilidade",
        "pergunta": "Os dados que tenho acesso são consistentes, corretos e atendem às expectativas.",
        "tipo": "escala",
        "opcoes": [
            {"valor": 0, "texto": "Discordo totalmente"},
            {"valor": 1, "texto": "Discordo"},
            {"valor": 2, "texto": "Concordo"},
            {"valor": 3, "texto": "Concordo totalmente"},
        ],
        "ordem": 2,
    },
    {
        "id": "I03",
        "categoria": "Disponibilidade",
        "pergunta": "Os dados são atualizados e disponibilizados em tempo adequado para realizar o meu trabalho.",
        "tipo": "escala",
        "opcoes": [
            {"valor": 0, "texto": "Discordo totalmente"},
            {"valor": 1, "texto": "Discordo"},
            {"valor": 2, "texto": "Concordo"},
            {"valor": 3, "texto": "Concordo totalmente"},
        ],
        "ordem": 3,
    },
    {
        "id": "I04",
        "categoria": "Disponibilidade",
        "pergunta": "As ferramentas de análise de dados fornecidas pela empresa são adequadas para as análises que preciso realizar.",
        "tipo": "escala",
        "opcoes": [
            {"valor": 0, "texto": "Discordo totalmente"},
            {"valor": 1, "texto": "Discordo"},
            {"valor": 2, "texto": "Concordo"},
            {"valor": 3, "texto": "Concordo totalmente"},
        ],
        "ordem": 4,
    },
    {
        "id": "I05",
        "categoria": "Disponibilidade",
        "pergunta": "As ferramentas de dados disponibilizadas pela empresa são fáceis de serem utilizadas.",
        "tipo": "escala",
        "opcoes": [
            {"valor": 0, "texto": "Discordo totalmente"},
            {"valor": 1, "texto": "Discordo"},
            {"valor": 2, "texto": "Concordo"},
            {"valor": 3, "texto": "Concordo totalmente"},
        ],
        "ordem": 5,
    },
    {
        "id": "I06",
        "categoria": "Disponibilidade",
        "pergunta": "Quando temos problemas técnicos, o suporte técnico de dados e ferramentas é:",
        "tipo": "escala",
        "opcoes": [
            {"valor": 0, "texto": "Ineficaz"},
            {"valor": 1, "texto": "Pouco eficaz"},
            {"valor": 2, "texto": "Eficaz"},
            {"valor": 3, "texto": "Muito eficaz"},
        ],
        "ordem": 6,
    },
    {
        "id": "I07",
        "categoria": "Disponibilidade",
        "pergunta": "Posso contar com profissionais especializados para auxiliar, estruturar ou gerar os dados e análises necessários para o meu trabalho.",
        "tipo": "escala",
        "opcoes": [
            {"valor": 0, "texto": "Nunca"},
            {"valor": 1, "texto": "Poucas vezes"},
            {"valor": 2, "texto": "Na maioria das vezes"},
            {"valor": 3, "texto": "Sempre"},
        ],
        "ordem": 7,
    },
    {
        "id": "I08",
        "categoria": "Disponibilidade",
        "pergunta": "A documentação de como os dados são definidos, coletados e tratados facilita minha compreensão das métricas da empresa.",
        "tipo": "escala",
        "opcoes": [
            {"valor": 0, "texto": "Discordo totalmente"},
            {"valor": 1, "texto": "Discordo"},
            {"valor": 2, "texto": "Concordo"},
            {"valor": 3, "texto": "Concordo totalmente"},
        ],
        "ordem": 8,
    },
    {
        "id": "I09",
        "categoria": "Incentivo ao desenvolvimento",
        "pergunta": "Os treinamentos oferecidos pela empresa colaboram para que eu use mais os dados no meu dia a dia.",
        "tipo": "simNao",
        "opcoes": [{"valor": 0, "texto": "Não"}, {"valor": 1, "texto": "Sim"}],
        "ordem": 9,
    },
    {
        "id": "I10",
        "categoria": "Incentivo ao desenvolvimento",
        "pergunta": "A empresa incentiva o desenvolvimento de competências para gerar informações a partir dos dados.",
        "tipo": "simNao",
        "opcoes": [{"valor": 0, "texto": "Não"}, {"valor": 1, "texto": "Sim"}],
        "ordem": 10,
    },
    {
        "id": "I11",
        "categoria": "Incentivo ao desenvolvimento",
        "pergunta": "A empresa incentiva o desenvolvimento de técnicas de comunicação para apresentar análises, insights e informações obtidas pelos dados.",
        "tipo": "simNao",
        "opcoes": [{"valor": 0, "texto": "Não"}, {"valor": 1, "texto": "Sim"}],
        "ordem": 11,
    },
    {
        "id": "I12",
        "categoria": "Incentivo ao desenvolvimento",
        "pergunta": "A empresa incentiva a realização de testes para verificar hipóteses de negócios.",
        "tipo": "simNao",
        "opcoes": [{"valor": 0, "texto": "Não"}, {"valor": 1, "texto": "Sim"}],
        "ordem": 12,
    },
    {
        "id": "I13",
        "categoria": "Suporte da liderança",
        "pergunta": "Os líderes investem em profissionais qualificados para a realização das análises com base em dados.",
        "tipo": "escala",
        "opcoes": [
            {"valor": 0, "texto": "Nunca"},
            {"valor": 1, "texto": "Nem sempre"},
            {"valor": 2, "texto": "Sempre"},
        ],
        "ordem": 13,
    },
    {
        "id": "I14",
        "categoria": "Suporte da liderança",
        "pergunta": "Sei quais são os objetivos da empresa para o uso de dados.",
        "tipo": "simNao",
        "opcoes": [{"valor": 0, "texto": "Não"}, {"valor": 1, "texto": "Sim"}],
        "ordem": 14,
    },
    {
        "id": "I15",
        "categoria": "Benefícios individuais",
        "pergunta": "Tomo ações melhores e mais rápidas com o uso de dados da empresa.",
        "tipo": "simNao",
        "opcoes": [{"valor": 0, "texto": "Não"}, {"valor": 1, "texto": "Sim"}],
        "ordem": 15,
    },
    {
        "id": "I16",
        "categoria": "Benefícios individuais",
        "pergunta": "As informações geradas pelos dados têm resultado aplicável aos processos da empresa.",
        "tipo": "simNao",
        "opcoes": [{"valor": 0, "texto": "Não"}, {"valor": 1, "texto": "Sim"}],
        "ordem": 16,
    },
    {
        "id": "I17",
        "categoria": "Resultados para a empresa",
        "pergunta": "Meus líderes utilizam as informações geradas a partir dos dados para tomar decisões.",
        "tipo": "escala",
        "opcoes": [
            {"valor": 0, "texto": "Nunca"},
            {"valor": 1, "texto": "Nem sempre"},
            {"valor": 2, "texto": "Sempre"},
        ],
        "ordem": 17,
    },
    {
        "id": "I18",
        "categoria": "Resultados para a empresa",
        "pergunta": "Os líderes investem em profissionais qualificados para a realização das análises com base em dados.",
        "tipo": "escala",
        "opcoes": [
            {"valor": 0, "texto": "Nunca"},
            {"valor": 1, "texto": "Nem sempre"},
            {"valor": 2, "texto": "Sempre"},
        ],
        "ordem": 18,
    },
]

PREFERENCIAS_TEXTOS = [
    "Analistas de dados mais antigos devem atuar como agentes de mudança",
    "Contratar especialistas e fortalecer a equipe já existente",
    "Desenvolver competências em gestão, uso e compartilhamento de dados",
    "Estimular no setor a comunicação e abertura para novas ideias",
    "Alinhar as atuações e análises entre a área de negócio e o TI",
    "Promover uma alfabetização de dados e domínios em ferramentas de análise de dados",
    "Desenvolver políticas de valorização, atração e retenção",
    "Divulgar as relações intersetoriais dos dados na organização",
    "Estimular participação ativa dos colaboradores nos processo de decisão",
    "Promover o intercâmbio de conhecimentos, habilidades e experiências",
    "Lideranças devem superar suas resistências e antigas suposições",
    "Líderes devem compreender o valor dos dados",
    "Líderes devem promover confiança e credibilidade para as análises geradas",
    "Objetivos e princípios comuns para o uso de dados devem ser divulgados",
    "Líderes devem promover o uso sistemático de dados para suporte das decisões",
    "Vantagens e benefícios do uso de dados devem ser divulgados",
    "Uso de dados para suportar decisões deve ser recompensado",
    "Alocar recursos para desenvolver a infraestrutura e gerenciamento dos dados",
    "Divulgar visões inspiradoras sobre o uso de tecnologias orientada a dados",
    "Utilizar eventuais falhas como oportunidades de aprendizado e criação de novas rotinas",
    "Diferentes áreas devem colaborar para criar análises mais robustas",
    "Colaboradores devem compartilhar e utilizar dados de forma clara sobre seu propósito",
    "Novos métodos de trabalho e análise devem ser testados em um ambiente seguro",
    "Aprimorar a aplicação do conhecimento para resolução de problemas",
    "Especialistas devem demonstrar o valor dos dados e suas limitações",
    "Os dados devem ser vistos como insumo valioso e não como custo",
    "Uma ferramenta para autoatendimento em dados é necessária",
    "O papel estratégico dos dados deve ser alinhado com a missão, metas e processos",
    "A confiança nos resultados das análises deve ser vista como algo crítico e responsabilizável",
    "Explorar de forma proativa os dados e sugerir novas ideias",
    "Garantir acesso fácil a dados relevantes em toda a organização",
    "Conectar nas análises de dados múltiplos pontos da organização",
    "Ferramentas de visualização e fácil interpretação dos dados devem ser disponibilizadas",
    "Compreender como capturar e utilizar dados de forma integrada e eficiente",
    "Compreender as limitações e potenciais das tecnologias disponíveis na empresa",
    "Aceitar e implementar novas melhorias tecnológicas",
    "Comunicar claramente as mudanças em curso e os progressos alcançados",
    "Integrar a objetividade dos dados com a experiência dos tomadores de decisão",
    "Capacitar em comunicação para traduzir dados em informações de negócios",
    "Promover workshop e espaços de aprendizados sobre casos de sucesso",
    "Compartilhar relatos que resgatem historias, valores e práticas orientadas a dados",
    "Implementar procedimentos, regras e políticas sobre uso dos dados",
    "Estabelecer uma fonte segura e confiável de dados",
    "Medir e monitorar os resultados das análises de dados",
    "Implementar setor responsável pelas iniciativas e projetos relacionados a dados",
    "Definir um gestor responsável por propagar e facilitar o uso de dados nas análises",
]

PERGUNTAS_PREFERENCIAS = [
    {
        "id": f"P{ordem:02d}",
        "categoria": "Preferencias",
        "pergunta": pergunta,
        "tipo": "ranking",
        "opcoes": [],
        "peso": 3,
        "ordem": ordem,
    }
    for ordem, pergunta in enumerate(PREFERENCIAS_TEXTOS, start=1)
]

SETORES = [
    {"nome": "RH"},
    {"nome": "Financeiro"},
]


PERGUNTAS_CULTURA = [
    {
        "id": "C01",
        "categoria": "Características dominantes da empresa",
        "pergunta": "Como você percebe as características mais marcantes da empresa?",
        "tipo": "distribuicao_100",
        "opcoes": [
            {"codigo": "A", "perfil": "colaborar", "texto": "A empresa se parece com um ambiente próximo e humano. As pessoas se sentem parte de uma comunidade e compartilham bastante entre si."},
            {"codigo": "B", "perfil": "criar", "texto": "A empresa é dinâmica, empreendedora e aberta a novas possibilidades. As pessoas se sentem encorajadas a experimentar e assumir riscos."},
            {"codigo": "C", "perfil": "competir", "texto": "A empresa é fortemente orientada a resultados. O foco principal está em entregar, bater metas e alcançar alto desempenho."},
            {"codigo": "D", "perfil": "controlar", "texto": "A empresa é estruturada e controlada. Processos, normas e procedimentos orientam grande parte do trabalho."},
        ],
        "ordem": 1,
    },
    {
        "id": "C02",
        "categoria": "Liderança na empresa",
        "pergunta": "Como as lideranças e chefias são vistas na empresa por você e por seus colegas?",
        "tipo": "distribuicao_100",
        "opcoes": [
            {"codigo": "A", "perfil": "colaborar", "texto": "A liderança na empresa é geralmente considerada como um exemplo de mentoria, facilitação ou desenvolvimento de pessoas."},
            {"codigo": "B", "perfil": "criar", "texto": "A liderança na empresa é geralmente considerada como um exemplo de inovação, disposição para assumir riscos ou empreendedorismo."},
            {"codigo": "C", "perfil": "competir", "texto": "A liderança da empresa é geralmente considerada como um exemplo de uma postura agressiva para o sucesso, orientada para resultados e efeitos práticos de melhoria e resultado."},
            {"codigo": "D", "perfil": "controlar", "texto": "A liderança na empresa é geralmente considerada um exemplo de eficiência na coordenação, na empresa ou na garantia de um funcionamento harmonioso."},
        ],
        "ordem": 2,
    },
    {
        "id": "C03",
        "categoria": "Gestão dos colaboradores",
        "pergunta": "Como é a gestão dos colaboradores na empresa?",
        "tipo": "distribuicao_100",
        "opcoes": [
            {"codigo": "A", "perfil": "colaborar", "texto": "O estilo de gestão valoriza trabalho em equipe, participação, consenso e envolvimento das pessoas nas decisões."},
            {"codigo": "B", "perfil": "criar", "texto": "O estilo de gestão valoriza liberdade, autonomia, criatividade, iniciativa individual e formas diferentes de fazer as coisas."},
            {"codigo": "C", "perfil": "competir", "texto": "O estilo de gestão valoriza competitividade, alta exigência, foco em performance e busca constante por conquistas."},
            {"codigo": "D", "perfil": "controlar", "texto": "O estilo de gestão valoriza estabilidade, previsibilidade, segurança, conformidade e clareza nas relações de trabalho."},
        ],
        "ordem": 3,
    },
    {
        "id": "C04",
        "categoria": "O que mantém a empresa unida",
        "pergunta": "Como as pessoas são mantidas unidas, engajadas e trabalhando juntas em prol da empresa?",
        "tipo": "distribuicao_100",
        "opcoes": [
            {"codigo": "A", "perfil": "colaborar", "texto": "O que une a empresa é a lealdade e confiança mútua. Observo um algo comprometimento meu e dos meus colegas junto aos objetivos da empresa."},
            {"codigo": "B", "perfil": "criar", "texto": "O que une a empresa é o compromisso e preocupação em ser pioneiro e inovador. Observo em mim e nos meus colegas a preocupação de criar algo novo e melhor do que existe."},
            {"codigo": "C", "perfil": "competir", "texto": "O que une a empresa é a ênfase na realização e no cumprimento de metas. Observo em mim e nos meus colegas a preocupação em bater as metas, superar a concorrência e temos orgulho de fazer parte de uma equipe altamente vencedora e competitiva."},
            {"codigo": "D", "perfil": "controlar", "texto": "O que une a empresa são as regras e políticas formais. Observo em mim e nos meus colegas a preocupação de manter a empresa funcionando perfeitamente conforme foi definido nos procedimentos da empresa."},
        ],
        "ordem": 4,
    },
    {
        "id": "C05",
        "categoria": "Ênfases estratégicas",
        "pergunta": "Como a empresa prioriza seu foco, ações e investimentos?",
        "tipo": "distribuicao_100",
        "opcoes": [
            {"codigo": "A", "perfil": "colaborar", "texto": "A empresa enfatiza o desenvolvimento humano. Observo que a empresa investe no potencial humano dos colaboradores, na confiança e no bem-estar das equipes."},
            {"codigo": "B", "perfil": "criar", "texto": "A empresa enfatiza a aquisição de novos recursos e a criação de novos desafios. Observo que a empresa valoriza tentar coisas novas e prospectar oportunidades."},
            {"codigo": "C", "perfil": "competir", "texto": "A empresa enfatiza ações competitivas e realização. Observo que a empresa valoriza atingir metas ambiciosas e vencer no mercado."},
            {"codigo": "D", "perfil": "controlar", "texto": "A empresa enfatiza a permanência e a estabilidade. Observo que a empresa valoriza a eficiência, controle e operações fluidas."},
        ],
        "ordem": 5,
    },
    {
        "id": "C06",
        "categoria": "Critérios de sucesso",
        "pergunta": "Como a empresa define sucesso?",
        "tipo": "distribuicao_100",
        "opcoes": [
            {"codigo": "A", "perfil": "colaborar", "texto": "A empresa define o sucesso com base no desenvolvimento dos recursos humanos, no trabalho em equipe, no comprometimento dos colaboradores e na preocupação com as pessoas."},
            {"codigo": "B", "perfil": "criar", "texto": "A empresa define o sucesso com base em ter os produtos mais exclusivos ou mais novos. Ela é uma líder em produtos e inovadora."},
            {"codigo": "C", "perfil": "competir", "texto": "A empresa define o sucesso com base na vitória no mercado e em superar a concorrência. A liderança de mercado competitiva é fundamental."},
            {"codigo": "D", "perfil": "controlar", "texto": "A empresa define o sucesso com base na eficiência. Entrega confiável, cronogramas funcionando e produção de baixo custo são essenciais."},
        ],
        "ordem": 6,
    },
]


async def seed() -> None:
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        for s in SETORES:
            await conn.execute(
                text("INSERT INTO public.setores (nome) VALUES (:nome) ON CONFLICT DO NOTHING"),
                {"nome": s["nome"]},
            )

        for p in PERGUNTAS_OPCOES:
            await conn.execute(
                text("""
                    INSERT INTO public.perguntas_opcoes (id, categoria, pergunta, tipo, opcoes, ordem)
                    VALUES (:id, :categoria, :pergunta, :tipo, :opcoes, :ordem)
                    ON CONFLICT (id) DO UPDATE SET
                        categoria = EXCLUDED.categoria,
                        pergunta = EXCLUDED.pergunta,
                        tipo = EXCLUDED.tipo,
                        opcoes = EXCLUDED.opcoes,
                        ordem = EXCLUDED.ordem
                """),
                {
                    "id": p["id"],
                    "categoria": p["categoria"],
                    "pergunta": p["pergunta"],
                    "tipo": p["tipo"],
                    "opcoes": json.dumps(p["opcoes"]),
                    "ordem": p["ordem"],
                },
            )

        for p in PERGUNTAS_PREFERENCIAS:
            await conn.execute(
                text("""
                    INSERT INTO public.perguntas_preferencias (id, categoria, pergunta, tipo, opcoes, peso, ordem)
                    VALUES (:id, :categoria, :pergunta, :tipo, :opcoes, :peso, :ordem)
                    ON CONFLICT (id) DO UPDATE SET
                        categoria = EXCLUDED.categoria,
                        pergunta = EXCLUDED.pergunta,
                        tipo = EXCLUDED.tipo,
                        opcoes = EXCLUDED.opcoes,
                        peso = EXCLUDED.peso,
                        ordem = EXCLUDED.ordem
                """),
                {
                    "id": p["id"],
                    "categoria": p["categoria"],
                    "pergunta": p["pergunta"],
                    "tipo": p["tipo"],
                    "opcoes": json.dumps(p["opcoes"]),
                    "peso": p["peso"],
                    "ordem": p["ordem"],
                },
            )

        for p in PERGUNTAS_CULTURA:
            await conn.execute(
                text("""
                    INSERT INTO public.perguntas_cultura (id, categoria, pergunta, tipo, opcoes, ordem)
                    VALUES (:id, :categoria, :pergunta, :tipo, :opcoes, :ordem)
                    ON CONFLICT (id) DO UPDATE SET
                        categoria = EXCLUDED.categoria,
                        pergunta = EXCLUDED.pergunta,
                        tipo = EXCLUDED.tipo,
                        opcoes = EXCLUDED.opcoes,
                        ordem = EXCLUDED.ordem
                """),
                {
                    "id": p["id"],
                    "categoria": p["categoria"],
                    "pergunta": p["pergunta"],
                    "tipo": p["tipo"],
                    "opcoes": json.dumps(p["opcoes"]),
                    "ordem": p["ordem"],
                },
            )

    await engine.dispose()
    print("Seed concluido com sucesso.")


if __name__ == "__main__":
    asyncio.run(seed())
