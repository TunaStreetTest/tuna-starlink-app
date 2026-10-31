import { useEffect, useRef } from "react";

import type { Post } from "../feed";

type Props = {
  post: Post;
  onClose: () => void;
};

export function Popout({ post, onClose }: Props) {
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    closeRef.current?.focus();
  }, [post.id]);

  return (
    <div className="pop" role="dialog" aria-modal="true" aria-label={post.headline} onClick={onClose}>
      <button ref={closeRef} type="button" className="pop-close" onClick={onClose}>
        Close
      </button>
      <figure className="pop-frame" onClick={(event) => event.stopPropagation()}>
        <img src={post.image} alt={post.headline} />
        <figcaption>{post.headline}</figcaption>
      </figure>
    </div>
  );
}
