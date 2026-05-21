from dataclasses import dataclass


@dataclass(frozen=True)
class Controle:
    id: str
    titulo: str
    descricao: str
    tema_id: str


TEMA_LABELS: dict[str, str] = {
    "org": "Organizacionais",
    "people": "Pessoas",
    "physical": "Físicos",
    "tech": "Tecnológicos",
}


_ORGANIZACIONAIS: list[Controle] = [
    Controle("5.1", "Políticas para segurança da informação", "Definir, aprovar, publicar e comunicar políticas de segurança da informação e tópicos relacionados.", "org"),
    Controle("5.2", "Funções e responsabilidades pela segurança da informação", "Definir e alocar funções e responsabilidades de segurança da informação conforme as necessidades da organização.", "org"),
    Controle("5.3", "Segregação de funções", "Segregar funções conflitantes e áreas de responsabilidade para reduzir oportunidades de modificação não autorizada ou uso indevido.", "org"),
    Controle("5.4", "Responsabilidades da direção", "A direção deve exigir que todo o pessoal aplique a segurança da informação de acordo com a política estabelecida.", "org"),
    Controle("5.5", "Contato com autoridades", "Estabelecer e manter contato com autoridades relevantes.", "org"),
    Controle("5.6", "Contato com grupos de interesse especial", "Manter contato com grupos de interesse especial, fóruns e associações profissionais de segurança.", "org"),
    Controle("5.7", "Inteligência de ameaças", "Coletar e analisar informações sobre ameaças à segurança para produzir inteligência de ameaças.", "org"),
    Controle("5.8", "Segurança da informação no gerenciamento de projetos", "Integrar a segurança da informação no gerenciamento de projetos.", "org"),
    Controle("5.9", "Inventário de informações e outros ativos associados", "Desenvolver e manter um inventário de informações e outros ativos, incluindo proprietários.", "org"),
    Controle("5.10", "Uso aceitável de informações e outros ativos associados", "Identificar, documentar e implementar regras para o uso aceitável e procedimentos para o manuseio dos ativos.", "org"),
    Controle("5.11", "Devolução de ativos", "O pessoal deve devolver todos os ativos da organização ao encerramento ou mudança do contrato.", "org"),
    Controle("5.12", "Classificação das informações", "Classificar informações conforme requisitos de segurança baseados em confidencialidade, integridade, disponibilidade e requisitos legais.", "org"),
    Controle("5.13", "Rotulagem de informações", "Desenvolver e implementar procedimentos para rotulagem de informações conforme o esquema de classificação.", "org"),
    Controle("5.14", "Transferência de informações", "Estabelecer regras, procedimentos ou acordos para transferência segura de informações.", "org"),
    Controle("5.15", "Controle de acesso", "Estabelecer e implementar regras de controle de acesso físico e lógico com base em requisitos de negócio e segurança.", "org"),
    Controle("5.16", "Gestão de identidade", "Gerenciar o ciclo de vida completo de identidades.", "org"),
    Controle("5.17", "Informações de autenticação", "Controlar a alocação e gestão de informações de autenticação por processo de gestão apropriado.", "org"),
    Controle("5.18", "Direitos de acesso", "Provisionar, revisar, modificar e remover direitos de acesso conforme política e regras de controle de acesso.", "org"),
    Controle("5.19", "Segurança da informação nas relações com fornecedores", "Definir e implementar processos para gerenciar riscos de segurança associados ao uso de produtos/serviços de fornecedores.", "org"),
    Controle("5.20", "Abordagem da segurança da informação nos contratos de fornecedores", "Estabelecer e acordar requisitos de segurança da informação com cada fornecedor conforme tipo de relação.", "org"),
    Controle("5.21", "Gestão da segurança da informação na cadeia de suprimentos de TIC", "Gerenciar riscos de segurança associados à cadeia de suprimentos de produtos e serviços de TIC.", "org"),
    Controle("5.22", "Monitoramento, análise crítica e gestão de mudanças dos serviços de fornecedores", "Monitorar, analisar criticamente, avaliar e gerenciar mudanças nas práticas de segurança dos fornecedores.", "org"),
    Controle("5.23", "Segurança da informação para uso de serviços em nuvem", "Estabelecer processos para aquisição, uso, gestão e saída de serviços em nuvem conforme requisitos de segurança.", "org"),
    Controle("5.24", "Planejamento e preparação da gestão de incidentes de segurança da informação", "Planejar e preparar a gestão de incidentes com processos, funções e responsabilidades.", "org"),
    Controle("5.25", "Avaliação e decisão sobre eventos de segurança da informação", "Avaliar eventos de segurança e decidir se devem ser categorizados como incidentes.", "org"),
    Controle("5.26", "Resposta a incidentes de segurança da informação", "Responder a incidentes conforme procedimentos documentados.", "org"),
    Controle("5.27", "Aprendendo com incidentes de segurança da informação", "Usar o conhecimento adquirido com incidentes para fortalecer e melhorar os controles.", "org"),
    Controle("5.28", "Coleta de evidências", "Estabelecer e implementar procedimentos para identificação, coleta, aquisição e preservação de evidências.", "org"),
    Controle("5.29", "Segurança da informação durante a disrupção", "Planejar como manter a segurança da informação em nível apropriado durante disrupções.", "org"),
    Controle("5.30", "Prontidão de TIC para continuidade de negócios", "Planejar, implementar, manter e testar a prontidão de TIC com base em objetivos de continuidade de negócios.", "org"),
    Controle("5.31", "Requisitos legais, estatutários, regulamentares e contratuais", "Identificar, documentar e manter atualizados requisitos legais, regulatórios e contratuais relevantes.", "org"),
    Controle("5.32", "Direitos de propriedade intelectual", "Implementar procedimentos apropriados para proteger direitos de propriedade intelectual.", "org"),
    Controle("5.33", "Proteção de registros", "Proteger registros contra perda, destruição, falsificação, acesso e divulgação não autorizados.", "org"),
    Controle("5.34", "Privacidade e proteção de DP (dados pessoais)", "Identificar e cumprir requisitos relativos à preservação da privacidade e proteção de dados pessoais.", "org"),
    Controle("5.35", "Análise crítica independente da segurança da informação", "Submeter a abordagem da organização para gestão da segurança a análise crítica independente em intervalos planejados.", "org"),
    Controle("5.36", "Conformidade com políticas, regras e normas para segurança da informação", "Analisar criticamente, de forma regular, a conformidade com a política, normas e padrões de segurança.", "org"),
    Controle("5.37", "Procedimentos operacionais documentados", "Documentar procedimentos operacionais para recursos de processamento de informações e disponibilizá-los ao pessoal.", "org"),
]


