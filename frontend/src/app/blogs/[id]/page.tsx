import Link from 'next/link';
import { notFound } from 'next/navigation';

import { fetchBlogById } from '@/lib/api';

export default async function BlogDetailsPage({ params }: { params: { id: string } }) {
  try {
    const blog = await fetchBlogById(params.id);

    return (
      <article className="detail">
        <Link href="/">← Back to blogs</Link>
        <h1>{blog.title}</h1>
        <p className="meta">
          {blog.author?.username ?? 'Anonymous'} · {new Date(blog.created_at).toLocaleDateString()}
        </p>
        <div className="content">{blog.content}</div>
      </article>
    );
  } catch {
    notFound();
  }
}
