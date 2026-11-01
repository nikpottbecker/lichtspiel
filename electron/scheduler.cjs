/** A deliberately one-shot scheduler: an overdue show must never start on wake. */
class ShowScheduler {
  constructor({ start, isBusy, onError, now = Date.now, tolerance = 10000 }) {
    Object.assign(this, { start, isBusy, onError, now, tolerance });
    this.pending = null;
  }
  arm(show) {
    if (show === null) {
      this.pending = null;
      return;
    }
    const time = Date.parse(show?.at);
    if (!Number.isFinite(time) || time <= this.now())
      throw new Error('Wähle eine Startzeit in der Zukunft.');
    this.pending = { ...show, time };
  }
  async tick() {
    if (!this.pending || this.now() < this.pending.time) return;
    const show = this.pending;
    this.pending = null;
    if (this.now() - show.time > this.tolerance) {
      this.onError(
        'Geplante Vorstellung übersprungen: Der Rechner war zur Startzeit nicht bereit. Bitte manuell starten.',
      );
      return;
    }
    if (this.isBusy()) {
      this.onError('Geplante Vorstellung übersprungen: Eine andere Vorstellung läuft bereits.');
      return;
    }
    try {
      await this.start(show);
    } catch (error) {
      this.onError(error.message);
    }
  }
}
module.exports = { ShowScheduler };
