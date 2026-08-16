package com.buscalendar.work_alarm

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log

internal class AlarmScheduler(private val context: Context) {
    private val alarmManager = context.getSystemService(AlarmManager::class.java)

    fun canScheduleExactAlarms(): Boolean =
        Build.VERSION.SDK_INT < Build.VERSION_CODES.S || alarmManager.canScheduleExactAlarms()

    fun schedule(alarm: StoredAlarm): Boolean {
        if (!canScheduleExactAlarms()) {
            Log.w(TAG, "schedule denied alarm_id=${alarm.alarmId} exact_permission=false")
            return false
        }
        val operation = pendingIntent(alarm, PendingIntent.FLAG_UPDATE_CURRENT)
            ?: error("Unable to create alarm PendingIntent")
        alarmManager.setExactAndAllowWhileIdle(
            AlarmManager.RTC_WAKEUP,
            alarm.triggerAt,
            operation,
        )
        Log.i(
            TAG,
            "scheduled alarm_id=${alarm.alarmId} request_code=${alarm.requestCode} trigger_at=${alarm.triggerAt}",
        )
        return true
    }

    fun cancel(alarm: StoredAlarm) {
        val operation = pendingIntent(alarm, PendingIntent.FLAG_NO_CREATE)
        if (operation != null) {
            alarmManager.cancel(operation)
            operation.cancel()
            Log.i(TAG, "cancelled alarm_id=${alarm.alarmId} request_code=${alarm.requestCode}")
        } else {
            Log.i(TAG, "cancel skipped alarm_id=${alarm.alarmId} pending_intent=false")
        }
    }

    private fun pendingIntent(alarm: StoredAlarm, lookupFlag: Int): PendingIntent? {
        val intent = Intent(ACTION_ALARM_FIRED).apply {
            component = ComponentName(context.packageName, ALARM_RECEIVER_CLASS)
            setPackage(context.packageName)
            putExtra("alarm_id", alarm.alarmId)
            putExtra("request_code", alarm.requestCode)
            putExtra("trigger_at", alarm.triggerAt)
            putExtra("payload", alarm.payload.toString())
        }
        return PendingIntent.getBroadcast(
            context,
            alarm.requestCode,
            intent,
            lookupFlag or PendingIntent.FLAG_IMMUTABLE,
        )
    }

    companion object {
        const val ACTION_ALARM_FIRED = "com.buscalendar.work_alarm.ALARM_FIRED"
        const val ALARM_RECEIVER_CLASS = "com.buscalendar.work_alarm.AlarmReceiver"
        private const val TAG = "AlarmScheduler"
    }
}
