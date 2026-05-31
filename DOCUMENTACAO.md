# Smart Parking Lot

## Descrição

Smart Parking Lot é uma plataforma para gestão de parques de estacionamento com sistema de reservas, reconhecimento automático de matrículas (LPR - License Plate Recognition) e gestão distribuída através de dispositivos Edge e Cloud.

O sistema permite que os utilizadores efetuem reservas antecipadas de lugares de estacionamento utilizando a matrícula do veículo. Quando o veículo chega ao parque, a matrícula é reconhecida automaticamente e validada contra as reservas existentes.

A arquitetura foi desenvolvida segundo um modelo Edge-Cloud:

- Smartphone para captura de imagem da matrícula;
- Raspberry Pi para processamento local (LPR);
- Servidor Cloud para gestão centralizada;
- Base de dados SQLite para armazenamento dos dados.

---

# Arquitetura

## Componentes

### Smartphone

Responsável pela captura da imagem da matrícula.

Funções:

- Acesso à câmara através do navegador;
- Captura da imagem;
- Envio da imagem para o Raspberry Pi.

---

### Raspberry Pi (Edge Node)

Responsável pelo processamento local das imagens.

Funções:

- Receber imagens do smartphone;
- Executar OCR/LPR;
- Extrair a matrícula;
- Comunicar com o Cloud Server através de HTTP.

Vantagens:

- Redução do tráfego de rede;
- Menor latência;
- Processamento distribuído.

---

### Cloud Server

Servidor principal da aplicação.

Funções:

- Gestão de utilizadores;
- Gestão de parques;
- Gestão de reservas;
- Gestão de administradores;
- Cálculo de preços;
- Validação de entradas e saídas.

Tecnologias:

- Python
- Flask
- SQLite

---

## Fluxo Geral

1. O utilizador cria uma reserva.
2. A reserva fica associada à matrícula.
3. O smartphone captura uma imagem da matrícula.
4. O Raspberry Pi processa a imagem.
5. A matrícula é enviada para o servidor.
6. O servidor valida a reserva.
7. A entrada é autorizada.
8. Na saída é calculado o valor a pagar.

---

# Funcionalidades

## Utilizador

- Consulta de parques disponíveis;
- Visualização da ocupação dos parques;
- Criação de reservas;
- Consulta das próprias reservas.

## Administrador de Parque

- Gestão dos parques associados;
- Consulta de reservas;
- Gestão de capacidade;
- Abertura e encerramento de parques.

## Administrador de Sistema

- Gestão de administradores;
- Gestão de tokens de registo;
- Gestão global dos parques.

---

# Base de Dados

## Tabela `parques`

| Campo | Tipo | Descrição |
|---------|---------|---------|
| id | INTEGER | Identificador |
| nome | TEXT | Nome do parque |
| localizacao | TEXT | Localização |
| capacidade | INTEGER | Número máximo de lugares |
| preco_base | REAL | Valor mínimo a pagar |
| preco_min | REAL | Preço por minuto |
| ativo | INTEGER | Estado do parque |

### Regras

- `ativo = 1` → Parque aberto.
- `ativo = 0` → Parque encerrado.

---

## Tabela `tokens`

| Campo | Tipo |
|---------|---------|
| id | INTEGER |
| token | TEXT |
| criado_em | TEXT |
| usado | INTEGER |
| max_parques | INTEGER |
| usado_em | TEXT |

### Objetivo

Permitir a criação controlada de administradores de parque.

Cada token pode:

- Ser utilizado apenas uma vez;
- Definir o número máximo de parques que podem ser criados durante o registo.

---

# Sistema de Registo de Administradores

O administrador do sistema gera um token.

O utilizador acede à página:

```
/register
```

Durante o registo:

1. É criado o administrador de parque;
2. São criados os parques definidos;
3. É criada a associação entre administrador e parques;
4. O token fica marcado como utilizado.

---

# Sistema de Reservas

## Criação

A reserva contém:

- Matrícula;
- Parque;
- Data/hora de início;
- Data/hora de expiração.

## Validação

Quando uma matrícula é recebida pelo sistema:

1. É procurada uma reserva ativa.
2. É validado o período temporal.
3. É autorizada a entrada.

---

# Sistema de Preços

Cada parque define:

- `preco_base`
- `preco_min`

O valor final é calculado através de:

```
valor = preco_base + (minutos * preco_min)
```

O valor mínimo cobrado é sempre `preco_base`.

---

# Tecnologias Utilizadas

- Python
- Flask
- SQLite
- HTML
- CSS
- JavaScript
- Raspberry Pi
- OCR / LPR

---

# Melhorias Futuras

- Pagamentos online;
- Dashboard estatístico;
- Aplicação móvel;
- Integração com barreiras automáticas;
- Notificações em tempo real;
- Suporte para múltiplos Edge Nodes.