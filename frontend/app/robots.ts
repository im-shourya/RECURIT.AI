import { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || 'https://recruitai.shouryaparashar.in'

  return {
    rules: {
      userAgent: '*',
      allow: '/',
      // Every one of these carries a capability token in the path. The routes
      // also set `robots: { index: false }` in their own metadata, because a
      // disallow rule is advisory and only reaches crawlers that read it.
      disallow: ['/dashboard/', '/interview/', '/apply/', '/submit/', '/status/'],
    },
    sitemap: `${baseUrl}/sitemap.xml`,
  }
}
