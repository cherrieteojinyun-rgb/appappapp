import flet as ft

from theme import CORAL, CORAL_SOFT, MUTED, PRIMARY, PURPLE_SOFT, card, label, primary_button, title


def live(camera, status, on_capture, on_cancel):
    return ft.Column([
        ft.TextButton("←  Kembali ke transaksi", on_click=on_cancel),
        title("Imbas resit", size=27),
        label("Halakan kamera ke resit atau tangkap skrin pembelian anda.", color=MUTED),
        card(ft.Column([
            camera,
            status,
        ], spacing=10), padding=10),
        card(ft.Row([
            ft.Icon(ft.Icons.INFO_OUTLINE, color=PRIMARY),
            label("Gambar resit dihantar kepada Gemini untuk analisis automatik. Semak cadangan sebelum menyimpan.", size=12, color=MUTED),
        ], spacing=9), color=PURPLE_SOFT, padding=12),
        primary_button("Ambil gambar", on_capture, icon=ft.Icons.CAMERA_ALT),
    ], spacing=14, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)


def review(photo, items, total, message, on_save, on_retake, on_cancel, busy=False):
    if busy:
        return ft.Column([
            ft.TextButton("←  Kembali ke transaksi", on_click=on_cancel),
            title("Analisis resit", size=27),
            message,
            ft.ProgressBar(),
        ])

    item_rows = []
    for item in items or []:
        item_rows.append(
            ft.Row([
                ft.Text(str(item.get("name", "")).strip() or "Item tanpa nama", expand=True),
                ft.Text(f"RM {float(item.get('price', 0.0)):.2f}", width=100, text_align=ft.TextAlign.RIGHT),
            ], spacing=10)
        )

    if not item_rows:
        item_rows = [ft.Text("Tiada item yang dapat dikenal pasti.", color=MUTED)]

    return ft.Column([
        ft.TextButton("←  Kembali ke transaksi", on_click=on_cancel),
        title("Semak pembelian anda", size=27),
        label("Item yang dikenalpasti daripada resit anda.", color=MUTED),
        card(ft.Image(src=photo, height=185, fit=ft.BoxFit.CONTAIN, border_radius=16), color=ft.Colors.WHITE, padding=10),
        ft.Container(content=ft.Row([
            ft.Icon(ft.Icons.EDIT_NOTE, color=CORAL),
            label("Gambar berjaya diambil. Semak senarai item sebelum simpan.", size=12, color=CORAL),
        ], spacing=8), bgcolor=CORAL_SOFT, padding=12, border_radius=16),
        card(ft.Column([
            ft.Row([
                ft.Text("Item", weight=ft.FontWeight.BOLD, expand=True),
                ft.Text("Harga", weight=ft.FontWeight.BOLD, width=100, text_align=ft.TextAlign.RIGHT),
            ], spacing=10),
            *item_rows,
            ft.Divider(),
            ft.Row([
                ft.Text("Jumlah", weight=ft.FontWeight.BOLD, expand=True),
                ft.Text(f"RM {float(total or 0.0):.2f}", width=100, text_align=ft.TextAlign.RIGHT, weight=ft.FontWeight.BOLD),
            ], spacing=10),
        ], spacing=8), padding=10),
        message,
        ft.Row([
            ft.OutlinedButton(content=ft.Text("Ambil semula"), icon=ft.Icons.CAMERA_ALT, on_click=on_retake),
            ft.Container(expand=True),
            primary_button("Tambah transaksi", on_save, icon=ft.Icons.CHECK),
        ], wrap=True, spacing=8),
    ], spacing=13, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
