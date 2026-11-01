export const categories = ['Werbung', 'Trailer', 'Film', 'Intro'];
export function durationLabel(value) {
  const seconds = Math.max(0, Math.floor(Number(value) || 0));
  return [Math.floor(seconds / 3600), Math.floor(seconds / 60) % 60, seconds % 60]
    .map((n) => String(n).padStart(2, '0'))
    .join(':');
}
export function moveItem(items, from, to) {
  if (from < 0 || to < 0 || from >= items.length || to >= items.length) return items;
  const copy = [...items];
  const [item] = copy.splice(from, 1);
  copy.splice(to, 0, item);
  return copy;
}
export function validateShow(items, displayId) {
  if (!items.length) return 'Füge zuerst Medien zu deinem Ablauf hinzu.';
  if (!displayId) return 'Wähle zuerst eine Ausgabe aus.';
  if (items.some((item) => item.demo))
    return 'Der Beispielablauf enthält keine Videos. Ersetze die Beispiele durch eigene Medien.';
  if (items.some((item) => !item.path && !item.url))
    return 'Eine Mediendatei ist nicht mehr verfügbar. Importiere sie erneut.';
  if (items.some((item) => !Number.isFinite(item.duration) || item.duration <= 0))
    return 'Die Laufzeit einer Datei konnte nicht gelesen werden. Importiere eine abspielbare Videodatei.';
  return null;
}
export function scheduledTime(value, now = Date.now()) {
  const time = new Date(value).getTime();
  if (!Number.isFinite(time) || time <= now)
    throw new Error('Die Startzeit muss in der Zukunft liegen.');
  return time;
}
