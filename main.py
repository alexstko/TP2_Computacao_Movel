from dataclasses import dataclass, field
import base64
import mimetypes
import os
import flet as ft


@dataclass
class Message:
    user: str
    text: str
    message_type: str
    room: str = "Geral"
    to_user: str = ""
    reaction: str = ""
    message_id: str = ""
    file_name: str = ""   # nome original do ficheiro
    file_data: str = ""   # base64 do conteúdo
    file_mime: str = ""   # ex: "image/png", "application/pdf"


# ── Paletas de cores ──────────────────────────────────────────────────────────
THEMES = {
    "dark": {
        "page_bg":          ft.Colors.BLUE_GREY_900,
        "sidebar_bg":       ft.Colors.BLUE_GREY_800,
        "header_bg":        ft.Colors.BLUE_GREY_900,
        "bubble_me_bg":     ft.Colors.BLUE_GREY_800,
        "bubble_other_bg":  ft.Colors.BLUE_GREY_900,
        "emoji_panel_bg":   ft.Colors.BLUE_GREY_800,
        "reaction_bg":      ft.Colors.BLUE_GREY_700,
        "room_title_color": ft.Colors.WHITE,
        "sidebar_title":    ft.Colors.WHITE,
        "sidebar_sub":      ft.Colors.WHITE54,
        "room_btn_color":   ft.Colors.WHITE,
        "user_btn_color":   ft.Colors.WHITE,
        "user_icon_color":  ft.Colors.GREEN_400,
        "me_name_color":    ft.Colors.ORANGE_400,
        "other_name_color": ft.Colors.BLUE_400,
        "login_text_color": ft.Colors.BLACK45,
        "divider_color":    ft.Colors.WHITE24,
        "send_icon_color":  ft.Colors.BLUE_400,
        "emoji_icon_color": ft.Colors.YELLOW_400,
        "add_icon_color":   ft.Colors.WHITE,
        "edit_icon_color":  ft.Colors.BLUE_200,
        "del_icon_color":   ft.Colors.RED_300,
        "theme_icon":       ft.Icons.LIGHT_MODE,
        "theme_tooltip":    "Tema Claro",
    },
    "light": {
        "page_bg":          ft.Colors.GREY_100,
        "sidebar_bg":       ft.Colors.BLUE_GREY_100,
        "header_bg":        ft.Colors.WHITE,
        "bubble_me_bg":     ft.Colors.BLUE_100,
        "bubble_other_bg":  ft.Colors.WHITE,
        "emoji_panel_bg":   ft.Colors.GREY_200,
        "reaction_bg":      ft.Colors.BLUE_GREY_100,
        "room_title_color": ft.Colors.BLUE_GREY_900,
        "sidebar_title":    ft.Colors.BLUE_GREY_900,
        "sidebar_sub":      ft.Colors.BLUE_GREY_400,
        "room_btn_color":   ft.Colors.BLUE_GREY_800,
        "user_btn_color":   ft.Colors.BLUE_GREY_800,
        "user_icon_color":  ft.Colors.GREEN_600,
        "me_name_color":    ft.Colors.DEEP_ORANGE_400,
        "other_name_color": ft.Colors.BLUE_700,
        "login_text_color": ft.Colors.GREY_600,
        "divider_color":    ft.Colors.BLUE_GREY_200,
        "send_icon_color":  ft.Colors.BLUE_700,
        "emoji_icon_color": ft.Colors.AMBER_700,
        "add_icon_color":   ft.Colors.BLUE_GREY_700,
        "edit_icon_color":  ft.Colors.BLUE_700,
        "del_icon_color":   ft.Colors.RED_600,
        "theme_icon":       ft.Icons.DARK_MODE,
        "theme_tooltip":    "Tema Escuro",
    },
}


