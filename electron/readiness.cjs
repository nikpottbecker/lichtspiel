const { preflight, validMpv } = require('./mpv.cjs');

async function checkShowReadiness(
  show,
  { displayList, mpvPath, checkFiles = preflight, checkPlayer = validMpv },
) {
  const [media, playerReady] = await Promise.all([
    checkFiles(show?.items).then(
      () => ({ ok: true, message: `${show.items.length} Medien lesbar` }),
      (error) => ({ ok: false, message: error.message }),
    ),
    checkPlayer(mpvPath),
  ]);
  const selectedDisplay =
    typeof show?.displayId === 'string'
      ? displayList.find((display) => display.id === show.displayId)
      : undefined;
  const checks = [
    { id: 'media', label: 'Medien', ...media },
    {
      id: 'player',
      label: 'Wiedergabe',
      ok: playerReady,
      message: playerReady ? 'mpv ist verfügbar' : 'mpv in der Einrichtung auswählen',
    },
    {
      id: 'display',
      label: 'Ausgabe',
      ok: !!selectedDisplay,
      message: selectedDisplay?.label || 'Beamer / Bildschirm auswählen oder neu erkennen',
    },
  ];
  return { ready: checks.every((check) => check.ok), checks };
}

module.exports = { checkShowReadiness };
