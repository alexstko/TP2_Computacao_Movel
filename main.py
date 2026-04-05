from dataclasses import dataclass
import flet as ft


@dataclass
class Message:
    user: str
    text: str
    message_type: str
    room: str = "Geral"


def main(page: ft.Page):
    page.title = "Chat App"

    # ── Estado atual ──────────────────────────────────────────────────────────
    current_room = ["Geral"]

    # ── Salas disponíveis ─────────────────────────────────────────────────────
    rooms = ["Geral", "Tecnologia", "Desporto"]

    # ── Chat e input ──────────────────────────────────────────────────────────
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

    # ── Receber mensagens ─────────────────────────────────────────────────────
    def on_message(message: Message):
        if message.room != current_room[0]:
            return
        if message.message_type == "chat_message":
            chat.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                message.user,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLUE_400,
                                size=12,
                            ),
                            ft.Text(message.text, size=14),
                        ],
                        spacing=2,
                    ),
                    bgcolor=ft.Colors.BLUE_GREY_900,
                    border_radius=10,
                    padding=10,
                    margin=ft.Margin(0, 0, 0, 4),
                )
            )
        elif message.message_type == "login_message":
            chat.controls.append(
                ft.Text(message.text, italic=True, color=ft.Colors.BLACK_45, size=12)
            )
        page.update()

    page.pubsub.subscribe(on_message)

    # ── Enviar mensagem ───────────────────────────────────────────────────────
    def send_click(e):
        if not new_message.value:
            return
        page.pubsub.send_all(
            Message(
                user=page.session.store.get("user_name"),
                text=new_message.value,
                message_type="chat_message",
                room=current_room[0],
            )
        )
        new_message.value = ""
        page.update()

    # ── Mudar de sala ─────────────────────────────────────────────────────────
    def change_room(room: str):
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

    # ── Lista de salas ────────────────────────────────────────────────────────
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
                padding=10,
                content=ft.Row(
                    controls=[
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
            page.session.store.set("user_name", user_name.value)
            page.pop_dialog()
            page.pubsub.send_all(
                Message(
                    user=user_name.value,
                    text=f"{user_name.value} entrou no chat.",
                    message_type="login_message",
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