# Launcher Conversor

Interface centralizada para instalação, atualização e execução dos conversores da **Domínio Sistemas** (Thomson Reuters e eSocial XML).

---

## Funcionalidades

### Gerenciamento de Aplicativos
- Suporta múltiplos conversores via seletor (ComboBox)
- Instalação automática do conversor a partir do servidor FTP
- Verificação de novas versões com comparação por data e tamanho do arquivo
- Download com barra de progresso em tempo real
- Extração automática do `.zip` para a pasta local

### Verificação de Integridade
- Verifica existência da pasta de instalação
- Verifica existência do executável principal
- Exibe contagem de arquivos instalados
- Exibe data do último registro de atualização

### Desinstalação
- Remove todos os arquivos da pasta do conversor
- Limpa o registro de instalação do Windows Registry

### Controle de Versão
- Painel com **versão instalada** e **versão disponível** com código de cores:
  - 🟢 Verde: em dia / versão mais recente
  - 🟡 Amarelo: desatualizado
  - ⬜ Cinza: sem informação

---

## Autenticação SGD

O Launcher exige login com credenciais da **Domínio Sistemas (SGD)** antes de ser utilizado. A autenticação é feita diretamente pela API oficial:

```
GET https://app01.dominiosistemas.com.br/loginVerifyServlet?ps_xml=...
```

A senha é enviada como hash **MD5** e o retorno `<codigo_retorno>1</codigo_retorno>` indica sucesso.

As credenciais podem ser salvas localmente com a opção **"Lembrar-me"**. Quando ativada, usuário e senha são armazenados no **Windows Registry** com criptografia via **Windows DPAPI** (`CryptProtectData`), garantindo que os dados só possam ser decriptados pelo mesmo usuário Windows que os salvou.

- **Chave de registro:** `HKCU\Software\ConversorThomsonReuters\Launcher`

---

## Credenciais FTP via GitHub Gist

Para evitar que uma mudança de senha no servidor FTP exija redistribuição do Launcher, as credenciais são carregadas dinamicamente de um **GitHub Gist privado** a cada conexão:

```
https://gist.githubusercontent.com/RenanMendesTR/540cfe34c461ea73ba6c0f112fd7c910/raw/ftp_config.json
```

**Formato esperado do Gist:**
```json
{
  "host": "ftp.dominiosistemas.com.br",
  "user": "usuario",
  "password": "senha_nova"
}
```

Caso o Gist esteja inacessível (sem internet, Gist indisponível, etc.), o Launcher usa automaticamente os valores de **fallback** embutidos no código, garantindo que nunca quebre sem aviso.

Para atualizar a senha FTP: basta editar o arquivo `ftp_config.json` no Gist — todos os usuários passarão a usar a nova senha na próxima vez que verificarem atualizações, **sem necessidade de baixar uma nova versão do Launcher**.

---

## Comunicação com o Conversor

O Launcher abre o conversor como um **subprocesso** (`subprocess.Popen`), herdando o ambiente de variáveis. As flags são passadas via **variáveis de ambiente**, que são automaticamente propagadas para o processo filho e seus filhos:

| Variável de Ambiente | Valor | Descrição |
|---|---|---|
| `CONV_AUTH` | `THOMSON_KEY_2025` | Chave obrigatória. O conversor rejeita execução direta sem ela. |
| `CONV_IGNORE_DB_WARNING` | `1` | Suprime o aviso sobre banco de dados de inscrições não encontrado. |
| `CONV_DETECT_UNIT` | `1` | Ativa detecção automática da unidade do cliente via SGD. |
| `CONV_CLIENT_CODE_CONN` | `1` | Usa o código do cliente como nome da conexão Sybase. |

> **Importante:** O conversor verifica `CONV_AUTH` na inicialização. Se não for encontrada (ou seja, se o usuário tentar abrir o executável diretamente sem o Launcher), o programa exibe uma mensagem e encerra imediatamente.

---

## Parâmetros (⚙ Configurações)

Acessíveis pelo ícone de engrenagem na interface. As configurações são persistidas via **QSettings** em:
`HKCU\Software\DominioSistemas\LauncherConversor`

| Parâmetro | Descrição |
|---|---|
| Detectar unidade automaticamente | Consulta o SGD para identificar a unidade do cliente e preenche o `configuracoes.xlsx` automaticamente |
| Ignorar aviso sobre banco de dados das inscrições | Suprime a mensagem de banco de dados ausente na inicialização |
| Utilizar código do cliente como nome da conexão Sybase | Passa o código do cliente diretamente como identificador da conexão com o banco |

---

## Registro de Atualizações (Windows Registry)

O controle da última versão instalada é armazenado no **Windows Registry**, evitando arquivos `.txt` visíveis na pasta de instalação:

- **Chave:** `HKCU\SOFTWARE\DominioSistemas\LauncherConversor\Updates`
- **Valores:** `ThomsonReuters` e `eSocial` (formato: `YYYYMMDDHHMMSS|tamanho_bytes`)

Na primeira execução após migração, arquivos `.txt` legados (`last_update_thomson.txt`, `last_update_esocial.txt`) são importados automaticamente para o Registry e excluídos.

---

## Dependências

- Python 3.11+
- PyQt6
- requests

---

## Build

```bash
pyinstaller launcher.spec
```
