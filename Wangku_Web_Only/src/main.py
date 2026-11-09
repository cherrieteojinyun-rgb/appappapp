    def page_wrapper(view, width=None, include_nav=False):
        screen_width = width if width else content_width()
        if isinstance(view, ft.Column):
            content = ft.Column(
                controls=view.controls,
                spacing=view.spacing,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                tight=True,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            )
        else:
            content = ft.Column(
                [view],
                spacing=0,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            )
        body = ft.Container(
            content=content,
            width=screen_width,
            expand=True,
            padding=0,
        )
        elements = [body]
        if include_nav:
            elements.append(nav_bar())
        viewport_height = max((page.height or 620) - 36, 320)
        return ft.Row([
            ft.Container(
                content=ft.Column(elements, spacing=8, expand=True),
                width=screen_width,
                height=viewport_height,
                bgcolor=ft.Colors.WHITE,
            ),
        ], alignment=ft.MainAxisAlignment.CENTER, expand=True, vertical_alignment=ft.CrossAxisAlignment.STRETCH)
