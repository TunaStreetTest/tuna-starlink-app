import { useCallback, useEffect, useRef, useState } from "react";

import { acquire } from "./acquire";
import { useFeed, type Post } from "./feed";
import { Stage } from "./scene/Scene";
import { LowerThird } from "./ui/LowerThird";
import { useReducedMotion } from "./useMedia";

export default function App() {
  const feed = useFeed();
  const reduced = useReducedMotion();
  const [channelId, setChannelId] = useState<string | null>(null);
  const [generation, setGeneration] = useState(0);
  const [hint, setHint] = useState(false);
  const postsRef = useRef<Post[]>([]);
  const channelRef = useRef<string | null>(null);
  const newestRef = useRef<string | null>(null);
  // True while the glass is following the newest plate, including the render
  // where a new id has arrived and channelId has not caught up yet.
  const onLive = useRef(true);

  postsRef.current = feed.posts;
  channelRef.current = channelId;
  acquire.reduced = reduced;

  const retune = useCallback((id: string) => {
    acquire.trigger();
    setGeneration((value) => value + 1);
    setChannelId(id);
    channelRef.current = id;
  }, []);

  useEffect(() => {
    const posts = feed.posts;
    if (!posts.length) return;
    setChannelId((current) => {
      if (current && posts.some((post) => post.id === current)) return current;
      return posts[0].id;
    });
  }, [feed.posts]);

  useEffect(() => {
    const newest = feed.posts[0]?.id ?? null;
    if (!newest) return;
    const previous = newestRef.current;
    newestRef.current = newest;
    if (!previous || previous === newest) return;
    if (onLive.current) {
      retune(newest);
      setHint(false);
      return;
    }
    setHint(true);
  }, [feed.posts, retune]);

  const go = useCallback(
    (delta: number) => {
      const posts = postsRef.current;
      if (!posts.length) return;
      const index = posts.findIndex((post) => post.id === channelRef.current);
      const base = index < 0 ? 0 : index;
      const next = Math.max(0, Math.min(posts.length - 1, base + delta));
      if (posts[next].id === channelRef.current) return;
      onLive.current = next === 0;
      if (next === 0) setHint(false);
      retune(posts[next].id);
    },
    [retune],
  );

  const goLive = useCallback(() => {
    const posts = postsRef.current;
    if (!posts.length) return;
    setHint(false);
    onLive.current = true;
    if (channelRef.current === posts[0].id) return;
    retune(posts[0].id);
  }, [retune]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "ArrowLeft" || event.key === "ArrowDown") {
        event.preventDefault();
        go(1);
      } else if (event.key === "ArrowRight" || event.key === "ArrowUp") {
        event.preventDefault();
        go(-1);
      } else if (event.key === "Escape" || event.key === "Backspace") {
        event.preventDefault();
        goLive();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [go, goLive]);

  useEffect(() => {
    const posts = postsRef.current;
    const index = posts.findIndex((post) => post.id === channelId);
    [posts[index - 1], posts[index + 1]].forEach((post) => {
      if (!post) return;
      const img = new Image();
      img.src = post.image;
    });
  }, [channelId, feed.posts]);

  const post = feed.posts.find((item) => item.id === channelId) ?? null;
  const emptyLabel = feed.loaded ? "No signal" : "Acquiring";

  return (
    <div className="stage">
      <Stage url={post?.image ?? null} onTune={() => go(1)} />
      <div className="vignette" />
      <LowerThird
        post={post}
        emptyLabel={emptyLabel}
        showHint={hint}
        onLive={goLive}
        generation={generation}
      />
    </div>
  );
}
