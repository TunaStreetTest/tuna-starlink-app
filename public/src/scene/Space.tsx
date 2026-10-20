import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import {
  BufferAttribute,
  BufferGeometry,
  Group,
  Mesh,
  MeshBasicMaterial,
  Vector3,
} from "three";

import { acquire } from "../acquire";
import { dishWorld } from "./Television";

const UP = new Vector3(0, 1, 0);
const satWorld = new Vector3();
const mid = new Vector3();
const dir = new Vector3();

function aimCylinder(mesh: Mesh, from: Vector3, to: Vector3) {
  dir.subVectors(to, from);
  const length = Math.max(dir.length(), 0.001);
  mid.copy(from).add(to).multiplyScalar(0.5);
  mesh.position.copy(mid);
  mesh.scale.set(1, length, 1);
  dir.multiplyScalar(1 / length);
  mesh.quaternion.setFromUnitVectors(UP, dir);
}

function Starfield() {
  const geometry = useMemo(() => {
    const count = 1600;
    const position = new Float32Array(count * 3);
    const color = new Float32Array(count * 3);
    for (let i = 0; i < count; i += 1) {
      const radius = 16 + Math.random() * 36;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      position[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      position[i * 3 + 1] = radius * Math.cos(phi);
      position[i * 3 + 2] = radius * Math.sin(phi) * Math.sin(theta);
      const cyan = Math.random() > 0.84;
      color[i * 3] = cyan ? 0.45 : 0.9;
      color[i * 3 + 1] = cyan ? 0.95 : 0.9;
      color[i * 3 + 2] = cyan ? 1 : 0.86;
    }
    const geo = new BufferGeometry();
    geo.setAttribute("position", new BufferAttribute(position, 3));
    geo.setAttribute("color", new BufferAttribute(color, 3));
    return geo;
  }, []);

  return (
    <points geometry={geometry}>
      <pointsMaterial
        size={0.05}
        sizeAttenuation
        vertexColors
        depthWrite={false}
        transparent
        opacity={0.92}
        toneMapped={false}
      />
    </points>
  );
}

function Satellites() {
  const train = useRef<Group>(null);
  const lock = useRef<Group>(null);
  const beam = useRef<Mesh>(null);
  const beamMat = useRef<MeshBasicMaterial>(null);
  const origin = useRef<Vector3 | null>(null);
  const moved = useRef(false);

  const seats = useMemo(() => {
    return Array.from({ length: 8 }, (_, index) => {
      const angle = (index / 8) * Math.PI * 2;
      return {
        key: index,
        lock: index === 2,
        position: [
          Math.cos(angle) * 2.4,
          1.55 + Math.sin(angle * 2) * 0.15,
          Math.sin(angle) * 1.6 - 0.6,
        ] as [number, number, number],
      };
    });
  }, []);

  useFrame((state) => {
    if (train.current && !acquire.reduced) {
      train.current.rotation.y = state.clock.elapsedTime * 0.05;
    }
    const sample = acquire.sample();
    if (lock.current && beam.current && beamMat.current) {
      lock.current.getWorldPosition(satWorld);
      aimCylinder(beam.current, satWorld, dishWorld);
      beamMat.current.opacity = 0.05 + sample.beam * 0.9;
      beam.current.visible = sample.beam > 0.04;
      if (!origin.current) origin.current = satWorld.clone();
      if (!moved.current && !acquire.reduced && state.clock.elapsedTime > 1.2 && origin.current) {
        moved.current = true;
        const traveled = origin.current.distanceTo(satWorld);
        console.assert(traveled > 0.05, `satellite train froze (${traveled.toFixed(3)})`);
      }
    }
  });

  return (
    <>
      <group ref={train}>
        {seats.map((seat) => (
          <group key={seat.key} position={seat.position} ref={seat.lock ? lock : undefined}>
            <mesh>
              <boxGeometry args={[0.16, 0.04, 0.06]} />
              <meshStandardMaterial
                color="#d7dee4"
                metalness={0.72}
                roughness={0.22}
                emissive={seat.lock ? "#8ef6ff" : "#123"}
                emissiveIntensity={seat.lock ? 0.35 : 0.05}
              />
            </mesh>
            <mesh position={[0.14, 0, 0]}>
              <boxGeometry args={[0.1, 0.012, 0.07]} />
              <meshStandardMaterial color="#b9ecff" emissive="#39e7ff" emissiveIntensity={0.55} />
            </mesh>
            <mesh position={[-0.14, 0, 0]}>
              <boxGeometry args={[0.1, 0.012, 0.07]} />
              <meshStandardMaterial color="#b9ecff" emissive="#39e7ff" emissiveIntensity={0.55} />
            </mesh>
          </group>
        ))}
      </group>
      <mesh ref={beam} visible={false}>
        <cylinderGeometry args={[0.006, 0.006, 1, 6]} />
        <meshBasicMaterial
          ref={beamMat}
          color="#7af6ff"
          transparent
          opacity={0}
          depthWrite={false}
          toneMapped={false}
        />
      </mesh>
    </>
  );
}

export function Space() {
  return (
    <>
      <Starfield />
      <mesh rotation={[1.15, 0.25, 0.35]}>
        <torusGeometry args={[6.4, 0.008, 8, 180]} />
        <meshBasicMaterial color="#3ce7ff" transparent opacity={0.38} toneMapped={false} />
      </mesh>
      <mesh rotation={[1.4, -0.35, 0.1]}>
        <torusGeometry args={[7.3, 0.004, 8, 160]} />
        <meshBasicMaterial color="#ff4ec8" transparent opacity={0.22} toneMapped={false} />
      </mesh>
      <Satellites />
    </>
  );
}
