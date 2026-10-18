package com.truecost.autopilot.ui.main

import android.annotation.SuppressLint
import android.content.Context
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.view.ViewGroup
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import androidx.navigation3.runtime.NavKey

@SuppressLint("SetJavaScriptEnabled")
@Composable
fun MainScreen(
  onItemClick: ((NavKey) -> Unit)? = null,
  modifier: Modifier = Modifier
) {
  AndroidView(
    modifier = modifier.fillMaxSize(),
    factory = { context ->
      WebView(context).apply {
        layoutParams = ViewGroup.LayoutParams(
          ViewGroup.LayoutParams.MATCH_PARENT,
          ViewGroup.LayoutParams.MATCH_PARENT
        )
        settings.apply {
          javaScriptEnabled = true
          domStorageEnabled = true
          databaseEnabled = true
          allowFileAccess = true
          allowContentAccess = true
          loadWithOverviewMode = true
          useWideViewPort = true
          cacheMode = WebSettings.LOAD_DEFAULT
          builtInZoomControls = false
          displayZoomControls = false
          mediaPlaybackRequiresUserGesture = false
        }
        addJavascriptInterface(AndroidJsBridge(context), "AndroidBridge")
        webViewClient = object : WebViewClient() {
          override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
            return false
          }
        }
        webChromeClient = WebChromeClient()
        loadUrl("file:///android_asset/www/index.html")
      }
    }
  )
}

class AndroidJsBridge(private val context: Context) {
  @JavascriptInterface
  fun showToast(message: String) {
    Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
  }

  @JavascriptInterface
  fun onTabChanged(tabName: String) {
    // Tab tracking callback
  }

  @JavascriptInterface
  fun triggerHaptic(type: String) {
    try {
      val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
        val vibratorManager = context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
        vibratorManager?.defaultVibrator
      } else {
        @Suppress("DEPRECATION")
        context.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
      }
      vibrator?.let { v ->
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
          val effect = when (type) {
            "click" -> VibrationEffect.createPredefined(VibrationEffect.EFFECT_CLICK)
            "heavy" -> VibrationEffect.createPredefined(VibrationEffect.EFFECT_HEAVY_CLICK)
            "success" -> VibrationEffect.createWaveform(longArrayOf(0, 30, 50, 40), -1)
            else -> VibrationEffect.createPredefined(VibrationEffect.EFFECT_TICK)
          }
          v.vibrate(effect)
        } else {
          @Suppress("DEPRECATION")
          v.vibrate(30)
        }
      }
    } catch (_: Exception) {
      // Graceful fallback
    }
  }
}
