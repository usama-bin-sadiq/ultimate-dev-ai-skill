"""
Browser Automation - Playwright-based browser automation.
Replaces the MCP stub with real Playwright-based browser automation.
"""
from __future__ import annotations
import asyncio
import json
import base64
import tempfile
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Any, List, Dict, Union

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class BrowserType(Enum):
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


@dataclass
class BrowserConfig:
    browser_type: BrowserType = BrowserType.CHROMIUM
    headless: bool = True
    viewport: Dict[str, int] = field(default_factory=lambda: {"width": 1280, "height": 720})
    user_agent: Optional[str] = None
    timeout_ms: int = 30000
    headless: bool = True


@dataclass
class BrowserResult:
    success: bool
    data: Any = None
    error: Optional[str] = None
    screenshot: Optional[bytes] = None
    logs: List[str] = field(default_factory=list)


class BrowserAutomation:
    """
    Playwright-based browser automation.
    Replaces the MCP chrome-devtools stub with real Playwright automation.
    """
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize Playwright browser."""
        if not PLAYWRIGHT_AVAILABLE:
            return False
        
        try:
            self.playwright = await async_playwright().start()
            browser_type = getattr(self.playwright, self.config.browser_type.value)
            self.browser = await browser_type.launch(headless=self.config.headless)
            self.context = await self.browser.new_context(
                viewport=self.config.viewport,
                user_agent=self.config.user_agent
            )
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.config.timeout_ms)
            self._initialized = True
            return True
        except Exception as e:
            return False
    
    async def navigate(self, url: str, wait_until: str = "networkidle") -> BrowserResult:
        """Navigate to URL."""
        if not self._initialized:
            if not await self.initialize():
                return BrowserResult(success=False, error="Failed to initialize browser")
        
        try:
            response = await self.page.goto(url, wait_until=wait_until)
            return BrowserResult(
                success=True,
                data={"url": self.page.url, "status": response.status if response else None}
            )
        except Exception as e:
            return BrowserResult(success=False, error=str(e))
    
    async def click(self, selector: str) -> BrowserResult:
        """Click element."""
        try:
            await self.page.click(selector)
            return BrowserResult(success=True)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))
    
    async def type_text(self, selector: str, text: str) -> BrowserResult:
        """Type text into element."""
        try:
            await self.page.fill(selector, text)
            return BrowserResult(success=True)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))
    
    async def screenshot(self, full_page: bool = False, path: Optional[str] = None) -> BrowserResult:
        """Take screenshot."""
        try:
            screenshot_bytes = await self.page.screenshot(full_page=full_page, path=path)
            return BrowserResult(success=True, data={"screenshot_path": path}, screenshot=screenshot_bytes)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))
    
    async def evaluate(self, script: str) -> BrowserResult:
        """Evaluate JavaScript in page context."""
        try:
            result = await self.page.evaluate(script)
            return BrowserResult(success=True, data=result)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))
    
    async def wait_for_selector(self, selector: str, timeout: Optional[int] = None) -> BrowserResult:
        """Wait for element to appear."""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout or self.config.timeout_ms)
            return BrowserResult(success=True)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))
    
    async def get_content(self) -> BrowserResult:
        """Get page content."""
        try:
            content = await self.page.content()
            return BrowserResult(success=True, data=content)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))
    
    async def close(self):
        """Close browser and cleanup."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self._initialized = False


# Sync wrapper for sync contexts
class SyncBrowserAutomation:
    """Synchronous wrapper for BrowserAutomation."""
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self._async = BrowserAutomation(config)
        self._loop = None
    
    def _get_loop(self):
        if self._loop is None:
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop
    
    def initialize(self) -> bool:
        return self._get_loop().run_until_complete(self._async.initialize())
    
    def navigate(self, url: str, wait_until: str = "networkidle") -> BrowserResult:
        return self._get_loop().run_until_complete(self._async.navigate(url, wait_until))
    
    def click(self, selector: str) -> BrowserResult:
        return self._get_loop().run_until_complete(self._async.click(selector))
    
    def type_text(self, selector: str, text: str) -> BrowserResult:
        return self._get_loop().run_until_complete(self._async.type_text(selector, text))
    
    def screenshot(self, full_page: bool = False, path: Optional[str] = None) -> BrowserResult:
        return self._get_loop().run_until_complete(self._async.screenshot(full_page, path))
    
    def evaluate(self, script: str) -> BrowserResult:
        return self._get_loop().run_until_complete(self._async.evaluate(script))
    
    def wait_for_selector(self, selector: str, timeout: Optional[int] = None) -> BrowserResult:
        return self._get_loop().run_until_complete(self._async.wait_for_selector(selector, timeout))
    
    def get_content(self) -> BrowserResult:
        return self._get_loop().run_until_complete(self._async.get_content())
    
    def close(self):
        self._get_loop().run_until_complete(self._async.close())


def create_browser_automation(config: Optional[Dict] = None) -> SyncBrowserAutomation:
    """Factory function to create browser automation."""
    return SyncBrowserAutomation(BrowserConfig(**config) if config else BrowserConfig())