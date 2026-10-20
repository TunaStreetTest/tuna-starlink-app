import { useEffect, useState } from "react";

import { acquire } from "../acquire";
import type { Post } from "../feed";

type Props = {
  post: Post | null;
  emptyLabel: string;
  showHint: boolean;
  onLive: () => void;
  generation: number;
};

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

export function LowerThird({ post, emptyLabel, showHint, onLive, generation }: Props) {
  const [visible, setVisible] = useState(false);

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

  const stamp = post ? when(post.at) : "";
  const shown = post ? visible : true;

  return (
    <>
      {showHint ? (
        <button type="button" className="pass" onClick={onLive}>
          new pass
        </button>
      ) : null}
      <div className={shown ? "lower on" : "lower"}>
        <div className="bug">Planet Hack</div>
        {post ? (
          <>
            <h1 className="headline">{post.headline}</h1>
            {post.caption ? <p className="caption">{post.caption}</p> : null}
            <p className="meta">
              {stamp ? <span>{stamp}</span> : null}
              {post.x_url ? (
                <a href={post.x_url} target="_blank" rel="noopener noreferrer">
                  on X
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
