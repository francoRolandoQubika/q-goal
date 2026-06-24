import { env } from "@q-goal/env/web";

const cache = new Map<number, string>();

/** Threshold values for green-screen chroma-key detection. */
const GREEN_CHANNEL_MIN = 80;
const GREEN_OVER_RED_RATIO = 1.2;
const GREEN_OVER_BLUE_RATIO = 1.2;
/** Alpha multiplier for soft edge pixels (partial green match). */
const EDGE_ALPHA_FACTOR = 0.3;

/**
 * Loads the player's face image from the genai service and returns a data URL
 * with the green-screen background removed via canvas chroma-key knockout.
 *
 * Returns null when the image fails to load, is blocked by CORS, or the
 * environment lacks canvas support. Results are cached per playerId so
 * repeated calls incur no extra network or CPU cost.
 */
export async function getFaceDataUrl(playerId: number): Promise<string | null> {
  const cached = cache.get(playerId);
  if (cached !== undefined) return cached;

  const dataUrl = await loadAndKnockout(playerId);
  if (dataUrl !== null) {
    cache.set(playerId, dataUrl);
  }
  return dataUrl;
}

async function loadAndKnockout(playerId: number): Promise<string | null> {
  const img = await loadImage(`${env.VITE_GENAI_URL}/faces/${playerId}`);
  if (img === null) return null;

  const canvas = document.createElement("canvas");
  canvas.width = img.naturalWidth;
  canvas.height = img.naturalHeight;

  const ctx = canvas.getContext("2d");
  if (ctx === null) return null;

  ctx.drawImage(img, 0, 0);

  let imageData: ImageData;
  try {
    imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  } catch (err) {
    if (err instanceof DOMException && err.name === "SecurityError") {
      return null;
    }
    return null;
  }

  applyChromaKey(imageData);
  ctx.putImageData(imageData, 0, 0);

  return canvas.toDataURL("image/png");
}

/**
 * Mutates the pixel buffer in-place, removing green-dominant pixels.
 * Edge pixels that only partially match the green criteria receive a soft
 * alpha (feathering) rather than full transparency, producing smoother cutout
 * borders without a hard staircase edge.
 */
function applyChromaKey(imageData: ImageData): void {
  const data = imageData.data;

  for (let i = 0; i < data.length; i += 4) {
    const r = data[i] ?? 0;
    const g = data[i + 1] ?? 0;
    const b = data[i + 2] ?? 0;

    const isGreenOverRed = g > r * GREEN_OVER_RED_RATIO;
    const isGreenOverBlue = g > b * GREEN_OVER_BLUE_RATIO;
    const isGreenBright = g > GREEN_CHANNEL_MIN;

    const matchCount = [isGreenOverRed, isGreenOverBlue, isGreenBright].filter(Boolean).length;

    if (matchCount === 3) {
      data[i + 3] = 0;
    } else if (matchCount === 2) {
      const currentAlpha = data[i + 3] ?? 255;
      data[i + 3] = Math.round(currentAlpha * EDGE_ALPHA_FACTOR);
    }
  }
}

async function loadImage(src: string): Promise<HTMLImageElement | null> {
  return new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => resolve(img);
    img.onerror = () => resolve(null);
    img.src = src;
  });
}
