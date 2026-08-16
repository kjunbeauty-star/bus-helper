package com.buscalendar.work_alarm

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

class StopAlarmReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != AlarmRingingService.ACTION_STOP_RINGING) return
        val alarmId = intent.getStringExtra("alarm_id").orEmpty()
        Log.i(TAG, "stop requested alarm_id=$alarmId")
        try {
            val stopped = context.stopService(Intent(context, AlarmRingingService::class.java))
            AlarmStore(context).setCurrentAlarm(null)
            Log.i(TAG, "stopService result=$stopped alarm_id=$alarmId")
        } catch (error: Exception) {
            val reason =
                "stop_alarm_failed:${error.javaClass.simpleName}:${error.message.orEmpty()}"
            Log.e(TAG, reason, error)
            AlarmStore(context).recordFailure(reason, System.currentTimeMillis())
        }
    }

    companion object {
        private const val TAG = "StopAlarmReceiver"
    }
}
