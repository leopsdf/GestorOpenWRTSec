# GestorOpenWRTSec

Sistema de gerenciamento seguro para dispositivos OpenWRT com integração a conceitos de Redes Definidas por Software (SDN) e observabilidade via OpenSearch.

Este projeto visa facilitar o controle, monitoramento e configuração de roteadores OpenWRT por meio de uma API REST desenvolvida em Python com Flask, além de oferecer suporte à geração de chaves e certificados para comunicação segura.

---

## Funcionalidades

-  Geração de chaves e certificados para autenticação SSL
-  Configuração automatizada de dispositivos OpenWRT
-  API REST com Flask para controle e gerenciamento
-  Integração com OpenSearch para observabilidade e análise de dados
-  Estrutura modular para expansão de funcionalidades

---

## Tecnologias Utilizadas

- **Python 3.9+**
- **Flask** – Framework web para a API REST
- **OpenWRT** – Sistema operacional para dispositivos embarcados
- **OpenSearch** – Armazenamento e visualização de logs/telemetria
- **JWT (JSON Web Tokens)** – Autenticação baseada em token
- **Shell Script** – Automação de configurações em dispositivos

---

## Como Executar o Projeto

### 1. Clone o repositório

```bash
git clone https://github.com/leopsdf/GestorOpenWRTSec.git
cd GestorOpenWRTSec
