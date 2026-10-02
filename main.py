# flet-android-notifications-patch --project-root build/flutter
# $env:Path = "C:\Users\ASUSPRO\flutter\3.44.8\bin;$env:Path"
# where.exe flutter
# flutter --version 
# flutter doctor
import os
import sys
import time
import json
import uuid
import atexit
import asyncio
import datetime
import requests
import subprocess
import flet as ft
import colors as cr
import flet_charts as fc
from typing import Dict, Any
from flet_android_notifications import FletAndroidNotifications
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)
from dotenv import load_dotenv
if os.environ.get("FLET_PLATFORM") not in ("android", "ios"):
    load_dotenv()

# ================================================ Back-End =================================================
def obter_cambio():
    API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")
    if not API_KEY:
        return None

    url = "https://v6.exchangerate-api.com/v6/latest/USD"

    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        resposta = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        resposta.raise_for_status()

        dados = resposta.json()

        if dados.get("result") != "success":
            print("Erro da API:", dados)
            return None

        return dados["conversion_rates"].get("AOA")

    except Exception as erro:
        print("Erro ao consultar ExchangeRate-API:", erro)
        return None

# AMBIENTE DA APLICAÇÃO

IS_ANDROID = sys.platform == "android" or os.getenv("ANDROID_ARGUMENT") is not None

KAMBA_URL_ANDROID = "https://kamba-backend-oaw2.onrender.com"

KAMBA_URL = (
    KAMBA_URL_ANDROID
    if IS_ANDROID
    else "http://127.0.0.1:8000"
)


def perguntar_kamba(conversa_id, mensagem):
    dados = {
        "conversa_id": conversa_id,
        "mensagem": mensagem
    }
    
    try:
        resposta = requests.post(
            f"{KAMBA_URL}/kamba",
            json=dados,
            timeout=60
        )
        
        if resposta.status_code == 200:
            resultado = resposta.json()
            return resultado.get(
                "resposta",
                "O Kamba IA não devolveu uma resposta."
            )
        
        if resposta.status_code == 422:
            return (
                "A mensagem enviada para o Kamba IA "
                "não é válida."
            )

        if resposta.status_code == 502:
            return (
                "O Kamba IA não conseguiu comunicar "
                "com o serviço de inteligência artificial."
            )

        return (
            f"Erro no servidor Kamba IA "
            f"({resposta.status_code})."
        )

    except requests.exceptions.Timeout:
        return (
            "O Kamba IA demorou demasiado para responder. "
            "Tenta novamente."
        )

    except requests.exceptions.ConnectionError:
        return (
            "Não foi possível conectar ao servidor "
            "do Kamba IA."
        )

    except requests.exceptions.RequestException as erro:
        print("Erro Kamba IA:", erro)

        return (
            "Ocorreu um erro ao comunicar com "
            "o Kamba IA."
        )

    except Exception as erro:
        print("Erro inesperado Kamba IA:", erro)

        return (
            "O Kamba IA encontrou um erro inesperado."
        )

def user_file_path() -> str:
    data_dir = os.getenv("APPDATA")
    if data_dir:
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir,"user_data.json")
    
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "json")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "user_data.json")

def load_user_data() -> Dict[str, Any]:
    file_path = user_file_path()
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                dados = json.load(f)
            # Verificar se existem usuários no formato antigo
            alterado = False

            for usuario, dados_usuario in dados.items():

                # Formato antigo:
                if isinstance(dados_usuario, str):

                    dados[usuario] = {
                        "password": dados_usuario,
                        "transacoes": []
                    }

                    alterado = True

                # Formato novo, mas sem transacoes
                elif isinstance(dados_usuario, dict):

                    if "password" not in dados_usuario:
                        dados_usuario["password"] = ""

                    if "transacoes" not in dados_usuario:
                        dados_usuario["transacoes"] = []
                    
                    if "orcamentos" not in dados_usuario:
                        dados_usuario["orcamentos"] = []

            # Se converteu alguma coisa, salvar novamente
            if alterado:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(
                        dados,
                        f,
                        indent=2,
                        ensure_ascii=False
                    )

            return dados
        except Exception as erro:
            print("Erro ao carregar usuário: ", erro)
            return{}
    return {}

def save_user_data(data: Dict[str, Any]):
    file_path = user_file_path()
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
# ================================================ INICIAR BACKEND DO KAMBA IA AUTOMATICAMENTE ================================================

backend_processo = None

def iniciar_backend():
    global backend_processo
    
    # path where be server.py
    path_backend = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "kamba_backend"
    )
    server = os.path.join(path_backend, "server.py")
    
    # Check that there server.py
    if not os.path.exists(server):
        print("I dont found the server.py.")
        print(f"Seach path: {server}")
        return False
    
    try:
        backend_processo = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "server:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000"
            ],
            cwd=path_backend
        )
        
        # Hold on the server start
        for _ in range(20):
            try:
                resposta = requests.get(
                    "http://127.0.0.1:8000/health",
                    timeout=0.5
                )
                
                if resposta.status_code == 200:
                    print("Kamba IA: servidor iniciado com sucesso.")
                    return True
            except requests.RequestException:
                pass
            time.sleep(0.5)
        print("ERRO: o servidor do Kamba IA não iniciou a tempo.")
        return False
    except Exception as erro:
        print("ERRO ao start the server Kamba IA:")
        print(erro)
        return False

def parar_backend():
    global backend_processo
    
    if backend_processo is not None:
        try:
            backend_processo.terminate()
            backend_processo.wait(timeout=5)
        except Exception:
            try:
                backend_processo.kill()
            except Exception:
                pass
atexit.register(parar_backend)

