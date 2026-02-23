"""Tests for KernelBrowser cloud browser utility."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.clients.kernel_browser import KernelBrowser, KernelBrowserError


class TestKernelBrowserInit:
    def test_missing_api_key_raises(self):
        with (
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(KernelBrowserError, match="KERNEL_API_KEY"),
        ):
            KernelBrowser()

    def test_explicit_api_key(self):
        kb = KernelBrowser(api_key="test-key")
        assert kb._timeout_ms == 30_000

    def test_env_api_key(self):
        with patch.dict("os.environ", {"KERNEL_API_KEY": "env-key"}):
            kb = KernelBrowser()
            assert kb._timeout_ms == 30_000

    def test_custom_timeout(self):
        kb = KernelBrowser(api_key="test-key", timeout_ms=60_000)
        assert kb._timeout_ms == 60_000


class TestKernelBrowserContextManager:
    @pytest.mark.asyncio
    async def test_context_manager(self):
        async with KernelBrowser(api_key="test-key") as kb:
            assert isinstance(kb, KernelBrowser)


class TestFetchRendered:
    @pytest.mark.asyncio
    async def test_happy_path(self):
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_timeout = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html><body>Rendered</body></html>")

        mock_context = MagicMock()
        mock_context.pages = [mock_page]

        mock_browser = AsyncMock()
        mock_browser.contexts = [mock_context]
        mock_browser.close = AsyncMock()

        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.connect_over_cdp = AsyncMock(
            return_value=mock_browser
        )
        mock_playwright_instance.stop = AsyncMock()

        mock_kernel_browser = MagicMock()
        mock_kernel_browser.session_id = "test-session"
        mock_kernel_browser.cdp_ws_url = "ws://test:1234"

        mock_kernel = AsyncMock()
        mock_kernel.browsers.create = AsyncMock(return_value=mock_kernel_browser)
        mock_kernel.browsers.delete_by_id = AsyncMock()

        with (
            patch(
                "src.clients.kernel_browser.AsyncKernel",
                return_value=mock_kernel,
            ),
            patch(
                "src.clients.kernel_browser.async_playwright",
            ) as mock_pw_fn,
        ):
            mock_pw_fn.return_value.start = AsyncMock(
                return_value=mock_playwright_instance
            )

            kb = KernelBrowser(api_key="test-key")
            html = await kb.fetch_rendered("https://example.com")

        assert html == "<html><body>Rendered</body></html>"
        mock_page.goto.assert_awaited_once_with("https://example.com", timeout=30_000)
        mock_page.wait_for_timeout.assert_awaited_once_with(3000)
        mock_browser.close.assert_awaited_once()
        mock_kernel.browsers.delete_by_id.assert_awaited_once_with("test-session")

    @pytest.mark.asyncio
    async def test_with_wait_selector(self):
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()
        mock_page.wait_for_timeout = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html>OK</html>")

        mock_context = MagicMock()
        mock_context.pages = [mock_page]

        mock_browser = AsyncMock()
        mock_browser.contexts = [mock_context]
        mock_browser.close = AsyncMock()

        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.connect_over_cdp = AsyncMock(
            return_value=mock_browser
        )
        mock_playwright_instance.stop = AsyncMock()

        mock_kernel_browser = MagicMock()
        mock_kernel_browser.session_id = "test-session"
        mock_kernel_browser.cdp_ws_url = "ws://test:1234"

        mock_kernel = AsyncMock()
        mock_kernel.browsers.create = AsyncMock(return_value=mock_kernel_browser)
        mock_kernel.browsers.delete_by_id = AsyncMock()

        with (
            patch(
                "src.clients.kernel_browser.AsyncKernel",
                return_value=mock_kernel,
            ),
            patch(
                "src.clients.kernel_browser.async_playwright",
            ) as mock_pw_fn,
        ):
            mock_pw_fn.return_value.start = AsyncMock(
                return_value=mock_playwright_instance
            )

            kb = KernelBrowser(api_key="test-key")
            await kb.fetch_rendered(
                "https://example.com",
                wait_selector=".content",
            )

        mock_page.wait_for_selector.assert_awaited_once_with(".content", timeout=30_000)

    @pytest.mark.asyncio
    async def test_navigation_error_cleans_up(self):
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock(side_effect=Exception("Navigation timeout"))

        mock_context = MagicMock()
        mock_context.pages = [mock_page]

        mock_browser = AsyncMock()
        mock_browser.contexts = [mock_context]
        mock_browser.close = AsyncMock()

        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.connect_over_cdp = AsyncMock(
            return_value=mock_browser
        )
        mock_playwright_instance.stop = AsyncMock()

        mock_kernel_browser = MagicMock()
        mock_kernel_browser.session_id = "test-session"
        mock_kernel_browser.cdp_ws_url = "ws://test:1234"

        mock_kernel = AsyncMock()
        mock_kernel.browsers.create = AsyncMock(return_value=mock_kernel_browser)
        mock_kernel.browsers.delete_by_id = AsyncMock()

        with (
            patch(
                "src.clients.kernel_browser.AsyncKernel",
                return_value=mock_kernel,
            ),
            patch(
                "src.clients.kernel_browser.async_playwright",
            ) as mock_pw_fn,
        ):
            mock_pw_fn.return_value.start = AsyncMock(
                return_value=mock_playwright_instance
            )

            kb = KernelBrowser(api_key="test-key")
            with pytest.raises(KernelBrowserError, match="Navigation timeout"):
                await kb.fetch_rendered("https://example.com")

        mock_browser.close.assert_awaited_once()
        mock_playwright_instance.stop.assert_awaited_once()
        mock_kernel.browsers.delete_by_id.assert_awaited_once_with("test-session")

    @pytest.mark.asyncio
    async def test_cleanup_failure_does_not_raise(self):
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_timeout = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html>OK</html>")

        mock_context = MagicMock()
        mock_context.pages = [mock_page]

        mock_browser = AsyncMock()
        mock_browser.contexts = [mock_context]
        mock_browser.close = AsyncMock()

        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.connect_over_cdp = AsyncMock(
            return_value=mock_browser
        )
        mock_playwright_instance.stop = AsyncMock()

        mock_kernel_browser = MagicMock()
        mock_kernel_browser.session_id = "test-session"
        mock_kernel_browser.cdp_ws_url = "ws://test:1234"

        mock_kernel = AsyncMock()
        mock_kernel.browsers.create = AsyncMock(return_value=mock_kernel_browser)
        mock_kernel.browsers.delete_by_id = AsyncMock(
            side_effect=Exception("Cleanup failed")
        )

        with (
            patch(
                "src.clients.kernel_browser.AsyncKernel",
                return_value=mock_kernel,
            ),
            patch(
                "src.clients.kernel_browser.async_playwright",
            ) as mock_pw_fn,
        ):
            mock_pw_fn.return_value.start = AsyncMock(
                return_value=mock_playwright_instance
            )

            kb = KernelBrowser(api_key="test-key")
            html = await kb.fetch_rendered("https://example.com")

        assert html == "<html>OK</html>"
