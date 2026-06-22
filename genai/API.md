# GenAI API — Endpoint Contracts

Base URL: `http://localhost:8002`

> CORS is fully open (`*`) — call directly from the browser.
> Interactive docs: `http://localhost:8002/docs`

---

## GET `/players/{id}`

Returns full metadata for a player.

**Request**
```
GET /players/1
```

**Response**
```json
{
  "id": 1,
  "name": "Adil Boulbina",
  "team": "algeria",
  "face_path": "faces/algeria/adil_boulbina.jpg",
  "position": "FW",
  "dob": "02/05/2003",
  "club": "Al Duhail SC (QAT)",
  "height_cm": 183,
  "caps": 12,
  "goals": 5
}
```

---

## GET `/faces/{id}`

Returns the player's cropped face image (JPEG, 300×300).

**Request**
```
GET /faces/1
→ image/jpeg
```

Use directly as an image tag — no auth needed:
```html
<img src="http://localhost:8002/faces/1" />
```

---

## POST `/match`

Upload a photo and get the most visually similar WC2026 players.

**Request** — `multipart/form-data`

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `photo` | file | ✓ | — | JPG/PNG photo |
| `model` | string | | `clip` | `facenet` \| `clip` \| `insightface` |
| `top` | int | | `3` | How many matches to return (1–20) |

```bash
curl -X POST http://localhost:8002/match \
  -F "photo=@photo.jpg" \
  -F "model=clip" \
  -F "top=3"
```

**Response**
```json
{
  "model": "clip",
  "matches": [
    {
      "rank": 1,
      "id": 42,
      "name": "Lionel Messi",
      "team": "argentina",
      "face_path": "faces/argentina/lionel_messi.jpg",
      "similarity": 0.8341,
      "position": "FW",
      "dob": "24/06/1987",
      "club": "Inter Miami CF (USA)",
      "height_cm": 169,
      "caps": 200,
      "goals": 120
    }
  ]
}
```

**Errors**
- `400` — requested model not loaded
- `422` — no face detected in the photo

---

## Quiz — Flow

The quiz requires exactly **2 HTTP calls**:

```
1. POST /quiz/start   { "role": "Soy desarrollador backend..." }
        ↓ returns session_id + all 4 questions

2. POST /quiz/answer  { "session_id": "...", "answers": ["A", "B", "C", "D"] }
        ↓ returns 6 player assignments with descriptions + outro
```

Sessions are in-memory — they reset if the server restarts.

---

## POST `/quiz/start`

Generates all 4 questions tailored to the user's role and opens a session.

**Request** — `application/json`
```json
{
  "role": "Soy desarrollador backend, trabajo con Python y APIs REST"
}
```

`role` — free text describing what the person does at Qubika. Examples:
- `"Soy desarrollador frontend, trabajo con React"`
- `"Trabajo como tech lead en el equipo de pagos"`
- `"Soy QA y testeo la app mobile"`
- `"Soy diseñadora UX, me encargo de los prototipos"`

**Response**
```json
{
  "session_id": "89609457-654a-495e-98c5-42bccfcdef98",
  "questions": [
    "Te despertás y te das cuenta que el sistema está caído. ¿Qué hacés? 🤯\nA) ...\nB) ...\nC) ...\nD) ...",
    "Es hora del standup y el PM se pone a hablar de su gato. ¿Cómo reaccionás? 🐱\nA) ...",
    "Tenés que hacer una review de código y te encontrás con un PR de 500 líneas. ¿Qué hacés? 📋\nA) ...",
    "La fecha de entrega se acerca y faltan 10 features por hacer. ¿Cómo manejás la presión? ⏰\nA) ..."
  ],
  "total_questions": 4
}
```

Save `session_id` — required for the next call.

---

## POST `/quiz/answer`

Submits all 4 answers at once and returns the final team.

**Request** — `application/json`
```json
{
  "session_id": "89609457-654a-495e-98c5-42bccfcdef98",
  "answers": ["A", "B", "C", "D"]
}
```

`answers` must have exactly 4 elements (one per question, in order). Values are the letter chosen (`"A"`, `"B"`, `"C"`, or `"D"`).