def main(page: ft.Page):
    page.title = "Chat App"

    current_room = ["Geral"]
    is_private = [False]
    private_with = [""]
    current_theme = ["dark"]

    rooms = ["Geral", "Tecnologia", "Desporto"]
    online_users = {}
    message_registry = {}

    # ── Contadores de não lidas ───────────────────────────────────────────────
    # { "Geral": 3, "Tecnologia": 1, ... }  para salas
    # { "username": 2, ... }                para privados
    unread_rooms   = {}   # room -> count
    unread_private = {}   # username -> count
    room_badge_refs   = {}   # room -> ft.Text (badge)
    private_badge_refs = {}  # username -> ft.Text (badge)

    def T(key: str):
        """Devolve o valor da cor/ícone para o tema atual."""
        return THEMES[current_theme[0]][key]

    # ── Widgets principais ────────────────────────────────────────────────────
    chat = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        auto_scroll=True,
    )

    new_message = ft.TextField(
        hint_text="Escreve uma mensagem...",
        expand=True,
        on_submit=lambda e: send_click(e),
    )

    room_title = ft.Text(
        value=f"# {current_room[0]}",
        size=20,
        weight=ft.FontWeight.BOLD,
        color=T("room_title_color"),
    )

    users_list = ft.Column(spacing=4)

    # ── Botão de tema ─────────────────────────────────────────────────────────
    theme_button = ft.IconButton(
        icon=T("theme_icon"),
        icon_color=T("emoji_icon_color"),
        tooltip=T("theme_tooltip"),
    )

    # Referências a containers que precisam de ser recoloridos no toggle
    sidebar_ref = ft.Ref[ft.Container]()
    header_ref  = ft.Ref[ft.Container]()
    emoji_panel_container_ref = ft.Ref[ft.Container]()

    # ── Emoji picker ──────────────────────────────────────────────────────────
    EMOJI_CATEGORIES = {
        "😀": ["😀","😂","😍","😎","😭","😡","🥰","😱","🤔","😴","🤣","😇","🥳","😏","🤩"],
        "👋": ["👍","👎","❤️","🔥","✅","🎉","👏","🙌","🤝","🫶","💪","🤞","✌️","🖐️","👌"],
        "🐶": ["🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼","🐨","🐯","🦁","🐮","🐷","🐸","🐵"],
        "🍕": ["🍕","🍔","🍟","🌮","🌯","🍣","🍜","🍩","🍪","🎂","🍦","☕","🧃","🍺","🥤"],
        "⚽": ["⚽","🏀","🏈","⚾","🎾","🏐","🏉","🎱","🏓","🏸","🥊","⛷️","🏄","🚴","🏋️"],
    }

    emoji_panel_visible = [False]
    emoji_panel = ft.Container(visible=False)
    selected_category = [list(EMOJI_CATEGORIES.keys())[0]]
    emoji_grid = ft.Row(wrap=True, spacing=0)

    def insert_emoji(emoji: str):
        new_message.value = (new_message.value or "") + emoji
        emoji_panel.visible = False
        emoji_panel_visible[0] = False
        new_message.focus()
        page.update()

    def build_emoji_grid(cat: str):
        emoji_grid.controls.clear()
        for em in EMOJI_CATEGORIES[cat]:
            emoji_grid.controls.append(
                ft.TextButton(
                    content=ft.Text(em, size=20),
                    on_click=lambda ev, e=em: insert_emoji(e),
                    style=ft.ButtonStyle(padding=2),
                )
            )

    def build_category_bar():
        buttons = []
        for cat in EMOJI_CATEGORIES:
            buttons.append(
                ft.TextButton(
                    content=ft.Text(cat, size=18),
                    on_click=lambda ev, c=cat: switch_category(c),
                    style=ft.ButtonStyle(padding=4),
                )
            )
        return ft.Row(controls=buttons, spacing=0)

    def switch_category(cat: str):
        selected_category[0] = cat
        build_emoji_grid(cat)
        page.update()

    def build_emoji_panel_content():
        build_emoji_grid(selected_category[0])
        return ft.Container(
            width=300,
            height=200,
            bgcolor=T("emoji_panel_bg"),
            border_radius=10,
            border=ft.border.all(1, ft.Colors.WHITE24),
            padding=6,
            content=ft.Column(
                controls=[
                    build_category_bar(),
                    ft.Divider(height=1, color=ft.Colors.WHITE24),
                    ft.Container(content=emoji_grid, height=130),
                ],
                spacing=4,
            ),
        )

    def toggle_emoji_panel(e):
        emoji_panel_visible[0] = not emoji_panel_visible[0]
        if emoji_panel_visible[0]:
            emoji_panel.content = build_emoji_panel_content()
        emoji_panel.visible = emoji_panel_visible[0]
        page.update()

    # ── Reações ───────────────────────────────────────────────────────────────
    QUICK_REACTIONS = ["👍", "❤️", "😂", "😮", "😢", "🔥"]

    def send_reaction(message_id: str, emoji: str):
        my_name = page.session.store.get("user_name")
        page.pubsub.send_all(
            Message(
                user=my_name,
                text="",
                message_type="reaction",
                room=current_room[0],
                message_id=message_id,
                reaction=emoji,
            )
        )

    def build_reaction_bar(message_id: str):
        return ft.Row(
            controls=[
                ft.TextButton(
                    content=ft.Text(emoji, size=16),
                    on_click=lambda e, mid=message_id, em=emoji: send_reaction(mid, em),
                    style=ft.ButtonStyle(padding=2),
                    tooltip=emoji,
                )
                for emoji in QUICK_REACTIONS
            ],
            spacing=0,
            visible=False,
        )

    # ── Editar mensagem ───────────────────────────────────────────────────────
    def start_edit(msg_id: str):
        registry = message_registry[msg_id]
        current_text = registry["text_control"].value
        edit_field = ft.TextField(value=current_text, expand=True, autofocus=True)

        def confirm_edit(e):
            if not edit_field.value:
                return
            page.pubsub.send_all(
                Message(
                    user=page.session.store.get("user_name"),
                    text=edit_field.value,
                    message_type="edit_message",
                    room=current_room[0],
                    message_id=msg_id,
                )
            )
            page.pop_dialog()

        def cancel_edit(e):
            page.pop_dialog()

        page.show_dialog(
            ft.AlertDialog(
                open=True, modal=True,
                title=ft.Text("Editar mensagem"),
                content=ft.Column([edit_field], tight=True),
                actions=[
                    ft.TextButton("Cancelar", on_click=cancel_edit),
                    ft.TextButton("Guardar", on_click=confirm_edit),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    # ── Eliminar mensagem ─────────────────────────────────────────────────────
    def confirm_delete(msg_id: str):
        def do_delete(e):
            page.pubsub.send_all(
                Message(
                    user=page.session.store.get("user_name"),
                    text="",
                    message_type="delete_message",
                    room=current_room[0],
                    message_id=msg_id,
                )
            )
            page.pop_dialog()

        def cancel(e):
            page.pop_dialog()

        page.show_dialog(
            ft.AlertDialog(
                open=True, modal=True,
                title=ft.Text("Eliminar mensagem"),
                content=ft.Text("Tens a certeza que queres eliminar esta mensagem?"),
                actions=[
                    ft.TextButton("Cancelar", on_click=cancel),
                    ft.TextButton(
                        "Eliminar",
                        on_click=do_delete,
                        style=ft.ButtonStyle(color=ft.Colors.RED_400),
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    # ── Construir bolha de mensagem ───────────────────────────────────────────
    def build_message_bubble(msg_id: str, username: str, text: str, is_me: bool):
        reaction_bar = build_reaction_bar(msg_id)
        reactions_display = ft.Row(controls=[], spacing=4, wrap=True)
        text_control = ft.Text(text, size=14)

        edit_delete_row = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.EDIT,
                    icon_color=T("edit_icon_color"),
                    icon_size=14,
                    tooltip="Editar",
                    on_click=lambda e, mid=msg_id: start_edit(mid),
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color=T("del_icon_color"),
                    icon_size=14,
                    tooltip="Eliminar",
                    on_click=lambda e, mid=msg_id: confirm_delete(mid),
                ),
            ],
            spacing=0,
            visible=is_me,
        )

        def on_hover(e):
            reaction_bar.visible = e.data == "true"
            page.update()

        bubble = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Tu" if is_me else username,
                                weight=ft.FontWeight.BOLD,
                                color=T("me_name_color") if is_me else T("other_name_color"),
                                size=12,
                            ),
                            ft.Row(controls=[edit_delete_row, reaction_bar], spacing=0),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    text_control,
                    reactions_display,
                ],
                spacing=2,
            ),
            bgcolor=T("bubble_me_bg") if is_me else T("bubble_other_bg"),
            border_radius=10,
            padding=10,
            margin=ft.Margin(40 if is_me else 0, 0, 0 if is_me else 40, 4),
            on_hover=on_hover,
        )

        message_registry[msg_id] = {
            "reactions":         {e: [] for e in QUICK_REACTIONS},
            "reactions_display": reactions_display,
            "text_control":      text_control,
            "bubble":            bubble,
            "container":         bubble,
            "is_me":             is_me,
            "edit_delete_row":   edit_delete_row,
        }
        return bubble

    # ── Construir bolha de ficheiro ───────────────────────────────────────────
    def build_file_bubble(username: str, is_me: bool, file_name: str,
                          file_data: str, file_mime: str):
        is_image = file_mime.startswith("image/")

        if is_image:
            content_widget = ft.Image(
                src_base64=file_data,
                width=250,
                fit=ft.ImageFit.CONTAIN,
                border_radius=6,
            )
        else:
            # Ícone genérico para outros ficheiros
            ext = os.path.splitext(file_name)[1].upper() or "FILE"
            content_widget = ft.Row(
                controls=[
                    ft.Icon(ft.Icons.INSERT_DRIVE_FILE, color=ft.Colors.BLUE_300, size=32),
                    ft.Column(
                        controls=[
                            ft.Text(file_name, size=13, weight=ft.FontWeight.BOLD,
                                    overflow=ft.TextOverflow.ELLIPSIS, max_lines=1),
                            ft.Text(ext, size=11, color=ft.Colors.GREY_400),
                        ],
                        spacing=2,
                    ),
                ],
                spacing=8,
            )

        def save_file(e):
            raw = base64.b64decode(file_data)
            # Guarda na pasta Downloads do utilizador ou na pasta atual
            downloads = os.path.join(os.path.expanduser("~"), "Downloads")
            dest_dir = downloads if os.path.isdir(downloads) else os.getcwd()
            dest = os.path.join(dest_dir, file_name)
            # Evitar sobrescrever ficheiros existentes
            base, ext = os.path.splitext(file_name)
            counter = 1
            while os.path.exists(dest):
                dest = os.path.join(dest_dir, f"{base}_{counter}{ext}")
                counter += 1
            with open(dest, "wb") as f:
                f.write(raw)
            page.show_dialog(
                ft.AlertDialog(
                    open=True,
                    modal=False,
                    title=ft.Text("Ficheiro guardado"),
                    content=ft.Text(f"Guardado em:\n{dest}", size=12),
                    actions=[ft.TextButton("OK", on_click=lambda e: page.pop_dialog())],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
            )

        bubble = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Tu" if is_me else username,
                                weight=ft.FontWeight.BOLD,
                                color=T("me_name_color") if is_me else T("other_name_color"),
                                size=12,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DOWNLOAD,
                                icon_size=16,
                                icon_color=ft.Colors.BLUE_300,
                                tooltip="Guardar ficheiro",
                                on_click=save_file,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    content_widget,
                    ft.Text(file_name, size=11, color=ft.Colors.GREY_400,
                            italic=True, visible=is_image),
                ],
                spacing=4,
            ),
            bgcolor=T("bubble_me_bg") if is_me else T("bubble_other_bg"),
            border_radius=10,
            padding=10,
            margin=ft.Margin(40 if is_me else 0, 0, 0 if is_me else 40, 4),
        )
        return bubble

    # ── Upload manual via caminho ─────────────────────────────────────────────
    def open_file_dialog(e):
        path_field = ft.TextField(
            label="Caminho do ficheiro",
            hint_text=r"Ex: C:\imagens\foto.png",
            expand=True,
            autofocus=True,
        )
        error_text = ft.Text("", color=ft.Colors.RED_400, size=12)

        def send_file(e):
            path = path_field.value.strip() if path_field.value else ""
            if not path:
                error_text.value = "Introduz um caminho válido."
                page.update()
                return
            if not os.path.isfile(path):
                error_text.value = "Ficheiro não encontrado."
                page.update()
                return
            try:
                with open(path, "rb") as fh:
                    raw = fh.read()
            except Exception as ex:
                error_text.value = f"Erro ao ler ficheiro: {ex}"
                page.update()
                return

            file_name = os.path.basename(path)
            b64 = base64.b64encode(raw).decode()
            mime = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
            my_name = page.session.store.get("user_name")

            page.pubsub.send_all(
                Message(
                    user=my_name,
                    text="",
                    message_type="file_message",
                    room=current_room[0],
                    to_user=private_with[0] if is_private[0] else "",
                    file_name=file_name,
                    file_data=b64,
                    file_mime=mime,
                )
            )
            page.pop_dialog()

        def cancel(e):
            page.pop_dialog()

        page.show_dialog(
            ft.AlertDialog(
                open=True,
                modal=True,
                title=ft.Text("Enviar ficheiro / imagem"),
                content=ft.Column(
                    controls=[
                        ft.Text("Cola o caminho completo do ficheiro:", size=13),
                        path_field,
                        error_text,
                    ],
                    tight=True,
                    spacing=8,
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=cancel),
                    ft.TextButton("Enviar", on_click=send_file),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def apply_theme():
        """Atualiza todas as cores da UI para o tema atual."""
        page.bgcolor = T("page_bg")

        # Título da sala
        room_title.color = T("room_title_color")

        # Header
        if header_ref.current:
            header_ref.current.bgcolor = T("header_bg")

        # Sidebar
        if sidebar_ref.current:
            sidebar_ref.current.bgcolor = T("sidebar_bg")
            # Textos dentro da sidebar
            col = sidebar_ref.current.content
            if col and col.controls:
                for ctrl in col.controls:
                    if isinstance(ctrl, ft.Text):
                        if ctrl.weight == ft.FontWeight.BOLD:
                            ctrl.color = T("sidebar_title")
                        else:
                            ctrl.color = T("sidebar_sub")
                    elif isinstance(ctrl, ft.Divider):
                        ctrl.color = T("divider_color")

        # Botões de sala
        for btn in rooms_list.controls:
            if isinstance(btn, ft.TextButton) and isinstance(btn.content, ft.Row):
                for ctrl in btn.content.controls:
                    if isinstance(ctrl, ft.Text):
                        ctrl.color = T("room_btn_color")

        # Lista de utilizadores online
        for btn in users_list.controls:
            if isinstance(btn, ft.TextButton):
                row = btn.content
                if isinstance(row, ft.Row):
                    for ctrl in row.controls:
                        if isinstance(ctrl, ft.Icon):
                            ctrl.color = T("user_icon_color")
                        elif isinstance(ctrl, ft.Text):
                            ctrl.color = T("user_btn_color")

        # Bolhas de mensagem existentes
        for mid, reg in message_registry.items():
            is_me = reg.get("is_me", False)
            reg["container"].bgcolor = T("bubble_me_bg") if is_me else T("bubble_other_bg")

            # Cores dos nomes nas bolhas
            bubble_col = reg["container"].content
            if bubble_col and isinstance(bubble_col, ft.Column) and bubble_col.controls:
                header_row = bubble_col.controls[0]
                if isinstance(header_row, ft.Row) and header_row.controls:
                    name_text = header_row.controls[0]
                    if isinstance(name_text, ft.Text):
                        name_text.color = T("me_name_color") if is_me else T("other_name_color")

            # Ícones editar/eliminar
            edr = reg.get("edit_delete_row")
            if edr and isinstance(edr, ft.Row):
                for btn in edr.controls:
                    if isinstance(btn, ft.IconButton):
                        if btn.icon == ft.Icons.EDIT:
                            btn.icon_color = T("edit_icon_color")
                        elif btn.icon == ft.Icons.DELETE:
                            btn.icon_color = T("del_icon_color")

            # Reações
            for chip in reg["reactions_display"].controls:
                if isinstance(chip, ft.Container):
                    chip.bgcolor = T("reaction_bg")

        # Botão de tema
        theme_button.icon = T("theme_icon")
        theme_button.tooltip = T("theme_tooltip")
        theme_button.icon_color = T("emoji_icon_color")

        # Emoji panel (reconstrói se visível)
        if emoji_panel_visible[0]:
            emoji_panel.content = build_emoji_panel_content()

        page.update()

    def toggle_theme(e):
        current_theme[0] = "light" if current_theme[0] == "dark" else "dark"
        page.theme_mode = ft.ThemeMode.LIGHT if current_theme[0] == "light" else ft.ThemeMode.DARK
        apply_theme()

    theme_button.on_click = toggle_theme

    # ── Atualizar lista de utilizadores ──────────────────────────────────────
    def refresh_users():
        users_list.controls.clear()
        for username in online_users:
            my_name = page.session.store.get("user_name")
            if username == my_name:
                continue

            count = unread_private.get(username, 0)
            priv_badge_text = ft.Text(
                str(count) if count > 0 else "",
                size=10,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
                visible=count > 0,
            )
            priv_badge_container = ft.Container(
                content=priv_badge_text,
                bgcolor=ft.Colors.RED_500,
                border_radius=10,
                padding=ft.padding.symmetric(horizontal=5, vertical=1),
                visible=count > 0,
            )
            private_badge_refs[username] = (priv_badge_text, priv_badge_container)

            users_list.controls.append(
                ft.TextButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.PERSON, color=T("user_icon_color"), size=14),
                            ft.Text(username, color=T("user_btn_color"), size=13),
                            priv_badge_container,
                        ],
                        spacing=6,
                    ),
                    on_click=lambda e, u=username: open_private_chat(u),
                )
            )
        page.update()

    # ── Helpers de badge ──────────────────────────────────────────────────────
    def update_room_badge(room: str, count: int):
        badge_text = room_badge_refs.get(room)
        badge_container = room_badge_refs.get(f"{room}__container")
        if badge_text and badge_container:
            if count > 0:
                badge_text.value = str(count)
                badge_text.visible = True
                badge_container.visible = True
            else:
                badge_text.value = ""
                badge_text.visible = False
                badge_container.visible = False

    def update_private_badge(username: str, count: int):
        refs = private_badge_refs.get(username)
        if refs:
            badge_text, badge_container = refs
            if count > 0:
                badge_text.value = str(count)
                badge_text.visible = True
                badge_container.visible = True
            else:
                badge_text.value = ""
                badge_text.visible = False
                badge_container.visible = False

    def open_private_chat(username: str):
        is_private[0] = True
        private_with[0] = username
        room_title.value = f"🔒 Privado com {username}"
        chat.controls.clear()
        # limpar badge privado ao abrir
        unread_private[username] = 0
        update_private_badge(username, 0)
        page.update()

    def change_room(room: str):
        is_private[0] = False
        private_with[0] = ""
        current_room[0] = room
        room_title.value = f"# {room}"
        chat.controls.clear()
        # limpar badge da sala ao entrar
        unread_rooms[room] = 0
        update_room_badge(room, 0)
        page.pubsub.send_all(
            Message(
                user=page.session.store.get("user_name"),
                text=f"{page.session.store.get('user_name')} entrou na sala {room}.",
                message_type="login_message",
                room=room,
            )
        )
        page.update()

    # ── Receber mensagens ─────────────────────────────────────────────────────
    msg_counter = [0]

    def on_message(message: Message):
        my_name = page.session.store.get("user_name")

        if message.message_type == "user_update":
            online_users.update({message.user: message.room})
            refresh_users()
            return

        if message.message_type == "edit_message":
            mid = message.message_id
            if mid not in message_registry:
                return
            message_registry[mid]["text_control"].value = message.text + "  ✏️"
            page.update()
            return

        if message.message_type == "delete_message":
            mid = message.message_id
            if mid not in message_registry:
                return
            tc = message_registry[mid]["text_control"]
            tc.value = "🗑️ Mensagem eliminada"
            tc.color = ft.Colors.GREY_500
            tc.italic = True
            page.update()
            return

        if message.message_type == "reaction":
            mid = message.message_id
            if mid not in message_registry:
                return
            registry = message_registry[mid]
            emoji = message.reaction
            user = message.user
            users_reacted = registry["reactions"].get(emoji, [])
            if user not in users_reacted:
                users_reacted.append(user)
                registry["reactions"][emoji] = users_reacted
            rd = registry["reactions_display"]
            rd.controls.clear()
            for em, users in registry["reactions"].items():
                if users:
                    rd.controls.append(
                        ft.Container(
                            content=ft.Text(f"{em} {len(users)}", size=12),
                            bgcolor=T("reaction_bg"),
                            border_radius=10,
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            tooltip=", ".join(users),
                        )
                    )
            page.update()
            return

        if message.message_type == "file_message":
            is_me = message.user == my_name
            # Filtrar por sala/privado igual às mensagens normais
            if message.to_user:  # privado
                other = message.user if is_me else message.to_user
                if not (is_private[0] and private_with[0] == other):
                    if not is_me:
                        unread_private[message.user] = unread_private.get(message.user, 0) + 1
                        update_private_badge(message.user, unread_private[message.user])
                        page.update()
                    return
            else:  # sala
                if is_private[0] or message.room != current_room[0]:
                    if not is_me and message.room != current_room[0]:
                        unread_rooms[message.room] = unread_rooms.get(message.room, 0) + 1
                        update_room_badge(message.room, unread_rooms[message.room])
                        page.update()
                    return
            chat.controls.append(
                build_file_bubble(message.user, is_me, message.file_name,
                                  message.file_data, message.file_mime)
            )
            page.update()
            return

        if message.message_type == "private_message":
            # Só interessa se eu for o destinatário ou o remetente
            is_for_me = message.to_user == my_name
            is_from_me = message.user == my_name
            involves_me = is_for_me or (is_from_me and message.to_user == private_with[0])
            if not involves_me:
                return

            # Se não estou na conversa privada com esse utilizador → badge
            other = message.user if is_for_me else message.to_user
            viewing_this = is_private[0] and private_with[0] == other
            if not viewing_this and is_for_me:
                unread_private[other] = unread_private.get(other, 0) + 1
                update_private_badge(other, unread_private[other])
                page.update()
                return

            if not viewing_this:
                return

            is_me = is_from_me
            msg_counter[0] += 1
            mid = f"msg_{msg_counter[0]}"
            chat.controls.append(build_message_bubble(mid, message.user, message.text, is_me))
            page.update()
            return

        if message.message_type == "chat_message":
            is_me = message.user == my_name
            # Mensagem na sala ativa
            if not is_private[0] and message.room == current_room[0]:
                msg_counter[0] += 1
                mid = f"msg_{msg_counter[0]}"
                chat.controls.append(build_message_bubble(mid, message.user, message.text, is_me))
                page.update()
                return
            # Mensagem numa sala diferente (não sou eu a enviar) → badge
            if not is_me and message.room != current_room[0]:
                unread_rooms[message.room] = unread_rooms.get(message.room, 0) + 1
                update_room_badge(message.room, unread_rooms[message.room])
                page.update()
            return

        if message.message_type == "login_message":
            if message.room != current_room[0]:
                return
            chat.controls.append(
                ft.Text(message.text, italic=True, color=T("login_text_color"), size=12)
            )
            page.update()

    page.pubsub.subscribe(on_message)

    # ── Enviar mensagem ───────────────────────────────────────────────────────
    def send_click(e):
        if not new_message.value:
            return
        my_name = page.session.store.get("user_name")
        if is_private[0]:
            page.pubsub.send_all(
                Message(
                    user=my_name,
                    text=new_message.value,
                    message_type="private_message",
                    room=current_room[0],
                    to_user=private_with[0],
                )
            )
        else:
            page.pubsub.send_all(
                Message(
                    user=my_name,
                    text=new_message.value,
                    message_type="chat_message",
                    room=current_room[0],
                )
            )
        new_message.value = ""
        emoji_panel.visible = False
        emoji_panel_visible[0] = False
        page.update()

    # ── Criar sala nova ───────────────────────────────────────────────────────
    room_name_field = ft.TextField(label="Nome da sala", expand=True)

    def create_room(e):
        if not room_name_field.value:
            return
        new_room = room_name_field.value.strip()
        if new_room not in rooms:
            rooms.append(new_room)
            rooms_list.controls.append(build_room_button(new_room))
        room_name_field.value = ""
        page.update()

    def build_room_button(room: str):
        badge_text = ft.Text(
            "",
            size=10,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
            visible=False,
        )
        room_badge_refs[room] = badge_text

        badge_container = ft.Container(
            content=badge_text,
            bgcolor=ft.Colors.RED_500,
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=5, vertical=1),
            visible=False,
        )
        room_badge_refs[f"{room}__container"] = badge_container

        return ft.TextButton(
            content=ft.Row(
                controls=[
                    ft.Text(f"# {room}", color=T("room_btn_color")),
                    badge_container,
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            on_click=lambda e, r=room: change_room(r),
        )

    rooms_list = ft.Column(
        controls=[build_room_button(r) for r in rooms],
        spacing=4,
    )

    # ── Sidebar ───────────────────────────────────────────────────────────────
    sidebar = ft.Container(
        ref=sidebar_ref,
        width=200,
        bgcolor=T("sidebar_bg"),
        padding=10,
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text("Salas", color=T("sidebar_title"), weight=ft.FontWeight.BOLD, size=16),
                ft.Divider(color=T("divider_color")),
                rooms_list,
                ft.Divider(color=T("divider_color")),
                ft.Text("Nova sala", color=T("sidebar_sub"), size=12),
                ft.Row(
                    controls=[
                        room_name_field,
                        ft.IconButton(
                            icon=ft.Icons.ADD,
                            icon_color=T("add_icon_color"),
                            on_click=create_room,
                        ),
                    ]
                ),
                ft.Divider(color=T("divider_color")),
                ft.Text("Online", color=T("sidebar_title"), weight=ft.FontWeight.BOLD, size=16),
                ft.Divider(color=T("divider_color")),
                users_list,
            ]
        ),
    )

    # ── Layout principal ──────────────────────────────────────────────────────
    main_content = ft.Column(
        expand=True,
        controls=[
            ft.Container(
                ref=header_ref,
                bgcolor=T("header_bg"),
                padding=10,
                content=ft.Row(
                    controls=[
                        room_title,
                        ft.Row(
                            controls=[theme_button],
                            alignment=ft.MainAxisAlignment.END,
                            expand=True,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ),
            ft.Container(
                expand=True,
                padding=10,
                content=chat,
            ),
            ft.Container(
                padding=ft.padding.symmetric(horizontal=10),
                content=emoji_panel,
            ),
            ft.Container(
                padding=10,
                content=ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.EMOJI_EMOTIONS,
                            icon_color=T("emoji_icon_color"),
                            tooltip="Emojis",
                            on_click=toggle_emoji_panel,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.ATTACH_FILE,
                            icon_color=T("send_icon_color"),
                            tooltip="Enviar ficheiro/imagem",
                            on_click=open_file_dialog,
                        ),
                        new_message,
                        ft.IconButton(
                            icon=ft.Icons.SEND,
                            icon_color=T("send_icon_color"),
                            on_click=send_click,
                        ),
                    ]
                ),
            ),
        ],
    )

    # ── Join dialog ───────────────────────────────────────────────────────────
    user_name = ft.TextField(label="O teu nome")

    def join_click(e):
        if not user_name.value:
            user_name.error_text = "Nome não pode ser vazio!"
            page.update()
        else:
            name = user_name.value
            page.session.store.set("user_name", name)
            online_users[name] = current_room[0]
            page.pop_dialog()
            page.pubsub.send_all(
                Message(
                    user=name,
                    text=f"{name} entrou no chat.",
                    message_type="login_message",
                    room=current_room[0],
                )
            )
            page.pubsub.send_all(
                Message(
                    user=name,
                    text="",
                    message_type="user_update",
                    room=current_room[0],
                )
            )
            page.update()

    page.bgcolor = T("page_bg")
    page.theme_mode = ft.ThemeMode.DARK

    page.show_dialog(
        ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text("Bem-vindo ao Chat!"),
            content=ft.Column([user_name], tight=True),
            actions=[ft.Button(content="Entrar", on_click=join_click)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    )

    page.add(
        ft.Row(
            expand=True,
            controls=[sidebar, main_content],
        )
    )


ft.run(main)