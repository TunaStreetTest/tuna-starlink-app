import { useEffect } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { Float, OrbitControls } from "@react-three/drei";
import { ACESFilmicToneMapping, PerspectiveCamera } from "three";

import { acquire } from "../acquire";
import { useNarrow } from "../useMedia";
import { Space } from "./Space";
import { Television } from "./Television";

function FrameCamera() {
  const narrow = useNarrow();
  const camera = useThree((state) => state.camera);

  useEffect(() => {
    camera.position.set(0.12, 0.14, narrow ? 6.5 : 4.55);
    if (camera instanceof PerspectiveCamera) {
      camera.fov = narrow ? 40 : 32;
      camera.near = 0.1;
      camera.far = 90;
      camera.updateProjectionMatrix();
    }
    camera.lookAt(0, 0.02, 0);
  }, [camera, narrow]);

  return null;
}

type StageProps = {
  url: string | null;
  onTune: () => void;
};

export function Stage({ url, onTune }: StageProps) {
  const narrow = useNarrow();
  const reduced = acquire.reduced;
  const set = <Television url={url} onTune={onTune} />;

  return (
    <Canvas
      camera={{ position: [0.12, 0.14, narrow ? 6.5 : 4.55], fov: narrow ? 40 : 32, near: 0.1, far: 90 }}
      dpr={[1, 1.75]}
      gl={{
        antialias: true,
        toneMapping: ACESFilmicToneMapping,
        toneMappingExposure: 1.15,
      }}
    >
      <color attach="background" args={["#070812"]} />
      <FrameCamera />
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
        enablePan={false}
        autoRotate={!reduced}
        autoRotateSpeed={0.32}
        enableDamping
        dampingFactor={0.08}
        minDistance={narrow ? 4.2 : 3.15}
        maxDistance={8}
        minPolarAngle={Math.PI / 2 - 0.42}
        maxPolarAngle={Math.PI / 2 + 0.32}
        target={[0, 0.02, 0]}
      />
    </Canvas>
  );
}
