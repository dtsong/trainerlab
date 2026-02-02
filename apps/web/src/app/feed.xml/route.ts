import { labNotesApi } from "@/lib/api";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://trainerlab.gg";

export async function GET() {
  try {
    const response = await labNotesApi.list({ limit: 50 });
    const notes = response.items;

    const rssItems = notes
      .map((note) => {
        const pubDate = note.published_at
          ? new Date(note.published_at).toUTCString()
          : new Date(note.created_at).toUTCString();

        return `
    <item>
      <title><![CDATA[${note.title}]]></title>
      <link>${SITE_URL}/lab-notes/${note.slug}</link>
      <guid isPermaLink="true">${SITE_URL}/lab-notes/${note.slug}</guid>
      <pubDate>${pubDate}</pubDate>
      ${note.summary ? `<description><![CDATA[${note.summary}]]></description>` : ""}
      ${note.author_name ? `<author>${note.author_name}</author>` : ""}
      <category>${note.note_type.replace(/_/g, " ")}</category>
    </item>`;
      })
      .join("");

    const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>TrainerLab - Lab Notes</title>
    <link>${SITE_URL}/lab-notes</link>
    <description>Analysis, reports, and insights for competitive Pokemon TCG</description>
    <language>en-us</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <atom:link href="${SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
    ${rssItems}
  </channel>
</rss>`;

    return new Response(rss, {
      headers: {
        "Content-Type": "application/xml",
        "Cache-Control": "public, max-age=3600, s-maxage=3600",
      },
    });
  } catch (error) {
    console.error("Error generating RSS feed:", error);
    return new Response("Error generating feed", { status: 500 });
  }
}
