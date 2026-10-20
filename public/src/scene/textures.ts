import { CanvasTexture, RepeatWrapping, SRGBColorSpace, type Texture } from "three";

function canvasTexture(draw: (ctx: CanvasRenderingContext2D, size: number) => void, size = 512): Texture {
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("2d canvas unavailable");
  draw(ctx, size);
  const tex = new CanvasTexture(canvas);
  tex.colorSpace = SRGBColorSpace;
  tex.anisotropy = 8;
  tex.needsUpdate = true;
  return tex;
}

export function makeWood(): Texture {
  const tex = canvasTexture((ctx, size) => {
    ctx.fillStyle = "#4a301c";
    ctx.fillRect(0, 0, size, size);
    for (let i = 0; i < 90; i += 1) {
      const x = Math.random() * size;
      ctx.strokeStyle = `rgba(${70 + Math.random() * 50}, ${36 + Math.random() * 24}, ${16 + Math.random() * 12}, ${0.18 + Math.random() * 0.35})`;
      ctx.lineWidth = 1 + Math.random() * 3.2;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.bezierCurveTo(x + 24, size * 0.33, x - 36, size * 0.66, x + 8, size);
      ctx.stroke();
    }
    for (let i = 0; i < 18; i += 1) {
      ctx.strokeStyle = "rgba(20, 10, 6, 0.18)";
      ctx.lineWidth = 6 + Math.random() * 10;
      const x = Math.random() * size;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x + 12, size);
      ctx.stroke();
    }
  });
  tex.wrapS = RepeatWrapping;
  tex.wrapT = RepeatWrapping;
  return tex;
}

export function makeGrille(): Texture {
  return canvasTexture((ctx, size) => {
    ctx.fillStyle = "#14110f";
    ctx.fillRect(0, 0, size, size);
    ctx.fillStyle = "#2a241e";
    const gap = 14;
    for (let y = 6; y < size; y += gap) {
      for (let x = 6; x < size; x += gap) {
        ctx.beginPath();
        ctx.arc(x, y, 3.2, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }, 128);
}

export function makeGlow(): Texture {
  return canvasTexture((ctx, size) => {
    const g = ctx.createRadialGradient(size / 2, size / 2, size * 0.08, size / 2, size / 2, size * 0.5);
    g.addColorStop(0, "rgba(190, 255, 255, 0.95)");
    g.addColorStop(0.35, "rgba(40, 190, 255, 0.28)");
    g.addColorStop(1, "rgba(0, 0, 0, 0)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, size, size);
  }, 256);
}
