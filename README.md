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

## Credenciais FTP via GitHub Gist (com criptografia)

Para evitar que uma mudança de senha no servidor FTP exija redistribuição do Launcher, as credenciais são carregadas dinamicamente de um **GitHub Gist** a cada conexão:

```
https://gist.githubusercontent.com/RenanMendesTR/e513c4973cecbb4ba67f14e543095b31/raw/ftp_config.json
```

Como o Gist é acessível por qualquer pessoa que possua o link, a **senha do FTP é armazenada criptografada** no JSON. Assim, mesmo que o link vaze, o conteúdo do Gist é inútil sem o Launcher compilado.

### Esquema criptográfico (formato V1)

Implementação 100% em stdlib do Python (sem dependências externas):

- **Key derivation:** PBKDF2-HMAC-SHA256 (200 000 iterações) derivando 64 bytes de `SECRET + salt`.
- **Cifra:** stream cipher via SHA-256 em counter mode (XOR) usando os 32 primeiros bytes da chave derivada.
- **Integridade:** HMAC-SHA256 sobre `salt + ciphertext` usando os 32 bytes finais da chave derivada. Qualquer modificação acidental ou maliciosa faz a decifragem falhar explicitamente.
- **Layout do blob (antes do base64):** `b"V1" | salt(16B) | hmac(32B) | ciphertext(NB)`.
- **Salt aleatório por token:** cada geração produz um token diferente, mesmo para a mesma senha — dificultando análise estatística.

A `SECRET` de 32 bytes fica embutida em `launcher_main.py` e, consequentemente, no executável compilado pelo PyInstaller.

### Formato atual do JSON no Gist

```json
{
    "host": "ftp.dominiosistemas.com.br",
    "user": "supuns",
    "password_enc": "VjH0...<token base64>..."
}
```

O campo legado `"password"` (texto puro) ainda é aceito para compatibilidade, mas seu uso é desencorajado. Se ambos os campos estiverem presentes, `password_enc` tem prioridade.

### Atualizando a senha do FTP

Sempre que a senha do servidor FTP mudar, execute o utilitário incluído no repositório:

```bash
python gerar_senha_cripto.py
```

Ele pede a senha nova (sem ecoar no terminal), gera um token V1 e imprime um JSON pronto para colar no Gist. Após salvar o Gist, todos os Launchers instalados passarão a usar a nova senha automaticamente **sem necessidade de recompilar ou redistribuir o `.exe`**.

> **Nota:** `gerar_senha_cripto.py` importa `_encrypt_password` / `_decrypt_password` do próprio `launcher_main.py`, portanto a `SECRET` usada para gerar tokens e a usada para decifrá-los **nunca ficam dessincronizadas**.

### Cache-buster de CDN

O CDN do GitHub (Fastly) cacheia o URL *raw* do Gist por aproximadamente 5 minutos. Para que uma mudança no Gist reflita imediatamente no Launcher, cada requisição adiciona o parâmetro `?_=<unix_timestamp>` — isso muda a URL a cada chamada, forçando o CDN a buscar a versão atual no origem.

### Fallback

Caso o Gist esteja inacessível (sem internet, Gist indisponível, HMAC inválido, JSON malformado, etc.), o Launcher usa automaticamente os valores de **fallback** embutidos no código, garantindo que nunca quebre sem aviso.

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
