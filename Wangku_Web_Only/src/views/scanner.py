import flet as ft

from theme import (
    CORAL,
    CORAL_SOFT,
    MUTED,
    PRIMARY,
    PURPLE_SOFT,
    card,
    label,
    primary_button,
    title,
)


CATEGORY_LABELS = ("Makanan", "Pengangkutan", "Hiburan", "Buku", "Lain-lain")


def live(camera, status, on_capture, on_cancel):
    return ft.Column(
        [
            ft.TextButton("←  Kembali ke transaksi", on_click=on_cancel),
            title("Imbas resit", size=27),
            label(
                "Halakan kamera ke resit atau tangkap skrin pembelian anda.",
                color=MUTED,
            ),
            card(ft.Column([camera, status], spacing=10), padding=10),
            card(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.INFO_OUTLINE, color=PRIMARY),
                        label(
                            "Gambar resit dihantar kepada Gemini untuk analisis automatik. "
                            "Semak cadangan sebelum menyimpan.",
                            size=12,
                            color=MUTED,
                        ),
                    ],
                    spacing=9,
                ),
                color=PURPLE_SOFT,
                padding=12,
            ),
            primary_button("Ambil gambar", on_capture, icon=ft.Icons.CAMERA_ALT),
        ],
        spacing=14,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )


def review(
    photo,
    description,
    amount,
    category,
    message,
    on_save,
    on_retake,
    on_cancel,
    busy=False,
):
    """Receipt editor with manual entry and support for multiple purchases."""
    entries = [(description, amount, category)]
    extra_entries = ft.Column(spacing=10)

    def make_entry():
        style = {
            "filled": True,
            "fill_color": ft.Colors.WHITE,
            "border_color": ft.Colors.BLUE_GREY_100,
            "focused_border_color": PRIMARY,
            "border_radius": 14,
            "content_padding": 14,
        }
        entry = (
            ft.TextField(label="Apa yang dibeli?", **style),
            ft.TextField(
                label="Jumlah (RM)",
                prefix=ft.Text("RM "),
                keyboard_type=ft.KeyboardType.NUMBER,
                **style,
            ),
            ft.Dropdown(
                value="Lain-lain",
                label="Kategori",
                options=[ft.DropdownOption(text=item) for item in CATEGORY_LABELS],
                filled=True,
                fill_color=ft.Colors.WHITE,
                border_color=ft.Colors.BLUE_GREY_100,
                focused_border_color=PRIMARY,
                border_radius=14,
                content_padding=14,
            ),
        )
        return entry

    async def submit_entries(_=None):
        for item_description, item_amount, _item_category in entries:
            text = (item_description.value or "").strip()
            try:
                value = float((item_amount.value or "").replace(",", ""))
            except (TypeError, ValueError):
                value = 0
            if not text or value <= 0:
                message.value = "Isi keterangan dan jumlah melebihi RM 0 untuk setiap transaksi."
                message.color = ft.Colors.ERROR
                message.update()
                return

        # Reuse the app's existing save/persistence path for every entered item.
        for item_description, item_amount, item_category in entries:
            description.value = item_description.value
            amount.value = item_amount.value
            category.value = item_category.value
            await on_save()

    def add_entry(_=None):
        entry = make_entry()
        entries.append(entry)
        extra_entries.controls.append(
            card(
                ft.Column(
                    [
                        label(
                            f"Butiran transaksi {len(entries)}",
                            size=15,
                            weight=ft.FontWeight.BOLD,
                        ),
                        *entry,
                    ],
                    spacing=10,
                ),
                color=ft.Colors.WHITE,
                padding=14,
            )
        )
        extra_entries.update()

    controls = [
        ft.TextButton("←  Kembali ke transaksi", on_click=on_cancel),
        title("Semak pembelian anda", size=27),
        label(
            "Semak cadangan atau masukkan transaksi sendiri. Anda boleh tambah "
            "lebih daripada satu transaksi sebelum menghantar.",
            color=MUTED,
        ),
        card(
            ft.Image(
                src=photo,
                height=150,
                fit=ft.BoxFit.CONTAIN,
                border_radius=16,
            ),
            color=ft.Colors.WHITE,
            padding=8,
        ),
        ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.EDIT_NOTE, color=CORAL),
                    label(
                        "Semak atau edit butiran resit. Analisis AI tidak diperlukan "
                        "untuk menghantar secara manual.",
                        size=12,
                        color=CORAL,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=CORAL_SOFT,
            padding=12,
            border_radius=16,
        ),
        card(
            ft.Column(
                [
                    label("Butiran transaksi 1", size=16, weight=ft.FontWeight.BOLD),
                    description,
                    amount,
                    category,
                    message,
                ],
                spacing=12,
            ),
            color=ft.Colors.WHITE,
            padding=16,
        ),
        extra_entries,
    ]
    if busy:
        controls.append(ft.ProgressBar(color=PRIMARY))

    controls.extend(
        [
            ft.OutlinedButton(
                content=ft.Text("Tambah transaksi"),
                icon=ft.Icons.ADD,
                on_click=add_entry,
            ),
            ft.OutlinedButton(
                content=ft.Text("Ambil semula"),
                icon=ft.Icons.CAMERA_ALT,
                on_click=on_retake,
            ),
            primary_button(
                "Hantar transaksi secara manual",
                submit_entries,
                icon=ft.Icons.CHECK,
            ),
        ]
    )
    return ft.Column(
        controls,
        spacing=12,
        tight=True,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )
