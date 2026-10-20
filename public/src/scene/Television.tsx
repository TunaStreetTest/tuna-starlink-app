import { useEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { RoundedBox } from "@react-three/drei";
import {
  AdditiveBlending,
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
import { createScreenMaterial, curvedScreenGeometry } from "./screen";
import { makeGlow, makeGrille, makeWood } from "./textures";

/** Right-ear aim point. Satellites read this; the set is the only writer. */
export const dishWorld = new Vector3(0.55, 0.9, 0.25);

const tmp = new Vector3();

type Props = {
  url: string | null;
  onTune: () => void;
};

/**
 * Walnut portable, screen on local +z. The camera starts on +z, so the face
 * points at the lens and the right ear is world +x.
 * Cylinder knobs: rotation.x = -π/2 aims the cylinder's +y at the camera (+z).
 */
export function Television({ url, onTune }: Props) {
  const rightEar = useRef<Group>(null);
  const anchor = useRef<Mesh>(null);
  const dishFace = useRef<MeshStandardMaterial>(null);
  const led = useRef<MeshStandardMaterial>(null);
  const glowMat = useRef<MeshBasicMaterial>(null);
  const checked = useRef(false);

  const wood = useMemo(() => makeWood(), []);
  const grille = useMemo(() => makeGrille(), []);
  const glowMap = useMemo(() => makeGlow(), []);
  const screenGeo = useMemo(() => curvedScreenGeometry(0.92, 0.66), []);
  const screenMat = useMemo(() => createScreenMaterial(), []);

  useEffect(() => {
    return () => {
      wood.dispose();
      grille.dispose();
      glowMap.dispose();
      screenGeo.dispose();
      const map = screenMat.uniforms.uMap.value as { dispose?: () => void };
      map.dispose?.();
      screenMat.dispose();
    };
  }, [wood, grille, glowMap, screenGeo, screenMat]);

  useEffect(() => {
    if (!url) return;
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
  }, [url, screenMat]);

  useFrame((state) => {
    const sample = acquire.sample();
    const flicker = sample.snow > 0.35 ? 0.86 + 0.14 * Math.sin(state.clock.elapsedTime * 42) : 1;
    const uniforms = (screenMat as ShaderMaterial).uniforms;
    uniforms.uSnow.value = sample.snow;
    uniforms.uRoll.value = sample.roll;
    uniforms.uPower.value = sample.power * flicker;
    uniforms.uTime.value = state.clock.elapsedTime;

    if (rightEar.current) {
      const wobble = Math.sin(state.clock.elapsedTime * 17) * 0.07 * sample.twitch;
      rightEar.current.rotation.z = -0.62 + wobble;
    }
    if (anchor.current) {
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
      const locked = sample.caption > 0.6 && sample.snow < 0.25;
      led.current.color.set(locked ? "#8dffb0" : "#ffb15a");
      led.current.emissive.set(locked ? "#39ff86" : "#ff8a2a");
      led.current.emissiveIntensity = locked ? 1.4 : 0.7 + sample.snow;
    }
    if (glowMat.current) {
      glowMat.current.opacity = 0.15 + sample.power * (1 - sample.snow) * 0.75;
    }
  });

  return (
    <group
      onClick={(event) => {
        event.stopPropagation();
        onTune();
      }}
      onPointerOver={() => {
        document.body.style.cursor = "pointer";
      }}
      onPointerOut={() => {
        document.body.style.cursor = "";
      }}
    >
      <RoundedBox args={[1.28, 0.94, 0.46]} radius={0.055} smoothness={4} position={[0, 0.02, 0]}>
        <meshStandardMaterial map={wood} roughness={0.62} metalness={0.05} color="#ffffff" />
      </RoundedBox>

      <mesh position={[-0.06, 0.08, 0.228]}>
        <boxGeometry args={[1.02, 0.76, 0.02]} />
        <meshStandardMaterial color="#120e0c" roughness={0.45} metalness={0.08} />
      </mesh>

      <mesh position={[-0.06, 0.08, 0.236]} geometry={screenGeo} material={screenMat} />

      <mesh position={[-0.06, 0.08, 0.2]}>
        <planeGeometry args={[1.35, 1.05]} />
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

      <mesh position={[-0.06, -0.34, 0.236]}>
        <planeGeometry args={[0.78, 0.09]} />
        <meshStandardMaterial map={grille} roughness={0.85} metalness={0.05} />
      </mesh>

      <mesh position={[0.46, -0.02, 0.24]} rotation={[-Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.045, 0.05, 0.045, 18]} />
        <meshStandardMaterial color="#d5dbe1" metalness={0.88} roughness={0.2} />
      </mesh>
      <mesh position={[0.46, -0.16, 0.24]} rotation={[-Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.03, 0.034, 0.04, 16]} />
        <meshStandardMaterial color="#c5ccd2" metalness={0.9} roughness={0.18} />
      </mesh>
      <mesh position={[0.46, -0.3, 0.24]}>
        <sphereGeometry args={[0.012, 12, 12]} />
        <meshStandardMaterial ref={led} color="#ffb15a" emissive="#ff8a2a" emissiveIntensity={0.8} />
      </mesh>

      <mesh position={[-0.4, -0.5, 0.08]}>
        <boxGeometry args={[0.18, 0.045, 0.12]} />
        <meshStandardMaterial color="#1a120e" roughness={0.55} />
      </mesh>
      <mesh position={[0.4, -0.5, 0.08]}>
        <boxGeometry args={[0.18, 0.045, 0.12]} />
        <meshStandardMaterial color="#1a120e" roughness={0.55} />
      </mesh>

      <group position={[0, 0.5, 0]}>
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
  return <pointLight ref={light} position={[-0.06, 0.08, 0.85]} color="#d8fbff" distance={4.5} decay={2} />;
}
