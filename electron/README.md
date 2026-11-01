# Desktop engine

`main.cjs` is the Electron entry point. `preload.cjs` exposes only the typed-by-convention
`window.cinema` methods used by the renderer. The renderer does not have Node access.
During development set `VITE_DEV_SERVER_URL=http://localhost:5173`; packaged builds
load `../dist/index.html`.

## Player

Install mpv separately on each computer. No mpv binary or upstream source is bundled.
macOS Homebrew installations (`/opt/homebrew/bin/mpv` and `/usr/local/bin/mpv`), the
system PATH, and a manually selected executable are supported. Windows accepts
`mpv.exe` via PATH, `C:\mpv`, or the file picker. The executable is checked with
`--version`; media duration is probed with a separate silent mpv process.

The external mpv process receives commands through local JSON IPC (named pipe on
Windows, Unix socket on macOS/Linux). `--no-config` isolates playback from unrelated
user mpv settings. The process is closed when the app closes. Selected audio devices
are queried from mpv; `auto` follows the system output.

The output screen index uses Electron's OS display order. mpv and Electron do not
share display identifiers. **Verify screen assignment with a test clip on every
macOS/Windows setup**, especially after connecting or moving monitors. This is an
implementation foundation, not a claim of verified multi-monitor hardware support.

`blackout()` pauses playback and audio, hides subtitles, and sets brightness to -100.
`resumeShow()` restores brightness and subtitles and continues playback. It is not
a projector shutter command. There is currently no independent live monitor stream
from mpv; media URLs are available for a separate file preview in the renderer.

EOF advances to the next file. This is not guaranteed frame-perfect or gapless; clips
may have different frame rates, codecs, audio formats, and hardware startup costs.
The app supports ordinary local video files, not encrypted DCP/KDM playback.

## Scheduling and persistence

`scheduleShow({...show, at: ISODate})` arms one start; `scheduleShow(null)` cancels it.
The app must remain open. A sleep blocker is active for armed or running shows.
Starts more than 10 seconds late are skipped, and an active show is never interrupted.
Schedules are intentionally not restored on app launch. Errors are sent through
`onPlayback`; a skipped schedule does not alter a running show's playback status.

`saveProject` writes JSON atomically in Electron's userData directory and serializes
concurrent autosaves. `loadProject` returns `null` for a fresh installation. Media are
referenced at their original locations rather than copied; preflight checks every
file before playback. Moving a file therefore requires reimporting it.

## Checks

```sh
node --test electron/*.test.cjs
```

Tests cover chunked IPC parsing, scheduling exactly once, overdue/occupied handling,
cancellation, invalid dates, and missing media preflight. Actual video, audio,
multi-display output and installation require a separate smoke test on macOS and
Windows with mpv installed.

Additional development smoke check: Linux mpv 0.40.0 read the duration of a real
2-second H.264 MP4 correctly. A headless run using null audio/video outputs passed
start, pause, blackout, resume, next clip, natural finish, and stop through real
JSON IPC. This checks the process/transport path, not visible monitor output or
audible sound. Duration probing uses one frame because zero frames skips playback
initialization; the duration marker must remain enabled at INFO log level.

## Home Assistant lighting

The optional lighting integration is disabled initially. Save the Home Assistant
base address and a long-lived access token, run the read-only connection test, then
select a `light.*` entity and enable the desired rules. Light groups can be configured
in Home Assistant and selected like individual lights. No third-party cloud service
is required by this implementation.

`testLightingConnection()` requests only `GET /api/` and `GET /api/states` and never
changes devices. `previewLighting(event)` describes a saved rule without networking.
`applyLighting(event)` is the explicit physical test: enabled rules send Home
Assistant's `light.turn_on` service with brightness percent, or `light.turn_off` when
brightness is zero. Both include the configured transition in seconds; the selected
light must support dimming/transitions for those effects to work.

When enabled, automatic rules run on actual playback status or clip changes:
advertisement/trailer/intro → preshow, category `Film` → feature, pause → pause,
natural finish or user stop → end. Resume reapplies the current clip rule. Repeated
playback position events do not send duplicate commands. Blackout and playback
errors do not raise the lights. Quitting the app cancels outstanding requests;
it is not a guaranteed end-light action, so stop the show before closing the app.

Requests are serialized, expire after four seconds, and lighting errors are reported
separately without blocking video playback. Commands queued for an outdated
configuration or playback state are skipped. Changes cannot undo commands already
received by Home Assistant.

Tokens and their server origin are encrypted together with Electron `safeStorage`
and written separately to `lighting.json` in userData. They never enter the renderer
or project JSON. Linux's `basic_text` fallback is rejected; macOS/Windows use the OS
credential protection supplied by Electron. A server change requires a fresh token.
URLs cannot contain credentials, paths, queries, or fragments. Requests use the
configured origin only and refuse redirects. HTTP is supported for local installations;
use HTTPS when the network is not trusted.

Lighting tests use a mocked Home Assistant endpoint and a test encryption adapter.
They cover read-only checks, no-op previews, origin binding, no plaintext fallback,
service payloads, transitions/deduplication, timeouts, and non-blocking failures.
No physical lights are changed by the test suite.
