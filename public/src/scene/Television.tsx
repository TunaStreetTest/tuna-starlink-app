import { useEffect, useMemo, useRef } from "react";
import { useFrame, type ThreeEvent } from "@react-three/fiber";
import { RoundedBox } from "@react-three/drei";
import {
  AdditiveBlending,
  CanvasTexture,
  DoubleSide,
  Group,
  Mesh,
  MeshBasicMaterial,
  MeshStandardMaterial,
  PointLight,
  SRGBColorSpace,
  TextureLoader,
  Vector3,
  type ShaderMaterial,
} from "three";

import { acquire } from "../acquire";
import { blankTexture, createScreenMaterial, curvedScreenGeometry } from "./screen";
import { makeGlow, makeGrille, makeWood } from "./textures";

/** Right-ear aim point. Satellites read this; the set is the only writer. */
export const dishWorld = new Vector3(0.55, 0.9, 0.25);

const tmp = new Vector3();

type Props = {
  url: string | null;
  canBack: boolean;
  canForward: boolean;
  onOpen: () => void;
  onBack: () => void;
  onForward: () => void;
  /** Main set reports the dish. A second set in the plate view must not. */
  trackDish?: boolean;
  /** Screen click opens the plate. Off on the plate view itself. */
  openable?: boolean;
  /** Glass can be clicked even when it has no picture. */
  interactive?: boolean;
  /** CRT failure card instead of a plate. */
  cardLines?: string[] | null;
};

/** Failure card for the glass. Cyan on a dark CRT, readable through the scan. */
function cardTexture(lines: string[]): CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = 1280;
  canvas.height = 720;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("failure card");
  ctx.fillStyle = "#05070d";
  ctx.fillRect(0, 0, 1280, 720);
  ctx.strokeStyle = "rgba(126, 240, 255, 0.45)";
  ctx.lineWidth = 3;
  ctx.strokeRect(46, 36, 1188, 648);
  ctx.fillStyle = "rgba(126, 240, 255, 0.05)";
  for (let y = 52; y < 668; y += 4) ctx.fillRect(54, y, 1172, 1);
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  ctx.font = "600 22px ui-monospace, monospace";
  ctx.fillStyle = "#7ef0ff";
  ctx.fillText("STARLINK", 96, 68);
  ctx.fillStyle = "#ff9ad6";
  ctx.fillText("DOWNLINK FAIL", 280, 68);
  for (let i = 0; i < 8; i += 1) {
    ctx.fillStyle = i < 2 ? "#7ef0ff" : "rgba(126, 240, 255, 0.16)";
    ctx.fillRect(980 + i * 26, 70, 16, 18);
  }
  ctx.strokeStyle = "rgba(126, 240, 255, 0.35)";
  ctx.beginPath();
  ctx.moveTo(96, 112);
  ctx.lineTo(1184, 112);
  ctx.stroke();
  let y = 148;
  lines.forEach((line, index) => {
    const title = index === 0;
    ctx.font = title ? "600 72px ui-monospace, monospace" : "34px ui-monospace, monospace";
    ctx.fillStyle = title ? "#7ef0ff" : "#d7f7ff";
    ctx.fillText(line, 96, y);
    y += title ? 96 : line ? 48 : 26;
  });
  const tex = new CanvasTexture(canvas);
  tex.colorSpace = SRGBColorSpace;
  tex.needsUpdate = true;
  return tex;
}

/** White chevron on a clear plate. Material color tints it. */
function chevronMap(dir: -1 | 1): CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = 128;
  canvas.height = 128;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("channel mark");
  ctx.clearRect(0, 0, 128, 128);
  ctx.strokeStyle = "#ffffff";
  ctx.lineWidth = 16;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.beginPath();
  if (dir < 0) {
    ctx.moveTo(88, 26);
    ctx.lineTo(40, 64);
    ctx.lineTo(88, 102);
  } else {
    ctx.moveTo(40, 26);
    ctx.lineTo(88, 64);
    ctx.lineTo(40, 102);
  }
  ctx.stroke();
  const tex = new CanvasTexture(canvas);
  tex.colorSpace = SRGBColorSpace;
  tex.needsUpdate = true;
  return tex;
}

