import { useEffect, useState } from "react";

import { acquire } from "../acquire";
import type { Post } from "../feed";
import { useCompact } from "../useMedia";

type Props = {
  post: Post | null;
  emptyLabel: string;
  showHint: boolean;
  onLive: () => void;
  hintLabel?: string;
  generation: number;
  /** Plate is open: keep the page text up while the channel changes. */
  hold?: boolean;
  /** Replaces the Planet Hack mark on a dead channel. */
  kicker?: string | null;
  /** Real navigation off a missing plate. A button can leave the address stuck. */
  homeHref?: string | null;
};

function bodyAfterHeadline(headline: string, caption: string): string {
  const parts = caption.split(/\n\s*\n/);
  const first = (parts[0] || "").replace(/\s+/g, " ").trim();
  const head = headline.replace(/\s+/g, " ").trim();
  if (!head || !first) return caption;
  const n = Math.min(40, head.length, first.length);
  if (n >= 24 && (first.slice(0, n) === head.slice(0, n) || head.slice(0, n) === first.slice(0, n))) {
    return parts.slice(1).join("\n\n").trim();
  }
  return caption;
}

function when(iso: string): string {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function LowerThird({
  post,
  emptyLabel,
  showHint,
  onLive,
  hintLabel = "new pass",
  generation,
  hold = false,
  kicker = null,
  homeHref = null,
}: Props) {
  const compact = useCompact();
  const [visible, setVisible] = useState(false);
  const [faultIn, setFaultIn] = useState(false);
  const [captionsOn, setCaptionsOn] = useState(false);

  useEffect(() => {
    if (!kicker) {
      setFaultIn(false);
      return;
    }
    setFaultIn(false);
    const id = window.setTimeout(() => setFaultIn(true), 90);
    return () => window.clearTimeout(id);
  }, [kicker, post?.id, post?.headline]);

  useEffect(() => {
    setVisible(acquire.sample().caption > 0.55);
    let frame = 0;
    const tick = () => {
      const on = acquire.sample().caption > 0.55;
      setVisible((prev) => (prev === on ? prev : on));
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [generation]);

  useEffect(() => {
    setCaptionsOn(false);
  }, [post?.id]);

  const stamp = post ? when(post.at) : "";
  const shown = kicker
    ? faultIn
    : compact
      ? !post || captionsOn
      : hold || (post ? visible : true);
  const sheet = compact && captionsOn && !kicker;
  const caption = post?.caption
    ? sheet
      ? bodyAfterHeadline(post.headline, post.caption)
      : post.caption
    : "";

  return (
    <>
      {compact && post && !kicker ? (
        <button
          type="button"
          className={captionsOn ? "cc on" : "cc"}
          aria-pressed={captionsOn}
          aria-label={captionsOn ? "Hide captions" : "Show captions"}
          onClick={() => setCaptionsOn((open) => !open)}
        >
          CC
        </button>
      ) : null}
      {homeHref ? (
        <a className="pass" href={homeHref}>
          live plates
        </a>
      ) : showHint ? (
        <button type="button" className="pass" onClick={onLive}>
          {hintLabel}
        </button>
      ) : null}
      <div
        className={
          (shown ? (kicker ? "lower on fault" : "lower on") : kicker ? "lower fault" : "lower") +
          (sheet ? " sheet" : "")
        }
      >
        <div className="bug">{kicker ?? "Planet Hack"}</div>
        {post ? (
          <>
            <h1 className="headline">{post.headline}</h1>
            {caption ? <p className="caption">{caption}</p> : null}
            <p className="meta">
              {stamp ? <span>{stamp}</span> : null}
              {post.x_url ? (
                <a href={post.x_url} target="_blank" rel="noopener noreferrer">
                  on X
                </a>
              ) : null}
              {homeHref ? (
                <a className="home" href={homeHref}>
                  The live picture is still on the set.
                </a>
              ) : null}
            </p>
          </>
        ) : (
          <h1 className="headline">{emptyLabel}</h1>
        )}
      </div>
      <p className="sr" aria-live="polite">
        {post?.headline ?? emptyLabel}
      </p>
    </>
  );
}
