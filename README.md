# url2epub

Link → EPUB → e-mail na PocketBook (Send-to-PocketBook).

## Uruchomienie

```bash
cp .env.example .env   # uzupełnij SMTP i API_TOKEN (np. `openssl rand -hex 24`)
docker compose up -d
curl "http://HOST:8000/health"
```

Obraz `ghcr.io/norbiox/url2epub` buduje GitHub Actions przy każdym pushu na `master` (amd64 i arm64). Jeśli wolisz budować lokalnie, w `docker-compose.yml` zamień `image:` na `build: .`.

Dla Gmaila potrzebujesz hasła aplikacji (Konto Google → Bezpieczeństwo → Hasła aplikacji).

**Jednorazowo:** dodaj `MAIL_FROM` do zaufanych nadawców w PocketBook Cloud
(albo potwierdź pierwszy mail, jeśli przyjdzie prośba o weryfikację).

## Endpointy

| Endpoint | Działanie |
|---|---|
| `GET/POST /send?url=...` | pobiera stronę, robi EPUB, wysyła mailem |
| `GET /epub?url=...` | zwraca EPUB do pobrania (podgląd/debug) |
| `GET /health` | `ok` |

Token: nagłówek `X-Token: ...` albo parametr `?token=...`.
`url` może zawierać dodatkowy tekst (np. „Tytuł https://...” z menu Udostępnij). Wyciągany jest pierwszy link.

## Wysyłanie z telefonu

**Android – HTTP Shortcuts**
1. Nowy skrót → Regular Shortcut, metoda `POST`,
   URL: `http://HOST:8000/send?url={share_text}` (zmienna typu „Shared text”, z URL-encode).
2. Nagłówek `X-Token: <API_TOKEN>`.
3. W ustawieniach skrótu włącz „Show in Share menu”. Odpowiedź wyświetlaj jako Toast.

**iOS – Skróty**
1. Skrót z „Pokaż w arkuszu udostępniania”, wejście: URL.
2. Akcja „Pobierz zawartość URL”: `http://HOST:8000/send?url=[Wejście skrótu]`, metoda POST, nagłówek `X-Token`.
3. „Pokaż powiadomienie” z wynikiem.

**Desktop – bookmarklet**
```
javascript:window.open('http://HOST:8000/send?token=TOKEN&url='+encodeURIComponent(location.href))
```

`HOST` to najlepiej adres w Tailnecie. Wtedy działa też poza domem i nie trzeba nic wystawiać publicznie.

## Ograniczenia

- Treść wyciąga readability (jak „Widok czytnika” w Firefoksie). Strony renderowane wyłącznie w JS i paywalle nie zadziałają.
- Obrazy pobiera i osadza pandoc. Gdy któryś się nie pobierze, w książce zostaje alt-tekst.
- Czas odpowiedzi to kilka sekund: żądanie czeka na wysłanie maila, więc od razu widać błąd.
