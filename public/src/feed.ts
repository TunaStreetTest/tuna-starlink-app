import { useEffect, useState } from "react";

export type Post = {
  id: string;
  headline: string;
  caption: string;
  at: string;
  image: string;
  x_url?: string;
};

export type FeedState = {
  posts: Post[];
  loaded: boolean;
  error: string | null;
};

export function useFeed(): FeedState {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let stop = false;

    async function pull() {
      try {
        const res = await fetch("/feed.json", { cache: "no-store" });
        if (!res.ok) throw new Error(`feed ${res.status}`);
        const body = (await res.json()) as { posts?: Post[] };
        if (stop) return;
        setPosts(Array.isArray(body.posts) ? body.posts : []);
        setError(null);
      } catch (err) {
        if (stop) return;
        setError(err instanceof Error ? err.message : "feed");
      } finally {
        if (!stop) setLoaded(true);
      }
    }

    void pull();
    const id = window.setInterval(() => void pull(), 20_000);
    return () => {
      stop = true;
      window.clearInterval(id);
    };
  }, []);

  return { posts, loaded, error };
}
