
"""Wangku AI connection. Gemini API keys stay on the backend."""

import asyncio
import base64
import binascii
import json
import math
import urllib.error
import urllib.request

from urllib.parse import urlparse

from finance import category_totals


class CoachError(Exception):
    """A safe Malay message suitable for the interface."""


def _get_context(state):
    return {
        "elaun": state.get("allowance", 0),
        "perbelanjaan_direkod": state.get("spent", 0),
        "baki": state.get("balance", 0),
        "kategori": category_totals(state.get("transactions", [])),
        "matlamat": state.get("goals", []),
    }


def _get_contents(messages):
    contents = []

    for sender, message in messages[-20:]:
        if sender not in ("you", "coach"):
            continue

        role = "user" if sender == "you" else "model"

        if not contents and role != "user":
            continue

        contents.append({
            "role": role,
            "parts": [{"text": str(message)}],
        })

    return contents


def build_payload(state, messages):
    context = _get_context(state)

    return {
        "systemInstruction": {
            "parts": [{
                "text": (
                    "Anda ialah Jurulatih Wangku, pembimbing pendidikan "
                    "kewangan pelajar. Jawab dalam Bahasa Melayu sahaja. "
                    "Gunakan bahasa mesra, ringkas dan tidak menghakimi. "
                    "Bantu pengguna mengawal perbelanjaan dan merancang "
                    "simpanan. Jangan mereka harga atau pendapatan. "
                    "Jangan menggalakkan hutang, perjudian atau pelaburan "
                    "berisiko.\nKonteks kewangan:\n"
                    + json.dumps(context, ensure_ascii=False)
                )
            }]
        },
        "contents": _get_contents(messages),
        "generationConfig": {
            "maxOutputTokens": 1200,
            "temperature": 0.4,
        },
    }


def _request(payload, url, token, endpoint="/coach"):
    parsed = urlparse(str(url or "").strip())

    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
    ):
        raise CoachError(
            "Masukkan alamat HTTPS pelayan Wangku yang sah melalui Tetapan AI."
        )

    token = str(token or "").strip()

    if not token:
        raise CoachError(
            "Masukkan kod akses pelayan melalui Tetapan AI. "
            "Kod ini bukan kunci Gemini."
        )

    request = urllib.request.Request(
        url.rstrip("/") + endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.load(response)

    except urllib.error.HTTPError as error:
        if error.code in (401, 403):
            raise CoachError(
                "Kod akses tidak sah. Semak Tetapan AI."
            ) from None

        if error.code == 413:
            raise CoachError(
                "Gambar terlalu besar. Sila gunakan gambar yang lebih kecil."
            ) from None

        if error.code == 429:
            raise CoachError(
                "Had penggunaan AI dicapai. Cuba lagi kemudian."
            ) from None

        if error.code in (502, 503, 504):
            raise CoachError(
                "Perkhidmatan AI terganggu buat sementara waktu."
            ) from None

        raise CoachError(
            "Permintaan gagal. Semak alamat pelayan dan cuba lagi."
        ) from None

    except (urllib.error.URLError, TimeoutError, OSError):
        raise CoachError(
            "Pelayan tidak dapat dihubungi. Semak sambungan internet."
        ) from None

    except (ValueError, TypeError):
        raise CoachError(
            "Jawapan pelayan tidak dapat dibaca."
        ) from None

    answer = result.get("reply") if isinstance(result, dict) else None

    if not isinstance(answer, str) or not answer.strip():
        raise CoachError("Tiada jawapan diterima. Cuba lagi.")

    return answer.strip()


async def reply(state, messages):
    contents = _get_contents(messages)

    if not contents:
        raise CoachError("Sila masukkan mesej terlebih dahulu.")

    payload = {
        "context": _get_context(state),
        "contents": contents,
    }

    return await asyncio.to_thread(
        _request,
        payload,
        state.get("backend_url", ""),
        state.get("backend_token", ""),
        "/coach",
    )


def _decode_photo(photo):
    if isinstance(photo, (bytes, bytearray)):
        image = bytes(photo)

    elif isinstance(photo, str):
        photo = photo.strip()

        if photo.startswith("data:image/"):
            if ";base64," not in photo:
                raise CoachError("Format gambar tidak sah.")
            photo = photo.split(",", 1)[1]

        try:
            image = base64.b64decode(photo, validate=True)
        except (ValueError, binascii.Error):
            raise CoachError(
                "Format gambar tidak disokong."
            ) from None

    else:
        raise CoachError(
            "Data gambar tidak diterima. Sila cuba ambil gambar semula."
        )

    if not image or len(image) > 4 * 1024 * 1024:
        raise CoachError(
            "Gambar terlalu besar. Had maksimum ialah 4 MB."
        )

    is_jpeg = image.startswith(b"\xff\xd8\xff")
    is_png = image.startswith(b"\x89PNG\r\n\x1a\n")
    is_webp = (
        image.startswith(b"RIFF")
        and image[8:12] == b"WEBP"
    )

    if not (is_jpeg or is_png or is_webp):
        raise CoachError(
            "Gunakan gambar JPEG, PNG atau WebP."
        )

    return base64.b64encode(image).decode("ascii")


def _parse_receipt(answer):
    try:
        result = json.loads(answer)
    except (ValueError, TypeError):
        raise CoachError(
            "AI tidak dapat membaca maklumat resit. Cuba gambar lain."
        ) from None

    if not isinstance(result, dict):
        raise CoachError("Format jawapan resit tidak sah.")

    description = result.get("description")
    amount = result.get("amount")
    category = result.get("category")

    if not isinstance(description, str) or not description.strip():
        description = "Perbelanjaan"

    if amount is not None:
        if (
            isinstance(amount, bool)
            or not isinstance(amount, (int, float))
            or not math.isfinite(amount)
            or amount < 0
        ):
            amount = None

    allowed_categories = {
        "Makanan",
        "Pengangkutan",
        "Hiburan",
        "Buku",
        "Lain-lain",
    }

    if category not in allowed_categories:
        category = "Lain-lain"

    return {
        "description": description.strip()[:200],
        "amount": amount,
        "category": category,
    }


async def analyze_receipt(state, photo):
    encoded = _decode_photo(photo)

    answer = await asyncio.to_thread(
        _request,
        {"image": encoded},
        state.get("backend_url", ""),
        state.get("backend_token", ""),
        "/receipt",
    )

    return _parse_receipt(answer)
