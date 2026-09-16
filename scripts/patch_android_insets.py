from pathlib import Path
import sys


ANDROID_ACTIVITY = r'''package com.scholarpulse.app

import android.graphics.Color
import android.os.Build
import android.os.Bundle
import android.view.ViewGroup
import android.view.WindowInsets
import android.webkit.WebView
import androidx.activity.enableEdgeToEdge
import kotlin.math.roundToInt

class MainActivity : TauriActivity() {
    private var contentWebView: WebView? = null
    private var contentRoot: ViewGroup? = null
    private var currentInsets = WindowInsetValues()

    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        window.statusBarColor = Color.TRANSPARENT
        window.navigationBarColor = Color.TRANSPARENT
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            window.isNavigationBarContrastEnforced = false
        }
        window.decorView.setOnApplyWindowInsetsListener { _, insets ->
            currentInsets = readInsets(insets)
            applyNativeInsets()
            insets
        }
        contentRoot = findViewById(android.R.id.content)
        contentRoot?.setOnApplyWindowInsetsListener { _, insets ->
            currentInsets = readInsets(insets)
            applyNativeInsets()
            insets
        }
        window.decorView.post { window.decorView.requestApplyInsets() }
        contentRoot?.post { refreshInsetsFromRoot() }
    }

    override fun onWebViewCreate(webView: WebView) {
        super.onWebViewCreate(webView)
        contentWebView = webView
        contentRoot = findViewById(android.R.id.content)
        webView.setOnApplyWindowInsetsListener { _, insets ->
            applyNativeInsets()
            insets
        }
        requestInsets(webView)
        webView.postDelayed({ requestInsets(webView) }, 250)
        webView.postDelayed({ requestInsets(webView) }, 900)
        webView.postDelayed({ refreshInsetsFromRoot() }, 1200)
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) {
            window.decorView.post { window.decorView.requestApplyInsets() }
            contentRoot?.post { refreshInsetsFromRoot() }
        }
    }

    private fun requestInsets(webView: WebView) {
        webView.requestApplyInsets()
        window.decorView.requestApplyInsets()
        contentRoot?.requestApplyInsets()
        webView.post {
            refreshInsetsFromRoot()
            applyNativeInsets()
        }
    }

    private fun refreshInsetsFromRoot() {
        val root = contentRoot ?: findViewById<ViewGroup>(android.R.id.content)
        val rootInsets = window.decorView.rootWindowInsets ?: root.rootWindowInsets ?: return
        currentInsets = readInsets(rootInsets)
        applyNativeInsets()
    }

    private fun applyNativeInsets() {
        val root = contentRoot ?: return
        val insets = currentInsets
        root.setPadding(
            toNativePixels(insets.left),
            toNativePixels(insets.top),
            toNativePixels(insets.right),
            toNativePixels(insets.bottom),
        )
        root.clipToPadding = true
        root.clipChildren = true
        contentWebView?.setPadding(0, 0, 0, 0)
    }

    private fun toNativePixels(cssInset: Float): Int {
        return (cssInset * resources.displayMetrics.density).roundToInt()
    }

    private fun readInsets(insets: WindowInsets): WindowInsetValues {
        val density = resources.displayMetrics.density.coerceAtLeast(1f)
        val statusBarFallback = systemDimension("status_bar_height")
        val navigationBarFallback = maxOf(
            systemDimension("navigation_bar_height"),
            systemDimension("navigation_bar_height_gesture"),
        )
        val (left, top, right, bottom) = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            val types = WindowInsets.Type.systemBars() or WindowInsets.Type.displayCutout()
            val visibleBars = insets.getInsets(types)
            val stableBars = insets.getInsetsIgnoringVisibility(types)
            val gestures = insets.getInsetsIgnoringVisibility(WindowInsets.Type.mandatorySystemGestures())
            val tappable = insets.getInsetsIgnoringVisibility(WindowInsets.Type.tappableElement())
            listOf(
                maxOf(visibleBars.left, stableBars.left, gestures.left),
                maxOf(visibleBars.top, stableBars.top),
                maxOf(visibleBars.right, stableBars.right, gestures.right),
                maxOf(visibleBars.bottom, stableBars.bottom, gestures.bottom, tappable.bottom),
            )
        } else {
            @Suppress("DEPRECATION")
            listOf(
                insets.systemWindowInsetLeft,
                insets.systemWindowInsetTop,
                insets.systemWindowInsetRight,
                insets.systemWindowInsetBottom,
            )
        }
        return WindowInsetValues(
            top = maxOf(top, statusBarFallback) / density,
            right = right / density,
            bottom = maxOf(bottom, navigationBarFallback) / density,
            left = left / density,
        )
    }

    private fun systemDimension(name: String): Int {
        val resourceId = resources.getIdentifier(name, "dimen", "android")
        return if (resourceId == 0) 0 else resources.getDimensionPixelSize(resourceId)
    }

    private data class WindowInsetValues(
        val top: Float = 0f,
        val right: Float = 0f,
        val bottom: Float = 0f,
        val left: Float = 0f,
    )
}
'''


def main() -> None:
    android_root = Path(sys.argv[1] if len(sys.argv) > 1 else "src-tauri/gen/android")
    activities = sorted(android_root.rglob("MainActivity.kt"))
    if not activities:
        raise SystemExit(f"No generated MainActivity.kt found under {android_root}")
    activity = activities[0]
    activity.write_text(ANDROID_ACTIVITY, encoding="utf-8")
    print(f"Configured Android system-bar handling in {activity}")


if __name__ == "__main__":
    main()