# ================================================ Front-End ================================================
def main(page: ft.Page):
    file_picker = ft.FilePicker()
    page.services.append(file_picker)
    page.padding = 0
    page.spacing = 0
    page.adaptive = True
    page.theme_mode = 'Light'
    page.bgcolor = cr.Colors.BACKGROUND
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    notificacoes = FletAndroidNotifications()
    
    # ------------------------------- def Formulário ---------------------------
    login_user = ft.TextField(
        label='Nome de Usuário',
        border_radius=20,
        width=500,
        prefix_icon=ft.Icons.PERSON,
        bgcolor=cr.Colors.CARDS,
        border_color=cr.Colors.TEXT_SECUNDARIA,
        label_style=ft.TextStyle(color=cr.Colors.TEXT_SECUNDARIA),
        text_style=ft.TextStyle(color=cr.Colors.TEXT_PRINCIPAL),
    )

    login_pass = ft.TextField(
        label='Password',
        border_radius=20,
        width=500,
        password=True,
        can_reveal_password=True,
        bgcolor=cr.Colors.CARDS,
        border_color=cr.Colors.TEXT_SECUNDARIA,
        label_style=ft.TextStyle(color=cr.Colors.TEXT_SECUNDARIA),
        text_style=ft.TextStyle(color=cr.Colors.TEXT_PRINCIPAL),
    )
    
    sign_user = ft.TextField(
        label='Nome de Usuário',
        border_radius=20,
        width=500,
        prefix_icon=ft.Icons.PERSON,
        bgcolor=cr.Colors.CARDS,
        border_color=cr.Colors.TEXT_SECUNDARIA,
        label_style=ft.TextStyle(color=cr.Colors.TEXT_SECUNDARIA),
        text_style=ft.TextStyle(color=cr.Colors.TEXT_PRINCIPAL),
    )

    sign_pass = ft.TextField(
        label='Password',
        border_radius=20,
        width=500,
        password=True,
        can_reveal_password=True,
        bgcolor=cr.Colors.CARDS,
        border_color=cr.Colors.TEXT_SECUNDARIA,
        label_style=ft.TextStyle(color=cr.Colors.TEXT_SECUNDARIA),
        text_style=ft.TextStyle(color=cr.Colors.TEXT_PRINCIPAL),
    )

    sign_conf_pass = ft.TextField(
        label='Confirmar Password',
        border_radius=20,
        width=500,
        password=True,
        can_reveal_password=True,
        bgcolor=cr.Colors.CARDS,
        border_color=cr.Colors.TEXT_SECUNDARIA,
        label_style=ft.TextStyle(color=cr.Colors.TEXT_SECUNDARIA),
        text_style=ft.TextStyle(color=cr.Colors.TEXT_PRINCIPAL),
    )
    usuarios = load_user_data()
    usuarios_logados = [None]
    # ------------------------------- DEF SIGN ---------------------------
    warning = ft.Text(' ',color=cr.Colors.RED, size=13)
    modal = ft.AlertDialog(
        modal=True,
        content=ft.Row([ft.Icon(icon=ft.Icons.CHECK_CIRCLE_OUTLINE), ft.Text('Conta criada com sucesso!')], ),
        actions=[ft.TextButton('Ok', on_click=lambda e: page.pop_dialog())]
    )
    def do_sign_in(e):
        user = sign_user.value.strip()
        password = sign_pass.value
        conf_password = sign_conf_pass.value
        
        if not user or not password or not conf_password:
            warning.value = "Preencha todos os campos!"
            page.update()
            return

        if password != conf_password:
            warning.value = "As senhas não coincidem!"
            page.update()
            return

        if user in usuarios:
            warning.value = "Senha já cadastrada!"
            page.update()
            return
        
        usuarios[user] = {
            "password": password,
            "transacoes":[],
            "orcamentos":[]
        }
        save_user_data(usuarios)
        page.show_dialog(modal)
        sign_user.value = ""
        sign_pass.value = ""
        sign_conf_pass.value = ""
        warning.value = ""
        page.update()

    # ------------------------------- DEF LOGIN ---------------------------
    def do_login(e):
        user = login_user.value.strip()
        password = login_pass.value
        
        if not user or not password:
            warning.value = "Preencha todos os campos!"
            page.update()
            return

        if user not in usuarios:
            warning.value = "Usuário ou senha incorretos!"
            page.update()
            return
        
        if usuarios[user]["password"] != password:
            warning.value = "Usuário ou senha incorretos!"
            page.update()
            return
        usuarios_logados[0] = user
        transacoes.clear()
        transacoes.extend(
            usuarios[user].get("transacoes", [])
        )
        orcamentos.clear()
        orcamentos.extend(
            usuarios[user].get("orcamentos", [])
        )
        # Monta a tela primeiro; só depois atualiza os controles internos.
        show_layout()
        update_list()
        update_orcamentos()
        update_dashboard()
        login_user.value = ""
        login_pass.value = ""
        warning.value = ""
        page.update()
    
    def start():
        page.clean()
        page.add(login_display)
    
    login_display = ft.Container(
        aspect_ratio=25/28,
        padding=30,
        blur=50,
        border_radius=20,
        content=ft.Column([
            ft.Tabs(
                selected_index=0,
                length=2,
                content=ft.Column([
                    ft.TabBar(
                        tab_alignment=ft.TabAlignment.CENTER,
                        indicator_animation=ft.TabIndicatorAnimation.ELASTIC,
                        indicator_size=ft.TabBarIndicatorSize.LABEL,
                        indicator=ft.UnderlineTabIndicator(border_side=ft.BorderSide(color=cr.Colors.CARDS, width=3)),
                        tabs=[
                            ft.Tab(label='Login'),
                            ft.Tab(label='Cadastrar')
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        height=1000,
                        controls=[
                            ft.Container(
                                content=ft.Column([
                                    ft.Container(height=20),
                                    login_user, login_pass, warning,
                                    ft.Button(
                                        'Login',
                                        icon=ft.Icons.LOGIN,
                                        width=500,
                                        on_click=do_login,
                                        style=ft.ButtonStyle(
                                            padding=20,
                                            color=cr.Colors.CARDS,
                                            bgcolor={
                                                ft.ControlState.DEFAULT: cr.Colors.PRINCIPAL
                                            }
                                        )
                                    )
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                            ),
                            
                            ft.Container(
                                content=ft.Column([
                                    ft.Container(height=20),
                                    sign_user, sign_pass, sign_conf_pass, warning,
                                    ft.Button(
                                        'Cadastar',
                                        icon=ft.Icons.PERSON_ADD,
                                        width=500,
                                        on_click=do_sign_in,
                                        style=ft.ButtonStyle(
                                            padding=20,
                                            color=cr.Colors.CARDS,
                                            bgcolor={ft.ControlState.DEFAULT: cr.Colors.PRINCIPAL}
                                        )
                                    )
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                            )
                        ]
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.Alignment.CENTER)
            )
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

    def show_layout():
        page.clean()
        page.add(space, cabecario, content[0])
        page.floating_action_button = floating_btn
        page.floating_action_button_location = ft.FloatingActionButtonLocation.CENTER_DOCKED
        page.bottom_appbar = appbar
        on_resize(None)
    
    def logout():
        usuarios_logados[0] = None
        transacoes.clear()
        orcamentos.clear()
        page.clean()
        page.floating_action_button = None
        page.bottom_appbar = None
        page.appbar = None
        page.add(login_display)
        page.update()


    def change_display(indice):
        title_display.value = names_display[indice]
        page.clean()
        if indice == 1:
            page.add(space, cabecario_trans, content[indice])
        elif indice == 2:
            page.add(space, cabecario_orca, content[indice])
        elif indice == 3:
            page.add(space, cabecario_relatorios, content[indice])
            mostrar_lista_relatorios()
        else:
            page.add(space, cabecario, content[indice])
        page.update()

    def salvar_transacoes():
        usuario = usuarios_logados[0]
        if not usuario:
            return
        usuarios[usuario]["transacoes"] = transacoes.copy()
        save_user_data(usuarios)

    def add_transacao(e):
        tipo = ft.Dropdown(
            label="Tipo",
            width=1000,
            margin=5,
            border_radius=20,
            bgcolor=cr.Colors.CARDS,
            border_color=cr.Colors.TEXT_SECUNDARIA,
            label_style=ft.TextStyle(color=cr.Colors.TEXT_SECUNDARIA),
            text_style=ft.TextStyle(color=cr.Colors.TEXT_PRINCIPAL),
            options=[
                ft.DropdownOption("Receita"),
                ft.DropdownOption("Despesa"),
            ],
        )
        
        categoria = ft.Dropdown(
            label="Catelogia",
            width=1000,
            margin=5,
            border_radius=20,
            bgcolor=cr.Colors.CARDS,
            border_color=cr.Colors.TEXT_SECUNDARIA,
            label_style=ft.TextStyle(color=cr.Colors.TEXT_SECUNDARIA),
            text_style=ft.TextStyle(color=cr.Colors.TEXT_PRINCIPAL),
            options=[
                ft.DropdownOption("Salário"),
                ft.DropdownOption("Alimentação"),
                ft.DropdownOption("Transporte"),
                ft.DropdownOption("Moradia"),
                ft.DropdownOption("Lazer"),
                ft.DropdownOption("Educação"),
                ft.DropdownOption("Saúde"),
                ft.DropdownOption("Outros")
            ],
        )
        
        title = ft.TextField(
            label="Descrição",
            width=1000,
            hint_text="Ex: Bisno, Brinquedo...",
            prefix_icon=ft.Icons.EDIT,
            border_radius=20,
            margin=5,
            bgcolor=cr.Colors.CARDS,
            border_color=cr.Colors.TEXT_SECUNDARIA,
            label_style=ft.TextStyle(color=cr.Colors.TEXT_SECUNDARIA),
            text_style=ft.TextStyle(color=cr.Colors.TEXT_PRINCIPAL),
        )
        
        value = ft.TextField(
            label="Valor",
            prefix="Kz  ",
            width=1000,
            margin=5,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=20,
            bgcolor=cr.Colors.CARDS,
            border_color=cr.Colors.TEXT_SECUNDARIA,
            label_style=ft.TextStyle(color=cr.Colors.TEXT_SECUNDARIA),
            text_style=ft.TextStyle(color=cr.Colors.TEXT_PRINCIPAL),
        )
        
        mensagem = ft.Text('', size=15, color=cr.Colors.RED, weight='bold')

        async def salvar(e):
            nome = title.value.strip()
            valor_texto = value.value.strip()
            
            if not nome:
                mensagem.value = "Insira a descrição da transação."
                mensagem.color = cr.Colors.RED
                page.update()
                return
            
            if not valor_texto:
                mensagem.value = "Insira o valor da transação."
                mensagem.color = cr.Colors.RED
                page.update()
                return

            if tipo.value not in ("Receita", "Despesa"):
                mensagem.value = "Selecione o tipo da transação."
                mensagem.color = cr.Colors.RED
                page.update()
                return

            if categoria.value not in (
                "Salário",
                "Alimentação",
                "Transporte",
                "Moradia",
                "Lazer",
                "Educação",
                "Saúde",
                "Outros",
            ):
                mensagem.value = "Selecione a categoria da transação."
                mensagem.color = cr.Colors.RED
                page.update()
                return

            try:
                valor_numero = float(valor_texto.replace(",","."))
                if valor_numero <=0:
                    raise ValueError
            except ValueError:
                mensagem.value = "Digite um valor válido."
                mensagem.color = cr.Colors.RED
                page.update()
                return
            
            now = datetime.datetime.now()
            hour = now.strftime("%H:%M")
            
            if now.date() == datetime.date.today():
                date = "Hoje"
            else:
                date = now.strftime("%d/%m/%y")
            
            icons = {
                "Salário":"PERSON",
                "Alimentação":"RESTAURANT",
                "Transporte":"DIRECTIONS_BUS",
                "Moradia":"HOME",
                "Lazer":"SPORTS_ESPORTS",
                "Educação":"SCHOOL",
                "Saúde":"MEDICAL_SERVICES",
                "Outros":"MORE_HORIZ",
            }
            
            if tipo.value == "Receita":
                valor_formatado = f"+Kz {valor_numero:,.2f}"
            else:
                valor_formatado = f"-Kz {valor_numero:,.2f}"
                
            new_transacao = {
                "title":nome,
                "type":tipo.value,
                "category": categoria.value,
                "amount": valor_numero,
                "value": valor_formatado,
                "hour": hour,
                "date": date,
                "icon": icons.get(
                    categoria.value,
                    "MORE_HORIZ"
                )
            }
            
            transacoes.insert(0, new_transacao)
            salvar_transacoes()
            update_list()
            update_dashboard()
            
            # Despesa, verifica aba de orçamento
            if tipo.value == "Despesa":
                await check_orcamento(
                    categoria.value,
                    valor_numero
                )
            update_orcamentos()
            valor_notificacao = (
                f"{valor_numero:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )
            # Falhas de permissão/notificação não devem impedir a transação.
            try:
                permitido = await notificacoes.request_permissions()

                if permitido:
                    if tipo.value == "Receita":
                        await notificacoes.show_notification(
                            notification_id=int(datetime.datetime.now().timestamp()),
                            title="Tem Kumbo!",
                            body=(f"+{valor_notificacao}Kz no KwanzaMeter"),
                            importance="high"
                        )
                    elif tipo.value == "Despesa":
                        await notificacoes.show_notification(
                            notification_id=int(datetime.datetime.now().timestamp()),
                            title="Perdeste Kumbo!",
                            body=(f"-{valor_notificacao}Kz no KwanzaMeter"),
                            importance="high"
                        )
            except Exception as erro:
                print("Erro nas notificações Android:", erro)
            change_display(1)

        tela_add = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Container(
                    # bgcolor=cr.Colors.CARDS,
                    height=600,
                    padding=10,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=20,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: change_display(1)),
                                    ft.Text("Nova Transação", size=20, weight='bold'),
                                ],
                            ),
                            tipo, categoria, title, value, mensagem,
                            ft.Button(
                                "Salvar",
                                icon=ft.Icons.ADD,
                                width=500,
                                height=50,
                                on_click=salvar,
                                style=ft.ButtonStyle(
                                    text_style=ft.TextStyle(weight='bold'),
                                    padding=10,
                                    color=cr.Colors.CARDS,
                                    bgcolor={ft.ControlState.DEFAULT: cr.Colors.PRINCIPAL_BLACK}
                                )
                            )
                        ]
                    )
                )
            ]
        )
        page.clean()
        page.add(space, tela_add)
        page.update()
    
    transacoes = []
    orcamentos = []
    MESES = [
        "Janeiro",
        "Fevereiro",
        "Março",
        "Abril",
        "Maio",
        "Junho",
        "Julho",
        "Agosto",
        "Setembro",
        "Outubro",
        "Novembro",
        "Dezembro" 
    ]
    
    def obter_data_transacao(item):
        data = item.get("date", "")
        hoje = datetime.date.today()
        
        if data == "Hoje":
            return hoje
        
        formatos = [
            "%d%m%Y",
            "%d%m%y",
            "%Y-%m-%d",
        ]
        
        for formato in formatos:
            try:
                return datetime.datetime.strptime(
                    data,
                    formato
                ).date()
            except ValueError:
                pass
    
        return None
    
    def obter_meses_relatorios():
        meses = set()
        
        for item in transacoes:
            data = obter_data_transacao(item)
            
            if data:
                meses.add((data.year, data.month))
        
        return sorted(
            meses,
            key=lambda x: (x[0], x[1]),
            reverse=True
        )

    def transacoes_do_mes(ano, mes):
        resultado = []
        
        for item in transacoes:
            data = obter_data_transacao(item)
            
            if not data:
                continue
            
            if data.year == ano and data.month == mes:
                resultado.append(item)
        
        return resultado
    
    def nome_mes(mes):
        return MESES[mes - 1]
    
    def formatar_valor(valor):
        return (
            f"Kz {valor:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    
    lista_relatorios = ft.Column(
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )
    
    relatorio_detalhes = ft.Column(
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )
    
    lista = ft.Column(
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )
    
    lista_orcamentos = ft.Column(
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )
    
    lista_dashboard = ft.Column(
        spacing=8,
        tight=True
    )
    
    def despesas_por_categoria(ano, mes):
        categorias = {}
        
        for item in transacoes_do_mes(ano, mes):
            if item.get("type") != "Despesa":
                continue
            
            categoria = item.get("category", "Outros")
            valor = get_value_transacao(item)
            
            categorias[categoria] = (
                categorias.get(categoria, 0) + valor
            )
        return categorias
    
    def orcamento_do_mes(categoria, ano, mes):
        for item in orcamentos:
            if item.get("category") == categoria:
                limite = float(item.get("limit", 0) or 0)
                gasto = 0.0

                for transacao in transacoes_do_mes(ano, mes):
                    if (
                        transacao.get("type") == "Despesa"
                        and transacao.get("category") == categoria
                    ):
                        gasto += get_value_transacao(transacao)

                return limite, gasto

        return None, None
    
    def mostrar_relatorio_mes(ano, mes):
        relatorio_detalhes.controls.clear()
        transacoes_mes = transacoes_do_mes(
            ano,
            mes
        )
        total_receitas = 0
        total_despesas = 0
        for item in transacoes_mes:
            valor = get_value_transacao(item)
            
            if item.get("type") == "Receita":
                total_receitas += valor
            else:
                total_despesas += valor
        saldo = total_receitas - total_despesas

        # ======================================================
        # CABEÇALHO
        # ======================================================

        relatorio_detalhes.controls.append(
            ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda e: mostrar_lista_relatorios()
                    ),

                    ft.Text(
                        f"{nome_mes(mes)} de {ano}",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=cr.Colors.TEXT_PRINCIPAL,
                        expand=True
                    ),
                    
                    ft.IconButton(
                        icon=ft.Icons.PICTURE_AS_PDF,
                        tooltip="Gerar PDF",
                        icon_color=cr.Colors.PRINCIPAL,
                        on_click=lambda e, a=ano, m=mes:
                            gerar_relatorio_pdf(a,m)
                    )
                ]
            )
        )

        # ======================================================
        # RESUMO
        # ======================================================

        relatorio_detalhes.controls.append(
            ft.Container(
                bgcolor=cr.Colors.CARDS,
                border_radius=16,
                padding=15,
                content=ft.Column(
                    spacing=10,
                    controls=[

                        ft.Text(
                            "Resumo financeiro",
                            size=15,
                            weight=ft.FontWeight.BOLD,
                            color=cr.Colors.TEXT_PRINCIPAL
                        ),

                        ft.Row(
                            controls=[
                                ft.Column(
                                    expand=True,
                                    controls=[
                                        ft.Text(
                                            "Receitas",
                                            size=11,
                                            color=cr.Colors.TEXT_SECUNDARIA
                                        ),
                                        ft.Text(
                                            formatar_valor(
                                                total_receitas
                                            ),
                                            size=14,
                                            weight="bold",
                                            color=cr.Colors.GREEN
                                        )
                                    ]
                                ),

                                ft.Column(
                                    expand=True,
                                    controls=[
                                        ft.Text(
                                            "Despesas",
                                            size=11,
                                            color=cr.Colors.TEXT_SECUNDARIA
                                        ),
                                        ft.Text(
                                            formatar_valor(
                                                total_despesas
                                            ),
                                            size=14,
                                            weight="bold",
                                            color=cr.Colors.RED
                                        )
                                    ]
                                )
                            ]
                        ),

                        ft.Divider(),

                        ft.Text(
                            "Saldo",
                            size=11,
                            color=cr.Colors.TEXT_SECUNDARIA
                        ),

                        ft.Text(
                            formatar_valor(saldo),
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=(
                                cr.Colors.GREEN
                                if saldo >= 0
                                else cr.Colors.RED
                            )
                        )
                    ]
                )
            )
        )
        # ======================================================
        # DESPESAS POR CATEGORIA
        # ======================================================

        relatorio_detalhes.controls.append(
            ft.Text(
                "Despesas por categoria",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=cr.Colors.TEXT_PRINCIPAL
            )
        )

        categorias = despesas_por_categoria(
            ano,
            mes
        )

        if not categorias:
        
            relatorio_detalhes.controls.append(
                ft.Container(
                    bgcolor=cr.Colors.CARDS,
                    border_radius=14,
                    padding=15,
                    content=ft.Text(
                        "Não existem despesas neste mês.",
                        size=12,
                        color=cr.Colors.TEXT_SECUNDARIA
                    )
                )
            )

        else:
        
            for categoria, gasto in sorted(
                categorias.items(),
                key=lambda x: x[1],
                reverse=True
            ):

                relatorio_detalhes.controls.append(
                    ft.Container(
                        bgcolor=cr.Colors.CARDS,
                        border_radius=14,
                        padding=14,

                        content=ft.Row(
                            controls=[
                            
                                ft.Column(
                                    expand=True,
                                    spacing=3,
                                    controls=[
                                    
                                        ft.Text(
                                            categoria,
                                            size=13,
                                            weight="bold",
                                            color=cr.Colors.TEXT_PRINCIPAL
                                        ),

                                        ft.Text(
                                            "Despesas",
                                            size=10,
                                            color=cr.Colors.TEXT_SECUNDARIA
                                        )
                                    ]
                                ),

                                ft.Text(
                                    formatar_valor(gasto),
                                    size=12,
                                    weight="bold",
                                    color=cr.Colors.RED
                                )
                            ]
                        )
                    )
                )

        # ======================================================
        # ORÇAMENTOS
        # ======================================================
        
        relatorio_detalhes.controls.append(
            ft.Text(
                "Orçamentos",
                size=16,
                weight='bold',
                color=cr.Colors.TEXT_PRINCIPAL
            )
        )
        
        if not orcamentos:
            relatorio_detalhes.controls.append(
                ft.Container(
                    bgcolor=cr.Colors.CARDS,
                    border_radius=14,
                    padding=15,
                    content=ft.Text(
                        "Nenhum orçamento criado",
                        size=12,
                        color=cr.Colors.TEXT_SECUNDARIA
                    )
                )
            )
        else:
            for orcamento in orcamentos:
                categoria = orcamento.get("category", "Outros")
                limite, gasto = orcamento_do_mes(
                    categoria,
                    ano,
                    mes
                )
                
                if limite is None:
                    continue
                
                progresso = (
                    gasto / limite
                    if limite > 0
                    else 0
                )
                
                if progresso >= 1:
                    status = "Orçamento ultrapassado"
                    status_cor = cr.Colors.RED
                
                elif progresso >= 0.8:
                    status = "Atenção: Próximo do limite"
                    status_cor = cr.Colors.RED
                
                else:
                    restante = limite - gasto
                    status = (
                        f"Restante: {formatar_valor(restante)}"
                    )
                    status_cor = cr.Colors.GREEN
                
                relatorio_detalhes.controls.append(
                    ft.Container(
                        bgcolor=cr.Colors.CARDS,
                        border_radius=14,
                        padding=14,
                        content=ft.Column(
                            spacing=8,
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Column(
                                            expand=True,
                                            spacing=3,
                                            controls=[
                                                ft.Text(
                                                    categoria,
                                                    size=13,
                                                    weight='bold',
                                                    color=cr.Colors.TEXT_PRINCIPAL
                                                ),
                                                ft.Text(
                                                    f"{formatar_valor(gasto)} / "
                                                    f"{formatar_valor(limite)}",
                                                    size=10,
                                                    color=cr.Colors.TEXT_SECUNDARIA
                                                )
                                            ]
                                        ),
                                        
                                        ft.Text(
                                            f"{round(progresso*100)}%",
                                            size=13,
                                            weight='bold',
                                            color=status_cor
                                        )
                                    ]
                                ),
                                ft.ProgressBar(
                                    value=min(progresso, 1),
                                    height=7,
                                    bgcolor=cr.Colors.BACKGROUND,
                                    color=(
                                        cr.Colors.RED
                                        if progresso >= 1
                                        else cr.Colors.PRINCIPAL
                                    )
                                ),
                                ft.Text(
                                    status,
                                    size=10,
                                    weight='bold',
                                    color=status_cor
                                )
                            ]
                        )
                    )
                )
        # ======================================================
        # TRANSAÇÕES
        # ======================================================

        relatorio_detalhes.controls.append(
            ft.Text(
                "Transações do mês",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=cr.Colors.TEXT_PRINCIPAL
            )
        )

        if not transacoes_mes:
            relatorio_detalhes.controls.append(
                ft.Container(
                    padding=30,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(
                                ft.Icons.PAYMENT,
                                size=45,
                                color=cr.Colors.TEXT_SECUNDARIA
                            ),

                            ft.Text(
                                "Nenhuma transação neste mês.",
                                size=13,
                                color=cr.Colors.TEXT_SECUNDARIA
                            )
                        ]
                    )
                )
            )

        else:

            for item in transacoes_mes:
                valor = get_value_transacao(item)
                if item.get("type") == "Receita":
                    cor = cr.Colors.GREEN
                    sinal = "+"
                else:
                    cor = cr.Colors.RED
                    sinal = "-"
                    
                relatorio_detalhes.controls.append(
                    ft.Container(
                        bgcolor=cr.Colors.CARDS,
                        border_radius=14,
                        padding=12,
                        content=ft.Row(
                            controls=[
                                ft.Column(
                                    expand=True,
                                    spacing=3,
                                    controls=[
                                        ft.Text(
                                            item.get(
                                                "title",
                                                "Sem descrição"
                                            ),
                                            size=13,
                                            weight="bold",
                                            color=cr.Colors.TEXT_PRINCIPAL
                                        ),
                                        ft.Text(
                                            item.get(
                                                "category",
                                                "Outros"
                                            ),
                                            size=10,
                                            color=cr.Colors.TEXT_SECUNDARIA
                                        ),
                                        ft.Text(
                                            item.get(
                                                "date",
                                                ""
                                            ),
                                            size=9,
                                            color=cr.Colors.TEXT_SECUNDARIA
                                        )
                                    ]
                                ),
                                ft.Text(
                                    f"{sinal}{formatar_valor(valor)}",
                                    size=12,
                                    weight="bold",
                                    color=cor
                                )
                            ]
                        )
                    )
                )
        page.update()
    
    async def gerar_relatorio_pdf(ano, mes):
        try:
            # ==================================================
            # DADOS DO MÊS
            # ==================================================
            transacoes_mes = transacoes_do_mes(ano, mes)
            total_receitas = 0
            total_despesas = 0
            
            for item in transacoes_mes:
                valor = get_value_transacao(item)
                if item.get("type") == "Receita":
                    total_receitas += valor
                else:
                    total_despesas += valor
            saldo = total_receitas - total_despesas
            categorias = despesas_por_categoria(ano, mes)

            
            # ==================================================
            # CORES DO PDF
            # ==================================================
            VERDE = colors.HexColor("#5B8C72")
            VERDE_CLARO = colors.HexColor("#EAF3ED")
            CINZA = colors.HexColor("#6B7280")
            CINZA_CLARO = colors.HexColor("#F3F4F6")
            PRETO = colors.HexColor("#1F2937")
            VERMELHO = colors.HexColor("#DC5C5C")
            BRANCO = colors.white
            
            # ==================================================
            # DOCUMENTO
            # ==================================================
            buffer = BytesIO()
            
            documento = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=15 * mm,
                leftMargin=15 * mm,
                topMargin=18 * mm,
                bottomMargin=18 * mm
            )
            
            # ==================================================
            # ESTILO
            # ==================================================
            estilos = getSampleStyleSheet()
            
            estilo_titulo = ParagraphStyle(
                "Titulo",
                parent=estilos["Title"],
                fontName="Helvetica-Bold",
                fontSize=22,
                leading=26,
                textColor=PRETO,
                alignment=TA_CENTER,
                spaceAfter=5
            )
            
            estilo_subtitulo = ParagraphStyle(
                "Subtitulo",
                parent=estilos["Normal"],
                fontName="Helvetica",
                fontSize=10,
                leading=14,
                textColor=CINZA,
                alignment=TA_CENTER,
                spaceAfter=15
            )
            
            estilo_secao = ParagraphStyle(
                "Secao",
                parent=estilos["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=14,
                leading=18,
                textColor=PRETO,
                spaceBefore=12,
                spaceAfter=8
            )
            
            estilo_normal = ParagraphStyle(
                "NormalCustom",
                parent=estilos["Normal"],
                fontName="Helvetica",
                fontSize=9,
                leading=12,
                textColor=PRETO
            )

            estilo_pequeno = ParagraphStyle(
                "Pequeno",
                parent=estilos["Normal"],
                fontName="Helvetica",
                fontSize=8,
                leading=10,
                textColor=CINZA
            )
            
            # ==================================================
            # FUNÇÃO PARA FORMATAR KZ
            # ==================================================
            def kz(valor):
                return (
                    f"Kz {valor:,.2f}"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                )

            # ==================================================
            # CONTEÚDO
            # ==================================================
            elementos = []
            
            # --------------------------------------------------
            # CABEÇALHO
            # --------------------------------------------------

            elementos.append(
                Paragraph(
                    "KWANZAMETER",
                    estilo_titulo
                )
            )

            elementos.append(
                Paragraph(
                    f"Relatório Financeiro — "
                    f"{nome_mes(mes)} de {ano}",
                    estilo_subtitulo
                )
            )

            elementos.append(
                Table(
                    [
                        [
                            Paragraph(
                                "<b>Relatório mensal</b>",
                                estilo_normal
                            ),
                            Paragraph(
                                datetime.date.today().strftime(
                                    "Gerado em %d/%m/%Y"
                                ),
                                estilo_pequeno
                            )
                        ]
                    ],
                    colWidths=[
                        100 * mm,
                        70 * mm
                    ],
                    style=TableStyle([
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, -1),
                            VERDE_CLARO
                        ),
                        (
                            "BOX",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            VERDE
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "MIDDLE"
                        ),
                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            10
                        ),
                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            10
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            8
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            8
                        )
                    ])
                )
            )

            elementos.append(
                Spacer(1, 8 * mm)
            )

            # ==================================================
            # RESUMO FINANCEIRO
            # ==================================================

            elementos.append(
                Paragraph(
                    "Resumo financeiro",
                    estilo_secao
                )
            )

            resumo = Table(
                [
                    [
                        Paragraph(
                            "<b>Receitas</b>",
                            estilo_normal
                        ),
                        Paragraph(
                            "<b>Despesas</b>",
                            estilo_normal
                        ),
                        Paragraph(
                            "<b>Saldo</b>",
                            estilo_normal
                        )
                    ],
                    [
                        Paragraph(
                            kz(total_receitas),
                            estilo_normal
                        ),
                        Paragraph(
                            kz(total_despesas),
                            estilo_normal
                        ),
                        Paragraph(
                            kz(saldo),
                            estilo_normal
                        )
                    ]
                ],
                colWidths=[
                    57 * mm,
                    57 * mm,
                    57 * mm
                ]
            )

            resumo.setStyle(
                TableStyle([
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        CINZA_CLARO
                    ),
                    (
                        "BACKGROUND",
                        (0, 1),
                        (-1, 1),
                        BRANCO
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#D1D5DB")
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (-1, -1),
                        "CENTER"
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE"
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        9
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        9
                    )
                ])
            )

            elementos.append(resumo)

            # ==================================================
            # DESPESAS POR CATEGORIA
            # ==================================================

            elementos.append(
                Paragraph(
                    "Despesas por categoria",
                    estilo_secao
                )
            )

            if categorias:

                dados_categorias = [
                    [
                        Paragraph("<b>Categoria</b>", estilo_normal),
                        Paragraph("<b>Valor gasto</b>", estilo_normal)
                    ]
                ]

                for categoria, valor in sorted(
                    categorias.items(),
                    key=lambda x: x[1],
                    reverse=True
                ):

                    dados_categorias.append(
                        [
                            Paragraph(
                                categoria,
                                estilo_normal
                            ),
                            Paragraph(
                                kz(valor),
                                estilo_normal
                            )
                        ]
                    )

                tabela_categorias = Table(
                    dados_categorias,
                    colWidths=[
                        100 * mm,
                        71 * mm
                    ]
                )

                tabela_categorias.setStyle(
                    TableStyle([
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            VERDE
                        ),
                        (
                            "TEXTCOLOR",
                            (0, 0),
                            (-1, 0),
                            BRANCO
                        ),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.HexColor("#D1D5DB")
                        ),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [
                                BRANCO,
                                CINZA_CLARO
                            ]
                        ),
                        (
                            "ALIGN",
                            (1, 1),
                            (1, -1),
                            "RIGHT"
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            7
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            7
                        )
                    ])
                )

                elementos.append(
                    tabela_categorias
                )

            else:

                elementos.append(
                    Paragraph(
                        "Não existem despesas neste mês.",
                        estilo_pequeno
                    )
                )

            # ==================================================
            # ORÇAMENTOS
            # ==================================================

            elementos.append(
                Paragraph(
                    "Orçamentos",
                    estilo_secao
                )
            )

            dados_orcamentos = [
                [
                    Paragraph("<b>Categoria</b>", estilo_normal),
                    Paragraph("<b>Limite</b>", estilo_normal),
                    Paragraph("<b>Gasto</b>", estilo_normal),
                    Paragraph("<b>Estado</b>", estilo_normal)
                ]
            ]

            for orcamento in orcamentos:

                categoria = orcamento.get(
                    "category",
                    "Outros"
                )

                limite, gasto = orcamento_do_mes(
                    categoria,
                    ano,
                    mes
                )

                if limite is None:
                    continue

                if gasto > limite:

                    estado = "Ultrapassado"

                elif limite > 0 and gasto >= limite * 0.8:

                    estado = "Próximo do limite"

                else:

                    estado = "Dentro do limite"

                dados_orcamentos.append(
                    [
                        Paragraph(
                            categoria,
                            estilo_normal
                        ),
                        Paragraph(
                            kz(limite),
                            estilo_normal
                        ),
                        Paragraph(
                            kz(gasto),
                            estilo_normal
                        ),
                        Paragraph(
                            estado,
                            estilo_normal
                        )
                    ]
                )

            if len(dados_orcamentos) > 1:

                tabela_orcamentos = Table(
                    dados_orcamentos,
                    colWidths=[
                        48 * mm,
                        40 * mm,
                        40 * mm,
                        43 * mm
                    ]
                )

                tabela_orcamentos.setStyle(
                    TableStyle([
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            VERDE
                        ),
                        (
                            "TEXTCOLOR",
                            (0, 0),
                            (-1, 0),
                            BRANCO
                        ),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.HexColor("#D1D5DB")
                        ),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [
                                BRANCO,
                                CINZA_CLARO
                            ]
                        ),
                        (
                            "ALIGN",
                            (1, 1),
                            (2, -1),
                            "RIGHT"
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            7
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            7
                        )
                    ])
                )

                elementos.append(
                    tabela_orcamentos
                )

            else:

                elementos.append(
                    Paragraph(
                        "Nenhum orçamento disponível.",
                        estilo_pequeno
                    )
                )

            # ==================================================
            # NOVA PÁGINA
            # ==================================================

            elementos.append(
                PageBreak()
            )

            elementos.append(
                Paragraph(
                    "Transações do mês",
                    estilo_secao
                )
            )

            # ==================================================
            # TRANSAÇÕES
            # ==================================================

            dados_transacoes = [
                [
                    Paragraph("<b>Data</b>", estilo_normal),
                    Paragraph("<b>Descrição</b>", estilo_normal),
                    Paragraph("<b>Categoria</b>", estilo_normal),
                    Paragraph("<b>Tipo</b>", estilo_normal),
                    Paragraph("<b>Valor</b>", estilo_normal)
                ]
            ]

            for item in transacoes_mes:

                data = obter_data_transacao(item)

                if data:

                    data_formatada = data.strftime(
                        "%d/%m/%Y"
                    )

                else:

                    data_formatada = item.get(
                        "date",
                        "-"
                    )

                valor = get_value_transacao(item)

                tipo = item.get(
                    "type",
                    "-"
                )

                valor_texto = kz(valor)

                if tipo == "Receita":
                    valor_texto = "+" + valor_texto
                else:
                    valor_texto = "-" + valor_texto

                dados_transacoes.append(
                    [
                        Paragraph(
                            data_formatada,
                            estilo_pequeno
                        ),
                        Paragraph(
                            item.get(
                                "title",
                                "Sem descrição"
                            ),
                            estilo_normal
                        ),
                        Paragraph(
                            item.get(
                                "category",
                                "Outros"
                            ),
                            estilo_pequeno
                        ),
                        Paragraph(
                            tipo,
                            estilo_pequeno
                        ),
                        Paragraph(
                            valor_texto,
                            estilo_normal
                        )
                    ]
                )

            if len(dados_transacoes) > 1:

                tabela_transacoes = Table(
                    dados_transacoes,
                    colWidths=[
                        25 * mm,
                        52 * mm,
                        34 * mm,
                        25 * mm,
                        35 * mm
                    ],
                    repeatRows=1
                )

                tabela_transacoes.setStyle(
                    TableStyle([
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            VERDE
                        ),
                        (
                            "TEXTCOLOR",
                            (0, 0),
                            (-1, 0),
                            BRANCO
                        ),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.4,
                            colors.HexColor("#D1D5DB")
                        ),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [
                                BRANCO,
                                CINZA_CLARO
                            ]
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "MIDDLE"
                        ),
                        (
                            "ALIGN",
                            (4, 1),
                            (4, -1),
                            "RIGHT"
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            6
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            6
                        )
                    ])
                )

                elementos.append(
                    tabela_transacoes
                )

            else:

                elementos.append(
                    Paragraph(
                        "Nenhuma transação neste mês.",
                        estilo_pequeno
                    )
                )

            # ==================================================
            # RODAPÉ
            # ==================================================

            def rodape(canvas, doc):
                canvas.saveState()
                canvas.setFont(
                    "Helvetica",
                    8
                )
                canvas.setFillColor(
                    CINZA
                )
                canvas.drawString(
                    15 * mm,
                    10 * mm,
                    "KwanzaMeter — Relatório Financeiro"
                )
                canvas.drawRightString(
                    A4[0] - 15 * mm,
                    10 * mm,
                    f"Página {doc.page}"
                )

                canvas.restoreState()

            # ==================================================
            # GERAR
            # ==================================================

            documento.build(
                elementos,
                onFirstPage=rodape,
                onLaterPages=rodape
            )

            pdf_bytes = buffer.getvalue()

            buffer.close()

            # ==================================================
            # GUARDAR PDF
            # ==================================================

            nome_arquivo = (
                f"KwanzaMeter_Relatorio_"
                f"{ano}_{mes:02d}.pdf"
            )

            caminho = await file_picker.save_file(
                dialog_title="Guardar relatório PDF",
                file_name=nome_arquivo,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["pdf"],
                src_bytes=pdf_bytes
            )

            if caminho:
                page.show_dialog(
                    ft.SnackBar(
                        content=ft.Text(
                            "Relatório PDF guardado com sucesso."
                        )
                    )
                )
                page.update()
        except Exception as erro:

            print(
                "Erro ao gerar PDF:",
                erro
            )
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(
                        f"Erro ao gerar PDF: {erro}"
                    )
                )
            )
            page.update()

    def mostrar_lista_relatorios():
        relatorio_detalhes.controls.clear()
        lista_relatorios.controls.clear()
        meses = obter_meses_relatorios()

        if not meses:
            lista_relatorios.controls.append(
                ft.Container(
                    padding=30,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[

                            ft.Icon(
                                ft.Icons.INSERT_CHART_OUTLINED,
                                size=50,
                                color=cr.Colors.TEXT_SECUNDARIA
                            ),

                            ft.Text(
                                "Ainda não existem relatórios.",
                                size=14,
                                weight="bold",
                                color=cr.Colors.TEXT_PRINCIPAL
                            ),

                            ft.Text(
                                "Cria algumas transações para gerar os relatórios mensais.",
                                size=11,
                                color=cr.Colors.TEXT_SECUNDARIA,
                                text_align=ft.TextAlign.CENTER
                            )
                        ]
                    )
                )
            )

        else:
            ano_atual = None
            for ano, mes in meses:
                # Título do ano
                if ano != ano_atual:
                    ano_atual = ano
                    lista_relatorios.controls.append(
                        ft.Text(
                            str(ano),
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=cr.Colors.TEXT_PRINCIPAL
                        )
                    )

                quantidade = len(
                    transacoes_do_mes(
                        ano,
                        mes
                    )
                )

                lista_relatorios.controls.append(
                    ft.Container(
                        bgcolor=cr.Colors.CARDS,
                        border_radius=16,
                        padding=15,
                        on_click=lambda e, a=ano, m=mes:
                            mostrar_relatorio_mes(a, m),

                        content=ft.Row(
                            controls=[

                                ft.Container(
                                    width=45,
                                    height=45,
                                    border_radius=23,
                                    bgcolor=cr.Colors.BACKGROUND,
                                    alignment=ft.Alignment.CENTER,

                                    content=ft.Icon(
                                        ft.Icons.INSERT_CHART_OUTLINED,
                                        color=cr.Colors.PRINCIPAL,
                                        size=22
                                    )
                                ),

                                ft.Column(
                                    expand=True,
                                    spacing=3,
                                    controls=[

                                        ft.Text(
                                            nome_mes(mes),
                                            size=14,
                                            weight="bold",
                                            color=cr.Colors.TEXT_PRINCIPAL
                                        ),

                                        ft.Text(
                                            f"{quantidade} transação"
                                            + (
                                                "s"
                                                if quantidade != 1
                                                else ""
                                            ),
                                            size=10,
                                            color=cr.Colors.TEXT_SECUNDARIA
                                        )
                                    ]
                                ),

                                ft.Icon(
                                    ft.Icons.ARROW_FORWARD_IOS,
                                    size=16,
                                    color=cr.Colors.TEXT_SECUNDARIA
                                )
                            ]
                        )
                    )
                )

        page.update()
    
    def create_transacao(item):
        icon_name = item.get("icon", "MORE_HORIZ")
        icon = getattr(
            ft.Icons,
            icon_name,
            ft.Icons.MORE_HORIZ
        )
        tipo = item.get("type", "Despesa")
        titulo = item.get("title", "Sem descrição")
        valor_texto = item.get("value", "Kz 0,00")
        hora = item.get("hour", "")

        if tipo == "Receita":
            cor = cr.Colors.GREEN
            fundo = "#EAF8EF"
        else:
            cor = cr.Colors.RED
            fundo = "#FDECEC"
        
        return ft.Container(
            bgcolor= cr.Colors.CARDS,
            border_radius=16,
            padding=10,
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=38,
                        height=38,
                        border_radius=20,
                        bgcolor=fundo,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Icon(
                            icon,
                            color=cor,
                            size=19
                        )
                    ),
                    
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Text(titulo, size=12, weight='bold'),
                            ft.Text(tipo, size=9, color=cr.Colors.SECUDARIA)
                        ]
                    ),
                    
                    ft.Column(
                        spacing=2,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(valor_texto, size=10, weight='bold', color=cor),
                            ft.Text(hora, size=9, color=cr.Colors.SECUDARIA)
                        ]
                    )
                ]
            )
        )
    
    def valor_despesa_do_mes(categoria, ano=None, mes=None):

        if ano is None or mes is None:
            hoje = datetime.date.today()
            ano = hoje.year
            mes = hoje.month

        total = 0.0

        for item in transacoes:
            if item.get("type") != "Despesa":
                continue
            
            if item.get("category", "Outros") != categoria:
                continue
            
            data_item = item.get("date", "")

            if data_item == "Hoje":
                data_transacao = datetime.date.today()
            else:
                try:
                    data_transacao = datetime.datetime.strptime(
                        data_item,
                        "%d/%m/%y"
                    ).date()
                except ValueError:
                    continue
            if data_transacao.year == ano and data_transacao.month == mes:
                total += get_value_transacao(item)
        return total
    
    def apagar_orcamento(indice):
        
        def confirmar(e):
            orcamentos.pop(indice)
            save_orcamentos()
            update_orcamentos()
            page.pop_dialog()
            page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Apagar Orçamento", weight='bold'),
            content=ft.Text("Tens a certeza que queres eliminar este orçamento?"),
            actions=[
                ft.TextButton('Esquece', on_click=lambda e: page.pop_dialog()),
                ft.TextButton('Apaga', icon=ft.Icons.DELETE, on_click=confirmar)
            ]
        )
        page.show_dialog(dialog)
    
    def editar_orcamento(indice):
        item = orcamentos[indice]
        
        categoria = ft.Dropdown(
            label="Categoria",
            value=item.get("category", "Outros"),
            width=400,
            border_radius=20,
            bgcolor=cr.Colors.CARDS,
            border_color=cr.Colors.TEXT_SECUNDARIA,
            label_style=ft.TextStyle(color=cr.Colors.TEXT_SECUNDARIA),
            text_style=ft.TextStyle(color=cr.Colors.TEXT_PRINCIPAL),
            options=[
                ft.DropdownOption(x)
                for x in [
                    "Alimentação",
                    "Transporte",
                    "Moradia",
                    "Lazer",
                    "Educação",
                    "Saúde",
                    "Outros"
                ]
            ]
        )
        
        limite = ft.TextField(
            label="Limite Mensal",
            prefix="Kz ",
            value=str(item.get("limit", "")),
            width=400,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=20,
            bgcolor=cr.Colors.CARDS,
            border_color=cr.Colors.TEXT_SECUNDARIA,
            label_style=ft.TextStyle(cr.Colors.TEXT_SECUNDARIA),
            text_style=ft.TextStyle(color=cr.Colors.TEXT_PRINCIPAL)
        )
        
        mensagem = ft.Text("", size=13, color=cr.Colors.RED)
        
        def salvar_edicao(e):
            nova_categoria = categoria.value
            limite_texto = limite.value.strip()
            
            if not nova_categoria:
                mensagem.value = 'Selecione uma Categoria.'
                page.update()
                return
            
            if not limite_texto:
                mensagem.value = 'Insira o limite mensal'
                page.update()
                return
            
            if not limite_texto:
                mensagem.value = "Insira o limite mensal"
                page.update()
                return
            
            try:
                novo_limite = float(
                    limite_texto
                    .replace(".", "")
                    .replace(",", ".")
                )
                
                if novo_limite <= 0:
                    raise ValueError
            except ValueError:
                mensagem.value = "Insira um valor válido."
                page.update()
                return
            
            for i, outro in enumerate(orcamentos):
                if i != indice and outro.get("category") == nova_categoria:
                    mensagem.value = ('Já existe um orçamento para esta categoria.')
                    page.update()
                    return
            
            orcamentos[indice]["category"] = nova_categoria
            orcamentos[indice]["limit"] = novo_limite
            save_orcamentos()
            update_orcamentos()
            page.pop_dialog()
            page.update()
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar Orçamento", weight='bold'),
            content=ft.Column(
                tight=True,
                spacing=12,
                controls=[categoria, limite, mensagem]
            ),
            actions=[
                ft.TextButton(
                    'Esquece',
                    on_click=lambda e: page.pop_dialog()
                ),
                ft.Button(
                    'Salvar',
                    icon=ft.Icons.SAVE,
                    on_click=salvar_edicao
                )
            ]
        )
        page.show_dialog(dialog)
    
    def cartao_orcamento(item, indice):

        categoria = item.get("category", "Outros")
        limite = float(item.get("limit", 0) or 0)

        hoje = datetime.date.today()
        mes_orcamento = item.get(
            "month",
            hoje.strftime("%Y-%m")
        )

        try:
            ano_orcamento, numero_mes = map(
                int,
                mes_orcamento.split("-")
            )
        except ValueError:
            ano_orcamento = hoje.year
            numero_mes = hoje.month

        gasto = valor_despesa_do_mes(
            categoria,
            ano_orcamento,
            numero_mes
        )

        progresso = gasto / limite if limite > 0 else 0

        icones = {
            "Alimentação": ft.Icons.RESTAURANT,
            "Transporte": ft.Icons.DIRECTIONS_BUS,
            "Moradia": ft.Icons.HOME,
            "Lazer": ft.Icons.SPORTS_ESPORTS,
            "Educação": ft.Icons.SCHOOL,
            "Saúde": ft.Icons.MEDICAL_SERVICES,
            "Outros": ft.Icons.MORE_HORIZ,
        }

        if progresso >= 1:
            status = "Orçamento ultrapassado"
            status_cor = cr.Colors.RED

        elif progresso >= 0.8:
            status = "Atenção: próximo do limite"
            status_cor = cr.Colors.RED

        else:
            restante = max(limite - gasto, 0)

            status = (
                f"Restante: Kz "
                f"{restante:,.2f}"
            )

            status_cor = cr.Colors.GREEN

        option = ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT,
            items=[
                ft.PopupMenuItem(
                    content=ft.Text("Editar"),
                    on_click=lambda e, i=indice: editar_orcamento(i)
                ),
                ft.PopupMenuItem(
                    content=ft.Text("Apagar"),
                    on_click=lambda e, i=indice: apagar_orcamento(i)
                )
            ]
        )

        return ft.Container(
            bgcolor=cr.Colors.CARDS,
            border_radius=16,
            padding=14,

            content=ft.Column(
                spacing=8,

                controls=[

                    ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,

                        controls=[

                            ft.Container(
                                width=40,
                                height=40,
                                border_radius=20,
                                bgcolor=cr.Colors.BACKGROUND,
                                alignment=ft.Alignment.CENTER,

                                content=ft.Icon(
                                    icones.get(
                                        categoria,
                                        ft.Icons.MORE_HORIZ
                                    ),
                                    color=cr.Colors.PRINCIPAL,
                                    size=20
                                )
                            ),

                            ft.Column(
                                expand=True,
                                spacing=2,

                                controls=[

                                    ft.Text(
                                        categoria,
                                        size=14,
                                        weight='bold',
                                        color=cr.Colors.TEXT_PRINCIPAL
                                    ),

                                    ft.Text(
                                        f"Kz {gasto:,.2f} / Kz {limite:,.2f}",
                                        size=11,
                                        color=cr.Colors.TEXT_SECUNDARIA
                                    )
                                ]
                            ),

                            ft.Text(
                                f"{round(progresso * 100)}%",
                                size=13,
                                weight='bold',
                                color=status_cor
                            ),

                            option
                        ]
                    ),

                    ft.ProgressBar(
                        value=min(progresso, 1),
                        height=7,

                        color=(
                            cr.Colors.RED
                            if progresso >= 1
                            else cr.Colors.PRINCIPAL
                        ),

                        bgcolor=cr.Colors.BACKGROUND
                    ),

                    ft.Text(
                        status,
                        size=11,
                        color=status_cor,
                        weight=ft.FontWeight.BOLD
                    )
                ]
            )
        )

    def update_orcamentos():

        lista_orcamentos.controls.clear()
        mes_atual = datetime.date.today().strftime("%Y-%m")
        orcamentos_mes = [
            item
            for item in orcamentos
            if item.get("month", mes_atual) == mes_atual
        ]

        if not orcamentos_mes:
            lista_orcamentos.alignment = ft.MainAxisAlignment.CENTER
            lista_orcamentos.controls.append(
                ft.Container(
                    padding=30,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(
                                ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED,
                                size=50,
                                color=cr.Colors.TEXT_SECUNDARIA
                            ),

                            ft.Text(
                                "Nenhum orçamento criado para este mês.",
                                size=14,
                                weight='bold',
                                color=cr.Colors.TEXT_PRINCIPAL
                            )
                        ]
                    )
                )
            )
        else:
            lista_orcamentos.alignment = None
            for indice, item in enumerate(orcamentos):
                if item.get("month", mes_atual) != mes_atual:
                    continue
                lista_orcamentos.controls.append(
                    cartao_orcamento(item, indice)
                )
        # O Flet 1.x atualiza automaticamente os controles alterados pelo handler.
        # Não chamar update() aqui enquanto a coluna pode estar desmontada.
    
    async def check_orcamento(categoria, valor_despesa):
        usuario = usuarios_logados[0]
        
        if not usuario:
            return
        
        for orcamento in orcamentos:
            
            if orcamento.get("category") != categoria:
                continue
    
            limite = float(orcamento.get("limit", 0)or 0)
            if limite <= 0:
                continue
            
            gasto_atual = valor_despesa_do_mes(categoria)
            
            # Check if pass
            if gasto_atual > limite:
                mes_atual = datetime.date.today().strftime("%Y-%m")
                
                # Evitar mandar a mesma notificação varias vez
                last_aviso = orcamento.get("last_aviso", "")
                if last_aviso == mes_atual:
                    return
                
                # Guardar que já avisamos neste mês
                orcamento["last_aviso"] = mes_atual
                save_orcamentos()
                
                valor_excedido = gasto_atual - limite
                valor_formatado = (
                    f"{valor_excedido:,.2f}"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                )
                
                mensagem = (
                    f"O orçamento de {categoria} foi ultrapassado"
                    f"em {valor_formatado} Kz"
                )
                
                page.show_dialog(
                    ft.SnackBar(
                        bgcolor=cr.Colors.SECUDARIA,
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.WARNING, color=cr.Colors.CARDS),
                                ft.Column(
                                    spacing=2,
                                    controls=[
                                        ft.Text("Brincaste mal com o dinheiro!", weight='bold', color=cr.Colors.CARDS),
                                        ft.Text(mensagem, color=cr.Colors.CARDS)
                                    ]
                                )
                            ]
                        )
                    )
                )
                try:
                    permitido = await notificacoes.request_permissions()
                    
                    if permitido:
                        await notificacoes.show_notification(
                            notification_id=int(
                                datetime.datetime.now().timestamp()
                            ),
                            title="Brincaste Mal com o dinheiro!",
                            body=mensagem,
                            importance="high"
                        )
                except Exception as erro:
                    print("Erro ao enviar notificação: ",erro)
                return
    def save_orcamentos():
        usuario = usuarios_logados[0]
        if not usuario: return
        usuarios[usuario]["orcamentos"] = orcamentos.copy()
        save_user_data(usuarios)
    
    def update_list():
        lista.controls.clear()
        date_atual = None
        if not transacoes:
            lista.alignment = ft.MainAxisAlignment.CENTER
            lista.controls.append(
                ft.Container(
                    padding=30,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.PAYMENT, size=42, color=cr.Colors.TEXT_SECUNDARIA),
                            ft.Text("Nem uma Transação criada.", size=14, weight='bold', color=cr.Colors.TEXT_PRINCIPAL)
                        ]
                    )
                )
            )
        else:
            lista.alignment = None
            for item in transacoes:
                data_item = item.get("date", "Sem data")
                if data_item != date_atual:
                    date_atual = data_item
                    lista.controls.append(
                        ft.Text(
                            data_item,
                            size=11,
                            color=cr.Colors.TEXT_SECUNDARIA,
                            weight=ft.FontWeight.W_500
                        ),
                    )
                lista.controls.append(
                    create_transacao(item)
                )

    def update_dashboard():
        lista_dashboard.controls.clear()
        
        for item in transacoes[:5]:
            lista_dashboard.controls.append(create_transacao(item))
        
        recebido = 0
        despesas = 0
        
        for item in transacoes:
            valor = get_value_transacao(item)

            if item.get("type") == "Receita":
                recebido += valor
            elif item.get("type") == "Despesa":
                despesas += valor
        saldo = recebido - despesas
        received_total.value = f"Kz {recebido:,.2f}"
        spent_total.value = f"Kz {despesas:,.2f}"
        saldo_total.value = f"Kz {saldo:,.2f}"

        atualizar_donut()
        page.update()
    
    def kamba_IA(indice):
        title_display.value = "Kamba IA"
        page.clean()
        
        # ========================================================
        # ID ÚNICO DESTA CONVERSA
        # ========================================================

        conversa_id = str(uuid.uuid4())
        
        
        pergunta = ft.TextField(
            hint_text="Qual é tua duvidas hoje? ",
            multiline=True,
            expand=True,
            border_radius=15,
            text_size=13,
            border_width=0,
            bgcolor=cr.Colors.BACKGROUND
        )
        
        chat = ft.Column(
            expand=True,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH
        )
        
        # Mensagem Inicial 
        chat.controls.append(
            ft.Container(
                padding=15,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.CircleAvatar(scale=2, content=ft.Icon(icon=ft.Icons.SMART_TOY), bgcolor=cr.Colors.PRINCIPAL_BLACK, color=cr.Colors.CARDS),
                        ft.Text(f"\n Olá, {usuarios_logados[0]}!", size=20, color=cr.Colors.TEXT_PRINCIPAL, weight='bold'),
                        ft.Text(
                            "Vou te ajudar a gerir o teu dinheiro e impedir que sejas o pagate das festas e das amantes.",
                            size=13,
                            color=cr.Colors.TEXT_PRINCIPAL,
                            text_align=ft.TextAlign.CENTER
                        )
                    ]
                )
            )
        )
        
        # Enviar Pergunta
        async def send_question(e):
            text = pergunta.value.strip()
            if not text:
                return
            
            chat.controls.append(
                ft.Row(
                    controls=[
                    ft.Container(
                        bgcolor=cr.Colors.PRINCIPAL_BLACK,
                        padding=12,
                        width=290,
                        border_radius=15,
                        content=ft.Text(text, color=cr.Colors.CARDS, size=13)
                    )
                ], alignment=ft.MainAxisAlignment.END),
                
                
            )
            
            pergunta.value = ""
            page.update()
            
            loading = ft.Container(
                padding=12,
                border_radius=15,
                content=ft.Row(
                    controls=[
                        ft.ProgressRing(
                            width=16,
                            height=16,
                            stroke_width=2,
                            color=cr.Colors.PRINCIPAL
                        ),
                        ft.Text("Me deixa ainda pensar uma beca...", size=12, color=cr.Colors.TEXT_SECUNDARIA)
                    ], spacing=8
                )
            )
            
            
            loading_row = ft.Row(
                controls=[loading],
                alignment=ft.MainAxisAlignment.START
            )
            chat.controls.append(loading_row)
            page.update()

            # CHAMAR O BACKEND!!!!!!!!!!!!!!!!
            resposta = await asyncio.to_thread(
                perguntar_kamba,
                conversa_id,
                text
            )

            chat.controls.remove(loading_row)
            # Resposta do KAMBA
            chat.controls.append(
                ft.Row(
                    controls=[
                        ft.Container(
                            bgcolor=cr.Colors.IA,
                            padding=12,
                            border_radius=15,
                            width=290,
                            content=ft.Text(resposta, color=cr.Colors.TEXT_PRINCIPAL, size=13),
                        )
                    ], alignment=ft.MainAxisAlignment.START
                )
            )
            page.update()

        campo_pergunta = ft.Container(
            shadow=ft.BoxShadow(color=cr.Colors.TEXT_SECUNDARIA, blur_radius=10, offset=ft.Offset(0,6)),
            padding=5,
            bgcolor=cr.Colors.CARDS,
            border_radius=18,
            content=ft.Row(
                controls=[
                    pergunta,
                    ft.IconButton(icon=ft.CupertinoIcons.ARROW_UP_CIRCLE_FILL, icon_color=cr.Colors.PRINCIPAL, scale=1.5,tooltip="Enviar",on_click=send_question)
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
        IA = ft.Container(
            expand=True,
            padding=15,
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=chat,
                        expand=True,
                        padding=5
                    ),
                    campo_pergunta
                ],
                expand=True,
                spacing=10
            )
        )
        page.add(space, cabecario_IA, IA)
        page.update()
    
    def add_orcamento(e=None):
        categoria = ft.Dropdown(
            label="Categoria",
            width=1000,
            margin=5,
            border_radius=20,
            bgcolor=cr.Colors.CARDS,
            border_color=cr.Colors.TEXT_SECUNDARIA,
            label_style=ft.TextStyle(color=cr.Colors.TEXT_SECUNDARIA),
            text_style=ft.TextStyle(color=cr.Colors.TEXT_PRINCIPAL),
            options=[ft.DropdownOption(x) for x in ["Alimentação", "Transporte", "Moradia", "Lazer", "Educação", "Saúde", "Outros"]]
        )
        
        limite = ft.TextField(
            label="Limite mensal", 
            prefix="Kz ", 
            width=1000, 
            margin=5,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=20,
            bgcolor=cr.Colors.CARDS,
            border_color=cr.Colors.TEXT_SECUNDARIA,
            label_style=ft.TextStyle(color=cr.Colors.TEXT_SECUNDARIA),
            text_style=ft.TextStyle(color=cr.Colors.TEXT_PRINCIPAL),
        )
        
        mensagem = ft.Text("", size=14, color=cr.Colors.RED, weight='bold')
        
        def salver(e):
            nome_categoria = categoria.value
            limite_texto = limite.value.strip()
            if not nome_categoria:
                mensagem.value = "Selecione uma Categoria."; page.update(); return
            if not limite_texto:
                mensagem.value = "Insira o limite mensal."; page.update(); return
            try:
                limite_numero = float(limite_texto.replace(".", "").replace(",","."))
                if limite_numero <= 0: raise ValueError
            except ValueError:
                mensagem.value = "Insira um valor válido."; page.update(); return
            
            mes_atual = datetime.date.today().strftime("%Y-%m")
            if any(
                item.get("category") == nome_categoria 
                and item.get("month") == mes_atual
                for item in orcamentos
            ):
                mensagem.value = "Já existe um orçamento para esta categoria."
                page.update()
                return
        
            orcamentos.append({
                "category": nome_categoria, 
                "limit": limite_numero,
                "month": mes_atual,
                "last_aviso": ""
            })
            save_orcamentos()
            update_orcamentos()
            change_display(2)
        
        tela_orcamento = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Container(
                    bgcolor=cr.Colors.CARDS,
                    padding=10,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=20,
                        controls=[
                            ft.Row([ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: change_display(2))]),
                            categoria, limite, mensagem,
                            ft.Button(
                                "Salvar", 
                                icon=ft.Icons.ADD,
                                width=500,
                                height=50,
                                on_click=salver,
                                style=ft.ButtonStyle(
                                    text_style=ft.TextStyle(weight='bold'),
                                    padding=10,
                                    color=cr.Colors.CARDS,
                                    bgcolor={ft.ControlState.DEFAULT: cr.Colors.PRINCIPAL_BLACK}
                                )
                            )
                        ]
                    )
                )
            ]
        )
        page.clean()
        page.add(space, tela_orcamento)
        page.update()

    today = datetime.date.today()
    title_display = ft.Text("Bem-vindo, Utente", size=20, weight=ft.FontWeight.BOLD, color=cr.Colors.TEXT_PRINCIPAL)
    names_display = ["Bem-Vindo, Utente", "Transações", "Orçamentos", "Relatórios"]
    space = ft.Container(height=50)
    cabecario = ft.Container(
        padding=10,
        content=ft.Column(
            controls=[
                ft.Row([
                        title_display,
                        ft.IconButton(icon=ft.Icons.LOGOUT_ROUNDED, icon_color=cr.Colors.TEXT_PRINCIPAL, on_click=logout)
                    ],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Hoje, " + today.strftime("%d/%m/%Y"), size=12, color=cr.Colors.TEXT_SECUNDARIA)])
            ],
            spacing=5
        ),
    )
    cabecario_trans = ft.Container(
        padding=10,
        content=ft.Column(
            controls=[
                ft.Row([
                        title_display,
                        ft.IconButton(icon=ft.Icons.ADD_CIRCLE, icon_color=cr.Colors.TEXT_PRINCIPAL, on_click=add_transacao)
                    ],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Hoje, " + today.strftime("%d/%m/%Y"), size=12, color=cr.Colors.TEXT_SECUNDARIA)])
            ],
            spacing=5
        ),
    )
    cabecario_IA = ft.Container(
        padding=10,
        content=ft.Column(
            controls=[
                ft.Row([
                        title_display,
                        ft.IconButton(icon=ft.CupertinoIcons.SQUARE_PENCIL_FILL, icon_color=cr.Colors.TEXT_PRINCIPAL, on_click=lambda e: kamba_IA(0))
                    ],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Hoje, " + today.strftime("%d/%m/%Y"), size=12, color=cr.Colors.TEXT_SECUNDARIA)])
            ],
            spacing=5
        ),
    )
    cabecario_orca = ft.Container(
        padding=10,
        content=ft.Column(
            controls=[
                ft.Row([
                        title_display,
                        ft.IconButton(icon=ft.Icons.ADD_CIRCLE, icon_color=cr.Colors.TEXT_PRINCIPAL, on_click=add_orcamento)
                    ],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Hoje, " + today.strftime("%d/%m/%Y"), size=12, color=cr.Colors.TEXT_SECUNDARIA)])
            ],
            spacing=5
        ),
    )
    cabecario_relatorios = ft.Container(
        padding=10,
        content=ft.Column(
            controls=[
                ft.Row([
                    title_display
                ],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Relatório Financeiros", size=12, color=cr.Colors.TEXT_SECUNDARIA)])
            ],
            spacing=5
        ),
    )

    CATEGORIA = [
        {"nome": "Moradia", "cor": "#5B2EFF"},
        {"nome": "Alimentação", "cor": "#8B6CFF"},
        {"nome": "Transporte", "cor": "#22C55E"},
        {"nome": "Lazer", "cor": "#EF4444"},
        {"nome": "Outros", "cor": "#F59E0B"},
    ]
    ORDEM_DONUT = ["Moradia", "Alimentação", "Transporte", "Lazer", "Outros"]

    def linha_legenda(nome: str, percentagem: int, cor: str):
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=10,
                    tight=True,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(width=11, height=11, bgcolor=cor, border_radius=5),
                        ft.Text(nome, size=12, color=cr.Colors.TEXT_PRINCIPAL, weight=ft.FontWeight.W_500),
                    ]
                ),
                ft.Text(f"{percentagem}%", size=12, color=cr.Colors.TEXT_SECUNDARIA, weight=ft.FontWeight.W_600)
            ]
        )
    def get_value_transacao(item):
        if "amount" in item:
            try:
                return float(item["amount"])
            except (ValueError, TypeError):
                return 0
        
        valor = item.get("value", "0")
        
        valor = (
            valor
            .replace("Kz", "")
            .replace("+", "")
            .replace("-", "")
            .replace(" ", "")
            .replace(",", "")
        )
        
        try:
            return float(valor)
        except ValueError:
            return 0
    
    donut = fc.PieChart(
        width=138,
        height=138,
        sections_space=0,
        center_space_radius=42,
        center_space_color=cr.Colors.BACKGROUND,
        start_degree_offset=270,
        sections=[]
    )
    legenda_donut = ft.Column(
        expand=True,
        spacing=11,
        controls=[]
    )
    
    def atualizar_donut():
        por_nome = {item["nome"]: item for item in CATEGORIA}

        totais = {
            "Moradia": 0,
            "Alimentação": 0,
            "Transporte": 0,
            "Lazer": 0,
            "Outros": 0,
        }

        # Calcular despesas
        for item in transacoes:

            if item.get("type") != "Despesa":
                continue
            categoria = item.get("category", "Outros")
            if categoria not in totais:
                categoria = "Outros"
            valor = get_value_transacao(item)
            totais[categoria] += valor
        total_despesas = sum(totais.values())

        secoes_donut = []
        legendas = []

        # Existem despesas
        if total_despesas > 0:
            for nome in ORDEM_DONUT:
                valor = totais[nome]
                if valor <= 0:
                    continue
                percentagem = (valor / total_despesas) * 100
                cor = por_nome[nome]["cor"]

                secoes_donut.append(
                    fc.PieChartSection(
                        value=valor,
                        color=cor,
                        radius=26
                    )
                )

                legendas.append(
                    linha_legenda(
                        nome=nome,
                        percentagem=round(percentagem),
                        cor=cor
                    )
                )
        else:
            secoes_donut.append(
                fc.PieChartSection(
                    value=1,
                    color="#E5E7EB",
                    radius=26
                )
            )

            legendas.append(
                linha_legenda(
                    nome="Sem despesas",
                    percentagem=0,
                    cor="#E5E7EB"
                )
            )
        # Atualizar o gráfico existente
        donut.sections = secoes_donut
        # Atualizar a legenda existente
        legenda_donut.controls = legendas


    def cartao_resumo() -> ft.Container:
        return ft.Container(
            expand=True,
            height=300,
            margin=10,
            bgcolor=cr.Colors.CARDS,
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.only(
                left=22,
                right=24,
                top=20,
                bottom=22
            ),
            border_radius=28,
            shadow=ft.BoxShadow(
                color=cr.Colors.TEXT_SECUNDARIA,
                blur_radius=2,
                offset=ft.Offset(0,3)
            ),
            content=ft.Column(
                spacing=16,
                tight=True,
                controls=[
                    ft.Text(
                        "Resumo de Despesas do Mês",
                        size=20,
                        weight='bold',
                        color=cr.Colors.TEXT_PRINCIPAL
                    ),
                    ft.Row(
                        spacing=18,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,

                        controls=[
                            donut,

                            legenda_donut
                        ]
                    )
                ]
            )
        )
    
    received_total = ft.Text("Kz 0,00", size=13, weight=ft.FontWeight.BOLD, color=cr.Colors.GREEN)
    spent_total = ft.Text("Kz 0,00", size=13, weight=ft.FontWeight.BOLD, color=cr.Colors.RED)
    saldo_total = ft.Text("Kz 0,00",size=30, weight=ft.FontWeight.BOLD, color=cr.Colors.BACKGROUND)
    
    content = [
        ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            controls=[
                ft.Container(
                    padding=10,
                    content=ft.Column([
                        ft.Container(
                            padding=10,
                            expand=True,
                            # margin=10,
                            bgcolor=cr.Colors.PRINCIPAL_BLACK,
                            shadow=ft.BoxShadow(color=cr.Colors.TEXT_SECUNDARIA, blur_radius=2, offset=ft.Offset(0,6)),
                            border_radius=20,
                            # width=400,
                            height=180,
                            content=ft.Column([
                                ft.Row([
                                      ft.Text("Saldo Total", size=12, color=cr.Colors.BACKGROUND),
                                      ft.Icon(ft.Icons.ATTACH_MONEY, color=cr.Colors.BACKGROUND)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                saldo_total
                            ])
                        ),
                        ft.Row(
                            controls=[
                                ft.Container(
                                    padding=10,
                                    expand=True,
                                    # width=(page.window.width),
                                    height=120,
                                    shadow=ft.BoxShadow(color=cr.Colors.TEXT_SECUNDARIA, blur_radius=2, offset=ft.Offset(0,3)),
                                    bgcolor=cr.Colors.CARDS,
                                    border_radius=10,
                                    content=ft.Column([
                                        ft.Text("Recebido", size=12, color=cr.Colors.TEXT_PRINCIPAL),
                                        received_total,
                                        ft.Text("Este Mês", size=12, color=cr.Colors.TEXT_SECUNDARIA),
                                    ])
                                ),
                                ft.Container(
                                    padding=10,
                                    expand=True,
                                    # width=(page.window.width),
                                    height=120,
                                    shadow=ft.BoxShadow(color=cr.Colors.TEXT_SECUNDARIA, blur_radius=2, offset=ft.Offset(0,3)),
                                    bgcolor=cr.Colors.CARDS,
                                    border_radius=10,
                                    content=ft.Column([
                                        ft.Text("Despesas", size=12, color=cr.Colors.TEXT_PRINCIPAL),
                                        spent_total,
                                        ft.Text("Este Mês", size=12, color=cr.Colors.TEXT_SECUNDARIA),
                                    ])
                                ),
                            ], alignment=ft.MainAxisAlignment.SPACE_AROUND
                        ),
                        cartao_resumo(),
                        ft.Container(
                            padding=10,
                            content=ft.Column(
                                spacing=10,
                                controls=[
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        controls=[
                                            ft.Text("Transações Recentes", size=18, weight='bold', color=cr.Colors.TEXT_PRINCIPAL),
                                            ft.Button(
                                                "Ver Todas", 
                                                on_click=lambda e: change_display(1),
                                                style=ft.ButtonStyle(
                                                    padding=10,
                                                    color=cr.Colors.CARDS,
                                                    bgcolor={
                                                        ft.ControlState.DEFAULT: cr.Colors.PRINCIPAL
                                                    }
                                                )
                                            )
                                        ]
                                    ),
                                    lista_dashboard
                                ]
                            )
                        )
                    ])
                ),
            ]
        ),
        ft.Column(
            expand=True,
            spacing=12,
            controls=[lista]
        ),
        ft.Column(
            expand=True,
            spacing=12,
            controls=[lista_orcamentos]
        ),
        ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Container(
                    padding=10,
                    content=ft.Column(
                        spacing=15,
                        controls=[
                            lista_relatorios,
                            relatorio_detalhes
                        ])
                ),
            ]
        ),
    ]
    
    menu = [
        ft.TextButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.HOME, color=cr.Colors.TEXT_SECUNDARIA), ft.Text("Início", style=ft.TextStyle(color=cr.Colors.TEXT_SECUNDARIA))],
                spacing=4,
                tight=True
            ),
            on_click=lambda e: change_display(0)
        ),
        ft.TextButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.PAYMENT, color=cr.Colors.TEXT_SECUNDARIA), ft.Text("Transações", style=ft.TextStyle(color=cr.Colors.TEXT_SECUNDARIA))],
                spacing=4,
                tight=True
            ),
            on_click=lambda e: change_display(1)
        ),
        ft.TextButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.ASSIGNMENT, color=cr.Colors.TEXT_SECUNDARIA), ft.Text("Orçamentos", style=ft.TextStyle(color=cr.Colors.TEXT_SECUNDARIA))],
                spacing=4,
                tight=True
            ),
            on_click=lambda e: change_display(2)
        ),
        ft.TextButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.INSERT_CHART_OUTLINED, color=cr.Colors.TEXT_SECUNDARIA), ft.Text("Relatórios", style=ft.TextStyle(color=cr.Colors.TEXT_SECUNDARIA))],
                spacing=4,
                tight=True
            ),
            on_click=lambda e: change_display(3)
        ),
    ]
    
    # ============ Bolao de ação =================================================
    def on_resize(e):
        small = page.width < 600
        for btn in menu:
            btn.content.controls[1].visible = not small
        page.update()
    page.on_resize = on_resize
    
    floating_btn = ft.FloatingActionButton(
        shape=ft.CircleBorder(),
        bgcolor=cr.Colors.PRINCIPAL_BLACK,
        content=ft.Row(
            [ft.Icon(ft.Icons.SMART_TOY, color=cr.Colors.CARDS)],
            spacing=4,
            tight=True
        ),
        on_click=lambda _: kamba_IA(0)
    )    
    appbar = ft.BottomAppBar(
        border_radius=30,
        shape=ft.CircularRectangleNotchShape(),
        bgcolor=cr.Colors.CARDS,
        content=ft.Row(
            controls=menu,
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER
        )
    )
    show = ft.Container(
        blur=30,
        border_radius=20,
        margin=10,
        padding=20,
        content=ft.Column(
            controls=[
                ft.Image(
                    src='icon.png',
                    height=300,
                    width=300,
                ),
                ft.Text('Bem-vindo à nossa plataforma! Um lugar onde você pode encontrar os melhores serviços perto da sua localidade em apenas um clique, continua para saber mais!', color='black'),
                ft.Container(height=150),
                ft.Button(
                    'Vamos Começar!',
                    icon=ft.Icons.ARROW_FORWARD,
                    on_click=start,
                    align=ft.Alignment.BOTTOM_RIGHT,
                    style=ft.ButtonStyle(
                        padding=20,
                        color=cr.Colors.BACKGROUND,
                        bgcolor={
                            ft.ControlState.DEFAULT: cr.Colors.PRINCIPAL,
                            ft.ControlState.HOVERED: ft.Colors.GREY_400
                        }
                    )
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER
        )
    )
    update_list()
    page.add(show)
    on_resize(None)
if __name__ == '__main__':
    if not IS_ANDROID:
        iniciar_backend()
    ft.run(main, assets_dir="assets")