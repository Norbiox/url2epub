# url2epub

Mała usługa HTTP: dostaje link, zwraca EPUB z artykułem.
Wysyłką (np. na PocketBooka) zajmuje się n8n: gotowy workflow jest w `n8n/`.

```
telefon → [n8n webhook] → GET url2epub/epub?url=… → [n8n Send Email] → …@pbsync.com
```

## API

| Endpoint | Działanie |
|---|---|
| `GET /epub?url=...` | zwraca `application/epub+zip`, nazwa pliku z tytułu strony |
| `GET /health` | `ok` |

- `url` może zawierać dodatkowy tekst (np. „Tytuł https://...” z menu Udostępnij). Brany jest pierwszy link.
- Jeśli ustawisz `API_TOKEN`, trzeba wysłać nagłówek `X-Token` albo parametr `?token=`. Wewnątrz sieci Dockera z n8n nie jest potrzebny.

Treść wyciąga readability, tytuł, autora i datę trafilatura, EPUB składa pandoc (z obrazkami).

## Uruchomienie

Dodaj usługę z `docker-compose.yml` do tego samego projektu compose (albo sieci) co n8n:

```bash
docker compose up -d url2epub
docker compose exec n8n wget -qO- http://url2epub:8000/health
```

Obraz `ghcr.io/norbiox/url2epub` buduje GitHub Actions przy każdym pushu na `master` (amd64 i arm64).
Jeśli wolisz budować lokalnie, użyj `build: .`.

## n8n: Send to PocketBook

1. Zaimportuj `n8n/send-to-pocketbook.json`.
2. **Webhook**: utwórz poświadczenie *Header Auth* (np. `X-Token: <losowy ciąg>`).
3. **Send Email**: utwórz poświadczenie SMTP (np. Gmail z hasłem aplikacji) i ustaw `From`.
4. Aktywuj workflow.
5. Jednorazowo dodaj adres nadawcy do zaufanych w PocketBook Cloud (albo potwierdź pierwszy mail).

Wywołanie:

```bash
curl -X POST -H "X-Token: …" "https://N8N_HOST/webhook/send-to-pocketbook?url=https://example.com/artykul"
```

### Z telefonu

- **Android, HTTP Shortcuts**: skrót `POST` na `https://N8N_HOST/webhook/send-to-pocketbook?url={share_text}` z nagłówkiem `X-Token` i włączonym „Show in Share menu”.
- **iOS, Skróty**: „Pokaż w arkuszu udostępniania” → „Pobierz zawartość URL” (POST, nagłówek `X-Token`) → „Pokaż powiadomienie”.

## Ograniczenia

Strony renderowane wyłącznie w JS i paywalle nie zadziałają.
