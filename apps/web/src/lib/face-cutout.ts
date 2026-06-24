import { env } from "@q-goal/env/web";

const cache = new Map<number, string>();

/**
 * "Greenness" of a pixel = how far its green channel rises above the stronger
 * of red/blue. Background screen pixels score high; skin and hair score low or
 * negative. Two thresholds turn this into a soft matte so edges feather instead
 * of leaving a hard, aliased halo.
 */
const GREEN_KNOCKOUT = 55; // greenness at/above this → fully transparent
const GREEN_KEEP = 18; // greenness at/below this → fully opaque
/**
 * Despill strength. Green light bounces off the screen onto the subject, tinting
 * skin and hair. We pull the green channel back down toward red/blue, keeping a
 * sliver of the excess so the result doesn't look flat.
 */
const DESPILL_RETAIN = 0.15;

/**
 * Loads the player's face image from the genai service and returns a data URL
 * with the green-screen background removed via canvas chroma-key knockout and
 * green-spill suppression.
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
  } catch {
    // Tainted canvas (CORS) or unsupported — caller falls back gracefully.
    return null;
  }

  knockoutGreen(imageData);
  ctx.putImageData(imageData, 0, 0);

  return canvas.toDataURL("image/png");
}

/**
 * Mutates the pixel buffer in place: feathers green-screen pixels to
 * transparent on a greenness ramp and suppresses green spill on everything we
 * keep, so faces don't end up blotched or rimmed with green.
 */
function knockoutGreen(imageData: ImageData): void {
  const data = imageData.data;

  for (let i = 0; i < data.length; i += 4) {
    const r = data[i] ?? 0;
    const g = data[i + 1] ?? 0;
    const b = data[i + 2] ?? 0;

    const maxRB = Math.max(r, b);
    const greenness = g - maxRB;

    // Soft matte: opaque below GREEN_KEEP, transparent above GREEN_KNOCKOUT,
    // linear in between for a feathered edge.
    let alpha = 1;
    if (greenness >= GREEN_KNOCKOUT) {
      alpha = 0;
    } else if (greenness > GREEN_KEEP) {
      alpha = 1 - (greenness - GREEN_KEEP) / (GREEN_KNOCKOUT - GREEN_KEEP);
    }

    if (alpha === 0) {
      data[i + 3] = 0;
      continue;
    }

    // Despill: clamp the green channel toward red/blue so spill on the subject
    // reads as neutral instead of sickly green.
    if (g > maxRB) {
      data[i + 1] = Math.round(maxRB + (g - maxRB) * DESPILL_RETAIN);
    }

    const currentAlpha = data[i + 3] ?? 255;
    data[i + 3] = Math.round(currentAlpha * alpha);
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
