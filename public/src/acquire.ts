/** CRT acquire clock. The screen stays in snow until the JPEG is ready, then plays once. */

export type AcquireSample = {
  snow: number;
  roll: number;
  power: number;
  beam: number;
  twitch: number;
  caption: number;
};

const HOLD: AcquireSample = {
  snow: 1,
  roll: 0.45,
  power: 0.2,
  beam: 1,
  twitch: 1,
  caption: 0,
};

const LOCKED: AcquireSample = {
  snow: 0,
  roll: 0,
  power: 1,
  beam: 0,
  twitch: 0,
  caption: 1,
};

function clamp01(value: number): number {
  return Math.max(0, Math.min(1, value));
}

function smooth(value: number): number {
  const t = clamp01(value);
  return t * t * (3 - 2 * t);
}

export const acquire = {
  imageReady: false,
  reduced: false,
  startedAt: 0,

  trigger() {
    this.imageReady = false;
    this.startedAt = 0;
  },

  markReady() {
    if (this.imageReady) return;
    this.imageReady = true;
    this.startedAt = performance.now();
  },

  sample(now = performance.now()): AcquireSample {
    if (this.reduced && this.imageReady) return LOCKED;
    if (!this.imageReady) return HOLD;
    const t = (now - this.startedAt) / 1000;
    // t = 0 matches HOLD, so the picture does not pop when the JPEG arrives.
    const power = 0.2 + 0.8 * smooth(t / 0.35);
    const snow = t < 0.7 ? 1 : 1 - smooth((t - 0.7) / 0.7);
    const roll = (1 - smooth(t / 1.3)) * 0.45;
    const beam = t < 1.15 ? 1 : 1 - smooth((t - 1.15) / 0.35);
    const caption = smooth((t - 1.35) / 0.35);
    return {
      snow: clamp01(snow),
      roll: Math.max(0, roll),
      power,
      beam: clamp01(beam),
      twitch: clamp01(beam),
      caption: clamp01(caption),
    };
  },
};
