"""Cloud browser utility using Kernel (kernel.sh).

Provides rendered HTML fetching for JS-heavy sites like Pokecabook
and Pokekameshi. Uses Kernel's cloud browsers via Playwright CDP
so we don't need browser binaries in our Cloud Run container.
"""

import logging
import os
from typing import Self

from kernel import AsyncKernel
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


class KernelBrowserError(Exception):
    """Exception raised for Kernel browser errors."""


class KernelBrowser:
    """Async cloud browser client using Kernel.

    Creates ephemeral browser sessions via Kernel's API,
    connects via Playwright CDP, and returns rendered HTML.

    Usage::

        async with KernelBrowser() as kb:
            html = await kb.fetch_rendered("https://example.com")
    """

    def __init__(
        self,
        api_key: str | None = None,
        timeout_ms: int = 30_000,
    ):
        key = api_key or os.environ.get("KERNEL_API_KEY")
        if not key:
            raise KernelBrowserError("KERNEL_API_KEY environment variable is required")
        self._kernel = AsyncKernel(api_key=key)
        self._timeout_ms = timeout_ms

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        pass

    async def fetch_rendered(
        self,
        url: str,
        wait_selector: str | None = None,
        wait_ms: int = 3000,
    ) -> str:
        """Navigate to URL, wait for content, return rendered HTML.

        Args:
            url: Full URL to fetch.
            wait_selector: Optional CSS selector to wait for before
                capturing HTML.
            wait_ms: Milliseconds to wait after navigation or selector
                match for JS rendering to complete.

        Returns:
            Rendered page HTML as a string.

        Raises:
            KernelBrowserError: On browser creation, navigation, or
                timeout failures.
        """
        kernel_browser = None
        playwright = None
        browser = None

        try:
            kernel_browser = await self._kernel.browsers.create()
            logger.info(
                "kernel_browser_created session_id=%s url=%s",
                kernel_browser.session_id,
                url,
            )

            playwright = await async_playwright().start()
            browser = await playwright.chromium.connect_over_cdp(
                kernel_browser.cdp_ws_url
            )

            context = (
                browser.contexts[0] if browser.contexts else await browser.new_context()
            )
            page = context.pages[0] if context.pages else await context.new_page()

            await page.goto(url, timeout=self._timeout_ms)

            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=self._timeout_ms)

            if wait_ms > 0:
                await page.wait_for_timeout(wait_ms)

            html = await page.content()

            logger.info(
                "kernel_browser_fetched url=%s length=%d",
                url,
                len(html),
            )
            return html

        except KernelBrowserError:
            raise
        except Exception as e:
            raise KernelBrowserError(
                f"Failed to fetch rendered content from {url}: {e}"
            ) from e
        finally:
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()
            if kernel_browser:
                try:
                    await self._kernel.browsers.delete_by_id(kernel_browser.session_id)
                    logger.debug(
                        "kernel_browser_deleted session_id=%s",
                        kernel_browser.session_id,
                    )
                except Exception:
                    logger.warning(
                        "kernel_browser_cleanup_failed session_id=%s",
                        kernel_browser.session_id,
                        exc_info=True,
                    )
