package com.buscalendar.work_alarm

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.media.AudioAttributes
import android.media.MediaPlayer
import android.net.Uri
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.provider.Settings
import android.util.Log
import org.json.JSONObject

class AlarmRingingService : Service() {
    private var mediaPlayer: MediaPlayer? = null
    private var vibrator: Vibrator? = null
    private var wakeLock: PowerManager.WakeLock? = null

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "created")
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action != ACTION_START_RINGING) {
            stopSelf(startId)
            return START_NOT_STICKY
        }

        val alarmId = intent.getStringExtra("alarm_id").orEmpty()
        val requestCode = intent.getIntExtra("request_code", -1)
        val payload = parsePayload(intent.getStringExtra("payload"))
        val title = payload.optString("title", "버스캘린더 근무 알람")
        val message = payload.optString("message", "근무 시간을 확인하세요.")

        try {
            Log.i(TAG, "start requested alarm_id=$alarmId request_code=$requestCode")
            stopRingingResources()
            startForeground(
                NOTIFICATION_ID,
                buildNotification(alarmId, requestCode, title, message, payload),
            )
            Log.i(TAG, "foreground notification started alarm_id=$alarmId")
            acquireWakeLock()
            Log.i(TAG, "wake lock acquired alarm_id=$alarmId")
            if (payload.optBoolean("sound_enabled", true)) {
                startLoopingSound()
                Log.i(TAG, "ringtone started alarm_id=$alarmId")
            } else {
                Log.i(TAG, "ringtone disabled alarm_id=$alarmId")
            }
            if (payload.optBoolean("vibration_enabled", true)) {
                startLoopingVibration()
                Log.i(TAG, "vibration started alarm_id=$alarmId")
            } else {
                Log.i(TAG, "vibration disabled alarm_id=$alarmId")
            }
            Log.i(TAG, "started alarm_id=$alarmId")
            AlarmStore(this).setCurrentAlarm(alarmId)
        } catch (error: Exception) {
            val reason =
                "alarm_ringing_start_failed:${error.javaClass.simpleName}:${error.message.orEmpty()}"
            Log.e(TAG, reason, error)
            AlarmStore(this).recordFailure(reason, System.currentTimeMillis())
            stopRingingResources()
            stopSelf(startId)
        }

        // 사용자가 끈 알람이 시스템에 의해 자동 재시작되는 것을 막는다.
        return START_NOT_STICKY
    }

    override fun onDestroy() {
        Log.i(TAG, "stopping")
        stopRingingResources()
        AlarmStore(this).setCurrentAlarm(null)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            stopForeground(STOP_FOREGROUND_REMOVE)
        } else {
            @Suppress("DEPRECATION")
            stopForeground(true)
        }
        Log.i(TAG, "stopped")
        sendBroadcast(Intent(AlarmActivity.ACTION_CLOSE).setPackage(packageName))
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun parsePayload(raw: String?): JSONObject = try {
        if (raw.isNullOrBlank()) JSONObject() else JSONObject(raw)
    } catch (_: Exception) {
        JSONObject()
    }

    @Suppress("DEPRECATION")
    private fun buildNotification(
        alarmId: String,
        requestCode: Int,
        title: String,
        message: String,
        payload: JSONObject,
    ): Notification {
        val stopIntent = Intent(this, StopAlarmReceiver::class.java).apply {
            action = ACTION_STOP_RINGING
            putExtra("alarm_id", alarmId)
        }
        val stopPendingIntent = PendingIntent.getBroadcast(
            this,
            requestCode xor STOP_REQUEST_CODE_MASK,
            stopIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val fullScreenIntent = Intent(this, AlarmActivity::class.java).apply {
            putExtra("alarm_id", alarmId)
            putExtra("request_code", requestCode)
            putExtra("payload", JSONObject().apply {
                put("title", title)
                put("message", message)
                payload.keys().forEach { key -> put(key, payload.opt(key)) }
            }.toString())
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
        }
        val fullScreenPendingIntent = PendingIntent.getActivity(
            this,
            requestCode xor FULL_SCREEN_REQUEST_CODE_MASK,
            fullScreenIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val smallIcon = applicationInfo.icon.takeIf { it != 0 }
            ?: android.R.drawable.ic_lock_idle_alarm
        val builder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Notification.Builder(this, CHANNEL_ID)
        } else {
            Notification.Builder(this)
        }
        return builder
            .setSmallIcon(smallIcon)
            .setContentTitle(title)
            .setContentText(message)
            .setCategory(Notification.CATEGORY_ALARM)
            .setVisibility(Notification.VISIBILITY_PUBLIC)
            .setPriority(Notification.PRIORITY_MAX)
            .setOngoing(true)
            .setAutoCancel(false)
            .setOnlyAlertOnce(true)
            .setFullScreenIntent(fullScreenPendingIntent, true)
            .addAction(
                Notification.Action.Builder(
                    android.R.drawable.ic_media_pause,
                    "알람 끄기",
                    stopPendingIntent,
                ).build(),
            )
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val channel = NotificationChannel(
            CHANNEL_ID,
            "근무 알람",
            NotificationManager.IMPORTANCE_HIGH,
        ).apply {
            description = "오전·오후 근무 시작 알람"
            setSound(null, null)
            enableVibration(false)
            lockscreenVisibility = Notification.VISIBILITY_PUBLIC
        }
        getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
        Log.i(TAG, "notification channel ready channel_id=$CHANNEL_ID")
    }

    private fun startLoopingSound() {
        val alarmUri = Settings.System.DEFAULT_ALARM_ALERT_URI
            ?: Settings.System.DEFAULT_NOTIFICATION_URI
        mediaPlayer = createLoopingPlayer(alarmUri).also { it.start() }
    }

    private fun createLoopingPlayer(uri: Uri): MediaPlayer = MediaPlayer().apply {
        setAudioAttributes(
            AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_ALARM)
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                .build(),
        )
        isLooping = true
        setDataSource(this@AlarmRingingService, uri)
        prepare()
    }

    @Suppress("DEPRECATION")
    private fun startLoopingVibration() {
        vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            getSystemService(VibratorManager::class.java).defaultVibrator
        } else {
            getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
        }
        val pattern = longArrayOf(0L, 1000L, 500L)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator?.vibrate(VibrationEffect.createWaveform(pattern, 0))
        } else {
            vibrator?.vibrate(pattern, 0)
        }
    }

    private fun acquireWakeLock() {
        val powerManager = getSystemService(PowerManager::class.java)
        wakeLock = powerManager.newWakeLock(
            PowerManager.PARTIAL_WAKE_LOCK,
            "$packageName:WorkAlarmRinging",
        ).apply { acquire() }
    }

    private fun stopRingingResources() {
        mediaPlayer?.runCatching {
            if (isPlaying) stop()
            release()
        }
        mediaPlayer = null
        vibrator?.cancel()
        vibrator = null
        wakeLock?.takeIf { it.isHeld }?.release()
        wakeLock = null
        Log.i(TAG, "ringing resources released")
    }

    companion object {
        const val ACTION_START_RINGING = "com.buscalendar.work_alarm.START_RINGING"
        const val ACTION_STOP_RINGING = "com.buscalendar.work_alarm.STOP_RINGING"
        private const val CHANNEL_ID = "work_alarm_ringing"
        private const val NOTIFICATION_ID = 7301
        private const val STOP_REQUEST_CODE_MASK = 0x5A5A0000
        private const val FULL_SCREEN_REQUEST_CODE_MASK = 0x2F2F0000
        private const val TAG = "AlarmService"
    }
}
