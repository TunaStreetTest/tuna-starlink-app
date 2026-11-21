import { useEffect } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { Float, OrbitControls } from "@react-three/drei";
import { ACESFilmicToneMapping, PerspectiveCamera, Vector3 } from "three";

import { acquire } from "../acquire";
import { useNarrow } from "../useMedia";
import { Space } from "./Space";
import { Television } from "./Television";

const TARGET = new Vector3(0, 0.12, 0);
const _offset = new Vector3();

function restDistance(narrow: boolean): number {
  const z = narrow ? 5.55 : 3.95;
  return Math.hypot(0.12, 0.08, z);
}

/**
 * Close-in distance along the current orbit.
 * Face kept on screen is about 1.45 wide by 1.16 tall.
 * max() stops at the first edge that would clip, so the longer side
 * still has sky. Checked face-on: fov 32 aspect 1.78 lands near 2.02,
 * screen top around NDC y 0.90, knobs around y -0.70.
 */
function plateDistance(fovDeg: number, aspect: number): number {
  const tanV = Math.tan(((fovDeg * Math.PI) / 180) / 2);
  const byHeight = 1.16 / (2 * tanV);
  const byWidth = 1.45 / (2 * tanV * Math.max(aspect, 0.45));
  return Math.max(byHeight, byWidth);
}

function FrameCamera({ open }: { open: boolean }) {
  const narrow = useNarrow();
  const camera = useThree((state) => state.camera);
  const controls = useThree((state) => state.controls);
  const size = useThree((state) => state.size);

  useEffect(() => {
    const fov = narrow ? 40 : 32;
    if (camera instanceof PerspectiveCamera) {
      camera.fov = fov;
      camera.near = 0.1;
      camera.far = 90;
      camera.updateProjectionMatrix();
    }
    const orbit = controls as { target: Vector3; minDistance: number; update: () => void } | null;
    if (orbit) orbit.target.copy(TARGET);
    const aspect = size.width / Math.max(size.height, 1);
    const dist = open ? plateDistance(fov, aspect) : restDistance(narrow);
    _offset.copy(camera.position).sub(TARGET);
    if (_offset.lengthSq() < 1e-4) _offset.set(0.12, 0.08, 1);
    _offset.setLength(dist);
    camera.position.copy(TARGET).add(_offset);
    camera.lookAt(TARGET);
    if (orbit) {
      orbit.minDistance = open ? 1.35 : narrow ? 3.7 : 2.85;
      orbit.update();
    }
  }, [open, narrow, camera, controls, size.width, size.height]);

  return null;
}

type StageProps = {
  url: string | null;
  canBack: boolean;
  canForward: boolean;
  open: boolean;
  onOpen: () => void;
  onClose: () => void;
  onBack: () => void;
  onForward: () => void;
};

export function Stage({ url, canBack, canForward, open, onOpen, onClose, onBack, onForward }: StageProps) {
  const narrow = useNarrow();
  const reduced = acquire.reduced;
  const set = (
    <Television
      url={url}
      canBack={canBack}
      canForward={canForward}
      onOpen={onOpen}
      onBack={onBack}
      onForward={onForward}
    />
  );

  return (
    <Canvas
      camera={{ position: [0.12, 0.2, narrow ? 5.55 : 3.95], fov: narrow ? 40 : 32, near: 0.1, far: 90 }}
      dpr={[1, 1.75]}
      gl={{
        antialias: true,
        toneMapping: ACESFilmicToneMapping,
        toneMappingExposure: 1.15,
      }}
      onPointerMissed={() => {
        if (open) onClose();
      }}
    >
      <color attach="background" args={["#070812"]} />
      <FrameCamera open={open} />
      <hemisphereLight args={["#2a3a52", "#120c09", 0.7]} />
      <directionalLight position={[3.2, 4.2, 5]} intensity={2.4} color="#ffe6cc" />
      <directionalLight position={[-3.5, 1.4, 2]} intensity={0.7} color="#9fdfff" />
      <directionalLight position={[-2, 2.2, -3]} intensity={0.85} color="#37d6ff" />
      <Space />
      {reduced ? (
        set
      ) : (
        <Float speed={0.7} rotationIntensity={0.1} floatIntensity={0.28} floatingRange={[-0.04, 0.05]}>
          {set}
        </Float>
      )}
      <OrbitControls
        makeDefault
        enablePan={false}
        autoRotate={!reduced}
        autoRotateSpeed={0.32}
        enableDamping
        dampingFactor={0.08}
        minDistance={open ? 1.35 : narrow ? 3.7 : 2.85}
        maxDistance={8}
        minPolarAngle={Math.PI / 2 - 0.42}
        maxPolarAngle={Math.PI / 2 + 0.32}
        target={[0, 0.12, 0]}
      />
    </Canvas>
  );
}