function ChannelKnob({
  position,
  map,
  enabled,
  onPress,
}: {
  position: [number, number, number];
  map: CanvasTexture;
  enabled: boolean;
  onPress: () => void;
}) {
  const press = (event: ThreeEvent<MouseEvent>) => {
    event.stopPropagation();
    if (enabled) onPress();
  };

  return (
    <group position={position}>
      {/* rotation.x = -π/2 aims the cylinder cap at the camera (+z). */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        onClick={press}
        onPointerOver={(event) => {
          event.stopPropagation();
          document.body.style.cursor = enabled ? "pointer" : "";
        }}
        onPointerOut={() => {
          document.body.style.cursor = "";
        }}
      >
        <cylinderGeometry args={[0.044, 0.048, 0.032, 20]} />
        <meshStandardMaterial
          color={enabled ? "#d7dee4" : "#8e969c"}
          metalness={0.88}
          roughness={0.22}
        />
      </mesh>
      <mesh position={[0, 0, 0.018]} raycast={() => null}>
        <circleGeometry args={[0.03, 20]} />
        <meshBasicMaterial color={enabled ? "#12181c" : "#3c4448"} toneMapped={false} />
      </mesh>
      <mesh position={[0, 0, 0.02]} raycast={() => null}>
        <planeGeometry args={[0.046, 0.046]} />
        <meshBasicMaterial
          map={map}
          color={enabled ? "#7ef0ff" : "#4e585e"}
          transparent
          toneMapped={false}
        />
      </mesh>
    </group>
  );
}

/**
 * Walnut portable, screen on local +z. The camera starts on +z, so the face
 * points at the lens and the right ear is world +x. Cabinet depth stays 0.46
 * so the back is still the wood box when the set turns.
 * The screen fills the face. One row under it: < steps back toward the newest
 * plate, > steps forward through the older plates.
 */
export function Television({
  url,
  canBack,
  canForward,
  onOpen,
  onBack,
  onForward,
  trackDish = true,
  openable = true,
  interactive = false,
  cardLines = null,
}: Props) {
  const rightEar = useRef<Group>(null);
  const anchor = useRef<Mesh>(null);
  const dishFace = useRef<MeshStandardMaterial>(null);
  const led = useRef<MeshStandardMaterial>(null);
  const glowMat = useRef<MeshBasicMaterial>(null);
  const checked = useRef(false);

  const wood = useMemo(() => makeWood(), []);
  const grille = useMemo(() => makeGrille(), []);
  const glowMap = useMemo(() => makeGlow(), []);
  const backMark = useMemo(() => chevronMap(-1), []);
  const forwardMark = useMemo(() => chevronMap(1), []);
  const screenGeo = useMemo(() => curvedScreenGeometry(1.24, 0.7), []);
  const screenMat = useMemo(() => createScreenMaterial(), []);

  useEffect(() => {
    return () => {
      wood.dispose();
      grille.dispose();
      glowMap.dispose();
      backMark.dispose();
      forwardMark.dispose();
      screenGeo.dispose();
      const map = screenMat.uniforms.uMap.value as { dispose?: () => void };
      map.dispose?.();
      screenMat.dispose();
    };
  }, [wood, grille, glowMap, backMark, forwardMark, screenGeo, screenMat]);

  const cardKey = cardLines?.join("\n") ?? "";

  useEffect(() => {
    if (!cardKey) return;
    const tex = cardTexture(cardKey.split("\n"));
    const prev = screenMat.uniforms.uMap.value as { dispose?: () => void };
    screenMat.uniforms.uMap.value = tex;
    screenMat.uniforms.uHasMap.value = 1;
    if (prev && prev !== tex) prev.dispose?.();
    return () => {
      if (screenMat.uniforms.uMap.value === tex) {
        screenMat.uniforms.uMap.value = blankTexture();
        screenMat.uniforms.uHasMap.value = 0;
      }
      tex.dispose();
    };
  }, [cardKey, screenMat]);

  useEffect(() => {
    if (cardKey) return;
    if (!url) {
      screenMat.uniforms.uHasMap.value = 0;
      return;
    }
    let cancel = false;
    const loader = new TextureLoader();
    loader.load(url, (tex) => {
      if (cancel) {
        tex.dispose();
        return;
      }
      tex.colorSpace = SRGBColorSpace;
      tex.anisotropy = 8;
      const prev = screenMat.uniforms.uMap.value as { dispose?: () => void };
      screenMat.uniforms.uMap.value = tex;
      screenMat.uniforms.uHasMap.value = 1;
      if (prev && prev !== tex) prev.dispose?.();
      acquire.markReady();
    });
    return () => {
      cancel = true;
    };
  }, [url, cardKey, screenMat]);

  useFrame((state) => {
    const sample = acquire.sample();
    const flicker = sample.snow > 0.35 ? 0.86 + 0.14 * Math.sin(state.clock.elapsedTime * 42) : 1;
    const uniforms = (screenMat as ShaderMaterial).uniforms;
    if (cardKey) {
      uniforms.uSnow.value = 0.04;
      uniforms.uRoll.value = 0;
      uniforms.uPower.value = 1;
    } else {
      uniforms.uSnow.value = sample.snow;
      uniforms.uRoll.value = sample.roll;
      uniforms.uPower.value = sample.power * flicker;
    }
    uniforms.uTime.value = state.clock.elapsedTime;

    if (rightEar.current) {
      const wobble = Math.sin(state.clock.elapsedTime * 17) * 0.07 * sample.twitch;
      rightEar.current.rotation.z = -0.62 + wobble;
    }
    if (trackDish && anchor.current) {
      anchor.current.getWorldPosition(tmp);
      dishWorld.copy(tmp);
      if (!checked.current) {
        checked.current = true;
        // Camera starts on +z, so the strapped dish (right ear) is world +x.
        console.assert(tmp.x > 0.15, `dish should sit on +x, got ${tmp.x.toFixed(2)}`);
      }
    }
    if (dishFace.current) dishFace.current.emissiveIntensity = 0.12 + sample.beam * 2.6;
    if (led.current) {
      const locked = !cardKey && sample.caption > 0.6 && sample.snow < 0.25;
      led.current.color.set(locked ? "#8dffb0" : "#ffb15a");
      led.current.emissive.set(locked ? "#39ff86" : "#ff8a2a");
      led.current.emissiveIntensity = locked ? 1.4 : 0.7 + sample.snow;
    }
    if (glowMat.current) {
      glowMat.current.opacity = 0.15 + sample.power * (1 - sample.snow) * 0.75;
    }
  });

  const openGlass = (event: ThreeEvent<MouseEvent>) => {
    event.stopPropagation();
    if ((url || interactive) && openable) onOpen();
  };

  return (
    <group position={[0, 0.12, 0]} onClick={openGlass}>
      {/* Depth stays 0.46. The back face is this same wood box. */}
      <RoundedBox args={[1.42, 0.98, 0.46]} radius={0.055} smoothness={4} position={[0, 0.04, 0]}>
        <meshStandardMaterial map={wood} roughness={0.62} metalness={0.05} color="#ffffff" />
      </RoundedBox>

      <mesh position={[0, 0.12, 0.228]}>
        <boxGeometry args={[1.3, 0.76, 0.02]} />
        <meshStandardMaterial color="#120e0c" roughness={0.45} metalness={0.08} />
      </mesh>

      <mesh
        position={[0, 0.12, 0.238]}
        geometry={screenGeo}
        material={screenMat}
        onClick={openGlass}
        onPointerOver={() => {
          if ((url || interactive) && openable) document.body.style.cursor = "pointer";
        }}
        onPointerOut={() => {
          document.body.style.cursor = "";
        }}
      />

      <mesh position={[0, 0.12, 0.2]} raycast={() => null}>
        <planeGeometry args={[1.46, 0.92]} />
        <meshBasicMaterial
          ref={glowMat}
          map={glowMap}
          transparent
          depthWrite={false}
          blending={AdditiveBlending}
          toneMapped={false}
          opacity={0.2}
        />
      </mesh>

      <mesh position={[0, -0.34, 0.238]}>
        <planeGeometry args={[1.16, 0.08]} />
        <meshStandardMaterial map={grille} roughness={0.85} metalness={0.05} />
      </mesh>

      <ChannelKnob position={[-0.22, -0.34, 0.27]} map={backMark} enabled={canBack} onPress={onBack} />
      <ChannelKnob position={[0.22, -0.34, 0.27]} map={forwardMark} enabled={canForward} onPress={onForward} />
      <mesh position={[0.56, -0.34, 0.25]}>
        <sphereGeometry args={[0.012, 12, 12]} />
        <meshStandardMaterial ref={led} color="#ffb15a" emissive="#ff8a2a" emissiveIntensity={0.8} />
      </mesh>

      <mesh position={[-0.48, -0.48, 0.08]}>
        <boxGeometry args={[0.18, 0.045, 0.12]} />
        <meshStandardMaterial color="#1a120e" roughness={0.55} />
      </mesh>
      <mesh position={[0.48, -0.48, 0.08]}>
        <boxGeometry args={[0.18, 0.045, 0.12]} />
        <meshStandardMaterial color="#1a120e" roughness={0.55} />
      </mesh>

      <group position={[0, 0.53, 0]}>
        <group rotation={[0, 0, 0.62]}>
          <mesh position={[0, 0.28, 0]}>
            <cylinderGeometry args={[0.011, 0.011, 0.56, 10]} />
            <meshStandardMaterial color="#e4e8ec" metalness={0.92} roughness={0.16} />
          </mesh>
          <mesh position={[0, 0.57, 0]}>
            <sphereGeometry args={[0.02, 12, 12]} />
            <meshStandardMaterial color="#f4f7f8" metalness={0.84} roughness={0.18} />
          </mesh>
        </group>

        <group ref={rightEar} rotation={[0, 0, -0.62]}>
          <mesh position={[0, 0.28, 0]}>
            <cylinderGeometry args={[0.011, 0.011, 0.56, 10]} />
            <meshStandardMaterial color="#e4e8ec" metalness={0.92} roughness={0.16} />
          </mesh>
          <mesh position={[0.02, 0.26, 0.02]}>
            <cylinderGeometry args={[0.004, 0.004, 0.5, 6]} />
            <meshStandardMaterial color="#1b1d22" roughness={0.55} />
          </mesh>
          <group position={[0, 0.58, 0]} rotation={[-0.55, 0.15, 0]}>
            <mesh>
              <cylinderGeometry args={[0.18, 0.2, 0.045, 24]} />
              <meshStandardMaterial color="#e7eef3" metalness={0.28} roughness={0.32} />
            </mesh>
            <mesh position={[0, 0.024, 0]} rotation={[-Math.PI / 2, 0, 0]} ref={anchor}>
              <circleGeometry args={[0.15, 24]} />
              <meshStandardMaterial
                ref={dishFace}
                color="#14181c"
                emissive="#39f3ff"
                emissiveIntensity={0.45}
                roughness={0.35}
                side={DoubleSide}
              />
            </mesh>
          </group>
        </group>
      </group>

      <ScreenLamp />
    </group>
  );
}

function ScreenLamp() {
  const light = useRef<PointLight>(null);
  useFrame(() => {
    const sample = acquire.sample();
    if (light.current) {
      light.current.intensity = 0.15 + sample.power * (1 - sample.snow) * 6;
    }
  });
  return <pointLight ref={light} position={[0, 0.24, 0.95]} color="#d8fbff" distance={4.5} decay={2} />;
}
