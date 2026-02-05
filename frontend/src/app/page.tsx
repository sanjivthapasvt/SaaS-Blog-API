import { BlogCard } from '@/components/blog-card';
import { fetchBlogs } from '@/lib/api';

export default async function HomePage({
  searchParams
}: {
  searchParams?: { search?: string };
}) {
  const search = searchParams?.search;
  const blogs = await fetchBlogs({ search, limit: 12, offset: 0 });

  return (
    <section>
      <div className="heading-row">
        <h1>Latest posts</h1>
        <p>{blogs.total} total posts</p>
      </div>
      {blogs.data.length ? (
        <div className="grid">
          {blogs.data.map((blog) => (
            <BlogCard key={blog.id} blog={blog} />
          ))}
        </div>
      ) : (
        <p>No blogs found.</p>
      )}
    </section>
  );
}