_PESSOAS: list[Controle] = [
    Controle("6.1", "Seleção", "Realizar verificações de antecedentes de candidatos antes da contratação, conforme leis e regulamentos aplicáveis.", "people"),
    Controle("6.2", "Termos e condições de contratação", "Os contratos com pessoal devem declarar responsabilidades de segurança da informação.", "people"),
    Controle("6.3", "Conscientização, educação e treinamento em segurança da informação", "Pessoal e partes interessadas devem receber treinamento e atualizações regulares de políticas e procedimentos.", "people"),
    Controle("6.4", "Processo disciplinar", "Formalizar e comunicar processo disciplinar para violações de segurança da informação.", "people"),
    Controle("6.5", "Responsabilidades após encerramento ou mudança da contratação", "Definir, comunicar e fazer cumprir responsabilidades de segurança que permanecem válidas após encerramento ou mudança.", "people"),
    Controle("6.6", "Acordos de confidencialidade ou não divulgação", "Identificar, documentar, revisar regularmente e assinar acordos de confidencialidade refletindo as necessidades da organização.", "people"),
    Controle("6.7", "Trabalho remoto", "Implementar medidas de segurança para acessar, processar ou armazenar informações fora das dependências da organização.", "people"),
    Controle("6.8", "Relato de eventos de segurança da informação", "Fornecer mecanismo para o pessoal relatar eventos de segurança observados ou suspeitos em tempo hábil.", "people"),
]


