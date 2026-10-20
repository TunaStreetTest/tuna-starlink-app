import {
  BufferAttribute,
  DataTexture,
  PlaneGeometry,
  RGBAFormat,
  ShaderMaterial,
  SRGBColorSpace,
  UnsignedByteType,
  type BufferGeometry,
} from "three";

/**
 * Shallow CRT bulge. PlaneGeometry faces +z, and the camera sits on +z,
 * so the displaced center must keep a +z normal (toward the lens).
 */
export function curvedScreenGeometry(width: number, height: number): BufferGeometry {
  const geo = new PlaneGeometry(width, height, 48, 32);
  const pos = geo.attributes.position as BufferAttribute;
  const halfW = width / 2;
  const halfH = height / 2;
  for (let i = 0; i < pos.count; i += 1) {
    const nx = pos.getX(i) / halfW;
    const ny = pos.getY(i) / halfH;
    const bulge = 0.075 * Math.max(0, 1 - nx * nx) * Math.max(0, 1 - ny * ny);
    pos.setZ(i, bulge);
  }
  pos.needsUpdate = true;
  geo.computeVertexNormals();
  const normal = geo.attributes.normal as BufferAttribute;
  let centerZ = 0;
  let best = Infinity;
  for (let i = 0; i < pos.count; i += 1) {
    const dist = pos.getX(i) ** 2 + pos.getY(i) ** 2;
    if (dist < best) {
      best = dist;
      centerZ = normal.getZ(i);
    }
  }
  if (centerZ < 0.5) {
    throw new Error(`screen normal faces away from the camera (${centerZ.toFixed(2)})`);
  }
  return geo;
}

export function blankTexture(): DataTexture {
  const data = new Uint8Array([8, 12, 16, 255]);
  const tex = new DataTexture(data, 1, 1, RGBAFormat, UnsignedByteType);
  tex.colorSpace = SRGBColorSpace;
  tex.needsUpdate = true;
  return tex;
}

const vertexShader = /* glsl */ `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

const fragmentShader = /* glsl */ `
uniform sampler2D uMap;
uniform float uHasMap;
uniform float uSnow;
uniform float uRoll;
uniform float uPower;
uniform float uTime;
varying vec2 vUv;

float hash(vec2 p) {
  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void main() {
  vec2 uv = vUv - 0.5;
  float r2 = dot(uv, uv);
  uv *= 1.0 + 0.08 * r2;
  uv.x += (hash(vec2(uTime, floor(uv.y * 40.0))) - 0.5) * 0.012 * uSnow;
  uv += 0.5;
  uv.y = fract(uv.y + uRoll);

  if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
    gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
    return;
  }

  vec2 off = vec2(0.0008 + 0.005 * uSnow, 0.0);
  float rr = texture2D(uMap, uv + off).r;
  float gg = texture2D(uMap, uv).g;
  float bb = texture2D(uMap, uv - off).b;
  vec3 col = mix(vec3(0.02, 0.05, 0.06), vec3(rr, gg, bb), uHasMap);
  col = pow(max(col, vec3(0.0)), vec3(0.82));

  float scanAmp = mix(0.05, 0.22, uSnow);
  float scan = (1.0 - scanAmp) + scanAmp * sin(uv.y * 640.0 + uTime * 18.0);
  col *= scan;
  float triadAmp = mix(0.03, 0.12, uSnow);
  col *= (1.0 - triadAmp) + triadAmp * sin(uv.x * 860.0);
  col *= mix(2.15, 1.0, uSnow);

  vec2 q = vUv - 0.5;
  float vig = smoothstep(0.98, 0.32, length(q * vec2(1.15, 1.35)));
  col *= vig;

  float n = hash(vec2(floor(uv.x * 160.0), floor(uv.y * 120.0) + floor(uTime * 42.0)));
  col = mix(col, vec3(n * 0.85, n * 0.95, n), clamp(uSnow, 0.0, 1.0) * 0.94);

  float blank = smoothstep(0.012, 0.0, abs(fract(uv.y - uTime * 0.12) - 0.5));
  col = mix(col, vec3(0.9, 0.95, 1.0), blank * uSnow * 0.35);

  float glint = smoothstep(0.2, 0.0, length((q - vec2(-0.22, 0.2)) * vec2(1.1, 1.5)));
  col += vec3(0.35, 0.42, 0.45) * glint * uPower * (1.0 - uSnow) * 0.28;

  col *= uPower;
  gl_FragColor = vec4(col, 1.0);
}
`;

export function createScreenMaterial(): ShaderMaterial {
  const material = new ShaderMaterial({
    uniforms: {
      uMap: { value: blankTexture() },
      uHasMap: { value: 0 },
      uSnow: { value: 1 },
      uRoll: { value: 0.45 },
      uPower: { value: 0.2 },
      uTime: { value: 0 },
    },
    vertexShader,
    fragmentShader,
  });
  material.toneMapped = false;
  return material;
}
