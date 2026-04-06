from dataclasses import dataclass
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


def main(page: ft.Page):
    page.title = "Chat App"

    current_room = ["Geral"]
    is_private = [False]
    private_with = [""]

    rooms = ["Geral", "Tecnologia", "Desporto"]
    online_users = {}
    message_registry = {}

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
        color=ft.Colors.WHITE,
    )

    users_list = ft.Column(spacing=4)

    # ── Emoji picker ─────────────────────────────────────────────────────────
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
            bgcolor=ft.Colors.BLUE_GREY_800,
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
        edit_field = ft.TextField(
            value=current_text,
            expand=True,
            autofocus=True,
        )

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
                open=True,
                modal=True,
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
                open=True,
                modal=True,
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
                    icon_color=ft.Colors.BLUE_200,
                    icon_size=14,
                    tooltip="Editar",
                    on_click=lambda e, mid=msg_id: start_edit(mid),
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color=ft.Colors.RED_300,
                    icon_size=14,
                    tooltip="Eliminar",
                    on_click=lambda e, mid=msg_id: confirm_delete(mid),
                ),
            ],
            spacing=0,
            visible=is_me,  # só visível para o autor
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
                                color=ft.Colors.ORANGE_400 if is_me else ft.Colors.BLUE_400,
                                size=12,
                            ),
                            ft.Row(
                                controls=[edit_delete_row, reaction_bar],
                                spacing=0,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    text_control,
                    reactions_display,
                ],
                spacing=2,
            ),
            bgcolor=ft.Colors.BLUE_GREY_800 if is_me else ft.Colors.BLUE_GREY_900,
            border_radius=10,
            padding=10,
            margin=ft.Margin(40 if is_me else 0, 0, 0 if is_me else 40, 4),
            on_hover=on_hover,
        )

        message_registry[msg_id] = {
            "reactions": {e: [] for e in QUICK_REACTIONS},
            "reactions_display": reactions_display,
            "text_control": text_control,
            "bubble": bubble,
            "container": bubble,
        }
        return bubble

    # ── Atualizar lista de utilizadores ──────────────────────────────────────
    def refresh_users():
        users_list.controls.clear()
        for username in online_users:
            my_name = page.session.store.get("user_name")
            if username == my_name:
                continue
            users_list.controls.append(
                ft.TextButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.PERSON, color=ft.Colors.GREEN_400, size=14),
                            ft.Text(username, color=ft.Colors.WHITE, size=13),
                        ]
                    ),
                    on_click=lambda e, u=username: open_private_chat(u),
                )
            )
        page.update()

    def open_private_chat(username: str):
        is_private[0] = True
        private_with[0] = username
        room_title.value = f"🔒 Privado com {username}"
        chat.controls.clear()
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
            registry = message_registry[mid]
            registry["text_control"].value = message.text + "  ✏️"
            page.update()
            return

        if message.message_type == "delete_message":
            mid = message.message_id
            if mid not in message_registry:
                return
            registry = message_registry[mid]
            registry["text_control"].value = "🗑️ Mensagem eliminada"
            registry["text_control"].color = ft.Colors.GREY_500
            registry["text_control"].italic = True
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
                            bgcolor=ft.Colors.BLUE_GREY_700,
                            border_radius=10,
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            tooltip=", ".join(users),
                        )
                    )
            page.update()
            return

        if message.message_type == "private_message":
            if not (
                (message.user == my_name and message.to_user == private_with[0]) or
                (message.to_user == my_name and message.user == private_with[0])
            ):
                return
            if not (is_private[0] and (private_with[0] == message.user or private_with[0] == message.to_user)):
                return
            is_me = message.user == my_name
            msg_counter[0] += 1
            mid = f"msg_{msg_counter[0]}"
            chat.controls.append(build_message_bubble(mid, message.user, message.text, is_me))
            page.update()
            return

        if message.message_type == "chat_message":
            if is_private[0] or message.room != current_room[0]:
                return
            is_me = message.user == my_name
            msg_counter[0] += 1
            mid = f"msg_{msg_counter[0]}"
            chat.controls.append(build_message_bubble(mid, message.user, message.text, is_me))
            page.update()
            return

        if message.message_type == "login_message":
            if message.room != current_room[0]:
                return
            chat.controls.append(
                ft.Text(message.text, italic=True, color=ft.Colors.BLACK_45, size=12)
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

    # ── Mudar de sala ─────────────────────────────────────────────────────────
    def change_room(room: str):
        is_private[0] = False
        private_with[0] = ""
        current_room[0] = room
        room_title.value = f"# {room}"
        chat.controls.clear()
        page.pubsub.send_all(
            Message(
                user=page.session.store.get("user_name"),
                text=f"{page.session.store.get('user_name')} entrou na sala {room}.",
                message_type="login_message",
                room=room,
            )
        )
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
        return ft.TextButton(
            content=ft.Text(f"# {room}", color=ft.Colors.WHITE),
            on_click=lambda e, r=room: change_room(r),
        )

    rooms_list = ft.Column(
        controls=[build_room_button(r) for r in rooms],
        spacing=4,
    )

    # ── Sidebar ───────────────────────────────────────────────────────────────
    sidebar = ft.Container(
        width=200,
        bgcolor=ft.Colors.BLUE_GREY_800,
        padding=10,
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text("Salas", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=16),
                ft.Divider(color=ft.Colors.WHITE_24),
                rooms_list,
                ft.Divider(color=ft.Colors.WHITE_24),
                ft.Text("Nova sala", color=ft.Colors.WHITE_54, size=12),
                ft.Row(
                    controls=[
                        room_name_field,
                        ft.IconButton(
                            icon=ft.Icons.ADD,
                            icon_color=ft.Colors.WHITE,
                            on_click=create_room,
                        ),
                    ]
                ),
                ft.Divider(color=ft.Colors.WHITE_24),
                ft.Text("Online", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=16),
                ft.Divider(color=ft.Colors.WHITE_24),
                users_list,
            ]
        ),
    )

    # ── Layout principal ──────────────────────────────────────────────────────
    main_content = ft.Column(
        expand=True,
        controls=[
            ft.Container(
                bgcolor=ft.Colors.BLUE_GREY_900,
                padding=10,
                content=room_title,
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
                            icon_color=ft.Colors.YELLOW_400,
                            tooltip="Emojis",
                            on_click=toggle_emoji_panel,
                        ),
                        new_message,
                        ft.IconButton(
                            icon=ft.Icons.SEND,
                            icon_color=ft.Colors.BLUE_400,
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