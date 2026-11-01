export type Category = 'Werbung' | 'Trailer' | 'Film' | 'Intro';
export interface Media {
  id: string;
  name: string;
  path?: string;
  url?: string;
  duration: number;
  category: Category;
  size: number;
  demo?: boolean;
}
export interface Display {
  id: string;
  label: string;
  width: number;
  height: number;
  primary: boolean;
}
export interface Environment {
  desktop: boolean;
  platform: string;
  displays: Display[];
  mpvAvailable: boolean;
  mpvPath: string;
}
export interface Playback {
  status: 'idle' | 'playing' | 'paused' | 'blackout' | 'error' | 'finished';
  index: number;
  position: number;
  duration: number;
  message?: string;
}
export interface Project {
  version: 1;
  title: string;
  library: Media[];
  queue: string[];
  displayId: string;
  audioDevice: string;
  onboarded: boolean;
  startAt: string;
}
export interface ShowOptions {
  items: Media[];
  displayId: string;
  audioDevice?: string;
}
export interface ReadinessCheck {
  id: 'media' | 'player' | 'display';
  label: string;
  ok: boolean;
  message: string;
}
export interface Readiness {
  ready: boolean;
  checks: ReadinessCheck[];
}
export type LightEvent = 'preshow' | 'feature' | 'pause' | 'end';
export interface LightRule {
  enabled: boolean;
  brightness: number;
  transition: number;
}
export interface LightingConfig {
  enabled: boolean;
  baseUrl: string;
  entityId: string;
  hasToken: boolean;
  available: boolean;
  rules: Record<LightEvent, LightRule>;
}
export interface CinemaAPI {
  getEnvironment(): Promise<Environment>;
  chooseMpv(): Promise<Environment>;
  getAudioDevices(): Promise<{ id: string; label: string }[]>;
  importMedia(): Promise<Media[]>;
  checkShow(options: ShowOptions): Promise<Readiness>;
  startShow(options: ShowOptions): Promise<void>;
  pauseShow(): Promise<void>;
  resumeShow(): Promise<void>;
  stopShow(): Promise<void>;
  nextCue(): Promise<void>;
  blackout(): Promise<void>;
  onPlayback(cb: (state: Playback) => void): () => void;
  saveProject(data: Project): Promise<void>;
  loadProject(): Promise<Project | null>;
  scheduleShow(options: (ShowOptions & { at: string }) | null): Promise<void>;
  getLighting(): Promise<LightingConfig>;
  saveLighting(config: LightingConfig & { token?: string }): Promise<LightingConfig>;
  testLightingConnection(): Promise<{ lights: { id: string; label: string }[]; message: string }>;
  previewLighting(event: LightEvent): Promise<{ description: string }>;
  applyLighting(event: LightEvent): Promise<void>;
  onLighting(
    cb: (event: { status: 'success' | 'error' | 'info'; message: string }) => void,
  ): () => void;
}
declare global {
  interface Window {
    cinema?: CinemaAPI;
  }
}
