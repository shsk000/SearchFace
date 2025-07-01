// app/sitemap.xml/route.ts

export async function GET() {
  const baseUrl = "https://www.sokkuri-av.lol";

  const urls = [
    {
      loc: baseUrl,
      lastmod: new Date().toISOString(),
      changefreq: "daily",
      priority: 1.0,
    },
    {
      loc: `${baseUrl}/actresses`,
      lastmod: new Date().toISOString(),
      changefreq: "weekly",
      priority: 0.8,
    },
  ];

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls
  .map(
    (url) => `<url>
  <loc>${url.loc}</loc>
  <lastmod>${url.lastmod}</lastmod>
  <changefreq>${url.changefreq}</changefreq>
  <priority>${url.priority}</priority>
</url>`,
  )
  .join("\n")}
</urlset>`;

  return new Response(xml, {
    headers: {
      "Content-Type": "application/xml",
    },
  });
}
