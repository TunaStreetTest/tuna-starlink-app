import { useEffect, useRef } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { ACESFilmicToneMapping, PerspectiveCamera } from "three";

import type { Post } from "../feed";
import { Television } from "../scene/Television";
import { useNarrow } from "../useMedia";

type Props = {
  post: Post;
  canBack: boolean;
  canForward: boolean;
  onBack: () => void;
  onForward: () => void;
  onClose: () => void;
};

/**
 * Face-on close-up of the same set. Camera sits on +z at x=0, so screen-left
 * is world −x (the < knob) and screen-right is world +x (the > knob).
 * Desktop z=2.55 fov 30 keeps the screen top (world y ≈ 0.59) and both knobs
 * (world y ≈ −0.22) inside the canvas. Narrow z=3.35 fov 34 keeps the 1.24-wide
 * screen inside a portrait canvas.
 */
function PopCamera() {
  const narrow = useNarrow();
  const camera = useThree((state) => state.camera);

  useEffect(() => {
    const z = narrow ? 3.35 : 2.55;
    camera.position.set(0, 0.02, z);
    if (camera instanceof PerspectiveCamera) {
      camera.fov = narrow ? 34 : 30;
      camera.near = 0.1;
      camera.far = 40;
      camera.updateProjectionMatrix();
    }
    camera.lookAt(0, 0.02, 0);
  }, [camera, narrow]);

  return null;
}

export function Popout({ post, canBack, canForward, onBack, onForward, onClose }: Props) {
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    closeRef.current?.focus();
  }, [post.id]);

  return (
    <div className="pop" role="dialog" aria-modal="true" aria-label={post.headline}>
      <button ref={closeRef} type="button" className="pop-close" onClick={onClose}>
        Close
      </button>
      <div className="pop-set">
        <Canvas
          camera={{ position: [0, 0.02, 2.55], fov: 30, near: 0.1, far: 40 }}
          dpr={[1, 1.75]}
          gl={{
            antialias: true,
            toneMapping: ACESFilmicToneMapping,
            toneMappingExposure: 1.15,
          }}
        >
          <color attach="background" args={["#070812"]} />
          <PopCamera />
          <hemisphereLight args={["#2a3a52", "#120c09", 0.7]} />
          <directionalLight position={[3.2, 4.2, 5]} intensity={2.4} color="#ffe6cc" />
          <directionalLight position={[-3.5, 1.4, 2]} intensity={0.7} color="#9fdfff" />
          <directionalLight position={[-2, 2.2, -3]} intensity={0.85} color="#37d6ff" />
          <Television
            url={post.image}
            canBack={canBack}
            canForward={canForward}
            onOpen={() => {}}
            onBack={onBack}
            onForward={onForward}
            trackDish={false}
            openable={false}
          />
        </Canvas>
      </div>
    </div>
  );
}
