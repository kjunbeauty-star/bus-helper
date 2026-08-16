package com.buscalendar.work_alarm

import android.app.Activity
import android.content.Intent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.IntentFilter
import android.graphics.Color
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.view.Gravity
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import org.json.JSONObject

class AlarmActivity : Activity() {
    private var alarmId: String = ""
    private val closeReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent?.action == ACTION_CLOSE) finishAndRemoveTask()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            setShowWhenLocked(true)
            setTurnScreenOn(true)
        } else {
            @Suppress("DEPRECATION")
            window.addFlags(
                WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED or
                    WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON,
            )
        }
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(closeReceiver, IntentFilter(ACTION_CLOSE), RECEIVER_NOT_EXPORTED)
        } else {
            @Suppress("DEPRECATION")
            registerReceiver(closeReceiver, IntentFilter(ACTION_CLOSE))
        }
        renderAlarm(intent)
    }

    override fun onDestroy() {
        runCatching { unregisterReceiver(closeReceiver) }
        super.onDestroy()
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        renderAlarm(intent)
    }

    private fun renderAlarm(intent: Intent) {
        alarmId = intent.getStringExtra("alarm_id").orEmpty()
        val payload = parsePayload(intent.getStringExtra("payload"))
        val title = payload.optString("title", "버스캘린더 근무 알람")
        val date = payload.optString("date", "")
        val status = payload.optString("status", "")
        val firstTrip = payload.optString("first_trip", "")
        val memo = payload.optString("memo", "")
        Log.i(TAG, "shown alarm_id=$alarmId")

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(dp(28), dp(36), dp(28), dp(36))
            setBackgroundColor(Color.rgb(15, 23, 42))
        }
        root.addView(label(title, 30f, Color.WHITE, true))
        if (date.isNotBlank()) root.addView(label(date, 20f, Color.LTGRAY, false, 18))
        if (status.isNotBlank()) root.addView(label(status, 34f, Color.rgb(147, 197, 253), true, 28))
        if (firstTrip.isNotBlank()) root.addView(label("첫탕 $firstTrip", 24f, Color.WHITE, true, 14))
        if (memo.isNotBlank()) root.addView(label(memo, 18f, Color.LTGRAY, false, 18))
        root.addView(Button(this).apply {
            text = "알람 끄기"
            textSize = 24f
            setTextColor(Color.WHITE)
            setBackgroundColor(Color.rgb(217, 48, 37))
            setOnClickListener { stopAlarmAndClose() }
            layoutParams = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(72),
            ).apply { topMargin = dp(42) }
        })
        setContentView(root)
    }

    private fun label(
        value: String,
        size: Float,
        color: Int,
        bold: Boolean,
        topMargin: Int = 0,
    ) = TextView(this).apply {
        text = value
        textSize = size
        setTextColor(color)
        gravity = Gravity.CENTER
        if (bold) setTypeface(typeface, android.graphics.Typeface.BOLD)
        layoutParams = LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT,
        ).apply { this.topMargin = dp(topMargin) }
    }

    private fun stopAlarmAndClose() {
        Log.i(TAG, "stop requested alarm_id=$alarmId")
        stopService(Intent(this, AlarmRingingService::class.java))
        AlarmStore(this).setCurrentAlarm(null)
        finishAndRemoveTask()
    }

    @Deprecated("Back closes and stops the active alarm for safety")
    override fun onBackPressed() = stopAlarmAndClose()

    private fun parsePayload(raw: String?): JSONObject = try {
        if (raw.isNullOrBlank()) JSONObject() else JSONObject(raw)
    } catch (_: Exception) {
        JSONObject()
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    companion object {
        private const val TAG = "AlarmActivity"
        const val ACTION_CLOSE = "com.buscalendar.work_alarm.CLOSE_ALARM_ACTIVITY"
    }
}
