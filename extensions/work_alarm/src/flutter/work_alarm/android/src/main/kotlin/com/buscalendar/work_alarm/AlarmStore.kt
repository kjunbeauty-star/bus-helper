package com.buscalendar.work_alarm

import android.content.Context
import android.util.Log
import org.json.JSONArray
import org.json.JSONObject

internal data class StoredAlarm(
    val alarmId: String,
    val requestCode: Int,
    val triggerAt: Long,
    val payload: JSONObject,
)

internal class AlarmStore(context: Context) {
    private val preferences = context.applicationContext.getSharedPreferences(
        PREFERENCES_NAME,
        Context.MODE_PRIVATE,
    )

    fun readSnapshot(): JSONObject {
        val raw = preferences.getString(KEY_SNAPSHOT, null)
        val snapshot = try {
            if (raw.isNullOrBlank()) emptySnapshot() else JSONObject(raw)
        } catch (_: Exception) {
            emptySnapshot()
        }
        snapshot.put("native_persistence", true)
        snapshot.put("diagnostics", readDiagnostics())
        return snapshot
    }

    fun writeSnapshot(snapshot: JSONObject) {
        val copy = JSONObject(snapshot.toString())
        copy.put("schema_version", copy.optInt("schema_version", 1))
        copy.put("native_persistence", true)
        copy.remove("diagnostics")
        preferences.edit().putString(KEY_SNAPSHOT, copy.toString()).apply()
        Log.i(TAG, "snapshot saved alarms=${copy.optJSONArray("alarms")?.length() ?: 0}")
    }

    fun readAlarms(): List<StoredAlarm> {
        val alarms = readSnapshot().optJSONArray("alarms") ?: JSONArray()
        return buildList {
            for (index in 0 until alarms.length()) {
                val item = alarms.optJSONObject(index) ?: continue
                val alarmId = item.optString("alarm_id")
                val requestCode = item.optInt("request_code", -1)
                val triggerAt = item.optLong("trigger_at", -1L)
                if (alarmId.isNotBlank() && requestCode > 0 && triggerAt > 0L) {
                    add(StoredAlarm(alarmId, requestCode, triggerAt, item))
                }
            }
        }
    }

    fun recordFailure(reason: String, at: Long = System.currentTimeMillis()) {
        preferences.edit()
            .putString(KEY_LAST_FAILURE_REASON, reason)
            .putLong(KEY_LAST_FAILURE_AT, at)
            .apply()
        Log.e(TAG, "failure recorded at=$at reason=$reason")
    }

    fun recordSync(at: Long = System.currentTimeMillis()) {
        preferences.edit().putLong(KEY_LAST_SYNC_AT, at).apply()
    }

    fun setCurrentAlarm(alarmId: String?) {
        val editor = preferences.edit()
        if (alarmId.isNullOrBlank()) editor.remove(KEY_CURRENT_ALARM_ID)
        else editor.putString(KEY_CURRENT_ALARM_ID, alarmId)
        editor.apply()
    }

    fun clearFailure() {
        preferences.edit()
            .remove(KEY_LAST_FAILURE_REASON)
            .remove(KEY_LAST_FAILURE_AT)
            .apply()
    }

    private fun readDiagnostics(): JSONObject = JSONObject().apply {
        put("last_failure_reason", preferences.getString(KEY_LAST_FAILURE_REASON, null))
        put("last_failure_at", preferences.getLong(KEY_LAST_FAILURE_AT, 0L))
        put("last_sync_at", preferences.getLong(KEY_LAST_SYNC_AT, 0L))
        put("current_alarm_id", preferences.getString(KEY_CURRENT_ALARM_ID, null))
    }

    companion object {
        private const val PREFERENCES_NAME = "work_alarm_store"
        private const val KEY_SNAPSHOT = "snapshot_json"
        private const val KEY_LAST_FAILURE_REASON = "last_failure_reason"
        private const val KEY_LAST_FAILURE_AT = "last_failure_at"
        private const val KEY_LAST_SYNC_AT = "last_sync_at"
        private const val KEY_CURRENT_ALARM_ID = "current_alarm_id"
        private const val TAG = "AlarmStore"

        fun emptySnapshot(): JSONObject = JSONObject().apply {
            put("schema_version", 1)
            put("alarms", JSONArray())
            put("native_persistence", true)
        }
    }
}
