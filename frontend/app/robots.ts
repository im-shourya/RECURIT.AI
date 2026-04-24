import { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || 'https://recuritai.shouryaparashar.in'

  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: ['/dashboard/', '/interview/', '/apply/'],
    },
    sitemap: `${baseUrl}/sitemap.xml`,
  }
}
