import { useCallback, useEffect, useRef, useState } from "react";

import { acquire } from "./acquire";
import { useFeed, type Post } from "./feed";
import { Stage } from "./scene/Scene";
import { LowerThird } from "./ui/LowerThird";
import { Popout } from "./ui/Popout";
import { useReducedMotion } from "./useMedia";

const PLATE_PATH = /^\/p\/([A-Za-z0-9_-]+)\/?$/;
const SHORT_CODE = /^[0-9A-Za-z]{7}$/;

/** Plate token in `/p/<token>`, or null when the path is `/` or not a plate. */
export function currentPlate(pathname: string = window.location.pathname): string | null {
  const match = PLATE_PATH.exec(pathname);
  return match ? match[1] : null;
}

/** Address-bar token. A short code when the feed has one, otherwise the run id. */
export function plateToken(post: Post): string {
  return post.code && SHORT_CODE.test(post.code) ? post.code : post.id;
}

export function findPlate(posts: Post[], token: string): Post | undefined {
  return posts.find((post) => post.id === token || post.code === token);
}

function samePath(pathname: string, path: string): boolean {
  const now = pathname.replace(/\/$/, "") || "/";
  return now === path;
}

export default function App() {
  const feed = useFeed();
  const reduced = useReducedMotion();
  const [channelId, setChannelId] = useState<string | null>(null);
  const [generation, setGeneration] = useState(0);
  const [hint, setHint] = useState(false);
  const [plateOpen, setPlateOpen] = useState(false);
  const postsRef = useRef<Post[]>([]);
  const channelRef = useRef<string | null>(null);
  const newestRef = useRef<string | null>(null);
  // True while the glass is following the newest plate, including the render
  // where a new id has arrived and channelId has not caught up yet.
  const onLive = useRef(true);
  // A deep link is already a history entry. The first tune from `/` replaces it.
  const urlTouched = useRef(currentPlate() !== null);
  const tunedFromUrl = useRef(false);

  postsRef.current = feed.posts;
  channelRef.current = channelId;
  acquire.reduced = reduced;

  const retune = useCallback((id: string) => {
    acquire.trigger();
    setGeneration((value) => value + 1);
    setChannelId(id);
    channelRef.current = id;
  }, []);

  const writePlateUrl = useCallback((id: string, mode: "push" | "replace") => {
    const path = `/p/${id}`;
    if (samePath(window.location.pathname, path)) return;
    urlTouched.current = true;
    const state = { plate: id };
    if (mode === "replace") history.replaceState(state, "", path);
    else history.pushState(state, "", path);
  }, []);

  useEffect(() => {
    const posts = feed.posts;
    if (!posts.length) return;
    if (!tunedFromUrl.current) {
      tunedFromUrl.current = true;
      const wanted = currentPlate();
      const match = wanted ? findPlate(posts, wanted) : undefined;
      if (match) {
        onLive.current = false;
        setChannelId(match.id);
        channelRef.current = match.id;
        const token = plateToken(match);
        if (wanted !== token) writePlateUrl(token, "replace");
        return;
      }
    }
    setChannelId((current) => {
      if (current && posts.some((post) => post.id === current)) return current;
      return posts[0].id;
    });
  }, [feed.posts, writePlateUrl]);

  useEffect(() => {
    const newest = feed.posts[0]?.id ?? null;
    if (!newest) return;
    const previous = newestRef.current;
    newestRef.current = newest;
    if (!previous || previous === newest) return;
    if (onLive.current) {
      retune(newest);
      setHint(false);
      if (currentPlate()) {
        const live = feed.posts.find((post) => post.id === newest);
        if (live) writePlateUrl(plateToken(live), "replace");
      }
      return;
    }
    setHint(true);
  }, [feed.posts, retune, writePlateUrl]);

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
      const mode = urlTouched.current ? "push" : "replace";
      writePlateUrl(plateToken(posts[next]), mode);
    },
    [retune, writePlateUrl],
  );

  const goLive = useCallback(() => {
    const posts = postsRef.current;
    if (!posts.length) return;
    setHint(false);
    onLive.current = true;
    if (currentPlate()) {
      urlTouched.current = true;
      history.pushState({ plate: null }, "", "/");
    }
    if (channelRef.current === posts[0].id) return;
    retune(posts[0].id);
  }, [retune]);

  useEffect(() => {
    function onPop() {
      const posts = postsRef.current;
      const wanted = currentPlate();
      const match = wanted ? findPlate(posts, wanted) : undefined;
      if (match) {
        onLive.current = false;
        setHint(false);
        retune(match.id);
        return;
      }
      if (!posts.length) return;
      onLive.current = true;
      setHint(false);
      if (channelRef.current === posts[0].id) return;
      retune(posts[0].id);
    }
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, [retune]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (!plateOpen) return;
      if (event.key === "Escape" || event.key === "Backspace") {
        event.preventDefault();
        setPlateOpen(false);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [plateOpen]);

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
  const index = feed.posts.findIndex((item) => item.id === channelId);
  const canOlder = index >= 0 && index < feed.posts.length - 1;
  const canNewer = index > 0;
  const emptyLabel = feed.loaded ? "No signal" : "Acquiring";

  return (
    <div className="stage">
      <Stage
        url={post?.image ?? null}
        canOlder={canOlder}
        canNewer={canNewer}
        onOpen={() => post && setPlateOpen(true)}
        onOlder={() => go(1)}
        onNewer={() => go(-1)}
      />
      <div className="vignette" />
      <LowerThird
        post={post}
        emptyLabel={emptyLabel}
        showHint={hint}
        onLive={goLive}
        generation={generation}
      />
      {plateOpen && post ? (
        <Popout post={post} onClose={() => setPlateOpen(false)} />
      ) : null}
    </div>
  );
}