_FISICOS: list[Controle] = [
    Controle("7.1", "Perímetros de segurança física", "Definir e usar perímetros de segurança para proteger áreas que contenham informações e ativos.", "physical"),
    Controle("7.2", "Entrada física", "Áreas seguras devem ser protegidas por controles apropriados de entrada e pontos de acesso.", "physical"),
    Controle("7.3", "Segurança de escritórios, salas e instalações", "Projetar e implementar segurança física para escritórios, salas e instalações.", "physical"),
    Controle("7.4", "Monitoramento de segurança física", "Monitorar continuamente as instalações para detectar acesso físico não autorizado.", "physical"),
    Controle("7.5", "Proteção contra ameaças físicas e ambientais", "Projetar e implementar proteção contra ameaças físicas e ambientais (naturais ou intencionais).", "physical"),
    Controle("7.6", "Trabalho em áreas seguras", "Projetar e implementar medidas de segurança para trabalho em áreas seguras.", "physical"),
    Controle("7.7", "Mesa limpa e tela limpa", "Definir e fazer cumprir regras de mesa limpa para papéis/mídia e tela limpa para recursos de processamento.", "physical"),
    Controle("7.8", "Localização e proteção de equipamentos", "Localizar equipamentos com segurança e protegê-los.", "physical"),
    Controle("7.9", "Segurança de ativos fora das instalações", "Proteger ativos que estejam fora das instalações da organização.", "physical"),
    Controle("7.10", "Mídia de armazenamento", "Gerenciar mídias de armazenamento por todo o ciclo de vida conforme a classificação e requisitos de manuseio.", "physical"),
    Controle("7.11", "Serviços de infraestrutura", "Proteger recursos de processamento contra falhas em serviços de infraestrutura (energia, telecomunicações, água).", "physical"),
    Controle("7.12", "Segurança do cabeamento", "Proteger cabos de energia e telecomunicações contra interceptação, interferência ou danos.", "physical"),
    Controle("7.13", "Manutenção de equipamentos", "Manter equipamentos corretamente para assegurar disponibilidade, integridade e confidencialidade.", "physical"),
    Controle("7.14", "Descarte seguro ou reutilização de equipamentos", "Verificar equipamentos antes do descarte ou reutilização para garantir remoção de dados sensíveis e licenças.", "physical"),
]


