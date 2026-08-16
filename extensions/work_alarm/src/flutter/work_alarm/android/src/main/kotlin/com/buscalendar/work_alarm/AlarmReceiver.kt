package com.buscalendar.work_alarm

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log

class AlarmReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != AlarmScheduler.ACTION_ALARM_FIRED) return

        val alarmId = intent.getStringExtra("alarm_id").orEmpty()
        val requestCode = intent.getIntExtra("request_code", -1)
        Log.i(TAG, "alarm received alarm_id=$alarmId request_code=$requestCode")

        val serviceIntent = Intent(context, AlarmRingingService::class.java).apply {
            action = AlarmRingingService.ACTION_START_RINGING
            putExtra("alarm_id", alarmId)
            putExtra("request_code", requestCode)
            putExtra("trigger_at", intent.getLongExtra("trigger_at", 0L))
            putExtra("payload", intent.getStringExtra("payload"))
        }

        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(serviceIntent)
            } else {
                context.startService(serviceIntent)
            }
            Log.i(TAG, "service start requested alarm_id=$alarmId")
        } catch (error: Exception) {
            val reason =
                "alarm_receiver_service_start_failed:${error.javaClass.simpleName}:${error.message.orEmpty()}"
            Log.e(TAG, reason, error)
            AlarmStore(context).recordFailure(reason, System.currentTimeMillis())
        }
        // 발생한 항목은 여기서 삭제하지 않는다. 다음 Python reconcile에서 정리한다.
    }

    companion object {
        private const val TAG = "AlarmReceiver"
    }
}
