from core.types import ItemDiagnostico

MODULO_ID = "iso27701"


CATEGORIAS: dict[str, str] = {
    "A.1.2": "A.1.2 Condições para coleta e tratamento (Controlador)",
    "A.1.3": "A.1.3 Obrigações com os titulares de DP (Controlador)",
    "A.1.4": "A.1.4 Privacidade por design e por default (Controlador)",
    "A.1.5": "A.1.5 Compartilhamento, transferência e divulgação (Controlador)",
    "A.2.2": "A.2.2 Condições para coleta e tratamento (Operador)",
    "A.2.3": "A.2.3 Obrigações com os titulares de DP (Operador)",
    "A.2.4": "A.2.4 Privacidade por design e por default (Operador)",
    "A.2.5": "A.2.5 Compartilhamento, transferência e divulgação (Operador)",
    "A.3": "A.3 Segurança da informação para tratamento de DP (Controlador + Operador)",
}


def _lgpd_sufixo(lgpd: list[str] | None) -> str:
    """Formata a lista de artigos LGPD como sufixo legível para a descrição.

    Retorna string vazia quando não há mapeamento. Centraliza o formato
    ` · LGPD <art1>, <art2>` em um único lugar.
    """
    if not lgpd:
        return ""
    return f" · LGPD {', '.join(lgpd)}"


def _c(cid: str, titulo: str, descricao: str, lgpd: list[str] | None = None) -> ItemDiagnostico:
    """Cria um `ItemDiagnostico` derivando a categoria do `cid` e anexando o sufixo LGPD à descrição."""
    partes = cid.split(".")
    cat = ".".join(partes[:2]) if cid.startswith("A.3") else ".".join(partes[:3])
    desc = descricao + _lgpd_sufixo(lgpd)
    return ItemDiagnostico(id=cid, titulo=titulo, descricao=desc, categoria_id=cat, modulo=MODULO_ID)


CONTROLES: list[ItemDiagnostico] = [
    # A.1.2 — Controlador — Condições para coleta e tratamento
    _c(
        "A.1.2.2",
        "Identificação e documentação do propósito",
        "A organização deve identificar e documentar os propósitos específicos pelos quais os DP serão tratados.",
        ["Art. 6º II, V", "Art. 9º"],
    ),
    _c(
        "A.1.2.3",
        "Identificação de bases legais",
        "A organização deve determinar, documentar e ser capaz de demonstrar compliance com a base legal pertinente para o tratamento de DP para os propósitos identificados.",
        ["Art. 7º", "Art. 11"],
    ),
    _c(
        "A.1.2.4",
        "Determinação de quando e como o consentimento deve ser obtido",
        "A organização deve determinar e documentar um processo pelo qual ela pode demonstrar se, quando e como o consentimento para tratamento de DP foi obtido dos titulares de DP.",
        ["Art. 8º"],
    ),
    _c(
        "A.1.2.5",
        "Obtenção e registro do consentimento",
        "A organização deve obter e registrar o consentimento dos titulares de DP de acordo com os processos documentados.",
        ["Art. 8º §1º"],
    ),
    _c(
        "A.1.2.6",
        "Avaliação de impacto de privacidade",
        "A organização deve avaliar a necessidade de, e implementar onde apropriado, uma avaliação de impacto de privacidade sempre que um novo tratamento de DP ou mudanças no tratamento existente forem planejadas.",
        ["Art. 38"],
    ),
    _c(
        "A.1.2.7",
        "Contratos com operadores de DP",
        "A organização deve ter um contrato escrito com qualquer operador de DP que ela utilize e deve assegurar que seus contratos contemplem a implementação dos controles apropriados no Anexo A (Tabela A.2).",
        ["Art. 39"],
    ),
    _c(
        "A.1.2.8",
        "Controlador conjunto de DP",
        "A organização deve determinar os respectivos papéis e responsabilidades para o tratamento de DP (incluindo requisitos de proteção e segurança) com qualquer controlador conjunto de DP.",
        ["Art. 5º VI"],
    ),
    _c(
        "A.1.2.9",
        "Registros relacionados ao tratamento de DP",
        "A organização deve determinar e manter, de forma segura, os registros necessários ao suporte às suas obrigações para o tratamento de DP.",
        ["Art. 37"],
    ),
    # A.1.3 — Controlador — Obrigações com titulares
    _c(
        "A.1.3.2",
        "Determinação e cumprimento de obrigações com os titulares de DP",
        "A organização deve determinar e documentar suas obrigações legais, regulatórias e de negócios com os titulares de DP, relacionadas ao tratamento de seus DP, e fornecer meios para atender a essas obrigações.",
        ["Art. 17", "Art. 18"],
    ),
    _c(
        "A.1.3.3",
        "Determinação das informações para os titulares de DP",
        "A organização deve determinar e documentar a informação a ser fornecida aos titulares de DP relacionadas ao tratamento de seus DP e o momento de tal disponibilização.",
        ["Art. 9º"],
    ),
    _c(
        "A.1.3.4",
        "Fornecimento de informações aos titulares de DP",
        "A organização deve fornecer aos titulares de DP, de forma clara e facilmente acessível, informações que identifiquem o controlador de DP e descrevam o tratamento de seus DP.",
        ["Art. 6º VI", "Art. 9º"],
    ),
    _c(
        "A.1.3.5",
        "Fornecimento de mecanismo para modificar ou retirar o consentimento",
        "A organização deve fornecer um mecanismo para que os titulares de DP modifiquem ou retirem os seus consentimentos.",
        ["Art. 8º §5º"],
    ),
    _c(
        "A.1.3.6",
        "Fornecimento de mecanismo para se opor ao tratamento de DP",
        "A organização deve fornecer um mecanismo para os titulares de DP se oporem ao tratamento de seus DP.",
        ["Art. 18 §2º"],
    ),
    _c(
        "A.1.3.7",
        "Acesso, correção ou exclusão",
        "A organização deve implementar políticas, procedimentos ou mecanismos para atender às suas obrigações com os titulares de DP para acessarem, corrigirem ou excluírem seus DP.",
        ["Art. 18 I-VI"],
    ),
    _c(
        "A.1.3.8",
        "Obrigações dos controladores para informar aos terceiros",
        "A organização deve informar aos terceiros com os quais DP tenham sido compartilhados sobre qualquer modificação, retirada ou oposição pertinente aos DP, e implementar políticas, procedimentos ou mecanismos apropriados.",
        ["Art. 18 §6º"],
    ),
    _c(
        "A.1.3.9",
        "Fornecimento de cópia dos DP tratados",
        "A organização deve ser capaz de fornecer uma cópia dos DP que são tratados, quando requerida pelo titular de DP.",
        ["Art. 18 II, V"],
    ),
    _c(
        "A.1.3.10",
        "Tratamento de solicitações",
        "A organização deve definir e documentar políticas e procedimentos para tratamento e resposta a solicitações legítimas dos titulares de DP.",
        ["Art. 18 §1º"],
    ),
    _c(
        "A.1.3.11",
        "Tomada de decisão automatizada",
        "A organização deve identificar obrigações, incluindo legais, com os titulares de DP, resultantes de decisões baseadas exclusivamente em tratamento automatizado de DP, e demonstrar como atende a essas obrigações.",
        ["Art. 20"],
    ),
    # A.1.4 — Controlador — Privacidade por design e by default
    _c(
        "A.1.4.2",
        "Limitação da coleta",
        "A organização deve limitar a coleta de DP ao mínimo que seja pertinente, proporcional e necessário para os propósitos identificados.",
        ["Art. 6º III"],
    ),
    _c(
        "A.1.4.3",
        "Limitação do tratamento",
        "A organização deve limitar o tratamento de DP ao que seja adequado, pertinente e necessário para os propósitos identificados.",
        ["Art. 6º III"],
    ),
    _c(
        "A.1.4.4",
        "Precisão e qualidade",
        "A organização deve assegurar e documentar que os DP sejam precisos, completos e atualizados, quando necessário, para os propósitos para os quais são tratados, ao longo do ciclo de vida dos DP.",
        ["Art. 6º V"],
    ),
    _c(
        "A.1.4.5",
        "Objetivos de minimização de DP",
        "A organização deve definir e documentar objetivos de minimização de dados e quais mecanismos (como desidentificação) são usados para alcançar aqueles objetivos.",
        ["Art. 6º III"],
    ),
    _c(
        "A.1.4.6",
        "Desidentificação e exclusão de DP ao final do tratamento",
        "A organização deve excluir os DP ou entregá-los em uma forma que não permita identificação ou reidentificação, tão logo os DP originais não sejam mais necessários.",
        ["Art. 16"],
    ),
    _c(
        "A.1.4.7",
        "Arquivos temporários",
        "A organização deve assegurar que arquivos temporários criados como resultado do tratamento de DP sejam descartados seguindo procedimentos documentados dentro de um período de tempo especificado.",
        ["Art. 16"],
    ),
    _c(
        "A.1.4.8",
        "Retenção",
        "A organização não pode reter DP por período superior ao que seja necessário para os propósitos para os quais os DP sejam tratados.",
        ["Art. 16"],
    ),
    _c(
        "A.1.4.9",
        "Descarte",
        "A organização deve ter políticas, procedimentos ou mecanismos documentados para o descarte de DP.",
        ["Art. 16"],
    ),
    _c(
        "A.1.4.10",
        "Controles de transmissão de DP",
        "A organização deve submeter DP transmitidos por meio de rede aos controles apropriados projetados para assegurar que os dados cheguem ao seu destino pretendido.",
        ["Art. 46"],
    ),
    # A.1.5 — Controlador — Compartilhamento, transferência e divulgação
    _c(
        "A.1.5.2",
        "Identificação das bases para transferências de DP entre as jurisdições",
        "A organização deve identificar e documentar as bases pertinentes para transferências de DP entre as jurisdições.",
        ["Art. 33"],
    ),
    _c(
        "A.1.5.3",
        "Países e organizações internacionais para os quais os DP podem ser transferidos",
        "A organização deve especificar e documentar os países e organizações internacionais para os quais os DP podem ser transferidos.",
        ["Art. 33"],
    ),
    _c(
        "A.1.5.4",
        "Registros de transferência de DP",
        "A organização deve registrar transferências de DP para ou de terceiros e assegurar cooperação com aqueles terceiros para apoiar requisições relacionadas com as obrigações com os titulares de DP.",
        ["Art. 37", "Art. 33"],
    ),
    _c(
        "A.1.5.5",
        "Registros de divulgação de DP a terceiros",
        "A organização deve registrar as divulgações de DP para terceiros, incluindo quais DP foram divulgados, para quem e em que momento.",
        ["Art. 37"],
    ),
    # A.2.2 — Operador — Condições para coleta e tratamento
    _c(
        "A.2.2.2",
        "Acordo com o cliente",
        "A organização deve assegurar, onde pertinente, que o contrato para tratar os DP aborde o papel da organização em prestar assistência nas obrigações do cliente.",
        ["Art. 39"],
    ),
    _c(
        "A.2.2.3",
        "Propósitos da organização",
        "A organização deve assegurar que os DP tratados em nome de um cliente sejam tratados apenas para os propósitos expressos nas instruções documentadas do cliente.",
        ["Art. 39"],
    ),
    _c(
        "A.2.2.4",
        "Uso para marketing e propaganda",
        "A organização não pode usar os DP tratados sob um contrato para finalidades de marketing e propaganda sem estabelecer que o consentimento prévio foi obtido do respectivo titular de DP.",
        ["Art. 8º", "Art. 39"],
    ),
    _c(
        "A.2.2.5",
        "Instruções infratoras",
        "A organização deve informar ao cliente se, em sua opinião, uma instrução de tratamento infringe requisitos legais aplicáveis.",
        ["Art. 39"],
    ),
    _c(
        "A.2.2.6",
        "Obrigações do cliente",
        "A organização deve fornecer ao cliente informações apropriadas para que o cliente possa demonstrar compliance com suas obrigações.",
    ),
    _c(
        "A.2.2.7",
        "Registros relativos ao tratamento de DP",
        "A organização deve determinar e manter os registros necessários em apoio à demonstração de compliance com suas obrigações para o tratamento de DP conduzido em nome de um cliente.",
        ["Art. 37"],
    ),
    # A.2.3 — Operador — Obrigações com titulares
    _c(
        "A.2.3.2",
        "Compliance com obrigações com os titulares de DP",
        "A organização deve fornecer ao cliente os meios para estar em compliance com suas obrigações com os titulares de DP.",
        ["Art. 18"],
    ),
    # A.2.4 — Operador — Privacidade por design
    _c(
        "A.2.4.2",
        "Arquivos temporários",
        "A organização deve assegurar que arquivos temporários criados como resultado do tratamento de DP sejam descartados seguindo procedimentos documentados dentro de um período de tempo especificado.",
        ["Art. 16"],
    ),
    _c(
        "A.2.4.3",
        "Devolução, transferência ou descarte de DP",
        "A organização deve ser capaz de devolver, transferir ou descartar DP de forma segura. Ela deve também tornar sua política disponível para o cliente.",
        ["Art. 16", "Art. 39"],
    ),
    _c(
        "A.2.4.4",
        "Controles de transmissão de DP",
        "A organização deve submeter os DP transmitidos por meio de rede aos controles apropriados, projetados para assegurar que os dados cheguem ao seu destino pretendido.",
        ["Art. 46"],
    ),
    # A.2.5 — Operador — Compartilhamento, transferência e divulgação
    _c(
        "A.2.5.2",
        "Fundamentação para a transferência de DP entre as jurisdições",
        "A organização deve informar ao cliente de forma oportuna a fundamentação para as transferências de DP entre jurisdições e quaisquer alterações pretendidas.",
        ["Art. 33"],
    ),
    _c(
        "A.2.5.3",
        "Países e organizações internacionais para os quais os DP podem ser transferidos",
        "A organização deve especificar e documentar os países e organizações internacionais para os quais os DP podem ser transferidos.",
    ),
    _c(
        "A.2.5.4",
        "Registros de divulgações de DP a terceiros",
        "A organização deve registrar divulgações de DP para terceiros, incluindo quais DP foram divulgados, para quem e em que momento.",
        ["Art. 37"],
    ),
    _c(
        "A.2.5.5",
        "Notificação de solicitações de divulgação de DP",
        "A organização deve notificar o cliente de quaisquer solicitações legalmente obrigatórias de divulgação de DP.",
    ),
    _c(
        "A.2.5.6",
        "Divulgações de DP legalmente obrigatórias",
        "A organização deve rejeitar quaisquer solicitações de divulgação de DP que não sejam legalmente obrigatórias, consultar o cliente correspondente antes de realizar qualquer divulgação.",
    ),
    _c(
        "A.2.5.7",
        "Divulgação de subcontratados utilizados para tratar DP",
        "Antes da utilização, a organização deve informar ao cliente se algum subcontratado é utilizado para tratar DP.",
        ["Art. 39"],
    ),
    _c(
        "A.2.5.8",
        "Envolvimento de subcontratado para tratar os DP",
        "A organização somente deve envolver um subcontratado para tratar os DP conforme previsto no contrato com o cliente.",
        ["Art. 39"],
    ),
    _c(
        "A.2.5.9",
        "Troca de subcontratado para tratar os DP",
        "A organização deve, no caso de haver autorização geral por escrito, informar o cliente sobre quaisquer alterações pretendidas relativas à inclusão ou substituição de subcontratados.",
        ["Art. 39"],
    ),
    # A.3 — Considerações de segurança para controladores e operadores
    _c(
        "A.3.3",
        "Políticas de segurança da informação",
        "As políticas de segurança da informação relacionadas ao tratamento de DP devem ser definidas, aprovadas pela direção, publicadas, comunicadas e analisadas criticamente em intervalos planejados.",
        ["Art. 46"],
    ),
    _c(
        "A.3.4",
        "Papéis e responsabilidades em segurança da informação",
        "Os papéis e responsabilidades relacionados à segurança da informação no tratamento de DP devem ser definidos e alocados de acordo com as necessidades organizacionais.",
        ["Art. 41"],
    ),
    _c(
        "A.3.5",
        "Classificação da informação",
        "A informação deve ser classificada de acordo com as necessidades de segurança da informação da organização, levando em consideração os DP, com base na confidencialidade, integridade, disponibilidade e nos requisitos das partes interessadas.",
    ),
    _c(
        "A.3.6",
        "Rotulagem da informação",
        "Um conjunto apropriado de procedimentos para rotulagem da informação, que considere os DP, deve ser desenvolvido e implementado de acordo com o esquema de classificação adotado pela organização.",
    ),
    _c(
        "A.3.7",
        "Transferência de informação",
        "Regras, procedimentos ou acordos de transferência de informação relacionados ao tratamento de DP devem ser estabelecidos para todos os tipos de meios de transferência.",
        ["Art. 46"],
    ),
    _c(
        "A.3.8",
        "Gestão de identidade",
        "O ciclo de vida completo das identidades relacionadas ao tratamento de DP deve ser gerenciado.",
    ),
    _c(
        "A.3.9",
        "Direitos de acesso",
        "Os direitos de acesso aos DP e a outros ativos associados ao tratamento de DP devem ser provisionados, analisados criticamente, modificados e removidos de acordo com a política específica por tema da organização e com as regras de controle de acesso.",
        ["Art. 46"],
    ),
    _c(
        "A.3.10",
        "Abordagem da segurança da informação nos contratos de fornecedores",
        "Requisitos pertinentes de segurança da informação relacionados ao tratamento de DP devem ser estabelecidos e acordados com cada fornecedor, com base no tipo de relacionamento.",
        ["Art. 39"],
    ),
    _c(
        "A.3.11",
        "Planejamento e preparação para gestão de incidentes de segurança da informação",
        "A organização deve planejar e se preparar para a gestão de incidentes de segurança da informação relacionados ao tratamento de DP, definindo processos, papéis e responsabilidades.",
        ["Art. 48"],
    ),
    _c(
        "A.3.12",
        "Resposta a incidentes de segurança da informação",
        "As respostas a incidentes de segurança da informação relacionados ao tratamento de DP devem ser de acordo com os procedimentos documentados.",
        ["Art. 48"],
    ),
    _c(
        "A.3.13",
        "Requisitos legais, estatutários, regulatórios e contratuais",
        "Requisitos legais, estatutários, regulatórios e contratuais pertinentes à segurança da informação, relacionados ao tratamento de DP, e a abordagem da organização para cumpri-los, devem ser documentados e mantidos atualizados.",
        ["Art. 6º", "Art. 7º"],
    ),
    _c(
        "A.3.14",
        "Proteção de registros",
        "Registros relacionados ao tratamento de DP devem ser protegidos contra perda, destruição, falsificação, acesso não autorizado e divulgação não autorizada.",
    ),
    _c(
        "A.3.15",
        "Análise crítica independente da segurança da informação",
        "A abordagem da organização para gerenciar a segurança da informação relacionada ao tratamento de DP e sua implementação deve ser analisada criticamente de forma independente em intervalos planejados, ou quando ocorrerem mudanças significativas.",
    ),
    _c(
        "A.3.16",
        "Compliance com políticas, regras e normas de segurança da informação",
        "O compliance com a política de segurança da informação, políticas específicas, regras e normas relacionadas ao tratamento de DP deve ser regularmente analisado criticamente.",
    ),
    _c(
        "A.3.17",
        "Conscientização, educação e treinamento em segurança da informação",
        "O pessoal e as partes interessadas pertinentes devem receber conscientização, educação e treinamento apropriados em segurança da informação, conforme pertinente às suas funções no tratamento de DP.",
    ),
    _c(
        "A.3.18",
        "Acordos de confidencialidade ou não divulgação",
        "Os acordos de confidencialidade ou não divulgação que reflitam as necessidades da organização quanto à proteção de DP devem ser identificados, documentados, analisados criticamente regularmente e assinados pelos funcionários e outras partes pertinentes.",
    ),
    _c(
        "A.3.19",
        "Mesa limpa e tela limpa",
        "Regras de mesa limpa para documentos em papel e mídias removíveis e regras de tela limpa para instalações de processamento devem ser definidas e aplicadas adequadamente.",
    ),
    _c(
        "A.3.20",
        "Mídias de armazenamento",
        "Mídias de armazenamento contendo DP devem ser gerenciadas durante seu ciclo de vida de aquisição, uso, transporte e descarte, de acordo com o esquema de classificação e requisitos de manuseio.",
        ["Art. 16"],
    ),
    _c(
        "A.3.21",
        "Descarte seguro ou reutilização de equipamentos",
        "Itens dos equipamentos que contenham mídias com DP devem ser verificados para assegurar que quaisquer dados sensíveis e softwares licenciados tenham sido removidos ou sobrescritos de forma segura previamente ao descarte ou à reutilização.",
        ["Art. 16"],
    ),
    _c(
        "A.3.22",
        "Dispositivos endpoint do usuário",
        "DP armazenados, processados ou acessíveis por meio de dispositivos endpoint do usuário devem ser protegidos.",
    ),
    _c(
        "A.3.23",
        "Autenticação segura",
        "Tecnologias e procedimentos de autenticação segura relacionados ao tratamento de DP devem ser implementados com base em restrições de acesso à informação.",
    ),
    _c(
        "A.3.24",
        "Backup das informações",
        "O backup de DP, bem como de softwares e sistemas relacionados ao tratamento de DP, devem ser mantidos e testados regularmente.",
    ),
    _c(
        "A.3.25",
        "Log",
        "Logs que registrem atividades, exceções, falhas e outros eventos relevantes relacionados ao tratamento de DP devem ser produzidos, armazenados, protegidos e analisados.",
    ),
    _c(
        "A.3.26",
        "Uso de criptografia",
        "Regras para o uso efetivo de criptografia relacionada ao tratamento de DP, incluindo gerenciamento de chaves criptográficas, devem ser definidas e implementadas.",
        ["Art. 46"],
    ),
    _c(
        "A.3.27",
        "Ciclo de vida de desenvolvimento seguro",
        "Regras para o desenvolvimento seguro de software e sistemas relacionados ao tratamento de DP devem ser estabelecidas e aplicadas.",
    ),
    _c(
        "A.3.28",
        "Requisitos de segurança da aplicação",
        "Requisitos de segurança da informação relacionados ao tratamento de DP devem ser identificados, especificados e aprovados ao desenvolver ou adquirir aplicações.",
    ),
    _c(
        "A.3.29",
        "Princípios de arquitetura e engenharia de sistemas seguros",
        "Princípios para engenharia de sistemas seguros relacionados ao tratamento de DP devem ser estabelecidos, documentados, mantidos e aplicados a quaisquer atividades de desenvolvimento.",
    ),
    _c(
        "A.3.30",
        "Desenvolvimento terceirizado",
        "A organização deve dirigir, monitorar e analisar criticamente as atividades relacionadas à terceirização de desenvolvimento de sistemas de tratamento de DP.",
    ),
    _c(
        "A.3.31",
        "Informações de teste",
        "Informações de teste relacionadas ao tratamento de DP devem ser selecionadas, protegidas e gerenciadas adequadamente.",
    ),
]


CONTROLES_POR_CATEGORIA: dict[str, list[ItemDiagnostico]] = {cat: [c for c in CONTROLES if c.categoria_id == cat] for cat in CATEGORIAS}


assert len(CONTROLES) == sum(len(v) for v in CONTROLES_POR_CATEGORIA.values()), "Controles fora de categoria"

try:
    from core.db import listar_categorias_iso27701, listar_controles_iso27701

    _cats_db = listar_categorias_iso27701()
    _controles_db = listar_controles_iso27701()
    if _cats_db and _controles_db:
        CATEGORIAS = _cats_db
        CONTROLES = [
            ItemDiagnostico(
                id=c.id,
                titulo=c.titulo,
                descricao=c.descricao,
                categoria_id=c.categoria_id,
                modulo=MODULO_ID,
            )
            for c in _controles_db
        ]
        CONTROLES_POR_CATEGORIA = {cat: [c for c in CONTROLES if c.categoria_id == cat] for cat in CATEGORIAS}
except Exception:
    pass