_TECNOLOGICOS: list[Controle] = [
    Controle("8.1", "Dispositivos endpoint do usuário", "Proteger informações armazenadas, processadas ou acessadas em dispositivos endpoint.", "tech"),
    Controle("8.2", "Direitos de acesso privilegiados", "Restringir e gerenciar a alocação e uso de direitos de acesso privilegiados.", "tech"),
    Controle("8.3", "Restrição de acesso à informação", "Restringir o acesso a informações e funções de sistemas de aplicação conforme a política de controle de acesso.", "tech"),
    Controle("8.4", "Acesso ao código-fonte", "Gerenciar adequadamente o acesso ao código-fonte, ferramentas de desenvolvimento e bibliotecas.", "tech"),
    Controle("8.5", "Autenticação segura", "Implementar tecnologias e procedimentos de autenticação segura com base em restrições e política de controle de acesso.", "tech"),
    Controle("8.6", "Gestão de capacidade", "Monitorar e ajustar a utilização de recursos para garantir o desempenho requerido.", "tech"),
    Controle("8.7", "Proteção contra malware", "Implementar proteção contra malware apoiada por adequada conscientização do usuário.", "tech"),
    Controle("8.8", "Gestão de vulnerabilidades técnicas", "Obter informações sobre vulnerabilidades técnicas, avaliar exposição e tomar medidas apropriadas.", "tech"),
    Controle("8.9", "Gestão de configuração", "Estabelecer, documentar, implementar, monitorar e analisar criticamente configurações, incluindo de segurança.", "tech"),
    Controle("8.10", "Exclusão de informações", "Excluir informações armazenadas em sistemas, dispositivos ou outras mídias quando não mais necessárias.", "tech"),
    Controle("8.11", "Mascaramento de dados", "Usar mascaramento de dados conforme política de controle de acesso e demais políticas relevantes.", "tech"),
    Controle("8.12", "Prevenção de vazamento de dados", "Aplicar medidas de prevenção de vazamento de dados a sistemas, redes e dispositivos que processem informações sensíveis.", "tech"),
    Controle("8.13", "Backup de informações", "Manter e testar regularmente cópias de backup de informações, software e sistemas.", "tech"),
    Controle("8.14", "Redundância das instalações de processamento da informação", "Implementar redundância suficiente para atender requisitos de disponibilidade.", "tech"),
    Controle("8.15", "Log", "Produzir, armazenar, proteger e analisar logs que registrem atividades, exceções, falhas e eventos.", "tech"),
    Controle("8.16", "Atividades de monitoramento", "Monitorar redes, sistemas e aplicações em busca de comportamento anômalo e tomar ações apropriadas.", "tech"),
    Controle("8.17", "Sincronização dos relógios", "Sincronizar relógios de sistemas usados pela organização com fontes de tempo aprovadas.", "tech"),
    Controle("8.18", "Uso de programas utilitários privilegiados", "Restringir e controlar rigorosamente o uso de programas utilitários capazes de burlar controles do sistema.", "tech"),
    Controle("8.19", "Instalação de software em sistemas operacionais", "Implementar procedimentos e medidas para gerenciar instalação de software em sistemas operacionais.", "tech"),
    Controle("8.20", "Segurança de redes", "Proteger, gerenciar e controlar redes para salvaguardar informações em sistemas e aplicações.", "tech"),
    Controle("8.21", "Segurança dos serviços de rede", "Identificar, implementar e monitorar mecanismos de segurança, níveis de serviço e requisitos para serviços de rede.", "tech"),
    Controle("8.22", "Segregação de redes", "Segregar grupos de serviços, usuários e sistemas de informação em redes.", "tech"),
    Controle("8.23", "Filtragem da web", "Gerenciar acesso a sites externos para reduzir exposição a conteúdo malicioso.", "tech"),
    Controle("8.24", "Uso de criptografia", "Definir e implementar regras para uso efetivo de criptografia, incluindo gestão de chaves criptográficas.", "tech"),
    Controle("8.25", "Ciclo de vida de desenvolvimento seguro", "Estabelecer e aplicar regras para desenvolvimento seguro de software e sistemas.", "tech"),
    Controle("8.26", "Requisitos de segurança da aplicação", "Identificar, especificar e aprovar requisitos de segurança ao desenvolver ou adquirir aplicações.", "tech"),
    Controle("8.27", "Princípios de arquitetura e engenharia de sistemas seguros", "Estabelecer, documentar, manter e aplicar princípios de engenharia de sistemas seguros.", "tech"),
    Controle("8.28", "Codificação segura", "Aplicar princípios de codificação segura ao desenvolvimento de software.", "tech"),
    Controle("8.29", "Testes de segurança em desenvolvimento e aceitação", "Definir e implementar processos de teste de segurança no ciclo de vida de desenvolvimento.", "tech"),
    Controle("8.30", "Desenvolvimento terceirizado", "Direcionar, monitorar e analisar criticamente atividades de desenvolvimento terceirizado.", "tech"),
    Controle("8.31", "Separação dos ambientes de desenvolvimento, teste e produção", "Separar e proteger ambientes de desenvolvimento, teste e produção.", "tech"),
    Controle("8.32", "Gestão de mudanças", "Submeter mudanças em recursos de processamento e sistemas a procedimentos de gestão de mudanças.", "tech"),
    Controle("8.33", "Informações de teste", "Selecionar, proteger e gerenciar adequadamente informações usadas para teste.", "tech"),
    Controle("8.34", "Proteção de sistemas de informação durante testes de auditoria", "Planejar e acordar testes de auditoria envolvendo sistemas operacionais entre o auditor e a direção.", "tech"),
]


TEMAS: dict[str, list[Controle]] = {
    "org": _ORGANIZACIONAIS,
    "people": _PESSOAS,
    "physical": _FISICOS,
    "tech": _TECNOLOGICOS,
}


TODOS_CONTROLES: list[Controle] = [c for grupo in TEMAS.values() for c in grupo]

assert len(TODOS_CONTROLES) == 93, f"Esperado 93 controles, encontrado {len(TODOS_CONTROLES)}"
