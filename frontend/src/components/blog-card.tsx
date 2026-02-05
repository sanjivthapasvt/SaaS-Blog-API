import Link from 'next/link';

import { Blog } from '@/lib/types';

interface BlogCardProps {
  blog: Blog;
}

export function BlogCard({ blog }: BlogCardProps) {
  return (
    <article className="card">
      <p className="meta">
        {blog.author?.username ?? 'Anonymous'} · {new Date(blog.created_at).toLocaleDateString()}
      </p>
      <h2>
        <Link href={`/blogs/${blog.id}`}>{blog.title}</Link>
      </h2>
      {blog.tags?.length ? (
        <ul className="tags">
          {blog.tags.map((tag) => (
            <li key={tag}>{tag}</li>
          ))}
        </ul>
      ) : null}
      <div className="stats">
        <span>❤️ {blog.likes_count ?? 0}</span>
        <span>💬 {blog.comments_count ?? 0}</span>
      </div>
    </article>
  );
}