**Response**
```json
{
  "status": "complete",
  "session_id": "89609457-654a-495e-98c5-42bccfcdef98",
  "outro": "Con este equipo, tu ansiedad se transforma en risas y resiliencia. Son los cracks que, como buen desarrollador, saben que el humor y la meticulosidad son clave para hacer de cada partido en la oficina una victoria.",
  "assignments": [
    {
      "title": "El jugador con el que tomarías una birra 🍺",
      "description": "Harry Kane es el compañero ideal para tomarte una birra; después de un partido, siempre tiene una anécdota para alegrar el día, y seguro sabés que nunca va a esquivar la pregunta sobre el último deployment.",
      "player": {
        "id": 398,
        "name": "Harry Kane",
        "team": "England",
        "face_path": "faces/england/harry_kane.jpg",
        "position": "FW",
        "dob": "28/07/1993",
        "club": "FC Bayern München (GER)",
        "height_cm": 190,
        "caps": 115,
        "goals": 81
      }
    },
    {
      "title": "El jugador con el que resolverías tu peor sprint 💻",
      "description": "Konrad Laimer es el maestro en resolver desastres en la cancha, así que, cuando el código se pone complicado, sabe cómo hacer un sprint hasta la solución sin perder la cabeza.",
      "player": {
        "id": 87,
        "name": "Konrad Laimer",
        "team": "Austria",
        "face_path": "faces/austria/konrad_laimer.jpg",
        "position": "MF",
        "dob": "27/05/1997",
        "club": "FC Bayern München (GER)",
        "height_cm": 180,
        "caps": 58,
        "goals": 7
      }
    },
    {
      "title": "El jugador que deployaría en viernes 🔥",
      "description": "Christopher Bonsu Baah es el que lleva toda la emoción del viernes: viene a la oficina dispuesto a desplegar todo con la misma alegría que un gol en el último minuto, pero, ojo, que no te dé un vuelco el servidor.",
      "player": {
        "id": 475,
        "name": "Christopher Bonsu Baah",
        "team": "Ghana",
        "face_path": "faces/ghana/christopher_bonsu_baah.jpg",
        "position": "FW",
        "dob": "14/12/2004",
        "club": "Al Qadsiah FC (KSA)",
        "height_cm": 172,
        "caps": 9,
        "goals": 0
      }
    },
    {
      "title": "El jugador que haría el standup más largo 🎙️",
      "description": "Alberto Quintero tiene la chispa necesaria para hacer el standup más largo; siempre tiene una historia que contar y, si hay que explicar por qué el código no compila, agarra el micrófono y te lo narra como si fuera un partido épico.",
      "player": {
        "id": 777,
        "name": "Alberto Quintero",
        "team": "Panama",
        "face_path": "faces/panama/alberto_quintero.jpg",
        "position": "MF",
        "dob": "18/12/1987",
        "club": "CD Plaza Amador (PAN)",
        "height_cm": 165,
        "caps": 141,
        "goals": 7
      }
    },
    {
      "title": "El jugador que nunca escribe tests 😅",
      "description": "Ali Alhamadi es el típico que tira el código en producción y se va a tomar un café sin dejar un test; en la oficina, siempre hay un sprint que le queda grande, pero el humor se mantiene, al menos hasta que rompa el sistema.",
      "player": {
        "id": 548,
        "name": "Ali Alhamadi",
        "team": "Iraq",
        "face_path": "faces/iraq/ali_alhamadi.jpg",
        "position": "FW",
        "dob": "01/03/2002",
        "club": "Luton Town FC (ENG)",
        "height_cm": 187,
        "caps": 21,
        "goals": 5
      }
    },
    {
      "title": "El jugador con el que harías pair programming 🧑‍💻",
      "description": "Kieran Tierney es el compañero perfecto para pair programming: sólido en defensa y con una visión clara, sabe cómo mantener la calidad del código y que no te pase como en un partido donde todos van a la carga y nadie defiende.",
      "player": {
        "id": 921,
        "name": "Kieran Tierney",
        "team": "Scotland",
        "face_path": "faces/scotland/kieran_tierney.jpg",
        "position": "DF",
        "dob": "05/06/1997",
        "club": "Celtic FC (SCO)",
        "height_cm": 180,
        "caps": 56,
        "goals": 2
      }
    }
  ]
}
```

**Errors**
- `422` — `answers` array doesn't have exactly 4 elements
- `404` — session not found (expired or server restarted)

---

## Notes

- **Face image URL:** build it as `{VITE_GENAI_URL}/faces/{player.id}` — serves JPEG directly, works as `<img src>`.
- **Quiz questions** are dynamically generated by GPT-4o-mini each session — no two sessions are the same.
- **CORS** is fully open — call from any origin without a proxy.
- **Sessions** are in-memory — if the server restarts mid-quiz, `/quiz/answer` returns `404`. Handle by re-starting the quiz.
