import { precacheAndRoute } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { StaleWhileRevalidate } from 'workbox-strategies';

// Precache app shell
precacheAndRoute(self.__WB_MANIFEST);

// Cache API responses
registerRoute(
  ({url}) => url.pathname.startsWith('/api'),
  new StaleWhileRevalidate()
);

// Cache audio recordings
registerRoute(
  ({request}) => request.destination === 'audio',
  new CacheFirst()
);