package com.buscalendar.work_alarm

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Intent.ACTION_BOOT_COMPLETED &&
            intent.action != Intent.ACTION_MY_PACKAGE_REPLACED
        ) {
            return
        }
        Log.i(TAG, "restore requested action=${intent.action}")

        val pendingResult = goAsync()
        Thread {
            try {
                restoreFutureAlarms(context.applicationContext)
            } catch (error: Exception) {
                Log.e(TAG, "Failed to restore alarms after boot", error)
                AlarmStore(context).recordFailure(
                    "boot_restore_failed:${error.javaClass.simpleName}:${error.message.orEmpty()}",
                )
            } finally {
                pendingResult.finish()
            }
        }.start()
    }

    private fun restoreFutureAlarms(context: Context) {
        val store = AlarmStore(context)
        val scheduler = AlarmScheduler(context)
        val now = System.currentTimeMillis()

        if (!scheduler.canScheduleExactAlarms()) {
            store.recordFailure("boot_restore_exact_alarm_permission_missing")
            return
        }

        var restored = 0
        for (alarm in store.readAlarms()) {
            if (alarm.triggerAt > now && scheduler.schedule(alarm)) {
                restored += 1
                Log.i(TAG, "restored alarm_id=${alarm.alarmId} trigger_at=${alarm.triggerAt}")
            }
        }
        store.clearFailure()
        Log.i(TAG, "Restored $restored future alarms")
    }

    companion object {
        private const val TAG = "WorkAlarmBootReceiver"
    }
}
